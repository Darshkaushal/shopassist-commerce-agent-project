"""Typed response schemas used by the agent and UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Human-readable record of a tool execution."""

    name: str
    input: Dict[str, Any]
    status: str
    output_summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class AgentResult:
    """Structured result used by Streamlit while run_agent returns only the answer."""

    answer: str
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[ToolCall] = field(default_factory=list)
    safety_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "tool_calls": [call.__dict__ for call in self.tool_calls],
            "safety_notes": self.safety_notes,
        }
