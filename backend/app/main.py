from __future__ import annotations

import json
import uuid
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.database import NOW, db, row_to_dict, rows_to_dicts, setup_database
from app.decisions import analyze_decision
from app.drift import run_drift_check
from app.experts import select_experts
from app.ingestion import ingest_bytes
from app.model_gateway import get_provider
from app.retrieval import hybrid_search, vector_search


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=240)
    content_type: Literal["text", "markdown", "pdf", "docx", "image", "audio", "video", "spreadsheet", "code"] = "text"
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


class DriftCheckRequest(BaseModel):
    question: str = ""
    context: dict = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


app = FastAPI(title="ADT Vault API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    setup_database()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "adt-vault",
        "database": "postgresql" if settings.use_postgres else "sqlite",
        "llm_provider": settings.llm_provider,
    }


@app.get("/v1/constitution")
def list_constitution():
    with db() as connection:
        cur = connection.execute("SELECT * FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC")
        items = rows_to_dicts(cur.fetchall())
    for item in items:
        item["explicitly_confirmed_by_ajay"] = bool(item.get("explicitly_confirmed_by_ajay"))
    return items


@app.get("/v1/experts")
def list_experts():
    with db() as connection:
        cur = connection.execute("SELECT * FROM expert_profiles WHERE status = 'active' ORDER BY name")
        experts = rows_to_dicts(cur.fetchall())
    return [{**e, "domains": json.loads(e["domains"])} for e in experts]


@app.post("/v1/experts/route")
def route_experts(request: ExpertRouteRequest):
    high_risk = request.high_risk or any(
        t in request.query.lower() for t in ("patient", "medical", "clinical", "diagnosis")
    )
    experts = select_experts(request.query, request.domains, high_risk)
    return {
        "experts": experts,
        "routing_note": "Experts receive independent LLM prompts. Synthesis occurs only after views are recorded.",
        "high_risk_escalation": high_risk,
    }


@app.post("/v1/constitution/amendments", status_code=202)
def propose_amendment(item: KnowledgeCreate):
    proposal_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'constitution_amendment_proposed', %s, %s, %s)",
            (str(uuid.uuid4()), proposal_id, item.model_dump_json(), NOW()),
        )
    return {"id": proposal_id, "status": "proposed", "message": "Awaiting explicit Ajay approval; Constitution unchanged."}


@app.get("/v1/inbox")
def list_inbox():
    with db() as connection:
        cur = connection.execute("SELECT * FROM knowledge_items ORDER BY created_at DESC")
        return rows_to_dicts(cur.fetchall())


@app.post("/v1/inbox", status_code=201)
def add_knowledge(item: KnowledgeCreate):
    knowledge_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO knowledge_items VALUES (%s, %s, %s, %s, %s, 'received', %s)",
            (knowledge_id, item.title, item.content_type, item.summary, item.source_class, NOW()),
        )
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'knowledge_received', %s, %s, %s)",
            (str(uuid.uuid4()), knowledge_id, item.model_dump_json(), NOW()),
        )
    return {"id": knowledge_id, "status": "received", "constitutional_change": False}


@app.post("/v1/inbox/upload", status_code=201)
async def upload_file(file: UploadFile = File(...), source_class: str = "ajay"):
    content = await file.read()
    try:
        return await ingest_bytes(file.filename or "upload.txt", content, source_class)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/v1/knowledge/{knowledge_id}/claims", status_code=201)
def add_claim(knowledge_id: str, claim: ClaimCreate):
    claim_id = str(uuid.uuid4())
    with db() as connection:
        if not connection.execute("SELECT id FROM knowledge_items WHERE id = %s", (knowledge_id,)).fetchone():
            raise HTTPException(404, "Knowledge item not found")
        connection.execute(
            "INSERT INTO claims VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                claim_id,
                knowledge_id,
                claim.statement,
                claim.status,
                claim.confidence,
                json.dumps(claim.evidence_for),
                json.dumps(claim.evidence_against),
                NOW(),
            ),
        )
    return {"id": claim_id, "knowledge_id": knowledge_id, "status": claim.status}


@app.get("/v1/knowledge/search")
async def search_knowledge(q: str, include_proposed: bool = False):
    return await hybrid_search(q, include_proposed)


@app.get("/v1/knowledge/vector-search")
async def knowledge_vector_search(q: str, limit: int = 10):
    return await vector_search(q, limit)


