"""Pydantic schemas for proxy endpoints (OpenAI-compatible)."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="gpt-4o-mini", description="Model identifier")
    messages: list[ChatMessage] = Field(..., description="Conversation messages")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None)
    stream: bool = Field(default=False)
    # Source documents for hallucination checking
    source_documents: Optional[list[str]] = Field(
        default=None,
        description="Optional source docs for hallucination verification"
    )


class ChatChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class SafetyMetadata(BaseModel):
    injection_score: float = 0.0
    injection_method: str = "none"
    toxicity_scores: dict = {}
    hallucination_score: float = 0.0
    pii_detected: bool = False
    pii_entities: list[str] = []
    bias_score: float = 0.0
    policies_triggered: list[dict] = []
    final_status: str = "passed"  # passed, blocked, flagged


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatChoice]
    usage: TokenUsage
    safety: Optional[SafetyMetadata] = None


class EmbeddingRequest(BaseModel):
    model: str = "text-embedding-3-small"
    input: str | list[str]


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: list[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: list[EmbeddingData]
    model: str
    usage: dict
