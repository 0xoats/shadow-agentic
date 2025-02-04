import json
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class SolscanAPI:
    """Helper class to handle Solscan API V2 interactions"""
    BASE_URL = "https://api-v2.solscan.io"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "origin": "https://solscan.io",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        })
    
    def get_token_balance_changes(self, address: str, num_pages: int = 10, page_size: int = 10) -> Dict:
        """
        Fetch token balance changes for a wallet address from Solscan
        
        Args:
            address: Solana wallet address
            num_pages: Number of pages to fetch (default: 10)
            page_size: Number of transactions per page (default: 10)
            
        Returns:
            Dictionary containing transaction data and metadata
        """
        all_data = {
            "success": True,
            "data": [],
            "metadata": {
                "tokens": {}
            }
        }

        for page in range(1, num_pages + 1):
            params = {
                "address": address,
                "page_size": page_size,
                "page": page,
                "exclude_token": "So11111111111111111111111111111111111111111"  # Exclude native SOL
            }
            
            url = f"{self.BASE_URL}/v2/account/balance_change"
            
            try:
                # Make the actual GET request
                response = self.session.get(url, params=params)
                response.raise_for_status()
                page_data = response.json()
                
                if not page_data.get("success"):
                    print(f"Error fetching page {page}: {page_data.get('message', 'Unknown error')}")
                    continue
                
                # Add transaction data
                all_data["data"].extend(page_data.get("data", []))
                
                # Update metadata
                if "metadata" in page_data and "tokens" in page_data["metadata"]:
                    all_data["metadata"]["tokens"].update(page_data["metadata"]["tokens"])
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue
            
        return all_data

    def process_balance_changes(self, raw_data: Dict) -> List[Dict]:
        """
        Process raw balance change data into a standardized format
        """
        processed_txs = []
        tokens_metadata = raw_data.get("metadata", {}).get("tokens", {})
        
        for tx in raw_data.get("data", []):
            try:
                token_address = tx.get("token_address")
                token_info = tokens_metadata.get(token_address, {})
                
                # Calculate actual amount based on decimals
                decimals = tx.get("token_decimals", 0)
                raw_amount = float(tx.get("amount", 0))
                actual_amount = raw_amount / (10 ** decimals)
                
                processed_tx = {
                    "id": tx.get("trans_id"),
                    "token": token_info.get("token_symbol", "UNKNOWN"),
                    "token_address": token_address,
                    "amount": actual_amount,
                    "type": "buy" if tx.get("change_type") == "inc" else "sell",
                    "timestamp": datetime.fromtimestamp(
                        int(tx.get("block_time", 0))
                    ).isoformat() + "Z",
                    "usd_value": actual_amount * float(token_info.get("price_usdt", 0))
                }
                processed_txs.append(processed_tx)
                
            except Exception as e:
                print(f"Error processing transaction: {e}")
                continue
                
        return processed_txs


class WalletTool:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")
        self.solscan = SolscanAPI()

    def analyze_wallet(self, wallet_address: str) -> dict:
        """
        Analyze wallet token balance changes and generate insights.
        """
        # Fetch token balance changes
        raw_data = self.solscan.get_token_balance_changes(wallet_address)
        
        # Process the transactions
        processed_transactions = self.solscan.process_balance_changes(raw_data)
        
        data = {
            "wallet": wallet_address,
            "transactions": processed_transactions
        }

        # Prepare the prompt for analysis
        prompt = (
            f"Analyze the following wallet transactions for wallet {wallet_address}. "
            "Focus on:\n"
            "1. Most frequently traded tokens\n"
            "2. Largest transactions by USD value\n"
            "3. Trading patterns (buying vs selling)\n"
            "4. Token preferences\n\n"
            f"{json.dumps(data, indent=2)}"
        )

        chat_history = [
            SystemMessage(
                content="You are an expert blockchain analyst skilled in interpreting "
                        "Solana wallet transaction data and token movements."
            ),
            HumanMessage(content=prompt)
        ]

        result = self.model.invoke(chat_history)
        analysis = result.content

        return {
            "wallet": wallet_address,
            "wallet_insights": analysis,
            "raw_data": data
        }