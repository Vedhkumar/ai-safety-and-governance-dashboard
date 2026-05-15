"""LLM Provider Adapters — OpenAI, Anthropic, and Mock providers."""

import time
import random
import httpx
from abc import ABC, abstractmethod
from pydantic import BaseModel
from app.config import get_settings


class ProviderResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    latency_ms: int


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], model: str, **kwargs) -> ProviderResponse:
        ...


class OpenAIProvider(LLMProvider):
    async def complete(self, messages: list[dict], model: str, **kwargs) -> ProviderResponse:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        start = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"model": model, "messages": messages, **kwargs},
            )
            resp.raise_for_status()
            data = resp.json()
        latency = int((time.time() - start) * 1000)
        usage = data.get("usage", {})
        cost = self._calc_cost(model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        return ProviderResponse(
            content=data["choices"][0]["message"]["content"],
            model=model, input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_cost=cost, latency_ms=latency)

    def _calc_cost(self, model: str, in_tokens: int, out_tokens: int) -> float:
        rates = {"gpt-4o": (0.005, 0.015), "gpt-4o-mini": (0.00015, 0.0006),
                 "gpt-4-turbo": (0.01, 0.03), "gpt-3.5-turbo": (0.0005, 0.0015)}
        in_rate, out_rate = rates.get(model, (0.001, 0.002))
        return round((in_tokens / 1000) * in_rate + (out_tokens / 1000) * out_rate, 6)


class AnthropicProvider(LLMProvider):
    async def complete(self, messages: list[dict], model: str, **kwargs) -> ProviderResponse:
        settings = get_settings()
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        system_msg = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                filtered.append(m)
        start = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            body = {"model": model, "messages": filtered, "max_tokens": kwargs.get("max_tokens", 1024)}
            if system_msg:
                body["system"] = system_msg
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": settings.ANTHROPIC_API_KEY,
                         "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json=body)
            resp.raise_for_status()
            data = resp.json()
        latency = int((time.time() - start) * 1000)
        usage = data.get("usage", {})
        return ProviderResponse(
            content=data["content"][0]["text"], model=model,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_cost=round((usage.get("input_tokens", 0) / 1000) * 0.003 + (usage.get("output_tokens", 0) / 1000) * 0.015, 6),
            latency_ms=latency)


MOCK_RESPONSES = [
    "Based on my analysis, the quarterly revenue increased by 15% compared to last year, driven primarily by the expansion into new markets.",
    "The recommended approach involves implementing a microservices architecture with containerized deployments using Kubernetes for orchestration.",
    "According to the research paper by Smith et al. (2024), the neural network achieved 95.2% accuracy on the benchmark dataset.",
    "The patient should consult with their healthcare provider before making any changes to their medication regimen.",
    "The implementation uses a Red-Black tree data structure which provides O(log n) insertion, deletion, and search operations.",
    "Climate models project a 2.5°C increase in global average temperature by 2050 under the current emissions trajectory.",
]


class MockProvider(LLMProvider):
    """Mock provider for demo/testing — returns realistic simulated responses."""
    async def complete(self, messages: list[dict], model: str, **kwargs) -> ProviderResponse:
        import asyncio
        latency = random.randint(80, 500)
        await asyncio.sleep(latency / 1000)
        content = random.choice(MOCK_RESPONSES)
        in_tokens = sum(len(m.get("content", "").split()) * 2 for m in messages)
        out_tokens = len(content.split()) * 2
        cost_rates = {"gpt-4o": 0.005, "gpt-4o-mini": 0.0002, "claude-3-opus": 0.015,
                      "claude-3-sonnet": 0.003, "local-model": 0.0}
        rate = cost_rates.get(model, 0.001)
        cost = round((in_tokens + out_tokens) / 1000 * rate, 6)
        return ProviderResponse(content=content, model=model, input_tokens=in_tokens,
            output_tokens=out_tokens, total_cost=cost, latency_ms=latency)


def get_provider(model: str) -> LLMProvider:
    """Get the appropriate provider for a model."""
    settings = get_settings()
    if model.startswith("gpt") and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    elif model.startswith("claude") and settings.ANTHROPIC_API_KEY:
        return AnthropicProvider()
    else:
        return MockProvider()
