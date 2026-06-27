from shopassist_agent.agent import run_agent, run_agent_detailed
from shopassist_agent.nlu import classify, normalize_id, extract_budget, extract_category
from shopassist_agent.tools import get_order, get_product, search_products


def test_required_run_agent_returns_string():
    answer = run_agent("Where is order ORD-1002?")
    assert isinstance(answer, str)
    assert len(answer) > 20


def test_order_status_uses_order_tool():
    result = run_agent_detailed("Where is order ORD-1002?")
    assert result.intent == "order_status"
    assert "Shipped" in result.answer
    assert any(call.name == "get_order" for call in result.tool_calls)


def test_order_status_enriches_product_names():
    answer = run_agent("Track ORD-1002")
    assert "AeroFlex Running Shoes" in answer


def test_invalid_order_is_graceful():
    answer = run_agent("Where is order ORD-9999?")
    assert "could not find" in answer.lower()
    assert "ORD-9999" in answer


def test_product_lookup_valid_product():
    answer = run_agent("Tell me about P-4001")
    assert "BassBeat Wireless Headphones" in answer
    assert "₹2,499" in answer


def test_product_lookup_invalid_product():
    answer = run_agent("Tell me about P-9999")
    assert "could not find" in answer.lower()


def test_product_search_under_budget():
    answer = run_agent("Show me shoes under 2000")
    assert "under ₹2,000" in answer
    assert "Budget Street Sneakers" in answer
    assert "Classic Canvas" not in answer  # out-of-stock product should not be recommended


def test_product_search_category():
    result = run_agent_detailed("Recommend a backpack")
    assert result.intent == "product_search"
    assert "Backpack" in result.answer
    assert any(call.name == "search_products" for call in result.tool_calls)


def test_empty_search_result_without_guessing():
    answer = run_agent("Show me camera under 500")
    assert "could not find" in answer.lower()


def test_cheaper_alternative_from_order():
    result = run_agent_detailed("Is there a cheaper alternative to the shoes I ordered in ORD-1002?")
    assert result.intent == "alternative_search"
    assert "cheaper" in result.answer.lower()
    assert "Budget Street Sneakers" in result.answer
    tool_names = [call.name for call in result.tool_calls]
    assert "get_order" in tool_names
    assert "get_product" in tool_names
    assert "search_products" in tool_names


def test_cheaper_alternative_from_product():
    answer = run_agent("Find cheaper alternative to P-1002")
    assert "Budget Street Sneakers" in answer


def test_multi_item_order_alternative():
    answer = run_agent("cheaper alternative to bag in ORD-1005")
    assert "LiteCarry Backpack" in answer


def test_no_cheaper_available_message():
    answer = run_agent("cheaper alternative to P-3002")
    assert "could not find a cheaper available option" in answer.lower()


def test_greeting():
    answer = run_agent("hi")
    assert "ShopAssist" in answer


def test_fallback_guides_user():
    answer = run_agent("what is your return policy")
    assert "order status" in answer.lower()
    assert "product" in answer.lower()


def test_empty_question():
    result = run_agent_detailed("   ")
    assert result.intent == "empty_question"


def test_tool_get_order():
    assert get_order("ord-1002")["order_id"] == "ORD-1002"
    assert get_order("ORD-9999") is None


def test_tool_get_product():
    assert get_product("p-1002")["name"] == "AeroFlex Running Shoes"
    assert get_product("P-9999") is None


def test_tool_search_products():
    results = search_products("shoes")
    assert len(results) >= 3
    assert any(product["product_id"] == "P-1003" for product in results)


def test_normalize_id():
    assert normalize_id("ord 1002") == "ORD-1002"
    assert normalize_id("p1002") == "P-1002"


def test_extract_budget():
    assert extract_budget("shoes under 2000") == 2000
    assert extract_budget("budget 1500") == 1500


def test_extract_category():
    assert extract_category("show sneakers") == "shoes"
    assert extract_category("need backpack") == "bag"


def test_classify_entities():
    nlu = classify("Is there a cheaper alternative to the shoes I ordered in ORD-1002?")
    assert nlu.intent == "alternative_search"
    assert nlu.entities["order_id"] == "ORD-1002"
    assert nlu.entities["category"] == "shoes"
