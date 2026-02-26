import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "gpt-4o-mini"

CHROMA_PATH = "./chroma_db"
CHROMA_COLLECTION = "nova_collection"

DATA_PATH = "data/menu.txt"

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY,
    base_url=OPENROUTER_BASE_URL
)

llm = ChatOpenAI(
    model=OPENROUTER_MODEL,
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    openai_api_base=OPENROUTER_BASE_URL
)