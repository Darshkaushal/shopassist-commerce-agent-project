"""FastAPI backend for ShopAssist Commerce.

Run with:
    uvicorn backend.main:app --reload

The API keeps the assignment logic in the reusable shopassist_agent package and exposes
professional endpoints for the Streamlit UI, tests, and external evaluation.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shopassist_agent.agent import run_agent, run_agent_detailed
from shopassist_agent.data import ORDERS, PRODUCTS, ORDER_STATUSES, STATUS_DESCRIPTIONS, STATUS_PROGRESS
from shopassist_agent.logger import read_recent_logs
from shopassist_agent.tools import get_order, get_product, search_products, update_order_status


ADMIN_API_KEY = os.getenv("SHOPASSIST_ADMIN_KEY", "shopassist-admin-2026")


def require_admin_key(x_admin_key: Optional[str] = Header(default=None, alias="X-Admin-Key")) -> bool:
    """Protect backend-only operations such as fulfillment status updates."""
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Admin API key required for this operation")
    return True


class AskRequest(BaseModel):
    """Request body for customer support questions."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["Where is order ORD-1002?"],
        description="Customer question to be resolved by the support assistant.",
    )


class ToolCallResponse(BaseModel):
    name: str
    input: Dict[str, Any]
    status: str
    output_summary: str
    timestamp: str


class AskResponse(BaseModel):
    answer: str
    intent: str
    confidence: float
    entities: Dict[str, Any]
    tool_calls: List[ToolCallResponse]
    safety_notes: Optional[str] = None


class SimpleAnswerResponse(BaseModel):
    answer: str


class OrderStatusUpdateRequest(BaseModel):
    """Request body for updating fulfillment status from the operations dashboard."""

    status: str = Field(
        ...,
        examples=["Dispatched"],
        description="New order status. Examples: Processing, Dispatched, Shipped, Out for Delivery, Delivered, Cancelled.",
    )
    tracking_id: Optional[str] = Field(default=None, examples=["TRK-88420"], description="Optional courier tracking ID.")
    carrier: Optional[str] = Field(default=None, examples=["Delhivery"], description="Optional courier partner name.")
    eta: Optional[str] = Field(default=None, examples=["Expected by 2026-06-28"], description="Optional customer-facing ETA.")
    last_update: Optional[str] = Field(
        default=None,
        examples=["Package has been dispatched from Jaipur warehouse."],
        description="Optional customer-facing update note.",
    )


