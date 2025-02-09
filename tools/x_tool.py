# agents/x_agent.py

import json
import os
from dotenv import load_dotenv
import requests

from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class XTool:
    def __init__(self):
        # Create a ChatOpenAI model instance (adjust the model as needed)
        self.model = ChatOpenAI(model="gpt-4o")

        # Farcaster search endpoint
        self.farcaster_search_endpoint = "https://client.warpcast.com/v2/search-casts"

    def search_casts(self, token_symbol: str, limit=5) -> list:
        """
        Search Farcaster 'casts' referencing the given token symbol.

        :param token_symbol: the crypto token symbol (e.g., 'ETH' or '$LINK')
        :param limit: how many casts to retrieve
        :return: a list of dicts, each containing cast data
        """
        params = {
            "q": token_symbol,
            "limit": limit
        }

        try:
            response = requests.get(self.farcaster_search_endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(data)
            # Structure:
            # {
            #   "result": {
            #     "casts": [...],
            #   },
            #   "next": {...}
            # }
            casts = data.get("result", {}).get("casts", [])

            # We'll convert each cast to a simplified dict: {"id": ..., "content": ...}
            cast_list = []
            for c in casts:
                # 'hash' is unique to each cast, 'text' is the post content
                cast_list.append({
                    "id": c.get("hash"),
                    "content": c.get("text", "")
                })

            return cast_list

        except Exception as e:
            print(f"Error searching casts for symbol '{token_symbol}': {e}")
            # Fallback to simulated data on error
            return [
                {"id": "fallback_1", "content": f"{token_symbol} is showing strong bullish signals on Farcaster."},
                {"id": "fallback_2", "content": f"Concerns remain about {token_symbol}'s volatility in the current market."}
            ]

    def _index_casts_of_interest(self, casts: list) -> list:
        """
        A simple placeholder function to 'index' or filter Farcaster casts.
        For now, it just returns them all, but you could add logic to:
          - Filter out spam or duplicates.
          - Score each cast by relevance or sentiment before returning.

        :param casts: a list of cast dicts with 'id' and 'content'.
        :return: a subset of casts that you consider relevant or interesting.
        """
        return casts  # no filtering for now

    def get_sentiment(self, token_symbol: str) -> dict:
        """
        Retrieve and analyze social sentiment data for the given token from Farcaster.

        Steps:
          1) Pull actual casts from Farcaster's /search-casts (or fallback to mock data).
          2) Index/filter casts as needed (dummy logic here).
          3) Pass them to the LLM for sentiment analysis.

        :param token_symbol: The token symbol (e.g., "ETH" or "$LINK")
        :return: {
            "token": <token_symbol>,
            "sentiment_analysis": <string from LLM>,
            "raw_data": { "casts": [...], ... }
        }
        """
        print(f"Getting sentiment for token: {token_symbol}")
        

        # 1) Integrate with Farcaster data
        raw_casts = self.search_casts(token_symbol, limit=5)

        # 2) Index or filter casts (optional advanced logic)
        filtered_casts = self._index_casts_of_interest(raw_casts)

        # Build the raw_data structure with our final set of posts
        raw_data = {
            "token": token_symbol,
            "casts": filtered_casts
        }

        # 3) Prepare the LLM prompt
        prompt = (
            f"Analyze the following social media data for token {token_symbol} and provide a sentiment analysis. "
            "Include an overall sentiment, key points, and any potential impact on the token's performance.\n\n"
            f"{json.dumps(raw_data, indent=2)}"
        )

        # Build the message history.
        chat_history = []
        system_message = SystemMessage(
            content="You are a market sentiment analyst with expertise in crypto trends and social media analysis."
        )
        chat_history.append(system_message)
        chat_history.append(HumanMessage(content=prompt))

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "token": token_symbol,
            "sentiment_analysis": analysis,
            "raw_data": raw_data
        }
