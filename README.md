# NovaBite AI Restaurant Assistant
### Multi-Agent RAG System
NovaBite AI Assistant is an AI-powered assistant for NovaBite Restaurants that helps customers get answers and take action — all in one conversation.
Customers can ask about the menu, check for allergens, find out opening hours, learn about events and packages, or ask anything covered in the restaurant's knowledge base. They can also check table availability, make a reservation, see today's specials, or look up their loyalty points — just by typing naturally.
The assistant remembers what was said earlier in the conversation, so customers don't have to repeat themselves. It only answers from verified restaurant information, so it will never make something up or give wrong details about the menu or policies.

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
|-- app.py                      # Streamlit chat UI
|-- evaluation.py              # LLM-as-a-judge RAG evaluation
|-- .env.example
|-- requirements.txt
```

---

## Architecture Explanation

```
User Message
     |
     v
intent_classifier       <- LLM call: returns rag / ops / farewell
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
Sends the conversation history and the latest user message to the LLM and asks it to return one word: `rag`, `ops`, or `farewell`. Passing the history is important for short follow-up messages" that have no meaning without context. Explicit routing rules in the prompt handle edge cases.

**orchestrator_agent.py**
The central coordinator. It does not answer questions itself. It loads conversation history, calls the intent classifier, passes the message to the right agent, and saves the result back to memory.

**agents/rag_agent.py**
Before retrieving, rewrites vague follow-up messages into a self-contained search query using the conversation history. Then retrieves the top relevant chunks from Chroma using MMR, injects them as context, and asks the LLM to answer using only that context. If the context does not contain the answer, the LLM is instructed to say so.

**agents/operations_agent.py**
A LangGraph `create_react_agent` that has access to 4 tools. The LLM decides which tool to call, calls it, reads the result, and forms a response. This is the ReAct pattern (Reason + Act).

---

## RAG Design Decisions

### Document Ingestion Pipeline


Steps:
1. Load `menu.txt` using `TextLoader`
2. Split into chunks using `RecursiveCharacterTextSplitter`
3. Embed each chunk using `text-embedding-3-small`
4. Save all vectors to Chroma

---

### Chunking Strategy

**chunk_size=500, chunk_overlap=50**

Why 500 characters? Each entry in the knowledge base (a menu item, a policy rule, an event package) is a self-contained paragraph. 500 characters is large enough to keep a full dish description — name, price, ingredients, dietary tags, and allergens — in one chunk without splitting it.

Why 50 character overlap? If a dish name ends one chunk and its allergen list starts the next, the overlap ensures the allergen chunk still carries the dish name as context.

Why RecursiveCharacterTextSplitter? It splits on different separators; paragraph breaks first, then line breaks, then spaces. This respects the natural structure of the document rather than cutting at arbitrary character positions.

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

```
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
```

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

The `@tool` decorator wraps the function as a `StructuredTool` that the LangGraph ReAct agent can discover and call. The docstring is required — the agent reads it to understand what the tool does and when to use it.

---

## Memory Design Explanation

Each session has its own `ChatMessageHistory` stored in a dict keyed by session ID. After each turn, the orchestrator calls `history.add_user_message()` and `history.add_ai_message()` to save the exchange. On the next turn the full history is loaded and passed to the active agent.

The RAG agent converts history to a plain string for the prompt. The operations agent passes the message list directly to the LangGraph agent.

**Limitation:** Memory is in-process only and resets when the program restarts. To persist across sessions, `ChatMessageHistory` can be swapped for `SQLChatMessageHistory` with a SQLite file and no other changes needed.

---

## Example Queries and Outputs

```
You:       Do you have vegan pasta?
[Intent:   rag]
Assistant: Yes, we have Vegan Garden Pasta, which is whole wheat penne with zucchini, cherry tomatoes, mushrooms, spinach, and garlic olive oil. It is sautéed and contains no dairy. The price is $14.99, and it is available at all branches.
```

