# agents/dexscreener_agent.py
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from configs.config import DEXS_ENDPOINT
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

class DexscreenerAgent:
    def __init__(self):
        self.endpoint = DEXS_ENDPOINT  # e.g., "https://api.dexscreener.com/latest/dex"
        # Create the ChatOpenAI model instance (adjust the model name/version as needed)
        self.model = ChatOpenAI(model="gpt-4o")

    def get_technical_analysis(self, token_symbol: str) -> dict:
        """
        Retrieve technical data for a given token using the Dexscreener API,
        then invoke an LLM to analyze the data and provide technical insights.

        Returns a dictionary containing:
          - token: The token symbol.
          - technical_analysis: The analysis produced by the model.
          - raw_data: The raw pair data returned by the API.
        """
        # 1. Search for token pairs related to the token symbol
        search_url = f"{self.endpoint}/search"
        params = {"q": token_symbol}
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error searching for token '{token_symbol}': {response.text}")
        
        search_data = response.json()
        pairs = search_data.get("pairs")
        if not pairs or len(pairs) == 0:
            raise Exception(f"No pairs found for token '{token_symbol}'.")

        # For simplicity, select the first returned pair
        pair_data = pairs[0]

        # 2. Prepare a prompt for the model with the raw data and instructions
        prompt = (
            f"Below is raw data from Dexscreener for a token pair related to {token_symbol}. "
            "Please analyze the data and provide a technical analysis that includes an assessment "
            "of the current trend, volatility, price, volume, and any other noteworthy technical insights. "
            "Provide your analysis in a concise format.\n\n"
            f"{json.dumps(pair_data, indent=2)}"
        )

        # 3. Prepare a message history and invoke the model
        chat_history = []
        # Optional system message to set context
        system_message = SystemMessage(
            content="You are a skilled market analyst with expertise in crypto technical analysis."
        )
        chat_history.append(system_message)
        # User message with our prompt
        human_message = HumanMessage(content=prompt)
        chat_history.append(human_message)

        # Invoke the model using the chat history
        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "token": token_symbol,
            "technical_analysis": analysis,
            "raw_data": pair_data
        }

# Example usage (for testing purposes, remove or modify in production):
if __name__ == "__main__":
    agent = DexscreenerAgent()
    try:
        result = agent.get_technical_analysis("ETH")
        print("Technical Analysis:")
        print(result["technical_analysis"])
    except Exception as e:
        print("Error:", e)
