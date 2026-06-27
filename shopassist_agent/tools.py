"""Assignment tools.

These functions intentionally keep the exact tool names from the company assignment:
- get_order(order_id)
- search_products(query)
- get_product(product_id)
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional

from .data import ORDERS, PRODUCTS, ORDER_STATUSES, STATUS_DEFAULT_UPDATES
from .logger import log_event


def _summarize_product(product: Dict[str, Any]) -> str:
    return f"{product['name']} ({product['product_id']}) - ₹{product['price']} - stock {product['stock']}"


def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """Fetch order details by order id."""
    normalized_id = order_id.upper().strip()
    result = deepcopy(ORDERS.get(normalized_id))
    log_event(
        "tool_call",
        {
            "tool": "get_order",
            "input": {"order_id": normalized_id},
            "success": result is not None,
            "output_summary": "found order" if result else "order not found",
        },
    )
    return result


def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Fetch product details by product id."""
    normalized_id = product_id.upper().strip()
    result = deepcopy(PRODUCTS.get(normalized_id))
    log_event(
        "tool_call",
        {
            "tool": "get_product",
            "input": {"product_id": normalized_id},
            "success": result is not None,
            "output_summary": _summarize_product(result) if result else "product not found",
        },
    )
    return result


def search_products(query: str) -> List[Dict[str, Any]]:
    """Search products using simple keyword matching."""
    terms = [term.strip().lower() for term in query.replace(",", " ").split() if term.strip()]
    if not terms:
        results = list(PRODUCTS.values())
    else:
        results = []
        for product in PRODUCTS.values():
            searchable = " ".join(
                [
                    product["product_id"],
                    product["name"],
                    product["category"],
                    product["brand"],
                    product["description"],
                    " ".join(product["keywords"]),
                ]
            ).lower()
            score = sum(1 for term in terms if term in searchable)
            if score > 0:
                item = deepcopy(product)
                item["_score"] = score
                results.append(item)

    results.sort(key=lambda p: (-p.get("_score", 0), p["price"], -p["rating"]))
    log_event(
        "tool_call",
        {
            "tool": "search_products",
            "input": {"query": query},
            "success": True,
            "output_summary": f"{len(results)} product(s) found",
        },
    )
    return results

def normalize_order_status(status: str) -> Optional[str]:
    """Normalize customer/admin status wording to one supported status label."""
    cleaned = " ".join(status.replace("_", " ").replace("-", " ").strip().lower().split())
    aliases = {
        "process": "Processing",
        "processing": "Processing",
        "packed": "Processing",
        "dispatch": "Dispatched",
        "dispatched": "Dispatched",
        "shipped": "Shipped",
        "ship": "Shipped",
        "out for delivery": "Out for Delivery",
        "ofd": "Out for Delivery",
        "delivered": "Delivered",
        "deliver": "Delivered",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
        "cancel": "Cancelled",
    }
    if cleaned in aliases:
        return aliases[cleaned]
    for allowed in ORDER_STATUSES:
        if cleaned == allowed.lower():
            return allowed
    return None


def _generated_tracking_id(order_id: str) -> str:
    digits = "".join(character for character in order_id if character.isdigit()) or "0000"
    return f"TRK-{digits[-4:]}{datetime.now().strftime('%H%M')}"


def update_order_status(
    order_id: str,
    status: str,
    *,
    tracking_id: Optional[str] = None,
    carrier: Optional[str] = None,
    eta: Optional[str] = None,
    last_update: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update an order's fulfillment status in the in-memory store.

    This is an extra backend operation for the demo. It does not replace the assignment's
    required tools, but it makes the dashboard interactive for company review.
    """
    normalized_id = order_id.upper().strip()
    normalized_status = normalize_order_status(status)
    if not normalized_status:
        allowed = ", ".join(ORDER_STATUSES)
        raise ValueError(f"Unsupported status '{status}'. Allowed statuses: {allowed}")

    order = ORDERS.get(normalized_id)
    if not order:
        log_event(
            "order_status_update",
            {
                "order_id": normalized_id,
                "requested_status": status,
                "success": False,
                "reason": "order not found",
            },
        )
        return None

    old_status = order.get("status")
    defaults = STATUS_DEFAULT_UPDATES.get(normalized_status, {})
    order["status"] = normalized_status
    order["eta"] = eta.strip() if isinstance(eta, str) and eta.strip() else defaults.get("eta", order.get("eta"))
    order["last_update"] = (
        last_update.strip()
        if isinstance(last_update, str) and last_update.strip()
        else defaults.get("last_update", order.get("last_update"))
    )

    needs_tracking = normalized_status in {"Dispatched", "Shipped", "Out for Delivery", "Delivered"}
    if needs_tracking:
        order["tracking_id"] = (
            tracking_id.strip()
            if isinstance(tracking_id, str) and tracking_id.strip()
            else order.get("tracking_id")
            or _generated_tracking_id(normalized_id)
        )
        order["carrier"] = (
            carrier.strip()
            if isinstance(carrier, str) and carrier.strip()
            else order.get("carrier")
            or defaults.get("carrier")
            or "Delhivery"
        )
    elif normalized_status in {"Processing", "Cancelled"}:
        order["tracking_id"] = tracking_id.strip() if isinstance(tracking_id, str) and tracking_id.strip() else defaults.get("tracking_id")
        order["carrier"] = carrier.strip() if isinstance(carrier, str) and carrier.strip() else defaults.get("carrier")

    order["updated_at"] = datetime.now().isoformat(timespec="seconds")
    log_event(
        "order_status_update",
        {
            "order_id": normalized_id,
            "old_status": old_status,
            "new_status": normalized_status,
            "tracking_id": order.get("tracking_id"),
            "carrier": order.get("carrier"),
            "success": True,
        },
    )
    return deepcopy(order)

