"""Lightweight NLU helpers for the deterministic agent."""

from __future__ import annotations

import re


def extract_order_id(text: str) -> str | None:
    match = re.search(r"ORD[- ]?\d{4,}", text or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(0).upper().replace(" ", "-")


def extract_product_id(text: str) -> str | None:
    match = re.search(r"P[- ]?\d{4,}", text or "", flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(0).upper().replace(" ", "-")


def extract_budget(text: str) -> int | None:
    match = re.search(r"(?:under|below|less than|upto|up to|<=?)\s*(?:rs\.?|₹)?\s*(\d{3,6})", text or "", flags=re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def detect_category(text: str) -> str | None:
    text = (text or "").lower()
    if any(word in text for word in ["shoe", "shoes", "sneaker", "sneakers"]):
        return "shoes"
    if any(word in text for word in ["tshirt", "t-shirt", "shirt", "polo"]):
        return "t-shirt"
    if any(word in text for word in ["bag", "backpack"]):
        return "bag"
    return None


def detect_intent(text: str) -> str:
    q = (text or "").lower()
    if any(word in q for word in ["cheaper", "alternative", "similar", "less expensive"]):
        return "cheaper_alternative"
    if extract_order_id(q) and any(word in q for word in ["where", "status", "track", "dispatched", "delivered", "shipped"]):
        return "order_status"
    if extract_product_id(q):
        return "product_detail"
    if extract_budget(q):
        return "budget_search"
    if detect_category(q) or any(word in q for word in ["show", "find", "search", "available"]):
        return "product_search"
    return "general"
