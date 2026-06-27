"""Interactive CLI for quick local testing."""

from shopassist_agent.agent import run_agent


def main() -> None:
    print("ShopAssist Agent CLI")
    print("Type 'exit' to stop. Example: Where is order ORD-1002?")
    while True:
        question = input("\nCustomer: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        print("Agent:", run_agent(question))


if __name__ == "__main__":
    main()
