from dotenv import load_dotenv
from chains.rag_recommendation_chain import RAGRecommendationChain
import json

def test_pipeline():
    """Simple function to test the recommendation pipeline"""
    # Test wallet address (replace with a real one)
    test_wallet = "AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm"
    
    # Test preferences (can be empty or specific)
    test_preferences = "interested in DeFi opportunities with medium risk"
    
    print(f"Testing pipeline with wallet: {test_wallet}")
    print(f"User preferences: {test_preferences}")
    
    # Initialize the chain
    chain = RAGRecommendationChain(test_wallet, test_preferences)
    
    try:
        print("\nInvoking pipeline...")
        result = chain.generate_recommendations()
        print("\nPipeline result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\nError processing pipeline: {e}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    test_pipeline() 