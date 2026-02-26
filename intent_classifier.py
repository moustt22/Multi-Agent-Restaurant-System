from langchain_core.prompts import ChatPromptTemplate
import os
import sys
sys.path.append(os.path.dirname(__file__))
from config import llm

prompt = ChatPromptTemplate.from_template("""
You are a router for a restaurant assistant.
Given the conversation history and the latest user message, reply with ONLY one word — the correct route:

- "rag"      -> user is asking about menu items, food descriptions, allergens, opening hours, policies, events, loyalty program rules
- "ops"      -> user wants to: check table availability, book a table, see today's special dish, check loyalty points balance
- "farewell" -> user is saying bye or ending the conversation

Routing rules:
- "today's special", "special dish", "what's special today", "daily special" → always "ops"
- "yes", "yes please", "sure", "go ahead", "book it", "ok" after a booking discussion → "ops"
- Questions about what food exists on the menu → "rag"
- Questions about opening hours, policies, allergens → "rag"

Conversation history:
{history}

Latest user message: {message}

Reply with only one word (rag / ops / farewell):
""")

chain = prompt | llm

def classify_intent(message: str, history: str = "") -> str:
    result = chain.invoke({"message": message, "history": history})
    intent = result.content.strip().lower()

    if intent not in ["rag", "ops", "farewell"]:
        return "rag"

    return intent
