# chains/recommendation_chain.py
from langchain.schema.runnable import RunnableLambda, RunnableParallel
from agents.x_agent import XAgent
from agents.dexscreener_agent import DexscreenerAgent
from agents.wallet_agent import WalletAgent
from agents.insights_agent import InsightsAgent

class RecommendationChain:
    def __init__(self, wallet_address: str, token_symbol: str):
        self.wallet_address = wallet_address
        self.token_symbol = token_symbol
        self.insights_agent = InsightsAgent()

    def generate_recommendations(self) -> dict:
        """
        Orchestrate the calls to the three agents in parallel and consolidate their outputs.
        """
        # Wrap each agent call in a RunnableLambda to capture required parameters.
        x_lambda = RunnableLambda(lambda _: XAgent().get_sentiment(self.token_symbol))
        dexs_lambda = RunnableLambda(lambda _: DexscreenerAgent().get_technical_analysis(self.token_symbol))
        wallet_lambda = RunnableLambda(lambda _: WalletAgent().analyze_wallet(self.wallet_address))
        
        # Execute the three lambdas in parallel.
        parallel_chain = RunnableParallel(branches={
            "x": x_lambda,
            "dexs": dexs_lambda,
            "wallet": wallet_lambda,
        })
        
        results = parallel_chain.invoke({})
        
        print(results)
        # Combine the results using the InsightsAgent.
        recommendation = self.insights_agent.consolidate(
            sentiment=results["x"],
            technical=results["dexs"],
            wallet=results["wallet"]
        )
        return recommendation
