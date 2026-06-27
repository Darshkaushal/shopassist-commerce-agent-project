from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
ADMIN_HEADERS = {"X-Admin-Key": "shopassist-admin-2026"}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_agent_api_returns_trace():
    response = client.post("/api/agent/ask", json={"question": "Where is order ORD-1002?"})
    assert response.status_code == 200
    data = response.json()
    assert "Shipped" in data["answer"]
    assert data["intent"] == "order_status"
    assert len(data["tool_calls"]) >= 1


def test_simple_agent_api_returns_answer_only():
    response = client.post("/api/agent/simple", json={"question": "Tell me about P-4001"})
    assert response.status_code == 200
    assert set(response.json().keys()) == {"answer"}
    assert "BassBeat" in response.json()["answer"]


def test_order_not_found_returns_404():
    response = client.get("/api/orders/ORD-9999")
    assert response.status_code == 404


def test_product_search_endpoint_filters_budget():
    response = client.get("/api/products/search", params={"query": "shoes", "budget": 2000})
    assert response.status_code == 200
    products = response.json()
    assert products
    assert all(product["price"] <= 2000 for product in products)
    assert all(product["stock"] > 0 for product in products)


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_products"] >= 1
    assert data["total_orders"] >= 1


def test_order_status_update_requires_admin_key():
    response = client.patch("/api/admin/orders/ORD-1003/status", json={"status": "Delivered"})
    assert response.status_code == 401


def test_admin_order_status_update_endpoint_dispatch_and_deliver():
    response = client.patch(
        "/api/admin/orders/ORD-1003/status",
        headers=ADMIN_HEADERS,
        json={
            "status": "Dispatched",
            "carrier": "Delhivery",
            "tracking_id": "TRK-TEST1003",
            "eta": "Expected by tomorrow",
            "last_update": "Package has been dispatched from the warehouse.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Dispatched"
    assert data["tracking_id"] == "TRK-TEST1003"

    response = client.patch("/api/admin/orders/ORD-1003/status", headers=ADMIN_HEADERS, json={"status": "Delivered"})
    assert response.status_code == 200
    assert response.json()["status"] == "Delivered"


def test_admin_order_status_update_rejects_invalid_status():
    response = client.patch("/api/admin/orders/ORD-1003/status", headers=ADMIN_HEADERS, json={"status": "Lost in space"})
    assert response.status_code == 400


def test_admin_order_list_requires_key():
    response = client.get("/api/admin/orders")
    assert response.status_code == 401

    response = client.get("/api/admin/orders", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_order_status_options_endpoint():
    response = client.get("/api/order-statuses")
    assert response.status_code == 200
    statuses = [item["status"] for item in response.json()]
    assert "Dispatched" in statuses
    assert "Delivered" in statuses
