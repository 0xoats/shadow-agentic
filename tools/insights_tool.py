# agents/insights_agent.py
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class InsightsTool:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")

    def consolidate(
        self, 
        sentiment: dict, 
        technical: dict, 
        wallet: dict, 
        user_preferences: str,
        volume_analysis: dict = None,
        technical_details: dict = None
    ) -> dict:
        """
        Consolidate analysis outputs from all tools to generate a comprehensive trading recommendation.
        
        Args:
            sentiment: Output from XTool's sentiment analysis
            technical: Output from DexscreenerTool's similar tokens analysis
            wallet: Output from WalletTool's wallet analysis
            user_preferences: User's trading preferences
            volume_analysis: Optional output from VolumeAnalysisTool
            technical_details: Optional output from TechnicalAnalysisTool
        
        Returns:
            dict: Consolidated insights and recommendations
        """
        prompt = (
            "You are a seasoned crypto market analyst. Synthesize the following analyses "
            "into a comprehensive trading recommendation:\n\n"
            
            "----- Wallet Analysis -----\n"
            f"{json.dumps(wallet, indent=2)}\n\n"
            
            "----- Social Sentiment Analysis -----\n"
            f"{json.dumps(sentiment, indent=2)}\n\n"
            
            "----- Similar Tokens Analysis -----\n"
            f"{json.dumps(technical, indent=2)}\n\n"
            
            f"{'----- Volume Analysis -----\n' if volume_analysis else ''}"
            f"{json.dumps(volume_analysis, indent=2) if volume_analysis else ''}\n\n"
            
            f"{'----- Detailed Technical Analysis -----\n' if technical_details else ''}"
            f"{json.dumps(technical_details, indent=2) if technical_details else ''}\n\n"
            
            "----- User Preferences -----\n"
            f"{user_preferences}\n\n"
            
            "Please provide a detailed recommendation including:\n"
            "1. Portfolio Analysis:\n"
            "   - Current portfolio composition\n"
            "   - Trading patterns and behavior\n"
            "   - Risk exposure assessment\n\n"
            "2. Market Context:\n"
            "   - Social sentiment trends\n"
            "   - Volume and liquidity analysis\n"
            "   - Technical indicators and patterns\n\n"
            "3. Opportunities:\n"
            "   - Similar tokens with potential\n"
            "   - Entry/exit points\n"
            "   - Risk-adjusted recommendations\n\n"
            "4. Risk Factors:\n"
            "   - Market risks\n"
            "   - Technical warnings\n"
            "   - Liquidity considerations\n\n"
            "5. Action Items:\n"
            "   - Specific trading recommendations\n"
            "   - Portfolio adjustments\n"
            "   - Risk management strategies"
        )

        chat_history = [
            SystemMessage(
                content="You are a professional crypto analyst specializing in portfolio optimization "
                        "and risk-adjusted trading recommendations."
            ),
            HumanMessage(content=prompt)
        ]

        result = self.model.invoke(chat_history)
        
        return {
            "consolidated_insights": result.content,
            "details": {
                "wallet_analysis": wallet,
                "sentiment_analysis": sentiment,
                "technical_analysis": technical,
                "volume_analysis": volume_analysis,
                "technical_details": technical_details,
                "user_preferences": user_preferences
            }
        }
