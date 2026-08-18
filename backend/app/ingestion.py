from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import fitz
from docx import Document

from app.config import settings
from app.database import NOW, db
from app.model_gateway import get_provider


ALLOWED = {".md", ".txt", ".pdf", ".docx", ".json"}
CHUNK = 800


def _safe_path(filename: str) -> Path:
    base = Path(settings.upload_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED:
        raise ValueError(f"Extension {ext} not allowed")
    dest = (base / f"{uuid.uuid4()}{ext}").resolve()
    if not str(dest).startswith(str(base)):
        raise ValueError("Invalid path")
    return dest


def parse_file(content: bytes, filename: str) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    if ext in {".md", ".txt", ".json"}:
        return ext.lstrip("."), content.decode("utf-8", errors="replace")
    if ext == ".pdf":
        doc = fitz.open(stream=content, filetype="pdf")
        return "pdf", "\n".join(page.get_text() for page in doc)
    if ext == ".docx":
        tmp = Path(settings.upload_dir) / f"_tmp_{uuid.uuid4()}.docx"
        tmp.write_bytes(content)
        try:
            doc = Document(str(tmp))
            return "docx", "\n".join(p.text for p in doc.paragraphs)
        finally:
            tmp.unlink(missing_ok=True)
    raise ValueError(f"Unsupported: {ext}")


def chunk_text(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in parts:
        if len(cur) + len(p) + 2 <= CHUNK:
            cur = f"{cur}\n\n{p}".strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p[:CHUNK]
    if cur:
        chunks.append(cur)
    return chunks or [text[:CHUNK]]


async def ingest_bytes(filename: str, content: bytes, source_class: str = "ajay") -> dict:
    if len(content) > settings.max_upload_bytes:
        raise ValueError("File too large")
    dest = _safe_path(filename)
    dest.write_bytes(content)
    ctype, text = parse_file(content, filename)
    kid = str(uuid.uuid4())
    title = Path(filename).stem

    provider = get_provider()
    chunks = chunk_text(text)
    embeddings = await provider.embed(chunks)

    with db() as connection:
        connection.execute(
            "INSERT INTO knowledge_items VALUES (%s, %s, %s, %s, %s, 'received', %s)",
            (kid, title, ctype, text[:8000], source_class, NOW()),
        )
        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings, strict=True)):
            cid = str(uuid.uuid4())
            if connection.dialect == "postgres":
                connection.execute(
                    "INSERT INTO knowledge_chunks (id, knowledge_id, chunk_index, content, embedding) VALUES (%s, %s, %s, %s, %s)",
                    (cid, kid, idx, chunk, emb),
                )
            else:
                connection.execute(
                    "INSERT INTO knowledge_chunks VALUES (%s, %s, %s, %s, %s)",
                    (cid, kid, idx, chunk, json.dumps(emb)),
                )
            if len(chunk) > 30:
                connection.execute(
                    "INSERT INTO claims VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (str(uuid.uuid4()), kid, chunk[:500], "supported", 0.65, "[]", "[]", NOW()),
                )
        connection.execute("UPDATE knowledge_items SET status = 'proposed' WHERE id = %s", (kid,))
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'knowledge_received', %s, %s, %s)",
            (str(uuid.uuid4()), kid, json.dumps({"filename": filename, "chunks": len(chunks)}), NOW()),
        )
    return {"id": kid, "title": title, "status": "proposed", "chunks": len(chunks), "constitutional_change": False}