```
You:       Is the chicken grilled or fried?
[Intent:   rag]
Assistant: The NovaBite Signature Grilled Chicken is grilled, while the Crispy Fried Chicken Platter is deep-fried.
```

```
You:       What are your opening hours on weekends?
[Intent:   rag]
Assistant: On weekends (Saturday-Sunday), our opening hours are Brunch from 10am-3pm and Dinner from 5pm-11:30pm.
```

```
You:       Do you host birthday events?”
[Intent:   ops]
Assistant: Yes, NovaBite offers private event hosting for birthday parties.
```

```
You:       What’s included in the premium catering package?
[Intent:   rag]
Assistant: The Premium Catering Package includes:

3 main dishes
2 appetizers
2 desserts
Beverage package
Dedicated event coordinator
Please note that the minimum booking is for 20 guests.
```

```
You:       I want to book a table on 1/3
[Intent:   ops]
Assistant: Could you please provide the time you would like to book the table for and the branch you wish to visit? Additionally, let me know the party size if it's different from the default of 2.
You: 19.00, at downtown, for 7 persons
[Intent:   ops]
Assistant: Your table has been successfully booked! Here are the details:

Branch: NovaBite Downtown
Date: January 3, 2023
Time: 19:00
Party Size: 7
Booking ID: NB-1001
If you need any further assistance, feel free to ask!
```

**Hallucination guard**
```
You:       do you serve sushi?
[Intent:   rag]
Assistant: We don't offer sushi, but we do have a variety of other delicious dishes, including our NovaBite Signature Grilled Chicken and Lemon Butter Grilled Salmon. Let me know if you'd like more information about our menu!
```


```
You:       What is the special dish today?
[Intent:   ops]  
Assistant: Please provide the branch location so I can check today's special dish for you.
You: Downtown
[Intent:   ops]  
Assistant: Today's specials at NovaBite Downtown are:

Starter: Lobster Bisque - $16
Main: Braised Lamb Shank - $38
Dessert: Pistachio Panna Cotta - $12
```

---

## Evaluation — LLM-as-a-Judge


The evaluation scores the RAG system on 8 test questions using another LLM call as the judge. Each answer is scored on two criteria from 1 to 5:

- **Faithfulness** — is the answer grounded in the retrieved context, or did the model make something up?
- **Relevance** — does the answer actually address what the customer asked?

The judge receives the question, the retrieved context, and the generated answer, then returns scores and a one-sentence reason for each.

Results are printed to the terminal and automatically saved to a timestamped `.txt` file:

```
evaluation_results.txt
```
---


---

## Setup and Running

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=gpt-4o-mini
```

### Streamlit UI

File: `app.py`

A simple chat interface built with Streamlit. Uses `st.chat_message` and `st.chat_input` for the native chat layout. Message history is stored in `st.session_state` so the UI stays consistent across reruns.

Run:
```bash
streamlit run app.py
```



Ingestion runs automatically on first use. To manually re-ingest after updating the knowledge base:
```bash
python rag/ingest.py
```

---

## Assumptions Made

1. **Single API key** — OpenRouter is used for both LLM completions and embeddings. No separate OpenAI key is required.

2. **In-memory database** — Reservations, bookings, loyalty points, and specials are Python dictionaries. Data resets on restart. In production these would be real database tables.

3. **In-memory session memory** — Conversation history resets on restart. A production system would use SQLChatMessageHistory or a Redis-backed store.

4. **Single session** — The current setup uses one hardcoded session ID. A web server version would generate a unique ID per user connection.

5. **English only** — Prompts and intent classification are designed for English input only.

6. **Static knowledge base** — Menu and policy updates require editing `menu.txt` and re-running ingestion. A production system would have a live data source.

7. **No authentication** — Loyalty lookups accept any user ID. A real system would verify the customer's identity before returning account data.
