import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from memory import get_session_history
from intent_classifier import classify_intent
from Agents.rag_agent import run_rag_agent
from Agents.op_agent import run_operations_agent


def chat(user_message: str, session_id: str = "default") -> str:
    history = get_session_history(session_id)
    chat_history = history.messages

    history_str = "\n".join(
        f"{'Customer' if i % 2 == 0 else 'Assistant'}: {msg.content}"
        for i, msg in enumerate(chat_history)
    )

    intent = classify_intent(user_message, history=history_str)
    print(f"[Intent: {intent}]")

    if intent == "farewell":
        response = "Thanks for visiting NovaBite! We hope to see you soon. Bon appétit!"

    elif intent == "ops":
        response = run_operations_agent(user_message, chat_history)

    else:
        response = run_rag_agent(user_message, history_str)

    history.add_user_message(user_message)
    history.add_ai_message(response)

    return response