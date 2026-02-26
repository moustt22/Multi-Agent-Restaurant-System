from langchain_core.prompts import ChatPromptTemplate
import os
import sys
sys.path.append(os.path.dirname(__file__))
from config import llm

prompt = ChatPromptTemplate.from_template("""
You are a router for a restaurant assistant.
Given the conversation history and the latest user message, reply with ONLY one word — the correct route:

- "rag"      -> user is asking about menu, food, allergens, hours, policies, events, loyalty program info
- "ops"      -> user wants to check table availability, book a table, see today's specials, or check loyalty points
- "greeting" -> user is saying hello or starting a conversation
- "farewell" -> user is saying bye or ending the conversation

Important: if the user message is a short reply like "yes", "yes please", "go ahead", "sure", "ok", "book it"
and the conversation history shows they were just discussing a booking or availability,
classify it as "ops".

Conversation history:
{history}

Latest user message: {message}

Reply with only one word (rag / ops / greeting / farewell):
""")

chain = prompt | llm

def classify_intent(message: str, history: str = "") -> str:
    result = chain.invoke({"message": message, "history": history})
    intent = result.content.strip().lower()

    if intent not in ["rag", "ops", "greeting", "farewell"]:
        return "rag"

    return intent
