from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "adt_vault.db"
NOW = lambda: datetime.now(UTC).isoformat()

SEED_CONSTITUTION = [
    ("value", "Dharma is the primary compass for consequential decisions.", 100),
    ("goal", "Create durable positive impact across family, leadership, research, and society.", 90),
    ("preference", "Diagnose deeply, act sparingly, align with vision, preserve resilience.", 90),
    ("blind_spot", "Check overextension and under-delegation before committing to new work.", 80),
    ("persona", "Dharma-Governed Systems Inventor: observation → theory → architecture → prototype → validation → refinement → scale.", 85),
    ("role", "Fulfill duties across self, family, physician, leader, citizen, creator and researcher roles.", 95),
    ("guardrail", "Expert analysis is independent; ADT synthesizes through evidence, Ajay values and dharma, while preserving disagreement.", 95),
    ("guardrail", "Never silently convert hypothesis to fact or silently rewrite core Ajay values.", 100),
    ("value", "Truth requires courage; courage requires character. Act with integrity between thought, speech and action.", 95),
    ("value", "Respect shown to others reflects one’s inner standard; seek win-win outcomes where possible.", 85),
    ("preference", "Knowledge without application is incomplete; prefer explainable systems and practical validation.", 85),
    ("leadership", "Lead rather than merely manage; create capability and psychological safety in others.", 90),
    ("wealth", "Treat wealth as capability and trusteeship: preserve family security, freedom to serve, resilience and long-term compounding.", 80),
    ("parenting", "Parenting is dharma: develop character, resilience, independence, humility, capability and purpose without projection.", 90),
    ("guardrail", "Distinguish Ajay believes, classical text states, modern research suggests, and system infers.", 100),
    ("guardrail", "Preserve contradictions, source provenance, uncertainty and versions; do not delete inconvenient evidence.", 100),
    ("guardrail", "For medical or high-impact decisions, state limitations, escalate appropriately and preserve Ajay autonomy.", 100),
]

SEED_EXPERTS = [
    ("dharma_governor", "ADT Dharma Governor", ["values", "ethics", "long_horizon", "governance"], "constitutional synthesis"),
    ("systems_strategy", "Systems & War Strategy", ["strategy", "optionality", "risk", "positioning"], "independent strategic analysis"),
    ("leadership", "Leadership & Organization Design", ["leadership", "people", "hr", "delegation"], "people and capability analysis"),
    ("research_methods", "Research Methods & Statistics", ["research", "statistics", "experiments", "causal_inference"], "study and evidence analysis"),
    ("ai_agi", "AI / AGI / Safety", ["ai", "llm", "agents", "safety", "aca"], "AI architecture and safety analysis"),
    ("ayurveda", "Ayurveda Clinical Expert", ["ayurveda", "vaidya_mitra", "pariksha", "nadi"], "Ayurveda domain analysis; requires clinical governance"),
    ("modern_medicine", "Modern Medicine & Clinical Safety", ["medicine", "clinical", "patient", "diagnosis"], "medical risk and escalation analysis"),
    ("founder", "Founder & Capital Allocation", ["business", "finance", "investing", "product"], "resource and compounding analysis"),
    ("engineering", "Engineering & Physical AI", ["engineering", "robotics", "sensors", "electronics"], "technical feasibility analysis"),
    ("civilizational_codex", "Indic Knowledge Codex", ["vedanta", "yoga", "nyaya", "niti", "classical"], "classical-source interpretation with provenance"),
]

WEB_SEED_KNOWLEDGE = [
    ("NIST AI RMF: governance reference", "web", "NIST AI RMF frames AI risk management around Govern, Map, Measure and Manage. Added as a governance reference; review before use in a production policy.", "web"),
    ("HL7 FHIR interoperability reference", "web", "FHIR specifies healthcare information resources and APIs for interoperability. Added as an interoperability reference for future Vaidya Mitra integrations; not a clinical data implementation.", "web"),
    ("AI-assisted clinical decision support: evidence review", "web", "Clinical AI decision support shows mixed results; its effectiveness depends on clinician and technology design factors. Added as a research reference requiring domain review.", "scientific"),
]


