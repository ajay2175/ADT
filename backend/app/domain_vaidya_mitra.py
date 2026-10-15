from __future__ import annotations

"""WP3 — Vaidya Mitra domain pack (research benchmark cases, not clinical advice)."""

VAIDYA_BENCHMARK_CASES = [
    {
        "id": "vm-guduchi-001",
        "entity": "Guduchi",
        "layer": "classical_text",
        "prompt": "What does classical materia medica assert about Guduchi as rasayana?",
        "expected_layers": ["classical_text", "interpretation"],
        "must_not_present_as": ["clinically_validated_evidence", "practitioner_authorization"],
    },
    {
        "id": "vm-rasayana-001",
        "entity": "Rasāyana",
        "layer": "interpretation",
        "prompt": "Distinguish rasayana as a classical category from modern antioxidant hypotheses.",
        "expected_layers": ["classical_text", "interpretation", "experimental_hypothesis"],
        "must_not_present_as": ["clinical_recommendation"],
    },
    {
        "id": "vm-prameha-001",
        "entity": "Prameha",
        "layer": "classical_text",
        "prompt": "Map prameha discourse to modern diabetes only where biomedical evidence supports linkage.",
        "expected_layers": ["classical_text", "biomedical_observation", "uncertainty"],
        "must_not_present_as": ["prescription"],
    },
]


def list_vaidya_benchmark_cases() -> list[dict]:
    return VAIDYA_BENCHMARK_CASES
