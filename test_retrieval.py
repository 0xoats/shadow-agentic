from utils.retriever import load_vector_store
from dotenv import load_dotenv

def test_retrieval():
    """Test retrieving context from the vector store"""
    load_dotenv()
    
    # Load the vector store
    vector_store = load_vector_store("trading_insights")
    
    # Test queries
    test_queries = [
        "What are the current DeFi opportunities?",
        "Tell me about SOL trading patterns",
        "What are typical wallet behaviors during launches?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_store.similarity_search(
            query,
            k=2  # Number of results to return
        )
        
        print("Retrieved contexts:")
        for doc in results:
            print(f"\n- Content: {doc.page_content}")
            print(f"  Metadata: {doc.metadata}")

if __name__ == "__main__":
    test_retrieval() 