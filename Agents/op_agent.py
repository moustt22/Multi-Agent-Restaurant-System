from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import llm
from tools.op_tools import check_table_availability, book_table, get_today_special, check_loyalty_points


tools = [check_table_availability, book_table, get_today_special, check_loyalty_points]

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are an operations assistant for NovaBite Restaurants. Use the tools to help the customer with bookings, availability, specials, and loyalty points."
)

def run_operations_agent(message: str, chat_history: list = []) -> str:
    messages = chat_history + [HumanMessage(content=message)]
    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content
