from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import embeddings, CHROMA_PATH, CHROMA_COLLECTION, DATA_PATH


def ingest():
    loader = TextLoader(DATA_PATH)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH,
        collection_name=CHROMA_COLLECTION
    )


if __name__ == "__main__":
    ingest()
