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
        
    def orchestrate(self) -> dict:
        """
        Uses the LLM to decide which tools to call and in what order, handling dependencies.
        """
        # Build a description of the available tools
        tool_descriptions = "\n".join(
            f"{name}: {data['description']}" for name, data in self.tools.items()
        )
        
        # Create an initial context prompt for the LLM
        initial_prompt = (
            f"User Input:\n"
            f"Wallet address: {self.wallet_address}\n"
            f"User preferences: {self.user_preferences}\n\n"
            f"Available tools:\n{tool_descriptions}\n\n"
            "Plan a sequence of tool calls that will produce all necessary data for a trading recommendation. "
            "Some tools may depend on outputs from previous tools.\n\n"
            "Output your response in the following format:\n"
            "```json\n"
            "[\n"
            "  {\n"
            "    \"step\": 1,\n"
            "    \"tool\": \"ToolName\",\n"
            "    \"input\": \"<direct_input_or_reference>\",\n"
            "    \"depends_on\": [],\n"
            "    \"input_mapping\": {}\n"
            "  },\n"
            "  {\n"
            "    \"step\": 2,\n"
            "    \"tool\": \"ToolName\",\n"
            "    \"input\": \"<direct_input_or_reference>\",\n"
            "    \"depends_on\": [\"step_1\"],\n"
            "    \"input_mapping\": {\"field\": \"$.step_1.output.specific_field\"}\n"
            "  }\n"
            "]\n"
            "```\n\n"
            "Where:\n"
            "- step: Numeric order of execution\n"
            "- tool: Name of the tool to call\n"
            "- input: Direct input value or placeholder for mapped input\n"
            "- depends_on: List of step numbers this step depends on\n"
            "- input_mapping: JSON path mapping from previous steps' outputs\n\n"
            "Explanation: <explain your plan>"
        )
        
        messages = [
            SystemMessage(content="You are an expert orchestrator for crypto trading analysis tools."),
            HumanMessage(content=initial_prompt)
        ]
        
        # Get the execution plan from LLM
        plan_response = self.llm.invoke(messages)
        plan_text = plan_response.content.strip()
        
        try:
            # Extract and parse the JSON plan
            if "```json" in plan_text:
                json_part = plan_text.split("```json")[1].split("```")[0].strip()
            else:
                json_match = re.search(r'\[\s*{.*}\s*\]', plan_text, re.DOTALL)
                if not json_match:
                    raise ValueError("No valid JSON plan found in response")
                json_part = json_match.group(0)
            
            plan = json.loads(json_part)
            
            # Sort plan by step number to ensure correct execution order
            plan.sort(key=lambda x: x["step"])
            
            # Store results of each step
            step_outputs = {}
            
            # Execute each step in order
            for step in plan:
                step_num = f"step_{step['step']}"
                tool_name = step["tool"]
                
                if tool_name not in self.tools:
                    print(f"Warning: Tool {tool_name} not found, skipping step {step['step']}")
                    continue
                
                # Resolve input based on dependencies
                final_input = step["input"]
                if step["depends_on"]:
                    # Create a context of all previous outputs this step depends on
                    dependency_context = {}
                    for dep in step["depends_on"]:
                        dep_step = f"step_{dep}"
                        if dep_step in step_outputs:
                            dependency_context[dep_step] = step_outputs[dep_step]
                    
                    # Apply input mappings using JSONPath
                    for target_field, source_path in step["input_mapping"].items():
                        try:
                        
                            jsonpath_expr = parse(source_path)
                            matches = [match.value for match in jsonpath_expr.find(dependency_context)]
                            if matches:
                                placeholder = f"${{{target_field}}}"
                                if placeholder in final_input:
                                    final_input = final_input.replace(placeholder, str(matches[0]))
                                else:
                                    final_input = matches[0]  # Direct value assignment if no placeholder
                        except Exception as e:
                            print(f"Error applying input mapping: {e}")
                            continue
                
                print(f"\nExecuting {tool_name} with input: {final_input}")
                
                # Execute the tool
                try:
                    func = self.tools[tool_name]["function"]
                    result = func(final_input)
                    step_outputs[step_num] = result
                    print(f"Step {step_num} output: {json.dumps(result, indent=2)}")
                except Exception as e:
                    print(f"Error executing step {step_num}: {e}")
                    step_outputs[step_num] = None
            
            # Prepare inputs for consolidation based on actual tool outputs
            consolidation_inputs = {
                "user_preferences": self.user_preferences  # This is always available
            }
            
            # Map tool names to their expected input names in consolidate
            tool_to_param_mapping = {
                "XTool": "sentiment",
                "DexscreenerTool": "technical",
                "WalletTool": "wallet",
                "VolumeAnalysisTool": "volume_analysis",
                "TechnicalAnalysisTool": "technical_details"
            }
            
            # Collect outputs from each step based on the tool used
            for step in plan:
                step_num = f"step_{step['step']}"
                tool_name = step["tool"]
                
                if tool_name in tool_to_param_mapping:
                    param_name = tool_to_param_mapping[tool_name]
                    consolidation_inputs[param_name] = step_outputs.get(step_num, {})
            
            # Generate final recommendation using all gathered data
            return self.insights_tool.consolidate(**consolidation_inputs)
            
        except Exception as e:
            print(f"Error executing plan: {str(e)}")
            raise
        
    def generate_recommendations(self) -> dict:
        """
        Public interface to generate recommendations via the orchestrated tool calls.
        """
        return self.orchestrate()
