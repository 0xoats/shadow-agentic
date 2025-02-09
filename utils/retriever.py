# utils/retrieval.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
import os

def init_qdrant_client():
    """Initialize Qdrant client with cloud configuration from environment variables"""
    load_dotenv()
    
    host = os.getenv("QDRANT_HOST")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if not host or not api_key:
        raise ValueError("QDRANT_HOST and QDRANT_API_KEY must be set in .env file")
        
    return QdrantClient(
        host,
        api_key=api_key
    )

def init_collections(client: QdrantClient):
    """Initialize collections if they don't exist"""
    collections = [
        "trading_insights",
        "market_sentiment",
        "technical_analysis",
        "wallet_patterns"
    ]
    
    for collection in collections:
        try:
            client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
        except Exception as e:
            print(f"Collection {collection} may already exist: {e}")

def load_vector_store(collection_name: str = "trading_insights") -> Qdrant:
    """Load Qdrant vector store using OpenAI embeddings"""
    client = init_qdrant_client()
    embeddings = OpenAIEmbeddings()
    vector_store = Qdrant(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )
    return vector_store

def retrieve_context(vector_store, query: str, k: int = 3) -> str:
    """Retrieve k relevant documents for a given query."""
    docs = vector_store.similarity_search(query, k=k)
    retrieved_text = "\n".join([doc.page_content for doc in docs])
    return retrieved_text
