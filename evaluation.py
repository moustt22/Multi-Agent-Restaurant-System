import json
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from config import llm
from RAG.retriever import get_retriever
from Agents.rag_agent import run_rag_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


judge_prompt = ChatPromptTemplate.from_template("""
You are evaluating a RAG system for a restaurant assistant.

Question: {question}
Retrieved Context: {context}
Answer: {answer}

Score the answer on two criteria from 1 to 5:

Faithfulness: Is the answer based only on the retrieved context? Does it avoid making up information?
- 5: Fully grounded in context, nothing fabricated
- 3: Mostly grounded but some minor unsupported claims
- 1: Answer contains made-up information not in the context

Relevance: Does the answer actually address what the customer asked?
- 5: Directly and completely answers the question
- 3: Partially answers the question
- 1: Does not answer the question at all

Reply in this exact JSON format with no extra text:
{{
  "faithfulness": <score>,
  "relevance": <score>,
  "faithfulness_reason": "<one sentence>",
  "relevance_reason": "<one sentence>"
}}
""")

judge_chain = judge_prompt | llm | StrOutputParser()

TEST_CASES = [
    "Do you have vegan options?",
    "What are the opening hours on weekends?",
    "Is the chicken grilled or fried?",
    "Where are your branches?",
    "Do you host birthday events?",
    "What is included in the premium catering package?",
    "Do you have parking?",
    "Do you serve sushi?",
]

def evaluate_single(question: str) -> dict:
    retriever = get_retriever()
    docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in docs)
    answer = run_rag_agent(question)

    raw = judge_chain.invoke({
        "question": question,
        "context": context,
        "answer": answer
    })

    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        scores = {
            "faithfulness": 0,
            "relevance": 0,
            "faithfulness_reason": "Could not parse judge response",
            "relevance_reason": "Could not parse judge response"
        }

    return {
        "question": question,
        "answer": answer,
        "faithfulness": scores.get("faithfulness", 0),
        "relevance": scores.get("relevance", 0),
        "faithfulness_reason": scores.get("faithfulness_reason", ""),
        "relevance_reason": scores.get("relevance_reason", "")
    }


def save_results(results: list):
    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_rel   = sum(r["relevance"]    for r in results) / len(results)
    overall   = (avg_faith + avg_rel) / 2

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename  = f"evaluation_results.txt"

    lines = []
    lines.append("=" * 60)
    lines.append("NovaBite RAG Evaluation — LLM-as-a-Judge")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)

    for i, r in enumerate(results, 1):
        lines.append(f"\n[{i}] Question:  {r['question']}")
        lines.append(f"    Answer:    {r['answer']}")
        lines.append(f"    Faithfulness: {r['faithfulness']}/5 — {r['faithfulness_reason']}")
        lines.append(f"    Relevance:    {r['relevance']}/5 — {r['relevance_reason']}")

    lines.append("\n" + "=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Average Faithfulness : {avg_faith:.1f} / 5")
    lines.append(f"Average Relevance    : {avg_rel:.1f} / 5")
    lines.append(f"Overall Score        : {overall:.1f} / 5")
    lines.append("=" * 60)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nResults saved to {filename}")


def run_evaluation():
    print("=" * 60)
    print("NovaBite RAG Evaluation — LLM-as-a-Judge")
    print("=" * 60)

    results = []

    for i, question in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {question}")
        result = evaluate_single(question)
        results.append(result)

        print(f"  Answer:       {result['answer'][:80]}...")
        print(f"  Faithfulness: {result['faithfulness']}/5 — {result['faithfulness_reason']}")
        print(f"  Relevance:    {result['relevance']}/5 — {result['relevance_reason']}")

    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    avg_rel   = sum(r["relevance"]    for r in results) / len(results)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Average Faithfulness : {avg_faith:.1f} / 5")
    print(f"  Average Relevance    : {avg_rel:.1f} / 5")
    print(f"  Overall Score        : {(avg_faith + avg_rel) / 2:.1f} / 5")
    print("=" * 60)

    save_results(results)
    return results


if __name__ == "__main__":
    run_evaluation()