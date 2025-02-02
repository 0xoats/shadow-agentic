# utils/retrieval.py
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

def load_vector_store(index_path: str = "faiss_index") -> FAISS:
    """Load a pre-built FAISS vector store using OpenAI embeddings."""
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.load_local(index_path, embeddings)
    return vector_store

def retrieve_context(vector_store, query: str, k: int = 3) -> str:
    """Retrieve k relevant documents for a given query."""
    docs = vector_store.similarity_search(query, k=k)
    retrieved_text = "\n".join([doc.page_content for doc in docs])
    return retrieved_text
