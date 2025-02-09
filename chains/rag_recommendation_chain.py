# chains/rag_recommendation_chain.py
import json
from langchain.schema.runnable import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from tools.x_tool import XTool
from tools.wallet_tool import WalletTool
from tools.dexscreener_tool import DexscreenerTool
from tools.insights_tool import InsightsTool
from utils.retriever import load_vector_store, retrieve_context
import re
from jsonpath_ng import parse

class ToolStateManager:
    def __init__(self):
        self.state = {}
        
    def set_output(self, tool_name: str, output: dict):
        self.state[tool_name] = output
        
    def get_output(self, tool_name: str) -> dict:
        return self.state.get(tool_name, {})
    
    def get_field(self, tool_name: str, field_path: str):
        """Get a specific field using dot notation (e.g., 'WalletTool.tokens_bought')"""
        try:
            data = self.state.get(tool_name, {})
            for key in field_path.split('.'):
                data = data[key]
            return data
        except (KeyError, TypeError):
            return None

class RAGRecommendationChain:
    def __init__(self, wallet_address: str, user_preferences: str = ""):
        """
        :param wallet_address: The user's Solana wallet address.
        :param user_preferences: Additional free-form text with trade preferences.
        """
        self.wallet_address = wallet_address
        self.user_preferences = user_preferences
        
         # Initialize the tools (agents) as callable functions with descriptions.
        self.tools = {
            "XTool": {
                "function": XTool().get_sentiment,
                "description": "Analyzes social sentiment from Farcaster for a given token symbol. Input: token symbol."
            },
            "WalletTool": {
                "function": WalletTool().analyze_wallet,
                "description": "Analyzes wallet transactions and patterns for both Solana and Ethereum addresses. Input: wallet address."
            },
            "DexscreenerTool": {
                "function": DexscreenerTool().analyze_similar_tokens,
                "description": "Analyzes similar tokens and provides technical analysis. Input: wallet analysis output."
            },
            "TechnicalAnalysisTool": {
                "function": DexscreenerTool().get_technical_analysis,
                "description": "Provides detailed technical analysis for a specific token. Input: token symbol."
            },
            "VolumeAnalysisTool": {
                "function": DexscreenerTool().get_volume_mcap_ratio,
                "description": "Calculates and analyzes volume to market cap ratios. Input: token symbol."
            },
            # "Retriever": {
            #     "function": lambda query: retrieve_context(self.vector_store, query, k=3),
            #     "description": "Retrieves relevant historical trading insights and patterns. Input: a text query."
            # }
        }
        
        
        # The final consolidation tool is InsightsTool.
        self.insights_tool = InsightsTool()
        # Load the vector store (assumes a pre-built index exists)
      #  self.vector_store = load_vector_store()
        # Initialize an LLM for orchestration decisions.
        self.llm = ChatOpenAI(model="gpt-4o")
        self.state_manager = ToolStateManager()
        
    def orchestrate(self) -> dict:
        """Uses the LLM to decide which tools to call and in what order."""
        # First, execute WalletTool as it's always the starting point
        try:
            wallet_result = self.tools["WalletTool"]["function"](self.wallet_address)
            self.state_manager.set_output("WalletTool", wallet_result)
            
            # Get tokens bought from wallet analysis
            tokens_bought = wallet_result.get("tokens_bought", [])
            if tokens_bought:
                # For each token found, analyze it
                for token in tokens_bought[:3]:  # Limit to first 3 tokens
                    # Get technical analysis
                    dex_result = self.tools["DexscreenerTool"]["function"](wallet_result)
                    self.state_manager.set_output("DexscreenerTool", dex_result)
                    
                    # Get sentiment analysis
                    sentiment_result = self.tools["XTool"]["function"](token)
                    self.state_manager.set_output("XTool", sentiment_result)
                    
                    # Get volume analysis
                    volume_result = self.tools["VolumeAnalysisTool"]["function"](token)
                    self.state_manager.set_output("VolumeAnalysisTool", volume_result)
                    
                    # Get detailed technical analysis
                    tech_result = self.tools["TechnicalAnalysisTool"]["function"](token)
                    self.state_manager.set_output("TechnicalAnalysisTool", tech_result)
            
            # Prepare consolidation inputs
            consolidation_inputs = {
                "user_preferences": self.user_preferences,
                "wallet": self.state_manager.get_output("WalletTool"),
                "technical": self.state_manager.get_output("DexscreenerTool"),
                "sentiment": self.state_manager.get_output("XTool"),
                "volume_analysis": self.state_manager.get_output("VolumeAnalysisTool"),
                "technical_details": self.state_manager.get_output("TechnicalAnalysisTool")
            }
            
            return self.insights_tool.consolidate(**consolidation_inputs)
            
        except Exception as e:
            print(f"Error executing tools: {str(e)}")
            raise
        
    def generate_recommendations(self) -> dict:
        """
        Public interface to generate recommendations via the orchestrated tool calls.
        """
        return self.orchestrate()
