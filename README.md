# NovaBite AI Restaurant Assistant
### Multi-Agent RAG System

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Architecture Explanation](#architecture-explanation)
4. [RAG Design Decisions](#rag-design-decisions)
5. [Tool Simulation Explanation](#tool-simulation-explanation)
6. [Memory Design Explanation](#memory-design-explanation)
7. [Example Queries and Outputs](#example-queries-and-outputs)
8. [Setup and Running](#setup-and-running)
9. [Assumptions Made](#assumptions-made)

---

## Project Overview

NovaBite AI Assistant is a multi-agent system that handles customer queries for a restaurant chain. It combines two approaches:

- **RAG Agent** — answers questions from a knowledge base (menu, hours, policies, events)
- **Operations Agent** — handles live tasks using tools (bookings, availability, specials, loyalty points)

A central **Orchestrator** uses an LLM to classify the intent of each message and route it to the right agent. Conversation memory is maintained across turns so the assistant feels like a continuous conversation.

---

## Project Structure

```
novabite_multi_agent/
|
|-- main.py                    # Entry point - starts the chat loop
|-- config.py                  # All settings, API keys, shared LLM and embeddings
|-- memory.py                  # Conversation memory using ChatMessageHistory
|-- intent_classifier.py       # LLM-based intent routing
|
|-- orchestrator/
|   |-- orchestrator_agent.py  # Loads memory, classifies intent, routes to correct agent
|
|-- agents/
|   |-- rag_agent.py           # Retrieves from Chroma, answers using context
|   |-- operations_agent.py    # LangGraph ReAct agent with 4 tools
|
|-- tools/
|   |-- operations_tools.py    # 4 simulated backend tools with in-memory database
|
|-- rag/
|   |-- ingest.py              # Loads, chunks, embeds, and saves docs to Chroma
|   |-- retriever.py           # Loads Chroma, auto-ingests if empty
|
|-- data/
|   |-- novabite_docs.txt      # Knowledge base: menu, hours, policies, events, loyalty
|
|-- .env.example
|-- requirements.txt
```

---

## Architecture Explanation

```
User Message
     |
     v
intent_classifier       <- LLM call: returns rag / ops / greeting / farewell
     |
     v
orchestrator            <- loads memory, routes message, saves response to memory
     |
     |----------------------|
     v                      v
RAG Agent           Operations Agent
  |                   |
retriever           LangGraph ReAct agent
  |                   |
Chroma DB           Tools:
  |                   - check_table_availability
LLM answer            - book_table
                      - get_today_special
                      - check_loyalty_points
```

### Component Breakdown

**intent_classifier.py**
Sends the user message to the LLM with a prompt asking it to return one word: `rag`, `ops`, or `farewell`. This is more robust than keyword matching because it understands phrasing variations naturally.

**orchestrator_agent.py**
The central coordinator. It does not answer questions itself. It loads conversation history, calls the intent classifier, passes the message to the right agent, and saves the result back to memory.

**agents/rag_agent.py**
Retrieves the top relevant chunks from Chroma using MMR, injects them into a prompt as context, and asks the LLM to answer using only that context. If the context does not contain the answer, the LLM is instructed to say so.

**agents/operations_agent.py**
A LangGraph `create_react_agent` that has access to 4 tools. The LLM decides which tool to call, calls it, reads the result, and forms a response. This is the ReAct pattern (Reason + Act).

---

## RAG Design Decisions

### Document Ingestion Pipeline

File: `rag/ingest.py`

Steps:
1. Load `menu.txt` using `TextLoader`
2. Split into chunks using `RecursiveCharacterTextSplitter`
3. Embed each chunk using `text-embedding-3-small`
4. Save all vectors to Chroma

Ingestion runs automatically on first use. The retriever checks if Chroma is empty and calls `ingest()` if it is. You can also trigger it manually:



---

### Chunking Strategy

**chunk_size=500, chunk_overlap=50**

Why 500 characters? Each entry in the knowledge base (a menu item, a policy rule, an event package) is a self-contained paragraph. 500 characters is large enough to keep a full dish description — name, price, ingredients, dietary tags, and allergens — in one chunk without splitting it.

Why 50 character overlap? If a dish name ends one chunk and its allergen list starts the next, the overlap ensures the allergen chunk still carries the dish name as context.

Why RecursiveCharacterTextSplitter? It splits different separators; on paragraph first, then line breaks, then spaces. This respects the natural structure of the document rather than cutting at arbitrary character positions.

---

### Embedding Model

**text-embedding-3-small via OpenRouter**

- Better retrieval performance than the older ada-002 model
- Low cost at approximately $0.02 per 1 million tokens
- 1536-dimensional vectors with strong semantic understanding
- Uses the same OpenRouter API key as the LLM — no second key needed

---

### Vector Database

**Chroma (local, persistent)**

Chroma was chosen over FAISS because it automatically persists to a `chroma_db/` folder on disk with no manual save or load calls needed. Simple to set up with no external services required. Easy to wipe and rebuild during development by deleting the folder and re-running ingestion.

---

### Retrieval Strategy

**MMR (Maximal Marginal Relevance) — k=4, fetch_k=10**

MMR fetches 10 candidate chunks by similarity score, then selects the 4 most diverse ones. This prevents returning 4 nearly identical overlapping chunks from the same section and ensures a broader, more useful context is passed to the LLM.

---

### Context Filtering

Retrieved chunks are joined and placed in the prompt under a `Context:` block. The prompt explicitly tells the LLM to answer using only that context. This means the model is constrained to what was retrieved from the knowledge base, not its general training knowledge.

---

### Hallucination Prevention

Two layers:

**1. Prompt constraint**
The system prompt says: *"If the answer is not in the context, say I don't have that information, please contact the restaurant."* The LLM has an explicit safe fallback instead of being left to guess.

**2. Retrieval grounding**
The LLM only sees the retrieved chunks as its information source. It cannot confidently fabricate details about dishes or policies that were not retrieved.

---

### Grounded Answer Generation

Prompt structure:



---

## Tool Simulation Explanation

The tools simulate a real restaurant backend using in-memory Python dictionaries. In production, each function body would be replaced with an HTTP call to a reservations API, a CRM, or a kitchen system. The tool interface and the agent that calls them would not change at all.

### Tools

| Tool | What it does |
|------|-------------|
| check_table_availability | Looks up reservations_db, subtracts seats_taken from BRANCH_CAPACITY (20) to return real availability |
| book_table | Checks availability, updates reservations_db, logs the booking in bookings_db with an auto-incrementing ID |
| get_today_special | Returns today's specials from specials_db for the requested branch with today's actual date |
| check_loyalty_points | Looks up the customer in loyalty_db by user ID and returns their points and tier benefit |

### Why the @tool decorator?

The `@tool` decorator wraps the function as a `StructuredTool` that the LangGraph (ReAct agent) can discover and call. The docstring is required — the agent reads it to understand what the tool does and when to use it.


---

## Memory Design Explanation

Each session has its own `ChatMessageHistory` stored in a dict keyed by session ID. After each turn, the orchestrator calls `history.add_user_message()` and `history.add_ai_message()` to save the exchange. On the next turn the full history is loaded and passed to the active agent.

The RAG agent converts history to a plain string for the prompt. The operations agent passes the message list directly to the LangGraph agent.

**Limitation:** Memory is in-process only and resets when the program restarts.

---

## Example Queries and Outputs

