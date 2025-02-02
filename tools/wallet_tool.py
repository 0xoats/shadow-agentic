# agents/wallet_agent.py
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class WalletTool:
    def __init__(self):
        # Create a ChatOpenAI model instance (adjust the model name/version as needed)
        self.model = ChatOpenAI(model="gpt-4o")

    def analyze_wallet(self, wallet_address: str) -> dict:
        """
        Index wallet transactions for the past 30 days and generate insights.
        
        Returns a dictionary containing:
          - wallet: The wallet address.
          - wallet_insights: The analysis provided by the LLM (e.g. tokens frequently traded).
          - raw_data: The raw (simulated) transaction data.
        """
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Simulate retrieving wallet transactions within the past 30 days.
        # TODO: find optimised way to index and retrieve wallet transactions
        raw_data = {
            "wallet": wallet_address,
            "transactions": [
                {
                    "id": "tx1",
                    "token": "ETH",
                    "amount": 2.5,
                    "type": "buy",
                    "timestamp": (now - timedelta(days=5)).isoformat() + "Z"
                },
                {
                    "id": "tx2",
                    "token": "BTC",
                    "amount": 0.1,
                    "type": "sell",
                    "timestamp": (now - timedelta(days=10)).isoformat() + "Z"
                },
                {
                    "id": "tx3",
                    "token": "ETH",
                    "amount": 1.0,
                    "type": "buy",
                    "timestamp": (now - timedelta(days=20)).isoformat() + "Z"
                },
                {
                    "id": "tx4",
                    "token": "SOL",
                    "amount": 50,
                    "type": "buy",
                    "timestamp": (now - timedelta(days=15)).isoformat() + "Z"
                },
                {
                    "id": "tx5",
                    "token": "ADA",
                    "amount": 100,
                    "type": "buy",
                    "timestamp": (now - timedelta(days=25)).isoformat() + "Z"
                },
            ]
        }

        # Prepare a prompt for the model to analyze the wallet transactions.
        prompt = (
            f"Analyze the following wallet transactions for wallet {wallet_address} over the past 30 days. "
            "Identify the most frequently traded tokens, trading patterns, and any insights that may indicate the wallet's preferred tokens or investment strategies.\n\n"
            f"{json.dumps(raw_data, indent=2)}"
        )

        chat_history = []
        system_message = SystemMessage(
            content="You are an expert blockchain analyst skilled in interpreting wallet transaction data."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "wallet": wallet_address,
            "wallet_insights": analysis,
            "raw_data": raw_data
        }
