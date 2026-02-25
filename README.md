# Multi-Agent RAG System – Smart Restaurant Assistant

---

# 📌 Scenario

You are building an AI system for a restaurant chain called:

# **NovaBite Restaurants**

NovaBite operates multiple branches and wants an AI assistant that can:

- Answer customer questions from internal knowledge base (RAG)
- Check live table availability
- Provide menu recommendations
- Handle follow-up questions using memory
- Call backend tools (MCP-style or simulated server logic)
- Route tasks intelligently using sub-agents

The system **must** be architected using:

- LangChain
- Sub-agents
- RAG
- Tool-based execution
- Memory
- Proper orchestration

> ⚠️ This is NOT a chatbot demo.  
> This is a real system design + implementation evaluation.

---

# 🎯 Goal

Build a production-style **multi-agent architecture** that:

- Uses RAG for restaurant knowledge
- Uses tool-calling for operational tasks
- Delegates properly through sub-agents
- Demonstrates memory continuity
- Minimizes hallucinations
- Can be evaluated for retrieval accuracy

---

# 🏗️ Required Architecture

You must implement the following components:

---

## 1️⃣ Main Orchestrator Agent

### Responsibilities

- Classify user intent
- Route requests to appropriate sub-agent
- Maintain conversation memory
- Merge and validate sub-agent responses
- Decide when to call tools
- Handle ambiguity and clarification
- Prevent hallucinated outputs

⚠️ The orchestrator must NOT contain business logic directly.  
It must delegate to sub-agents.

---

## 2️⃣ Required Sub-Agents

---

### 🍽️ A. Restaurant Knowledge RAG Agent

Responsible for answering questions from internal documents such as (You don't have to implement all domains below just pick 2):

- Menu descriptions  
- Allergen information  
- Opening hours  
- Branch policies  
- Loyalty program rules  
- Refund policy  
- Event hosting information  

---

### 🔍 RAG Implementation Requirements

You must implement:

- Document ingestion pipeline
- Chunking strategy (**justify your choice**)
- Embedding model (**justify your choice**)
- Vector database (FAISS / Chroma / etc.)
- Retrieval strategy (top-k, optional hybrid)
- Context filtering
- Hallucination prevention
- Grounded answer generation

Your system must NOT hallucinate nonexistent menu items.

---

### Example RAG Queries

- “Do you have vegan pasta?”
- “Is the chicken grilled or fried?”
- “What are your opening hours on weekends?”
- “Do you host birthday events?”
- “What’s included in the premium catering package?”

---

### 🛠️ B. Operations Agent (Tool-Based / MCP-Style)

This agent handles live operational queries.

You may:

- Connect to a real MCP server  
**OR**
- Implement functions that simulate server logic

The system must behave like it is calling real external tools.

---

### Required Tools (Implement At Least Two)


check_table_availability(date, time, branch)
book_table(name, date, time, branch)
get_today_special(branch)
check_loyalty_points(user_id)


---

# ⏳ Time Limit

You have **2 days (48 hours)** from the moment you receive this test to complete and submit your solution.

---

# 📬 Submission Instructions

1. Fork the provided repository.
2. Implement your solution in your fork.
3. Ensure your repository includes:
   - Complete source code
   - Updated README with:
     - Architecture explanation
     - RAG design decisions
     - Tool simulation or MCP integration explanation
     - Memory design explanation
     - Example queries and outputs
     - Assumptions made
4. Push your final implementation to your forked repository.
5. Send the repository link via email to:

📩 **careers@fekracorp.com**
