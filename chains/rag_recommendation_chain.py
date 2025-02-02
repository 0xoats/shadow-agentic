# chains/rag_recommendation_chain.py
import json
from langchain.schema.runnable import RunnableLambda
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from tools.x_tool import XAgent
from agents.wallet_agent import WalletAgent
from agents.dexscreener_tool import DexscreenerAgent
from agents.insights_agent import InsightsAgent
from retriever.retriever import load_vector_store, retrieve_context

class RAGRecommendationChain:
    def __init__(self, wallet_address: str, token_symbol: str, user_preferences: str = ""):
        """
        :param wallet_address: The user's Solana wallet address.
        :param token_symbol: The token symbol used for sentiment analysis.
        :param user_preferences: Additional free-form text with trade preferences.
        """
        self.wallet_address = wallet_address
        self.token_symbol = token_symbol
        self.user_preferences = user_preferences
        
        # Initialize the tools (agents) as callable functions with descriptions.
        self.tools = {
            "XAgent": {
                "function": XAgent().get_sentiment,
                "description": "Retrieves and analyzes social sentiment for a given token symbol. Input: token symbol."
            },
            "WalletAgent": {
                "function": WalletAgent().analyze_wallet,
                "description": "Analyzes wallet transactions over the past 30 days. Input: wallet address."
            },
            "DexscreenerAgent": {
                "function": DexscreenerAgent().analyze_similar_tokens,
                "description": "Uses wallet insights to search for similar tokens and conduct technical analysis. Input: wallet analysis output."
            },
            "Retriever": {
                "function": lambda query: retrieve_context(self.vector_store, query, k=3),
                "description": "Retrieves additional context from the vector store given a composite query. Input: a text query."
            }
        }
        
        # The final consolidation tool is InsightsAgent.
        self.insights_agent = InsightsAgent()
        # Load the vector store (assumes a pre-built index exists)
        self.vector_store = load_vector_store()
        # Initialize an LLM for orchestration decisions.
        self.llm = ChatOpenAI(model="gpt-4o")
        
    def orchestrate(self) -> dict:
        """
        Uses the LLM to decide which tools to call and in what order. The LLM is provided a prompt
        listing available tools, their descriptions, and the user inputs. It returns a JSON plan.
        
        The plan is expected to be a JSON array where each element is an object with:
          - "tool": the name of the tool to call,
          - "input": the input to provide to that tool.
        
        The chain then iterates over this plan, calls each tool, and collects their outputs.
        Finally, a composite query is built (augmented with user preferences) and additional context is retrieved.
        All results are passed to InsightsAgent to generate the final recommendation.
        
        :return: A dictionary with the final consolidated recommendation.
        """
        # Build a description of the available tools.
        tool_descriptions = "\n".join(
            f"{name}: {data['description']}" for name, data in self.tools.items()
        )
        
        # Create an initial context prompt for the LLM.
        initial_prompt = (
            f"User Input:\n"
            f"Wallet address: {self.wallet_address}\n"
            f"Token symbol: {self.token_symbol}\n"
            f"User preferences: {self.user_preferences}\n\n"
            f"Available tools:\n{tool_descriptions}\n\n"
            "Based on the above information, plan a sequence of tool calls that will produce "
            "all necessary data to generate a trading recommendation. "
            "Output the plan as a JSON array of steps, where each step is an object with 'tool' and 'input'. "
            "For example: "
            '[{"tool": "WalletAgent", "input": "<wallet_address>"}, '
            '{"tool": "XAgent", "input": "<token_symbol>"}].'
        )
        
        messages = [
            SystemMessage(content="You are an expert orchestrator for crypto trading analysis tools."),
            HumanMessage(content=initial_prompt)
        ]
        
        # Invoke the LLM to generate a plan.
        plan_response = self.llm.invoke(messages)
        plan_text = plan_response.content.strip()
        
        try:
            plan = json.loads(plan_text)
        except Exception as e:
            # If parsing fails, use a default plan.
            plan = [
                {"tool": "WalletAgent", "input": self.wallet_address},
                {"tool": "XAgent", "input": self.token_symbol},
                {"tool": "DexscreenerAgent", "input": self.wallet_address}
            ]
        
        # Execute the plan sequentially.
        tool_outputs = {}
        for step in plan:
            tool_name = step.get("tool")
            tool_input = step.get("input")
            if tool_name in self.tools:
                func = self.tools[tool_name]["function"]
                # For tools that expect outputs from previous steps:
                if tool_name == "DexscreenerAgent":
                    # Prefer using the output from WalletAgent if available.
                    wallet_out = tool_outputs.get("WalletAgent", self.wallet_address)
                    output = func(wallet_out)
                else:
                    output = func(tool_input)
                tool_outputs[tool_name] = output
        
        # Build a composite query from the outputs and user preferences.
        composite_query = (
            f"WalletAgent output: {tool_outputs.get('WalletAgent', '')}\n"
            f"XAgent output: {tool_outputs.get('XAgent', '')}\n"
            f"DexscreenerAgent output: {tool_outputs.get('DexscreenerAgent', '')}\n"
            f"User preferences: {self.user_preferences}"
        )
        
        # Retrieve additional context.
        retrieved_context = self.tools["Retriever"]["function"](composite_query)
        
        # Augment the XAgent result with user preferences and retrieved context.
        augmented_sentiment = {}
        if "XAgent" in tool_outputs:
            augmented_sentiment = {
                **tool_outputs["XAgent"],
                "user_preferences": self.user_preferences,
                "retrieved_context": retrieved_context
            }
        
        # Use InsightsAgent to consolidate all outputs.
        final_recommendation = self.insights_agent.consolidate(
            sentiment=augmented_sentiment,
            technical=tool_outputs.get("DexscreenerAgent", {}),
            wallet=tool_outputs.get("WalletAgent", {})
        )
        return final_recommendation
        
    def generate_recommendations(self) -> dict:
        """
        Public interface to generate recommendations via the orchestrated tool calls.
        """
        return self.orchestrate()
