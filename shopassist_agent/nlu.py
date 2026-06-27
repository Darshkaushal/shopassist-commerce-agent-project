"""Lightweight intent and entity extraction.

A rule-based approach is used so a fresher can explain every decision in evaluation.
The module can be replaced by an LLM classifier later without changing tool functions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

from .data import SUPPORTED_CATEGORIES

ORDER_RE = re.compile(r"\bORD[-_ ]?\d{4}\b", re.IGNORECASE)
PRODUCT_RE = re.compile(r"\bP[-_ ]?\d{4}\b", re.IGNORECASE)
MONEY_RE = re.compile(r"(?:under|below|less than|upto|up to|within|budget|₹|rs\.?|inr)\s*₹?\s*(\d{3,6})", re.IGNORECASE)


@dataclass
class NLUResult:
    intent: str
    confidence: float
    entities: Dict[str, object] = field(default_factory=dict)


def normalize_id(raw_id: str) -> str:
    clean = raw_id.upper().replace("_", "-").replace(" ", "-")
    if "-" not in clean and (clean.startswith("ORD") or clean.startswith("P")):
        prefix = "ORD" if clean.startswith("ORD") else "P"
        clean = f"{prefix}-{clean[len(prefix):]}"
    return clean


def extract_budget(text: str) -> Optional[int]:
    match = MONEY_RE.search(text)
    if match:
        return int(match.group(1))
    # Fallback: phrases like "shoes 2000 budget"
    budget_match = re.search(r"\b(\d{3,6})\s*(budget|rs|inr|rupees)\b", text, re.IGNORECASE)
    return int(budget_match.group(1)) if budget_match else None


def extract_category(text: str) -> Optional[str]:
    lower = text.lower()
    aliases = {
        "sneaker": "shoes",
        "sneakers": "shoes",
        "shoe": "shoes",
        "shoes": "shoes",
        "hoodies": "hoodie",
        "hoodie": "hoodie",
        "sweatshirt": "hoodie",
        "backpack": "bag",
        "bags": "bag",
        "bag": "bag",
        "headphone": "headphones",
        "headphones": "headphones",
        "earbuds": "earbuds",
        "earbud": "earbuds",
        "watch": "watch",
        "smartwatch": "watch",
    }
    for alias, category in aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", lower):
            return category
    for category in SUPPORTED_CATEGORIES:
        if category in lower:
            return category
    return None


def classify(question: str) -> NLUResult:
    text = question.strip()
    lower = text.lower()
    order_match = ORDER_RE.search(text)
    product_match = PRODUCT_RE.search(text)
    budget = extract_budget(text)
    category = extract_category(text)

    entities: Dict[str, object] = {}
    if order_match:
        entities["order_id"] = normalize_id(order_match.group(0))
    if product_match:
        entities["product_id"] = normalize_id(product_match.group(0))
    if budget:
        entities["budget"] = budget
    if category:
        entities["category"] = category

    alternative_words = ["cheaper", "alternative", "similar", "replace", "recommend instead", "less expensive", "budget option"]
    order_words = ["where", "track", "tracking", "status", "eta", "delivery", "arrive", "shipped", "delivered"]
    search_words = ["show", "find", "search", "recommend", "suggest", "available", "under", "below", "budget", "buy"]
    product_words = ["details", "price", "stock", "available", "rating", "tell me about"]

    if any(word in lower for word in alternative_words):
        return NLUResult("alternative_search", 0.92, entities)
    if "order_id" in entities and any(word in lower for word in order_words):
        return NLUResult("order_status", 0.95, entities)
    if "product_id" in entities and any(word in lower for word in product_words):
        return NLUResult("product_lookup", 0.88, entities)
    if category or budget or any(word in lower for word in search_words):
        return NLUResult("product_search", 0.82, entities)
    if lower in {"hi", "hello", "hey", "help", "start"}:
        return NLUResult("greeting", 0.98, entities)
    return NLUResult("fallback", 0.45, entities)
