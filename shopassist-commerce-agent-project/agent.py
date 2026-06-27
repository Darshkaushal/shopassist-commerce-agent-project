"""Compatibility entry point for the company assignment.

The assignment asks for create a function:
    run_agent(question: str) -> str

Import it from this file or from shopassist_agent.agent.
"""

from shopassist_agent.agent import run_agent, run_agent_detailed


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
