from langchain_core.prompts import ChatPromptTemplate
import os
import sys
sys.path.append(os.path.dirname(__file__))
from config import llm

prompt = ChatPromptTemplate.from_template("""
You are a router for a restaurant assistant.
Given the user message, reply with ONLY one word — the correct route:

- "rag"      → user is asking about menu, food, allergens, hours, policies, events, loyalty program info
- "ops"      → user wants to check table availability, book a table, see today's specials, or check loyalty points
- "farewell" → user is saying bye or ending the conversation

User message: {message}

Reply with only one word (rag / ops / farewell):
""")

chain = prompt | llm

def classify_intent(message: str) -> str:
    result = chain.invoke({"message": message})
    intent = result.content.strip().lower()

    if intent not in ["rag", "ops", "greeting", "farewell"]:
        return "rag"


    return intent
