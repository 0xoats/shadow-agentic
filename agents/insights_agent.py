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
        Consolidate analysis outputs from the sentiment, technical, and wallet agents
        to generate a final comprehensive trading recommendation.
        
        Returns a dictionary containing:
          - consolidated_insights: The final recommendation provided by the model.
          - details: The individual outputs from the sentiment, technical, and wallet agents.
        """
        # Construct a detailed prompt that clearly lays out each analysis section.
        prompt = (
            "You are a seasoned crypto market analyst. Your task is to synthesize the following analysis results "
            "from three specialized agents into a single, coherent final trading recommendation. Consider the overall "
            "market sentiment, technical trends, and the wallet's trading behavior, and provide your recommendation with "
            "insights regarding risk, potential future performance, and any actionable strategies.\n\n"
            "----- Sentiment Analysis (from XAgent) -----\n"
            f"{json.dumps(sentiment, indent=2)}\n\n"
            "----- Technical Analysis (from DexscreenerAgent) -----\n"
            f"{json.dumps(technical, indent=2)}\n\n"
            "----- Wallet Analysis (from WalletAgent) -----\n"
            f"{json.dumps(wallet, indent=2)}\n\n"
            "Based on the above information, please provide a consolidated trading recommendation that includes:\n"
            "- A summary of key findings from each analysis.\n"
            "- An overall market outlook for the token(s) in question.\n"
            "- Suggested trading strategies or optimizations.\n"
            "- Any risk factors or considerations."
        )

        # Build the chat history for the LLM.
        chat_history = []
        system_message = SystemMessage(
            content="You are a seasoned crypto market analyst tasked with synthesizing multi-source analysis into a clear trading recommendation."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        # Invoke the model with the chat history.
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
