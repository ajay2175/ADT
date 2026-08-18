from __future__ import annotations

import json
import re

from app.model_gateway import get_provider, parse_json_block


EXTRACTION_PROMPT = """Extract knowledge-graph entities and relations from this ADT vault document.
Respond ONLY with JSON:
{
  "entities": [{"name": "...", "type": "Concept|Person|Organization|Method|Domain|Value", "confidence": 0.0-1.0}],
  "relations": [{"from": "...", "to": "...", "type": "MENTIONS|RELATES_TO|SUPPORTS|CONTRADICTS|PART_OF", "confidence": 0.0-1.0}]
}
Rules:
- Use short canonical entity names (2-5 words max).
- Max 12 entities and 15 relations.
- Do NOT invent constitutional values; extract what the text states.
- Mark low confidence when uncertain.

TITLE: {title}

TEXT:
{text}
"""


async def extract_entities_relations(title: str, text: str, max_chars: int = 6000) -> dict:
    snippet = text[:max_chars]
    provider = get_provider()
    prompt = (
        EXTRACTION_PROMPT.replace("{title}", title).replace("{text}", snippet)
    )
    raw = await provider.generate([{"role": "user", "content": prompt}])
    parsed = parse_json_block(raw)

    entities = _normalize_entities(parsed.get("entities", []))
    relations = _normalize_relations(parsed.get("relations", []), entities)

    if not entities and snippet.strip():
        entities = _heuristic_entities(title, snippet)
        relations = _heuristic_relations(entities)

    return {"entities": entities, "relations": relations, "raw": raw[:4000]}


def _normalize_entities(raw: list) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = re.sub(r"\s+", " ", str(item.get("name", "")).strip())
        if len(name) < 2 or name.lower() in seen:
            continue
        seen.add(name.lower())
        etype = str(item.get("type", "Concept"))[:32]
        conf = float(item.get("confidence", 0.6))
        out.append({"name": name, "type": etype, "confidence": max(0.0, min(1.0, conf))})
    return out[:12]


def _normalize_relations(raw: list, entities: list[dict]) -> list[dict]:
    names = {e["name"].lower() for e in entities}
    out: list[dict] = []
    allowed = {"MENTIONS", "RELATES_TO", "SUPPORTS", "CONTRADICTS", "PART_OF"}
    for item in raw:
        if not isinstance(item, dict):
            continue
        src = str(item.get("from", "")).strip()
        dst = str(item.get("to", "")).strip()
        if src.lower() not in names or dst.lower() not in names:
            continue
        rtype = str(item.get("type", "RELATES_TO")).upper()
        if rtype not in allowed:
            rtype = "RELATES_TO"
        conf = float(item.get("confidence", 0.55))
        out.append({"from": src, "to": dst, "type": rtype, "confidence": max(0.0, min(1.0, conf))})
    return out[:15]


def _heuristic_entities(title: str, text: str) -> list[dict]:
    entities = [{"name": title[:80], "type": "Concept", "confidence": 0.7}]
    for token in re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2}\b", text):
        if len(token) > 3 and token.lower() not in {e["name"].lower() for e in entities}:
            entities.append({"name": token, "type": "Concept", "confidence": 0.45})
        if len(entities) >= 8:
            break
    return entities


def _heuristic_relations(entities: list[dict]) -> list[dict]:
    if len(entities) < 2:
        return []
    root = entities[0]["name"]
    return [
        {"from": root, "to": e["name"], "type": "MENTIONS", "confidence": 0.4}
        for e in entities[1:4]
    ]
