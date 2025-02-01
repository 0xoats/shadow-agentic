# agents/wallet_agent.py
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class WalletAgent:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")

    def analyze_wallet(self, wallet_address: str) -> dict:
        """
        Analyze historical transactions for a given wallet address.
        Returns a dictionary containing:
          - wallet: The wallet address.
          - wallet_analysis: The analysis provided by the LLM.
          - raw_data: The raw (simulated) transaction data.
        """
        # Simulate raw wallet transaction data. TODO: Replace with actual data indexed.
        raw_data = {
            "wallet": wallet_address,
            "transactions": [
                {"id": "tx1", "token": "ETH", "amount": 2.5, "type": "buy", "timestamp": "2023-01-01T12:00:00Z"},
                {"id": "tx2", "token": "BTC", "amount": 0.1, "type": "sell", "timestamp": "2023-01-10T15:30:00Z"},
                {"id": "tx3", "token": "ETH", "amount": 1.0, "type": "buy", "timestamp": "2023-02-05T09:45:00Z"}
            ]
        }

        # Prepare a prompt for the model.
        prompt = (
            f"Analyze the following wallet transaction data for wallet {wallet_address} and provide a comprehensive report "
            "detailing trading habits, token preferences, and any noticeable patterns or risks.\n\n"
            f"{json.dumps(raw_data, indent=2)}"
        )

        chat_history = []
        system_message = SystemMessage(
            content="You are an expert in blockchain analytics and crypto trading behavior."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "wallet": wallet_address,
            "wallet_analysis": analysis,
            "raw_data": raw_data
        }
