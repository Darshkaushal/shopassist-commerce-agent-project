"""FastAPI backend for ShopAssist Commerce."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from shopassist_agent.agent import run_agent, run_agent_detailed
from shopassist_agent.data import VALID_ORDER_STATUSES, get_all_orders, get_all_products
from shopassist_agent.logger import log_event, read_logs
from shopassist_agent.schemas import AgentAnswer, AgentQuestion, StatusUpdateRequest
from shopassist_agent.tools import get_order, get_product, search_products, update_order_status

ADMIN_KEY = os.getenv("SHOPASSIST_ADMIN_KEY", "shopassist-admin-2026")

app = FastAPI(
    title="ShopAssist Commerce API",
    version="1.0.0",
    description="Backend API for order support, product search, fulfillment updates, logs, metrics, and assistant responses.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "ShopAssist Commerce API", "status": "running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/api/agent/ask", response_model=AgentAnswer)
def ask_agent(payload: AgentQuestion) -> dict[str, Any]:
    return run_agent_detailed(payload.question)


@app.post("/api/agent/simple")
def ask_agent_simple(payload: AgentQuestion) -> dict[str, str]:
    return {"answer": run_agent(payload.question)}


@app.get("/api/orders")
def list_orders() -> list[dict[str, Any]]:
    return get_all_orders()


@app.get("/api/orders/{order_id}")
def order_details(order_id: str) -> dict[str, Any]:
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/api/order-statuses")
def order_statuses() -> list[str]:
    return VALID_ORDER_STATUSES


@app.patch("/api/admin/orders/{order_id}/status")
def admin_update_order_status(
    order_id: str,
    payload: StatusUpdateRequest,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict[str, Any]:
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    try:
        updated = update_order_status(
            order_id=order_id,
            status=payload.status,
            tracking_id=payload.tracking_id,
            carrier=payload.carrier,
            eta=payload.eta,
            last_update=payload.last_update,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Order not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    log_event("admin_status_update", {"order_id": order_id, "status": payload.status})
    return updated


@app.get("/api/products")
def list_products() -> list[dict[str, Any]]:
    return get_all_products()


@app.get("/api/products/search")
def product_search(
    q: str = Query(default=""),
    category: str | None = None,
    max_price: int | None = None,
) -> list[dict[str, Any]]:
    return search_products(query=q, category=category, max_price=max_price)


@app.get("/api/products/{product_id}")
def product_details(product_id: str) -> dict[str, Any]:
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    orders = get_all_orders()
    products = get_all_products()
    return {
        "orders": len(orders),
        "products": len(products),
        "in_stock_products": sum(1 for p in products if p.get("stock", 0) > 0),
        "statuses": {status: sum(1 for order in orders if order.get("status") == status) for status in VALID_ORDER_STATUSES},
    }


@app.get("/api/logs")
def logs(limit: int = 50) -> list[dict[str, Any]]:
    return read_logs(limit=limit)
