# agents/insights_agent.py
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class InsightsAgent:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")

    def consolidate(self, sentiment: dict, technical: dict, wallet: dict) -> dict:
        """
        Consolidate analysis outputs from the sentiment, technical, and wallet agents to generate
        a final recommendation.
        Returns a dictionary with:
          - consolidated_insights: The final recommendation analysis.
          - details: All individual agent outputs.
        """
        # Prepare a prompt that includes the outputs from the other agents.
        prompt = (
            "Below are the analysis results from different agents for a given token and wallet:\n\n"
            "1. Sentiment Analysis (from XAgent):\n"
            f"{json.dumps(sentiment, indent=2)}\n\n"
            "2. Technical Analysis (from DexscreenerAgent):\n"
            f"{json.dumps(technical, indent=2)}\n\n"
            "3. Wallet Analysis (from WalletAgent):\n"
            f"{json.dumps(wallet, indent=2)}\n\n"
            "Based on the above information, provide a consolidated recommendation for trading, including "
            "any insights into the token's potential future performance and suggested optimizations."
        )

        chat_history = []
        system_message = SystemMessage(
            content="You are a seasoned crypto market analyst tasked with consolidating multiple sources of analysis into a coherent final recommendation."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        consolidated_insights = result.content

        return {
            "consolidated_insights": consolidated_insights,
            "details": {
                "sentiment": sentiment,
                "technical": technical,
                "wallet": wallet
            }
        }
