"""Tool layer used by the agent.

The agent never reads raw data directly; it calls these functions as tools.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .data import PRODUCTS, ORDERS, VALID_ORDER_STATUSES, get_all_orders, get_all_products, update_order_record


def get_order(order_id: str) -> dict[str, Any] | None:
    if not order_id:
        return None
    return deepcopy(ORDERS.get(order_id.upper()))


def get_product(product_id: str) -> dict[str, Any] | None:
    if not product_id:
        return None
    return deepcopy(PRODUCTS.get(product_id.upper()))


def search_products(query: str = "", category: str | None = None, max_price: int | None = None, in_stock_only: bool = True) -> list[dict[str, Any]]:
    query = (query or "").lower().strip()
    category = (category or "").lower().strip() or None
    results: list[dict[str, Any]] = []

    for product in PRODUCTS.values():
        searchable = " ".join(
            str(product.get(key, "")) for key in ["product_id", "name", "category", "brand", "color", "description"]
        ).lower()
        if query and query not in searchable:
            # allow simple plural/singular matches such as shoe/shoes
            q = query[:-1] if query.endswith("s") else query
            if q and q not in searchable:
                continue
        if category and category not in product["category"].lower():
            continue
        if max_price is not None and product["price"] > max_price:
            continue
        if in_stock_only and product["stock"] <= 0:
            continue
        results.append(deepcopy(product))

    return sorted(results, key=lambda item: (item["price"], -item["rating"]))


def update_order_status(
    order_id: str,
    status: str,
    tracking_id: str | None = None,
    carrier: str | None = None,
    eta: str | None = None,
    last_update: str | None = None,
) -> dict[str, Any]:
    if status not in VALID_ORDER_STATUSES:
        raise ValueError(f"Invalid status. Allowed values: {', '.join(VALID_ORDER_STATUSES)}")

    updated = update_order_record(
        order_id,
        {
            "status": status,
            "tracking_id": tracking_id,
            "carrier": carrier,
            "eta": eta,
            "last_update": last_update,
        },
    )
    if not updated:
        raise KeyError(f"Order {order_id} was not found")
    return updated


__all__ = [
    "get_order",
    "get_product",
    "search_products",
    "update_order_status",
    "get_all_orders",
    "get_all_products",
    "VALID_ORDER_STATUSES",
]