app = FastAPI(
    title="ShopAssist Commerce API",
    version="1.0.0",
    description=(
        "Backend for the ShopAssist commerce support project. "
        "It exposes assistant, order, product, search, metrics, logs, and protected admin fulfillment endpoints."
    ),
    contact={"name": "ShopAssist Demo"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _public_product(product: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(product)
    item.pop("_score", None)
    return item


@app.get("/", tags=["System"])
def root() -> Dict[str, str]:
    """API landing response."""
    return {
        "service": "ShopAssist Commerce API",
        "status": "online",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health() -> Dict[str, Any]:
    """Health check for deployment platforms."""
    return {
        "status": "healthy",
        "products": len(PRODUCTS),
        "orders": len(ORDERS),
    }


@app.post("/api/agent/ask", response_model=AskResponse, tags=["Assistant"])
def ask_agent(payload: AskRequest) -> Dict[str, Any]:
    """Resolve a customer question and return answer plus internal data checks."""
    result = run_agent_detailed(payload.question)
    return result.to_dict()


@app.post("/api/agent/simple", response_model=SimpleAnswerResponse, tags=["Assistant"])
def ask_agent_simple(payload: AskRequest) -> Dict[str, str]:
    """Assignment-compatible API endpoint that returns only the customer-facing answer."""
    return {"answer": run_agent(payload.question)}


@app.get("/api/orders", tags=["Orders"])
def list_orders(status: Optional[str] = Query(default=None, description="Optional order status filter")) -> List[Dict[str, Any]]:
    """List mock orders for dashboard/demo review."""
    orders = list(ORDERS.values())
    if status:
        orders = [order for order in orders if order["status"].lower() == status.lower()]
    return orders


@app.get("/api/orders/{order_id}", tags=["Orders"])
def order_details(order_id: str) -> Dict[str, Any]:
    """Fetch one order by order ID using the required get_order tool."""
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id.upper()} was not found")
    return order


@app.get("/api/order-statuses", tags=["Orders"])
def order_statuses() -> List[Dict[str, Any]]:
    """Return supported order statuses for dashboards and external clients."""
    return [
        {
            "status": status,
            "progress": STATUS_PROGRESS.get(status, 0),
            "description": STATUS_DESCRIPTIONS.get(status, ""),
        }
        for status in ORDER_STATUSES
    ]


@app.get("/api/admin/orders", tags=["Admin"])
def admin_list_orders(_: bool = Depends(require_admin_key)) -> List[Dict[str, Any]]:
    """Protected backend order list for the internal operations panel."""
    return list(ORDERS.values())


@app.patch("/api/admin/orders/{order_id}/status", tags=["Admin"])
def admin_update_order_status_endpoint(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    _: bool = Depends(require_admin_key),
) -> Dict[str, Any]:
    """Protected backend operation to update fulfillment status such as Dispatched or Delivered."""
    try:
        order = update_order_status(
            order_id,
            payload.status,
            tracking_id=payload.tracking_id,
            carrier=payload.carrier,
            eta=payload.eta,
            last_update=payload.last_update,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id.upper()} was not found")
    return order


@app.patch("/api/orders/{order_id}/status", tags=["Admin"], deprecated=True)
def update_order_status_endpoint(
    order_id: str,
    payload: OrderStatusUpdateRequest,
    _: bool = Depends(require_admin_key),
) -> Dict[str, Any]:
    """Backward-compatible protected route. Use /api/admin/orders/{order_id}/status."""
    return admin_update_order_status_endpoint(order_id, payload)


@app.get("/api/products", tags=["Products"])
def list_products(
    category: Optional[str] = Query(default=None, description="Optional category filter"),
    in_stock: bool = Query(default=False, description="Return only in-stock products"),
) -> List[Dict[str, Any]]:
    """List products with optional category and stock filters."""
    products = [_public_product(product) for product in PRODUCTS.values()]
    if category:
        products = [product for product in products if product["category"].lower() == category.lower()]
    if in_stock:
        products = [product for product in products if product["stock"] > 0]
    return products


@app.get("/api/products/search", tags=["Products"])
def product_search(
    query: str = Query(..., min_length=1, description="Keyword/category search query"),
    budget: Optional[int] = Query(default=None, ge=1, description="Optional maximum price"),
    in_stock: bool = Query(default=True, description="Return only available products by default"),
) -> List[Dict[str, Any]]:
    """Search products using the required search_products tool."""
    products = [_public_product(product) for product in search_products(query)]
    if in_stock:
        products = [product for product in products if product["stock"] > 0]
    if budget is not None:
        products = [product for product in products if product["price"] <= budget]
    return products


@app.get("/api/products/{product_id}", tags=["Products"])
def product_details(product_id: str) -> Dict[str, Any]:
    """Fetch one product by product ID using the required get_product tool."""
    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id.upper()} was not found")
    return _public_product(product)


@app.get("/api/logs", tags=["Operations"])
def recent_logs(limit: int = Query(default=50, ge=1, le=200)) -> List[Dict[str, Any]]:
    """Return recent JSONL activity logs for review and debugging."""
    return read_recent_logs(limit=limit)


@app.get("/api/metrics", tags=["Operations"])
def metrics() -> Dict[str, Any]:
    """Small dashboard metrics for the web UI and evaluation discussion."""
    products = list(PRODUCTS.values())
    orders = list(ORDERS.values())
    in_stock_products = [product for product in products if product["stock"] > 0]
    low_stock_products = [product for product in products if 0 < product["stock"] <= 10]
    status_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    for order in orders:
        status_counts[order["status"]] = status_counts.get(order["status"], 0) + 1
    for product in products:
        category_counts[product["category"]] = category_counts.get(product["category"], 0) + 1
    return {
        "total_products": len(products),
        "in_stock_products": len(in_stock_products),
        "total_inventory_units": sum(product["stock"] for product in products),
        "low_stock_products": len(low_stock_products),
        "total_orders": len(orders),
        "status_counts": status_counts,
        "category_counts": category_counts,
    }
