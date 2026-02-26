from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import llm
from RAG.retriever import get_retriever


rewrite_prompt = ChatPromptTemplate.from_template("""
Given the conversation history and the latest message, rewrite the latest message
as a standalone search query that includes all necessary context.

Conversation history:
{chat_history}

Latest message: {question}

Standalone search query (one sentence, no explanation):
""")

answer_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant for NovaBite Restaurants.
Answer the customer's question using ONLY the context below.

Rules:
- If the context contains the answer, respond clearly and helpfully.
- If the customer asks about something that is clearly not a NovaBite product or service, confidently say we don't offer that and suggest what we do have instead.
- Only say "I don't have that information, please contact the restaurant" if the question is about NovaBite specifically but the answer is genuinely missing from the context.
- Never make up menu items, prices, hours, or policies that are not in the context.
- When referencing prices, copy them exactly from the retrieved context.

Context:
{context}

Chat history:
{chat_history}

Customer: {question}
Answer:
""")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def fix_prices(text: str) -> str:
    return re.sub(r'`(\d+)', r'$\1', text)

def run_rag_agent(question: str, chat_history: str = "") -> str:
    retriever = get_retriever()

    if chat_history:
        rewrite_chain = rewrite_prompt | llm | StrOutputParser()
        search_query = rewrite_chain.invoke({
            "chat_history": chat_history,
            "question": question
        })
    else:
        search_query = question

    docs = retriever.invoke(search_query)
    context = format_docs(docs)

    answer_chain = answer_prompt | llm | StrOutputParser()
    return answer_chain.invoke({
        "context": context,
        "chat_history": chat_history,
        "question": question
    })
