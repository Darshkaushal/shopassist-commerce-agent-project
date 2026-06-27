"""Core ShopAssist agent implementation.

Important: this file contains the actual implementation. Do not import
`run_agent` from `shopassist_agent.agent` inside this same file, because that
creates a circular import.
"""

from __future__ import annotations

from typing import Any

from .logger import log_event
from .nlu import detect_category, detect_intent, extract_budget, extract_order_id, extract_product_id
from .tools import get_order, get_product, search_products


def _format_product(product: dict[str, Any]) -> str:
    stock_text = "available" if product.get("stock", 0) > 0 else "currently out of stock"
    return f"{product['name']} ({product['product_id']}) for ₹{product['price']} — {stock_text}, rated {product.get('rating', 'N/A')}/5"


def _ordered_products(order: dict[str, Any]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for item in order.get("items", []):
        product = get_product(item.get("product_id", ""))
        if product:
            product["quantity"] = item.get("quantity", 1)
            products.append(product)
    return products


def run_agent_detailed(question: str) -> dict[str, Any]:
    question = (question or "").strip()
    intent = detect_intent(question)
    trace: list[str] = [f"Detected intent: {intent}"]
    tools_used: list[str] = []

    if not question:
        return {
            "answer": "Please enter a customer question so I can help with order or product support.",
            "intent": "empty",
            "tools_used": [],
            "trace": ["Question was empty"],
        }

    if intent == "order_status":
        order_id = extract_order_id(question)
        trace.append(f"Extracted order ID: {order_id}")
        tools_used.append("get_order")
        order = get_order(order_id or "")
        if not order:
            answer = f"I could not find order {order_id}. Please check the order ID and try again."
        else:
            answer = (
                f"Order {order['order_id']} for {order['customer_name']} is currently {order['status']}. "
                f"Tracking ID: {order['tracking_id']}. Courier: {order['carrier']}. "
                f"ETA: {order['eta']}. Latest update: {order['last_update']}"
            )

    elif intent == "cheaper_alternative":
        order_id = extract_order_id(question)
        product_id = extract_product_id(question)
        source_product: dict[str, Any] | None = None

        if order_id:
            trace.append(f"Extracted order ID: {order_id}")
            tools_used.append("get_order")
            order = get_order(order_id)
            if not order:
                answer = f"I could not find order {order_id}, so I cannot compare its product."
                return _result(answer, intent, tools_used, trace, question)
            order_products = _ordered_products(order)
            tools_used.append("get_product")
            source_product = order_products[0] if order_products else None
        elif product_id:
            trace.append(f"Extracted product ID: {product_id}")
            tools_used.append("get_product")
            source_product = get_product(product_id)

        if not source_product:
            answer = "Please share an order ID or product ID so I can find a cheaper alternative."
        else:
            category = source_product["category"]
            max_price = int(source_product["price"]) - 1
            trace.append(f"Searching alternatives in category '{category}' below ₹{source_product['price']}")
            tools_used.append("search_products")
            alternatives = [p for p in search_products(category=category, max_price=max_price) if p["product_id"] != source_product["product_id"]]
            if not alternatives:
                answer = f"I could not find a cheaper in-stock alternative to {source_product['name']} right now."
            else:
                top = alternatives[:3]
                answer = "Yes. Here are cheaper available alternatives: " + "; ".join(_format_product(p) for p in top) + "."

    elif intent == "product_detail":
        product_id = extract_product_id(question)
        trace.append(f"Extracted product ID: {product_id}")
        tools_used.append("get_product")
        product = get_product(product_id or "")
        if not product:
            answer = f"I could not find product {product_id}. Please check the product ID and try again."
        else:
            answer = f"{_format_product(product)}. {product.get('description', '')}"

    elif intent in {"budget_search", "product_search"}:
        budget = extract_budget(question)
        category = detect_category(question)
        trace.append(f"Extracted category: {category or 'not specified'}")
        trace.append(f"Extracted budget: {budget if budget else 'not specified'}")
        tools_used.append("search_products")
        products = search_products(query=category or "", category=category, max_price=budget)
        if not products:
            answer = "I could not find matching in-stock products for that request right now."
        else:
            answer = "Here are the best available options: " + "; ".join(_format_product(p) for p in products[:5]) + "."

    else:
        answer = (
            "I can help with order tracking, product details, cheaper alternatives, and budget-based product search. "
            "Please include an order ID like ORD-1002 or a product ID like P-4001."
        )

    return _result(answer, intent, tools_used, trace, question)


def _result(answer: str, intent: str, tools_used: list[str], trace: list[str], question: str) -> dict[str, Any]:
    payload = {"question": question, "intent": intent, "tools_used": tools_used, "answer": answer}
    log_event("agent_call", payload)
    return {"answer": answer, "intent": intent, "tools_used": tools_used, "trace": trace}


def run_agent(question: str) -> str:
    """Required assignment function: run_agent(question: str) -> str."""
    return run_agent_detailed(question)["answer"]


if __name__ == "__main__":
    examples = [
        "Where is order ORD-1002?",
        "Is there a cheaper alternative to the shoes I ordered in ORD-1002?",
        "Show me shoes under 2000",
        "Tell me about product P-4001",
    ]
    for example in examples:
        print(f"Q: {example}")
        print(f"A: {run_agent(example)}\n")
