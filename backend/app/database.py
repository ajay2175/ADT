from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.seeds import SEED_CONSTITUTION, SEED_EXPERTS, WEB_SEED_KNOWLEDGE

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SQLITE_PATH = DATA_DIR / "adt_vault.db"
NOW = lambda: datetime.now(UTC).isoformat()


def _pg_conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(settings.adt_database_url, cursor_factory=RealDictCursor)
    conn.autocommit = False
    return conn


@contextmanager
def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if settings.use_postgres:
        connection = _pg_conn()
        try:
            yield PgAdapter(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
    else:
        connection = sqlite3.connect(SQLITE_PATH)
        connection.row_factory = sqlite3.Row
        try:
            yield SqliteAdapter(connection)
            connection.commit()
        finally:
            connection.close()


class SqliteAdapter:
    def __init__(self, conn):
        self.conn = conn
        self.dialect = "sqlite"

    def execute(self, sql: str, params=()):
        return self.conn.execute(sql.replace("%s", "?"), params)

    def executemany(self, sql: str, params):
        return self.conn.executemany(sql.replace("%s", "?"), params)

    def executescript(self, sql: str):
        return self.conn.executescript(sql)


class PgAdapter:
    def __init__(self, conn):
        self.conn = conn
        self.dialect = "postgres"

    def execute(self, sql: str, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, params):
        cur = self.conn.cursor()
        cur.executemany(sql, params)
        return cur

    def executescript(self, sql: str):
        cur = self.conn.cursor()
        for stmt in sql.split(";"):
            s = stmt.strip()
            if s:
                cur.execute(s)


def setup_database() -> None:
    with db() as connection:
        if connection.dialect == "postgres":
            connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS constitution_items (
                  id TEXT PRIMARY KEY, category TEXT NOT NULL, statement TEXT NOT NULL,
                  status TEXT NOT NULL, priority INTEGER NOT NULL, version TEXT NOT NULL,
                  explicitly_confirmed_by_ajay BOOLEAN NOT NULL, created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_items (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, content_type TEXT NOT NULL,
                  summary TEXT NOT NULL, source_class TEXT NOT NULL, status TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                  id TEXT PRIMARY KEY, knowledge_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,
                  content TEXT NOT NULL, embedding vector(1536),
                  FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id)
                )
                """
            )
        else:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS constitution_items (
                  id TEXT PRIMARY KEY, category TEXT NOT NULL, statement TEXT NOT NULL,
                  status TEXT NOT NULL, priority INTEGER NOT NULL, version TEXT NOT NULL,
                  explicitly_confirmed_by_ajay INTEGER NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge_items (
                  id TEXT PRIMARY KEY, title TEXT NOT NULL, content_type TEXT NOT NULL,
                  summary TEXT NOT NULL, source_class TEXT NOT NULL, status TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                  id TEXT PRIMARY KEY, knowledge_id TEXT NOT NULL, chunk_index INTEGER NOT NULL,
                  content TEXT NOT NULL, embedding_json TEXT,
                  FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id)
                );
                """
            )

        for ddl in [
            """
            CREATE TABLE IF NOT EXISTS decision_records (
              id TEXT PRIMARY KEY, question TEXT NOT NULL, context TEXT NOT NULL,
              recommendation TEXT NOT NULL, confidence REAL NOT NULL,
              review_date TEXT, final_decision TEXT, created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_events (
              id TEXT PRIMARY KEY, event_type TEXT NOT NULL, subject_id TEXT NOT NULL,
              payload TEXT NOT NULL, created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS expert_profiles (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, domains TEXT NOT NULL,
              protocol TEXT NOT NULL, status TEXT NOT NULL, version TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS claims (
              id TEXT PRIMARY KEY, knowledge_id TEXT NOT NULL, statement TEXT NOT NULL,
              status TEXT NOT NULL, confidence REAL, evidence_for TEXT NOT NULL,
              evidence_against TEXT NOT NULL, last_reviewed TEXT,
              FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reasoning_records (
              decision_id TEXT PRIMARY KEY, facts_used TEXT NOT NULL, assumptions TEXT NOT NULL,
              experts TEXT NOT NULL, expert_views TEXT NOT NULL, disagreements TEXT NOT NULL,
              aca_risks TEXT NOT NULL, values_applied TEXT NOT NULL, uncertainty TEXT NOT NULL,
              synthesis TEXT NOT NULL,
              FOREIGN KEY(decision_id) REFERENCES decision_records(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS research_programs (
              id TEXT PRIMARY KEY, title TEXT NOT NULL, hypothesis TEXT NOT NULL,
              status TEXT NOT NULL, next_experiment TEXT NOT NULL, evidence_status TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS knowledge_edges (
              id TEXT PRIMARY KEY, from_id TEXT NOT NULL, to_id TEXT NOT NULL,
              relation TEXT NOT NULL, weight REAL NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS graph_nodes (
              id TEXT PRIMARY KEY, node_type TEXT NOT NULL, name TEXT NOT NULL,
              status TEXT NOT NULL, protected INTEGER NOT NULL DEFAULT 0,
              metadata TEXT NOT NULL, created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS graph_relations (
              id TEXT PRIMARY KEY, from_id TEXT NOT NULL, to_id TEXT NOT NULL,
              relation TEXT NOT NULL, weight REAL NOT NULL, status TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """,
        ]:
            if connection.dialect == "sqlite":
                connection.executescript(ddl)
            else:
                connection.execute(ddl)

        _seed_if_empty(connection)
        _seed_graph_mirror(connection)
        _migrate_schema(connection)


