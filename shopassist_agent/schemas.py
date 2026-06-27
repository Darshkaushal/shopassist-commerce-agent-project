"""Pydantic schemas shared by FastAPI endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentQuestion(BaseModel):
    question: str = Field(..., min_length=2)


class AgentAnswer(BaseModel):
    answer: str
    intent: str | None = None
    tools_used: list[str] = []
    trace: list[str] = []


class StatusUpdateRequest(BaseModel):
    status: str
    tracking_id: str | None = None
    carrier: str | None = None
    eta: str | None = None
    last_update: str | None = None
