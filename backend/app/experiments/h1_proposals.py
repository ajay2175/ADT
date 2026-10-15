from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from app.experiments.h1_emergence import SamanyaProposal, jaccard, observation_signature


@dataclass
class CandidateCategoryProposal:
    """Research-only proposal with source lineage (not applied to live ontology)."""

    proposal_id: str
    samanya_label: str
    signature_guna: tuple[str, ...]
    signature_karma: tuple[str, ...]
    source_lineage: dict[str, Any]
    visesha_attachments: list[str] = field(default_factory=list)
    abhava_attachments: list[str] = field(default_factory=list)
    novelty_check: dict[str, Any] = field(default_factory=dict)
    pramana_status: str = "proposed"
    jnana_status: str = "samsaya"
    h2_flags: dict[str, Any] = field(default_factory=lambda: {"contradictions": [], "uncertainty_notes": [], "revision_history": []})
    accepted: bool = False
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_contradictions(observations: list[dict], proposal: SamanyaProposal) -> list[dict]:
    """H2 embedded: observations matching guna but conflicting karma → contradiction flags."""
    flags: list[dict] = []
    for obs in observations:
        g, k = observation_signature(obs)
        if g == proposal.signature_guna and k != proposal.signature_karma and not obs.get("outlier"):
            flags.append(
                {
                    "observation_id": obs["id"],
                    "type": "guna_match_karma_mismatch",
                    "detail": f"expected karma {proposal.signature_karma}, saw {k}",
                }
            )
    return flags


def samanya_to_candidate(
    proposal: SamanyaProposal,
    observations: list[dict],
    seed: dict,
) -> CandidateCategoryProposal:
    max_j = max((jaccard(proposal.name, s) for s in seed.get("samanya", [])), default=0.0)
    contradictions = detect_contradictions(observations, proposal)
    jnana = "samsaya" if contradictions else ("prama" if proposal.accepted else "samsaya")
    pramana = "accepted" if proposal.accepted and not contradictions else ("rejected" if contradictions else "proposed")
    domains = list({o["domain"] for o in observations if o["id"] in proposal.member_ids})
    return CandidateCategoryProposal(
        proposal_id=str(uuid.uuid4()),
        samanya_label=proposal.name,
        signature_guna=proposal.signature_guna,
        signature_karma=proposal.signature_karma,
        source_lineage={
            "observation_ids": proposal.member_ids,
            "domains": domains,
            "derivation": "visesa_cluster",
        },
        visesha_attachments=proposal.visesha_ids,
        novelty_check={"jaccard_max_vs_seed": round(max_j, 4), "passed": proposal.novel and max_j < 0.6},
        pramana_status=pramana,
        jnana_status=jnana,
        h2_flags={
            "contradictions": contradictions,
            "uncertainty_notes": ["counterexample_present"] if contradictions else [],
            "revision_history": [],
        },
        accepted=proposal.accepted and not contradictions and proposal.novel,
        rejection_reason=proposal.rejection_reason or ("contradiction" if contradictions else ""),
    )