def _migrate_schema(connection) -> None:
    """Add Phase-2 columns to existing SQLite databases."""
    if connection.dialect != "sqlite":
        return
    cur = connection.execute("PRAGMA table_info(reasoning_records)")
    cols = {row[1] for row in cur.fetchall()}
    if "expert_views" not in cols:
        connection.execute("ALTER TABLE reasoning_records ADD COLUMN expert_views TEXT DEFAULT '[]'")
    if "synthesis" not in cols:
        connection.execute("ALTER TABLE reasoning_records ADD COLUMN synthesis TEXT DEFAULT ''")


def _seed_if_empty(connection) -> None:
    count = connection.execute("SELECT COUNT(*) AS c FROM constitution_items").fetchone()
    c = count["c"] if isinstance(count, dict) else count[0]
    if c == 0:
        connection.executemany("INSERT INTO constitution_items VALUES (%s, %s, %s, 'approved', %s, '1.0', %s, %s)", [(str(uuid.uuid4()), cat, stmt, pri, True if connection.dialect == "postgres" else 1, NOW()) for cat, stmt, pri in SEED_CONSTITUTION])
    else:
        for cat, stmt, pri in SEED_CONSTITUTION:
            if not connection.execute("SELECT id FROM constitution_items WHERE statement=%s", (stmt,)).fetchone():
                connection.execute("INSERT INTO constitution_items VALUES (%s,%s,%s,'approved',%s,'1.0',%s,%s)", (str(uuid.uuid4()), cat, stmt, pri, True if connection.dialect == "postgres" else 1, NOW()))
    expert_count = connection.execute("SELECT COUNT(*) AS c FROM expert_profiles").fetchone()
    if (expert_count["c"] if isinstance(expert_count, dict) else expert_count[0]) == 0:
        connection.executemany("INSERT INTO expert_profiles VALUES (%s,%s,%s,%s,'active','0.1')", [(eid, name, json.dumps(domains), protocol) for eid, name, domains, protocol in SEED_EXPERTS])
    research_count = connection.execute("SELECT COUNT(*) AS c FROM research_programs").fetchone()
    if (research_count["c"] if isinstance(research_count, dict) else research_count[0]) == 0:
        connection.execute("INSERT INTO research_programs VALUES (%s,%s,%s,'active',%s,'preliminary; replication required')", ("aca_faculty_dissociation", "ACA / AI Faculty Dissociation", "Are AI failures functionally decomposable into distinguishable stages, and does diagnosing the failure stage improve intervention selection?", "Run stage-aware intervention trial against generic correction and process supervision."))
    web_count = connection.execute("SELECT COUNT(*) AS c FROM knowledge_items WHERE source_class='web'").fetchone()
    if (web_count["c"] if isinstance(web_count, dict) else web_count[0]) == 0:
        connection.executemany("INSERT INTO knowledge_items VALUES (%s,%s,%s,%s,%s,'proposed',%s)", [(str(uuid.uuid4()), title, ctype, summary, sclass, NOW()) for title, ctype, summary, sclass in WEB_SEED_KNOWLEDGE])


def _seed_graph_mirror(connection) -> None:
    """Seed only protected Constitution and curated Expert nodes; never infer values."""
    for item in rows_to_dicts(connection.execute("SELECT id, statement FROM constitution_items WHERE status='approved'").fetchall()):
        connection.execute("INSERT INTO graph_nodes (id,node_type,name,status,protected,metadata,created_at) VALUES (%s,'ConstitutionItem',%s,'accepted',1,%s,%s) ON CONFLICT(id) DO NOTHING", (item["id"], item["statement"], "{}", NOW()))
    for expert in rows_to_dicts(connection.execute("SELECT id, name FROM expert_profiles WHERE status='active'").fetchall()):
        connection.execute("INSERT INTO graph_nodes (id,node_type,name,status,protected,metadata,created_at) VALUES (%s,'Expert',%s,'accepted',0,%s,%s) ON CONFLICT(id) DO NOTHING", (expert["id"], expert["name"], "{}", NOW()))


def row_to_dict(row: Any) -> dict:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    return dict(row)


def rows_to_dicts(rows) -> list[dict]:
    return [row_to_dict(r) for r in rows]
