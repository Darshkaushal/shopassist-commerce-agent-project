"""In-memory commerce data used by the agent tools.

This keeps the assignment self-contained. In a production system these records
would come from a database or order-management service.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

VALID_ORDER_STATUSES = [
    "Processing",
    "Dispatched",
    "Shipped",
    "Out for Delivery",
    "Delivered",
    "Cancelled",
]

PRODUCTS: dict[str, dict[str, Any]] = {
    "P-4001": {
        "product_id": "P-4001",
        "name": "AeroRun Lite Shoes",
        "category": "shoes",
        "brand": "AeroRun",
        "price": 2499,
        "color": "Black",
        "stock": 12,
        "rating": 4.4,
        "description": "Lightweight running shoes for daily comfort and casual training.",
    },
    "P-4002": {
        "product_id": "P-4002",
        "name": "StreetFlex Sneakers",
        "category": "shoes",
        "brand": "StreetFlex",
        "price": 1799,
        "color": "White",
        "stock": 8,
        "rating": 4.2,
        "description": "Budget-friendly sneakers with soft cushioning and clean streetwear styling.",
    },
    "P-4003": {
        "product_id": "P-4003",
        "name": "UrbanStep Canvas Shoes",
        "category": "shoes",
        "brand": "UrbanStep",
        "price": 1399,
        "color": "Navy",
        "stock": 0,
        "rating": 4.0,
        "description": "Classic canvas shoes for everyday use. Currently out of stock.",
    },
    "P-5001": {
        "product_id": "P-5001",
        "name": "Everyday Cotton T-Shirt",
        "category": "t-shirt",
        "brand": "BasicsCo",
        "price": 699,
        "color": "Blue",
        "stock": 25,
        "rating": 4.3,
        "description": "Soft cotton t-shirt with a regular fit for daily wear.",
    },
    "P-5002": {
        "product_id": "P-5002",
        "name": "Premium Polo T-Shirt",
        "category": "t-shirt",
        "brand": "BasicsCo",
        "price": 1199,
        "color": "Olive",
        "stock": 10,
        "rating": 4.5,
        "description": "Premium polo with breathable fabric and smart casual styling.",
    },
    "P-6001": {
        "product_id": "P-6001",
        "name": "TravelPro Backpack",
        "category": "bag",
        "brand": "TravelPro",
        "price": 1999,
        "color": "Grey",
        "stock": 6,
        "rating": 4.6,
        "description": "Durable backpack with laptop sleeve and multiple compartments.",
    },
}

ORDERS: dict[str, dict[str, Any]] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_name": "Aarav Sharma",
        "status": "Delivered",
        "tracking_id": "TRK-77210",
        "carrier": "BlueDart",
        "eta": "Delivered on 2026-06-24",
        "last_update": "Order was delivered successfully.",
        "items": [
            {"product_id": "P-5001", "quantity": 2},
        ],
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_name": "Priya Mehta",
        "status": "Shipped",
        "tracking_id": "TRK-88420",
        "carrier": "Delhivery",
        "eta": "Expected by 2026-06-28",
        "last_update": "Shipment left Jaipur hub and is in transit.",
        "items": [
            {"product_id": "P-4001", "quantity": 1},
        ],
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_name": "Rahul Verma",
        "status": "Processing",
        "tracking_id": "Not assigned yet",
        "carrier": "Not assigned yet",
        "eta": "Preparing for dispatch",
        "last_update": "Order is confirmed and being packed at the warehouse.",
        "items": [
            {"product_id": "P-6001", "quantity": 1},
            {"product_id": "P-5002", "quantity": 1},
        ],
    },
}


def get_all_orders() -> list[dict[str, Any]]:
    return deepcopy(list(ORDERS.values()))


def get_all_products() -> list[dict[str, Any]]:
    return deepcopy(list(PRODUCTS.values()))


def update_order_record(order_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    order = ORDERS.get(order_id.upper())
    if not order:
        return None
    order.update({k: v for k, v in updates.items() if v is not None and v != ""})
    return deepcopy(order)
