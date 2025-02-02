# agents/dexscreener_agent.py
import json
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

from configs.config import DEXS_ENDPOINT

class DexscreenerAgent:
    def __init__(self):
        # Base endpoint for the Dexscreener API (e.g., "https://api.dexscreener.com/latest/dex")
        self.endpoint = DEXS_ENDPOINT
        self.model = ChatOpenAI(model="gpt-4o")

    def analyze_similar_tokens(self, wallet_insights: dict) -> dict:
        """
        Using the insights from the wallet transactions, identify similar tokens using the Dexscreener API
        and conduct technical analysis on them.
        
        Steps:
          1. Extract tokens of interest from the wallet insights (e.g., a list of tokens mentioned in the analysis).
          2. For each token, use the Dexscreener API to search for similar token pairs.
          3. For each token pair, invoke the ChatOpenAI model to analyze the raw data and produce technical insights.
        
        Returns a dictionary containing:
          - similar_tokens_analysis: A mapping of token symbols to their technical analysis.
          - tokens_examined: The list of tokens that were analyzed.
        """
        # In a real-world scenario, you would parse wallet_insights to extract tokens.
        # For this example, we simulate by using a fixed list.
        # TODO: How to find the similar tokens of interest?
        tokens_of_interest = ["ETH", "BTC", "SOL", "ADA"]
        similar_tokens_analysis = {}

        for token in tokens_of_interest:
            # Step 1: Use the Dexscreener search endpoint to find token pairs related to this token.
            search_url = f"{self.endpoint}/search"
            params = {"q": token}
            response = requests.get(search_url, params=params)
            if response.status_code != 200:
                similar_tokens_analysis[token] = {
                    "error": f"Error searching for token '{token}': {response.text}"
                }
                continue

            search_data = response.json()
            pairs = search_data.get("pairs")
            if not pairs or len(pairs) == 0:
                similar_tokens_analysis[token] = {
                    "error": f"No pairs found for token '{token}'."
                }
                continue

            # For simplicity, select the first returned pair.
            pair_data = pairs[0]

            # Step 2: Prepare a prompt to analyze the technical data for this token pair.
            prompt = (
                f"Below is raw data from Dexscreener for a token pair related to {token}. "
                "Please analyze the data and provide technical insights, including trend, volatility, and key indicators.\n\n"
                f"{json.dumps(pair_data, indent=2)}"
            )

            chat_history = []
            system_message = SystemMessage(
                content="You are a skilled market analyst with expertise in crypto technical analysis."
            )
            chat_history.append(system_message)
            chat_history.append(HumanMessage(content=prompt))

            result = self.model.invoke(chat_history)
            analysis = result.content

            similar_tokens_analysis[token] = {
                "technical_analysis": analysis,
                "raw_data": pair_data
            }

        return {
            "similar_tokens_analysis": similar_tokens_analysis,
            "tokens_examined": tokens_of_interest
        }

    def get_technical_analysis(self, token_symbol: str) -> dict:
        """
        (Optional) Retrieve technical data for a given token using the Dexscreener API,
        then invoke an LLM to analyze the data and provide technical insights.
        
        Returns a dictionary containing:
          - token: The token symbol.
          - technical_analysis: The analysis provided by the model.
          - raw_data: The raw pair data from the API.
        """
        search_url = f"{self.endpoint}/search"
        params = {"q": token_symbol}
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error searching for token '{token_symbol}': {response.text}")

        search_data = response.json()
        pairs = search_data.get("pairs")
        if not pairs or len(pairs) == 0:
            raise Exception(f"No pairs found for token '{token_symbol}'.")

        pair_data = pairs[0]

        prompt = (
            f"Below is raw data from Dexscreener for a token pair related to {token_symbol}. "
            "Please analyze the data and provide technical insights, including trend, volatility, and key indicators.\n\n"
            f"{json.dumps(pair_data, indent=2)}"
        )

        chat_history = []
        # TODO: Refine the prompt
        system_message = SystemMessage(
            content="You are a skilled market analyst with expertise in crypto technical analysis."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "token": token_symbol,
            "technical_analysis": analysis,
            "raw_data": pair_data
        }
