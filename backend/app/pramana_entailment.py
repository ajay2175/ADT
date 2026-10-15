from __future__ import annotations

import re
from enum import Enum


class EntailmentRelation(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    INSUFFICIENT = "insufficient_evidence"
    UNRELATED = "unrelated"


def classify_entailment(claim: str, passage: str) -> dict:
    """
    WP2 v0.6.0 — heuristic entailment (deterministic).
    High-impact paths should add human review; NLI model can replace this layer later.
    """
    claim_tokens = _tokens(claim)
    passage_tokens = _tokens(passage)
    if not claim_tokens or not passage_tokens:
        return {"relation": EntailmentRelation.INSUFFICIENT.value, "confidence": 0.2}

    overlap = claim_tokens & passage_tokens
    ratio = len(overlap) / max(len(claim_tokens), 1)

    neg_claim = any(w in claim.lower() for w in ("not ", "no ", "never", "without"))
    neg_pass = any(w in passage.lower() for w in ("not ", "no ", "never", "without"))
    if ratio >= 0.35 and neg_claim != neg_pass:
        return {"relation": EntailmentRelation.CONTRADICTS.value, "confidence": min(0.85, ratio)}

    if ratio >= 0.25:
        return {"relation": EntailmentRelation.SUPPORTS.value, "confidence": min(0.9, ratio + 0.2)}

    if ratio >= 0.08:
        return {"relation": EntailmentRelation.INSUFFICIENT.value, "confidence": 0.45}

    return {"relation": EntailmentRelation.UNRELATED.value, "confidence": 0.7}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]{4,}", text.lower())}
