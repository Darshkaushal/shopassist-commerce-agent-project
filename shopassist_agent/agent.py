"""Core agent implementation.

Required public function:
    run_agent(question: str) -> str

The detailed function returns trace data for the Streamlit UI and tests.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .logger import log_event
from .nlu import classify
from .schemas import AgentResult, ToolCall
from .tools import get_order, get_product, search_products

RUPEE = "₹"


def _money(value: int) -> str:
    return f"{RUPEE}{value:,}"


def _tool_call(name: str, inputs: Dict[str, Any], status: str, output_summary: str) -> ToolCall:
    return ToolCall(name=name, input=inputs, status=status, output_summary=output_summary)


def _product_line(product: Dict[str, Any]) -> str:
    stock_note = "In stock" if product["stock"] > 0 else "Out of stock"
    return f"{product['name']} ({product['product_id']}) - {_money(product['price'])}, {stock_note}, rating {product['rating']}/5"


def _filter_in_stock(products: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [product for product in products if product.get("stock", 0) > 0]


def _friendly_product_list(products: List[Dict[str, Any]], intro: str) -> str:
    if not products:
        return "I could not find matching in-stock products right now. Please try another category or budget."
    lines = [intro]
    for index, product in enumerate(products[:3], start=1):
        lines.append(f"{index}. {_product_line(product)}")
    lines.append("Would you like me to narrow this by budget, brand, or rating?")
    return "\n".join(lines)


def _format_order_status(order: Dict[str, Any]) -> str:
    items = []
    for item in order["items"]:
        product = get_product(item["product_id"])
        product_name = product["name"] if product else item["product_id"]
        items.append(f"{product_name} x {item['quantity']}")
    item_text = ", ".join(items)
    tracking = f" Tracking ID: {order['tracking_id']} via {order['carrier']}." if order.get("tracking_id") else " Tracking details are not generated yet."
    latest_update = str(order['last_update']).rstrip('.')
    return (
        f"Your order {order['order_id']} is currently **{order['status']}**. "
        f"Items: {item_text}. {order['eta']}. "
        f"Latest update: {latest_update}.{tracking}"
    )


def _get_order_with_trace(order_id: str, trace: List[ToolCall]) -> Dict[str, Any] | None:
    order = get_order(order_id)
    trace.append(
        _tool_call(
            "get_order",
            {"order_id": order_id},
            "success" if order else "not_found",
            "Order details found" if order else "No order found for this ID",
        )
    )
    return order


def _get_product_with_trace(product_id: str, trace: List[ToolCall]) -> Dict[str, Any] | None:
    product = get_product(product_id)
    trace.append(
        _tool_call(
            "get_product",
            {"product_id": product_id},
            "success" if product else "not_found",
            _product_line(product) if product else "No product found for this ID",
        )
    )
    return product


def _search_with_trace(query: str, trace: List[ToolCall]) -> List[Dict[str, Any]]:
    products = search_products(query)
    trace.append(
        _tool_call(
            "search_products",
            {"query": query},
            "success",
            f"{len(products)} matching product(s) returned",
        )
    )
    return products


def _handle_order_status(order_id: str, trace: List[ToolCall]) -> str:
    order = _get_order_with_trace(order_id, trace)
    if not order:
        return f"I could not find order {order_id}. Please check the order ID and try again."
    # Chain get_product to enrich item names instead of returning raw IDs.
    for item in order["items"]:
        _get_product_with_trace(item["product_id"], trace)
    return _format_order_status(order)


def _handle_product_lookup(product_id: str, trace: List[ToolCall]) -> str:
    product = _get_product_with_trace(product_id, trace)
    if not product:
        return f"I could not find product {product_id}. Please check the product ID and try again."
    stock_msg = "available" if product["stock"] > 0 else "currently out of stock"
    return (
        f"{product['name']} ({product['product_id']}) is priced at {_money(product['price'])}. "
        f"It is {stock_msg}, rated {product['rating']}/5, and belongs to the {product['category']} category. "
        f"Description: {product['description']}"
    )


def _handle_product_search(entities: Dict[str, Any], question: str, trace: List[ToolCall]) -> str:
    query = str(entities.get("category") or question)
    budget = entities.get("budget")
    products = _search_with_trace(query, trace)
    products = _filter_in_stock(products)
    if budget:
        products = [product for product in products if product["price"] <= int(budget)]
        intro = f"Here are the best in-stock options I found under {_money(int(budget))}:"
    else:
        intro = "Here are the best in-stock options I found:"
    products.sort(key=lambda product: (product["price"], -product["rating"]))
    return _friendly_product_list(products, intro)


def _alternative_for_product(product: Dict[str, Any], trace: List[ToolCall]) -> str:
    category = product["category"]
    candidates = _search_with_trace(category, trace)
    alternatives = [
        candidate
        for candidate in candidates
        if candidate["product_id"] != product["product_id"]
        and candidate["stock"] > 0
        and candidate["price"] < product["price"]
    ]
    alternatives.sort(key=lambda candidate: (candidate["price"], -candidate["rating"]))
    if not alternatives:
        return (
            f"I checked cheaper in-stock alternatives for {product['name']}, but I could not find a cheaper available option right now."
        )
    intro = f"Yes. These are cheaper in-stock alternatives to {product['name']} ({_money(product['price'])}):"
    return _friendly_product_list(alternatives, intro)


def _handle_alternative_search(entities: Dict[str, Any], question: str, trace: List[ToolCall]) -> str:
    if "order_id" in entities:
        order_id = str(entities["order_id"])
        order = _get_order_with_trace(order_id, trace)
        if not order:
            return f"I could not find order {order_id}, so I cannot check alternatives for it. Please verify the order ID."
        products = []
        for item in order["items"]:
            product = _get_product_with_trace(item["product_id"], trace)
            if product:
                products.append(product)
        if not products:
            return "I found the order, but I could not identify its products. Please contact support for manual help."
        # For multi-item orders, focus on first product matching category mentioned by customer, else first item.
        category = entities.get("category")
        chosen = next((p for p in products if p["category"] == category), products[0])
        return _alternative_for_product(chosen, trace)

    if "product_id" in entities:
        product = _get_product_with_trace(str(entities["product_id"]), trace)
        if not product:
            return f"I could not find product {entities['product_id']}, so I cannot compare alternatives."
        return _alternative_for_product(product, trace)

    if "category" in entities:
        products = _search_with_trace(str(entities["category"]), trace)
        products = _filter_in_stock(products)
        budget = entities.get("budget")
        if budget:
            products = [p for p in products if p["price"] <= int(budget)]
        products.sort(key=lambda p: (p["price"], -p["rating"]))
        intro = "Here are affordable in-stock alternatives I found:"
        return _friendly_product_list(products, intro)

    return "Please share an order ID, product ID, or product category so I can find a cheaper alternative accurately."


def run_agent_detailed(question: str) -> AgentResult:
    """Run the agent and return answer plus explainability metadata."""
    clean_question = question.strip()
    trace: List[ToolCall] = []

    if not clean_question:
        return AgentResult(
            answer="Please enter a customer question, for example: 'Where is order ORD-1002?'",
            intent="empty_question",
            confidence=1.0,
            tool_calls=trace,
        )

    nlu = classify(clean_question)
    log_event("agent_decision", {"question": clean_question, "intent": nlu.intent, "entities": nlu.entities})

    if nlu.intent == "greeting":
        answer = (
            "Hi! I am ShopAssist. I can help with order tracking, product details, product search, "
            "and cheaper alternatives. Try asking: 'Where is order ORD-1002?'"
        )
    elif nlu.intent == "order_status":
        answer = _handle_order_status(str(nlu.entities["order_id"]), trace)
    elif nlu.intent == "product_lookup":
        answer = _handle_product_lookup(str(nlu.entities["product_id"]), trace)
    elif nlu.intent == "product_search":
        answer = _handle_product_search(nlu.entities, clean_question, trace)
    elif nlu.intent == "alternative_search":
        answer = _handle_alternative_search(nlu.entities, clean_question, trace)
    else:
        answer = (
            "I can help with order status, product details, product search, or cheaper alternatives. "
            "Please include an order ID like ORD-1002, a product ID like P-1002, or a category like shoes."
        )

    return AgentResult(
        answer=answer,
        intent=nlu.intent,
        confidence=nlu.confidence,
        entities=nlu.entities,
        tool_calls=trace,
        safety_notes="The agent only answers using available mock order/product data and does not fabricate missing information.",
    )


def run_agent(question: str) -> str:
    """Required assignment function: returns only the customer-friendly answer."""
    return run_agent_detailed(question).answer


if __name__ == "__main__":
    demo_questions = [
        "Where is order ORD-1002?",
        "Is there a cheaper alternative to the shoes I ordered in ORD-1002?",
        "Show me shoes under 2000",
        "Tell me about P-4001",
        "Where is order ORD-9999?",
    ]
    for question in demo_questions:
        print("\nCustomer:", question)
        print("Agent:", run_agent(question))
