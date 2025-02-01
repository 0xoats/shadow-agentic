# main.py
import sys
from chains.recommendation_chain import RecommendationChain

def main():
    if len(sys.argv) < 3:
        print("Usage: poetry run python main.py <wallet_address> <token_symbol>")
        sys.exit(1)

    wallet_address = sys.argv[1]
    token_symbol = sys.argv[2]

    chain = RecommendationChain(wallet_address=wallet_address, token_symbol=token_symbol)
    recommendations = chain.generate_recommendations()
    
    print("Recommendations:")
    print(recommendations)

if __name__ == "__main__":
    main()