@app.post("/v1/inbox/{knowledge_id}/review")
def review_knowledge(knowledge_id: str, action: Literal["accepted", "rejected", "deferred"]):
    with db() as connection:
        if not connection.execute("SELECT id FROM knowledge_items WHERE id = %s", (knowledge_id,)).fetchone():
            raise HTTPException(404, "Knowledge item not found")
        connection.execute("UPDATE knowledge_items SET status = %s WHERE id = %s", (action, knowledge_id))
        connection.execute(
            "INSERT INTO audit_events VALUES (%s, 'knowledge_reviewed', %s, %s, %s)",
            (str(uuid.uuid4()), knowledge_id, json.dumps({"action": action}), NOW()),
        )
    return {"id": knowledge_id, "status": action}


@app.get("/v1/decisions")
def list_decisions():
    with db() as connection:
        cur = connection.execute(
            "SELECT id, question, recommendation, confidence, final_decision, created_at FROM decision_records ORDER BY created_at DESC LIMIT 50"
        )
        return rows_to_dicts(cur.fetchall())


@app.post("/v1/decisions/analyze", status_code=201)
async def decisions_analyze(payload: DecisionAnalyze):
    return await analyze_decision(payload.question, payload.context)


@app.post("/v1/decisions/{decision_id}/finalize")
def finalize_decision(decision_id: str, payload: DecisionFinalize):
    with db() as connection:
        cur = connection.execute(
            "UPDATE decision_records SET final_decision = %s WHERE id = %s", (payload.final_decision, decision_id)
        )
        if getattr(cur, "rowcount", 0) == 0:
            raise HTTPException(404, "Decision record not found")
    return {"id": decision_id, "status": "finalized"}


@app.get("/v1/decisions/{decision_id}/reasoning-record")
def get_reasoning_record(decision_id: str):
    with db() as connection:
        cur = connection.execute("SELECT * FROM reasoning_records WHERE decision_id = %s", (decision_id,))
        record = cur.fetchone()
    if not record:
        raise HTTPException(404, "Reasoning record not found")
    record = row_to_dict(record)
    json_fields = {"facts_used", "assumptions", "experts", "expert_views", "disagreements", "aca_risks", "values_applied"}
    for key in json_fields:
        if key in record and isinstance(record[key], str):
            record[key] = json.loads(record[key])
    return record


@app.get("/v1/memories/recall")
def recall(q: str = ""):
    term = f"%{q}%"
    with db() as connection:
        cur = connection.execute(
            "SELECT id, question AS title, created_at, 'decision' AS memory_type FROM decision_records WHERE question LIKE %s ORDER BY created_at DESC LIMIT 10",
            (term,),
        )
        decisions = rows_to_dicts(cur.fetchall())
        cur = connection.execute(
            "SELECT id, title, created_at, 'knowledge' AS memory_type FROM knowledge_items WHERE status = 'accepted' AND (title LIKE %s OR summary LIKE %s) ORDER BY created_at DESC LIMIT 10",
            (term, term),
        )
        knowledge = rows_to_dicts(cur.fetchall())
    return [*decisions, *knowledge]


@app.get("/v1/research/programs")
def list_research_programs():
    with db() as connection:
        cur = connection.execute("SELECT * FROM research_programs ORDER BY title")
        return rows_to_dicts(cur.fetchall())


@app.get("/v1/governance/drift-check")
async def drift_check_get(q: str = ""):
    return await run_drift_check(q)


@app.post("/v1/governance/drift-check")
async def drift_check_post(body: DriftCheckRequest):
    return await run_drift_check(body.question, body.context)


@app.post("/v1/chat")
async def chat(body: ChatRequest):
    provider = get_provider()
    with db() as connection:
        cur = connection.execute("SELECT statement FROM constitution_items WHERE status = 'approved' ORDER BY priority DESC LIMIT 8")
        rows = cur.fetchall()
        constitution = [row["statement"] if isinstance(row, dict) else row[0] for row in rows]
    reply = await provider.generate(
        [
            {
                "role": "system",
                "content": "You are ADT — Ajay's dharma-governed digital twin. Never rewrite constitutional values.",
            },
            {
                "role": "user",
                "content": "Constitution excerpt:\n"
                + "\n".join(f"- {c}" for c in constitution)
                + f"\n\nMessage: {body.message}",
            },
        ]
    )
    return {"reply": reply, "llm_provider": provider.__class__.__name__}