@contextmanager
def db():
    DATA_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def setup_database() -> None:
    with db() as connection:
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
            CREATE TABLE IF NOT EXISTS decision_records (
              id TEXT PRIMARY KEY, question TEXT NOT NULL, context TEXT NOT NULL,
              recommendation TEXT NOT NULL, confidence REAL NOT NULL,
              review_date TEXT, final_decision TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
              id TEXT PRIMARY KEY, event_type TEXT NOT NULL, subject_id TEXT NOT NULL,
              payload TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expert_profiles (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, domains TEXT NOT NULL,
              protocol TEXT NOT NULL, status TEXT NOT NULL, version TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claims (
              id TEXT PRIMARY KEY, knowledge_id TEXT NOT NULL, statement TEXT NOT NULL,
              status TEXT NOT NULL, confidence REAL, evidence_for TEXT NOT NULL,
              evidence_against TEXT NOT NULL, last_reviewed TEXT,
              FOREIGN KEY(knowledge_id) REFERENCES knowledge_items(id)
            );
            CREATE TABLE IF NOT EXISTS reasoning_records (
              decision_id TEXT PRIMARY KEY, facts_used TEXT NOT NULL, assumptions TEXT NOT NULL,
              experts TEXT NOT NULL, disagreements TEXT NOT NULL, aca_risks TEXT NOT NULL,
              values_applied TEXT NOT NULL, uncertainty TEXT NOT NULL,
              FOREIGN KEY(decision_id) REFERENCES decision_records(id)
            );
            CREATE TABLE IF NOT EXISTS research_programs (
              id TEXT PRIMARY KEY, title TEXT NOT NULL, hypothesis TEXT NOT NULL,
              status TEXT NOT NULL, next_experiment TEXT NOT NULL, evidence_status TEXT NOT NULL
            );
            """
        )
        if connection.execute("SELECT COUNT(*) FROM constitution_items").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO constitution_items VALUES (?, ?, ?, 'approved', ?, '1.0', 1, ?)",
                [(str(uuid.uuid4()), category, statement, priority, NOW()) for category, statement, priority in SEED_CONSTITUTION],
            )
        else:
            for category, statement, priority in SEED_CONSTITUTION:
                if not connection.execute("SELECT id FROM constitution_items WHERE statement = ?", (statement,)).fetchone():
                    connection.execute(
                        "INSERT INTO constitution_items VALUES (?, ?, ?, 'approved', ?, '1.0', 1, ?)",
                        (str(uuid.uuid4()), category, statement, priority, NOW()),
                    )
        if connection.execute("SELECT COUNT(*) FROM expert_profiles").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO expert_profiles VALUES (?, ?, ?, ?, 'active', '0.1')",
                [(expert_id, name, json.dumps(domains), protocol) for expert_id, name, domains, protocol in SEED_EXPERTS],
            )
        if connection.execute("SELECT COUNT(*) FROM research_programs").fetchone()[0] == 0:
            connection.execute(
                "INSERT INTO research_programs VALUES (?, ?, ?, 'active', ?, 'preliminary; replication required')",
                ("aca_faculty_dissociation", "ACA / AI Faculty Dissociation", "Are AI failures functionally decomposable into distinguishable stages, and does diagnosing the failure stage improve intervention selection?", "Run stage-aware intervention trial against generic correction and process supervision."),
            )
        if connection.execute("SELECT COUNT(*) FROM knowledge_items WHERE source_class = 'web'").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO knowledge_items VALUES (?, ?, ?, ?, ?, 'proposed', ?)",
                [(str(uuid.uuid4()), title, content_type, summary, source_class, NOW()) for title, content_type, summary, source_class in WEB_SEED_KNOWLEDGE],
            )


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    content_type: Literal["text", "markdown", "pdf", "image", "audio", "video", "spreadsheet", "code"] = "text"
    summary: str = Field(min_length=2, max_length=8000)
    source_class: Literal["classical", "scientific", "expert", "ajay", "context", "web"] = "ajay"


class DecisionAnalyze(BaseModel):
    question: str = Field(min_length=10, max_length=4000)
    context: dict = Field(default_factory=dict)


class DecisionFinalize(BaseModel):
    final_decision: str = Field(min_length=2, max_length=4000)


class ClaimCreate(BaseModel):
    statement: str = Field(min_length=4, max_length=4000)
    status: Literal["known", "supported", "probable", "possible", "speculative", "unknown", "disputed"] = "possible"
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)


class ExpertRouteRequest(BaseModel):
    query: str = Field(min_length=3, max_length=4000)
    domains: list[str] = Field(default_factory=list)
    high_risk: bool = False


app = FastAPI(title="ADT Vault API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    setup_database()


@app.get("/health")
def health():
    return {"status": "ok", "service": "adt-vault"}


@app.get("/v1/constitution")
def list_constitution():
    with db() as connection:
        items = connection.execute("SELECT * FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC").fetchall()
    return [dict(item) | {"explicitly_confirmed_by_ajay": bool(item["explicitly_confirmed_by_ajay"])} for item in items]


@app.get("/v1/experts")
def list_experts():
    with db() as connection:
        experts = connection.execute("SELECT * FROM expert_profiles WHERE status = 'active' ORDER BY name").fetchall()
    return [dict(expert) | {"domains": json.loads(expert["domains"])} for expert in experts]


def select_experts(query: str, requested_domains: list[str] | None = None, high_risk: bool = False) -> list[dict]:
    """Deterministic, inspectable router: provider/model routing comes after this policy layer."""
    query_tokens = set(query.lower().replace("/", " ").replace("-", " ").split()) | set(requested_domains or [])
    with db() as connection:
        experts = connection.execute("SELECT * FROM expert_profiles WHERE status = 'active'").fetchall()
    ranked = []
    for expert in experts:
        domains = json.loads(expert["domains"])
        score = len(query_tokens & set(domains))
        if expert["id"] == "dharma_governor":
            score += 1
        if high_risk and expert["id"] in {"modern_medicine", "dharma_governor"}:
            score += 3
        ranked.append((score, dict(expert) | {"domains": domains}))
    selected = [expert for score, expert in sorted(ranked, key=lambda item: item[0], reverse=True) if score > 0][:4]
    return selected or [next(expert for _, expert in ranked if expert["id"] == "dharma_governor")]


@app.post("/v1/experts/route")
def route_experts(request: ExpertRouteRequest):
    experts = select_experts(request.query, request.domains, request.high_risk)
    return {
        "experts": experts,
        "routing_note": "Experts receive independent prompts and evidence bundles. Synthesis occurs only after their views are recorded.",
        "high_risk_escalation": request.high_risk,
    }


@app.post("/v1/constitution/amendments", status_code=202)
def propose_amendment(item: KnowledgeCreate):
    """Creates an auditable proposal only; it cannot alter approved Constitution rows."""
    proposal_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (?, 'constitution_amendment_proposed', ?, ?, ?)",
            (str(uuid.uuid4()), proposal_id, item.model_dump_json(), NOW()),
        )
    return {"id": proposal_id, "status": "proposed", "message": "Awaiting explicit Ajay approval; Constitution unchanged."}


@app.get("/v1/inbox")
def list_inbox():
    with db() as connection:
        items = connection.execute("SELECT * FROM knowledge_items ORDER BY created_at DESC").fetchall()
    return [dict(item) for item in items]


@app.post("/v1/inbox", status_code=201)
def add_knowledge(item: KnowledgeCreate):
    knowledge_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO knowledge_items VALUES (?, ?, ?, ?, ?, 'received', ?)",
            (knowledge_id, item.title, item.content_type, item.summary, item.source_class, NOW()),
        )
        connection.execute("INSERT INTO audit_events VALUES (?, 'knowledge_received', ?, ?, ?)", (str(uuid.uuid4()), knowledge_id, item.model_dump_json(), NOW()))
    return {"id": knowledge_id, "status": "received", "constitutional_change": False}


@app.post("/v1/knowledge/{knowledge_id}/claims", status_code=201)
def add_claim(knowledge_id: str, claim: ClaimCreate):
    claim_id = str(uuid.uuid4())
    with db() as connection:
        if not connection.execute("SELECT id FROM knowledge_items WHERE id = ?", (knowledge_id,)).fetchone():
            raise HTTPException(404, "Knowledge item not found")
        connection.execute(
            "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (claim_id, knowledge_id, claim.statement, claim.status, claim.confidence, json.dumps(claim.evidence_for), json.dumps(claim.evidence_against), NOW()),
        )
    return {"id": claim_id, "knowledge_id": knowledge_id, "status": claim.status}


@app.get("/v1/knowledge/search")
def search_knowledge(q: str, include_proposed: bool = False):
    term = f"%{q}%"
    approved_filter = "" if include_proposed else "AND k.status = 'accepted'"
    with db() as connection:
        rows = connection.execute(
            f"""SELECT k.id, k.title, k.summary, k.source_class, k.status,
                       c.statement AS claim, c.status AS claim_status, c.confidence
                FROM knowledge_items k LEFT JOIN claims c ON c.knowledge_id = k.id
                WHERE (k.title LIKE ? OR k.summary LIKE ? OR c.statement LIKE ?) {approved_filter}
                ORDER BY k.created_at DESC LIMIT 25""",
            (term, term, term),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/v1/inbox/{knowledge_id}/review")
def review_knowledge(knowledge_id: str, action: Literal["accepted", "rejected", "deferred"]):
    with db() as connection:
        existing = connection.execute("SELECT id FROM knowledge_items WHERE id = ?", (knowledge_id,)).fetchone()
        if not existing:
            raise HTTPException(404, "Knowledge item not found")
        connection.execute("UPDATE knowledge_items SET status = ? WHERE id = ?", (action, knowledge_id))
        connection.execute("INSERT INTO audit_events VALUES (?, 'knowledge_reviewed', ?, ?, ?)", (str(uuid.uuid4()), knowledge_id, json.dumps({"action": action}), NOW()))
    return {"id": knowledge_id, "status": action}


@app.post("/v1/decisions/analyze", status_code=201)
def analyze_decision(payload: DecisionAnalyze):
    """Deterministic Phase-1 scaffold; replace with routed expert services in Phase 2."""
    decision_id = str(uuid.uuid4())
    recommendation = "Stage the commitment with a short validation sprint, named ownership, and a stop/go review."
    high_risk = any(token in payload.question.lower() for token in ("patient", "medical", "diagnosis", "treatment", "clinical", "invest"))
    experts = select_experts(payload.question, high_risk=high_risk)
    with db() as connection:
        connection.execute(
            "INSERT INTO decision_records VALUES (?, ?, ?, ?, 0.78, NULL, NULL, ?)",
            (decision_id, payload.question, json.dumps(payload.context), recommendation, NOW()),
        )
        evidence = connection.execute("SELECT title, source_class, status FROM knowledge_items WHERE status = 'accepted' ORDER BY created_at DESC LIMIT 5").fetchall()
        connection.execute(
            "INSERT INTO reasoning_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (decision_id, json.dumps([dict(item) for item in evidence]), json.dumps(["Weights are default Phase-1 weights and must be sensitivity-tested."]), json.dumps([expert["id"] for expert in experts]), json.dumps(["Independent expert opinions are not yet model-generated in the local scaffold."]), json.dumps(["overextension", "under-delegation"]), json.dumps(["dharma", "long-term compounding", "resilience"]), "Evidence needs a clearly defined validation protocol before irreversible commitment."),
        )
    return {
        "id": decision_id,
        "recommendation": recommendation,
        "confidence": 0.78,
        "values_applied": ["dharma", "long-term compounding", "resilience"],
        "aca_risks": ["overextension", "under-delegation"],
        "experts": experts,
        "uncertainty": "Evidence needs a clearly defined validation protocol before irreversible commitment.",
        "next_steps": ["Define success criteria", "Assign owners", "Schedule 6-week stop/go review"],
    }


@app.post("/v1/decisions/{decision_id}/finalize")
def finalize_decision(decision_id: str, payload: DecisionFinalize):
    with db() as connection:
        result = connection.execute("UPDATE decision_records SET final_decision = ? WHERE id = ?", (payload.final_decision, decision_id))
        if result.rowcount == 0:
            raise HTTPException(404, "Decision record not found")
    return {"id": decision_id, "status": "finalized"}


@app.get("/v1/decisions/{decision_id}/reasoning-record")
def get_reasoning_record(decision_id: str):
    with db() as connection:
        record = connection.execute("SELECT * FROM reasoning_records WHERE decision_id = ?", (decision_id,)).fetchone()
    if not record:
        raise HTTPException(404, "Reasoning record not found")
    return {key: json.loads(record[key]) if key in {"facts_used", "assumptions", "experts", "disagreements", "aca_risks", "values_applied"} else record[key] for key in record.keys()}


@app.get("/v1/memories/recall")
def recall(q: str = ""):
    term = f"%{q}%"
    with db() as connection:
        decisions = connection.execute("SELECT id, question AS title, created_at, 'decision' AS memory_type FROM decision_records WHERE question LIKE ? ORDER BY created_at DESC LIMIT 10", (term,)).fetchall()
        knowledge = connection.execute("SELECT id, title, created_at, 'knowledge' AS memory_type FROM knowledge_items WHERE status = 'accepted' AND (title LIKE ? OR summary LIKE ?) ORDER BY created_at DESC LIMIT 10", (term, term)).fetchall()
    return [dict(item) for item in [*decisions, *knowledge]]


@app.get("/v1/research/programs")
def list_research_programs():
    with db() as connection:
        programs = connection.execute("SELECT * FROM research_programs ORDER BY title").fetchall()
    return [dict(program) for program in programs]


@app.get("/v1/governance/drift-check")
def drift_check():
    return {
        "protocol": ["mirror", "re-anchor", "alternative", "action"],
        "checks": ["dharma drift", "evidence drift", "overextension", "under-delegation", "family-role neglect", "false certainty", "expert echo-chamber"],
        "current_status": "No automatic state inference. Run only with explicit decision/context input in the next iteration.",
        "constitutional_integrity": "approved Constitution is separated from uploads, claims, decisions and web knowledge.",
    }
