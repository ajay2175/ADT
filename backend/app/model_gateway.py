from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod

from app.config import settings


class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class MockProvider(ModelProvider):
    async def generate(self, messages: list[dict], **kwargs) -> str:
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        if "expert" in user.lower()[:200] or "independent" in user.lower()[:200]:
            return json.dumps(
                {
                    "finding": "Staged commitment with explicit stop/go gate preserves optionality while honouring dharma and avoiding overextension.",
                    "signal": "support",
                    "evidence_refs": ["constitution:true-north"],
                    "unknowns": ["Delegation execution", "Energy load over 6 weeks"],
                }
            )
        if "extract knowledge-graph" in user.lower() or "entities and relations" in user.lower():
            return json.dumps(
                {
                    "entities": [
                        {"name": "ACA research", "type": "Concept", "confidence": 0.82},
                        {"name": "Vaidya Mitra", "type": "Organization", "confidence": 0.75},
                        {"name": "Clinical validation", "type": "Method", "confidence": 0.7},
                    ],
                    "relations": [
                        {"from": "ACA research", "to": "Clinical validation", "type": "RELATES_TO", "confidence": 0.68},
                        {"from": "Vaidya Mitra", "to": "Clinical validation", "type": "SUPPORTS", "confidence": 0.72},
                    ],
                }
            )
        if "drift" in user.lower()[:300]:
            return json.dumps(
                {
                    "drift_detected": True,
                    "flags": ["overextension", "under-delegation"],
                    "mirror": "Parallel 12-week commitments may exceed sustainable bandwidth.",
                    "re_anchor": "True North: diagnose deeply, act sparingly, preserve resilience.",
                    "alternative": "6-week staged sprint with named owners and stop/go review.",
                    "action": "Define validation protocol this week; defer full parallel launch.",
                }
            )
        return json.dumps(
            {
                "recommendation": "Run a bounded 6-week validation + research-design sprint with named owners and a stop/go gate.",
                "confidence": 0.78,
                "options": ["Staged sprint", "Clinical-only focus", "Defer research 12 weeks"],
                "next_steps": [
                    {"step": "Define validation protocol", "owner": "clinical lead", "when": "this week"},
                    {"step": "Ring-fence ACA design blocks", "owner": "Ajay", "when": "6 weeks"},
                    {"step": "Stop/go review", "owner": "Ajay", "when": "week 6"},
                ],
                "uncertainty": "Energy and delegation remain key unknowns.",
                "aca_risks": ["overextension", "under-delegation"],
                "scores": {
                    "dharma_alignment": 88,
                    "evidence_quality": 72,
                    "long_term_compounding": 84,
                    "people_impact": 76,
                    "energy_efficiency": 58,
                },
                "disagreements": ["Parallel work requires explicit delegation or programs diffuse."],
            }
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vec = [(digest[i % len(digest)] / 255.0) * 2 - 1 for i in range(1536)]
            vectors.append(vec)
        return vectors


class OpenAIProvider(ModelProvider):
    async def generate(self, messages: list[dict], **kwargs) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(model=settings.openai_model, messages=messages)
        return resp.choices[0].message.content or ""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(model=settings.openai_embedding_model, input=texts)
        return [item.embedding for item in resp.data]


class AnthropicProvider(ModelProvider):
    async def generate(self, messages: list[dict], **kwargs) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_msgs = [m for m in messages if m["role"] != "system"]
        resp = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=4096,
            system=system,
            messages=user_msgs,
        )
        return resp.content[0].text

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await MockProvider().embed(texts)


class LocalProvider(ModelProvider):
    async def generate(self, messages: list[dict], **kwargs) -> str:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.local_llm_base_url.rstrip('/')}/chat/completions",
                json={"model": settings.local_llm_model, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await MockProvider().embed(texts)


def get_provider() -> ModelProvider:
    p = settings.llm_provider.lower()
    if p == "openai" and settings.openai_api_key:
        return OpenAIProvider()
    if p == "anthropic" and settings.anthropic_api_key:
        return AnthropicProvider()
    if p == "local":
        return LocalProvider()
    return MockProvider()


def parse_json_block(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"raw": raw}
