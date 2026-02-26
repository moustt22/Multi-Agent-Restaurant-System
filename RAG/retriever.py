from langchain_chroma import Chroma
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import embeddings, CHROMA_PATH, CHROMA_COLLECTION


def get_retriever():
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings,
        collection_name=CHROMA_COLLECTION
    )

    if vectorstore._collection.count() == 0:
        print("[Retriever] Chroma is empty — running ingestion first...")
        from RAG.ingestion import ingest
        ingest()
        vectorstore = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings,
            collection_name=CHROMA_COLLECTION
        )

    return vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 10})
