import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv
import os
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage

load_dotenv()

class Chain(Enum):
    SOLANA = "solana"
    ETHEREUM = "ethereum"

class BaseAPI:
    """Base class for blockchain API interactions"""
    def __init__(self):
        self.session = requests.Session()
    
    def detect_chain(self, address: str) -> Chain:
        """Detect which chain the address belongs to"""
        # Ethereum addresses are 42 characters long and start with 0x
        if address.startswith("0x") and len(address) == 42:
            return Chain.ETHEREUM
        # Solana addresses are 32-44 characters and use base58
        elif len(address) >= 32 and len(address) <= 44:
            return Chain.SOLANA
        else:
            raise ValueError("Invalid address format")

class SolscanAPI(BaseAPI):
    """Helper class to handle Solscan API V2 interactions"""
    BASE_URL = "https://api-v2.solscan.io"
    
    def __init__(self):
        super().__init__()
        self.session.headers.update({
            "origin": "https://solscan.io",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
    
    def get_token_balance_changes(self, address: str, max_transactions: int = 40) -> Dict:
        """
        Fetch token balance changes for a Solana wallet from the last 10 days
        Limited to max_transactions to stay within model context limits
        """
        all_data = {
            "success": True,
            "data": [],
            "metadata": {"tokens": {}}
        }
        
        # Calculate timestamp for 10 days ago
        ten_days_ago = int((datetime.now() - timedelta(days=10)).timestamp())
        
        page = 1
        page_size = 20  # Smaller page size to avoid fetching too much at once
        
        while len(all_data["data"]) < max_transactions:
            params = {
                "address": address,
                "page_size": page_size,
                "page": page,
                "exclude_token": "So11111111111111111111111111111111111111111"
            }
            
            try:
                response = self.session.get(f"{self.BASE_URL}/v2/account/balance_change", params=params)
                response.raise_for_status()
                page_data = response.json()
                
                if not page_data.get("success"):
                    print(f"Error fetching page {page}: {page_data.get('message')}")
                    break
                
                # Filter transactions from the last 10 days
                filtered_data = [
                    tx for tx in page_data.get("data", [])
                    if int(tx.get("block_time", 0)) >= ten_days_ago
                ]
                
                # Add only up to max_transactions
                remaining_slots = max_transactions - len(all_data["data"])
                filtered_data = filtered_data[:remaining_slots]
                
                all_data["data"].extend(filtered_data)
                if "metadata" in page_data and "tokens" in page_data["metadata"]:
                    all_data["metadata"]["tokens"].update(page_data["metadata"]["tokens"])
                
                # Stop if we've reached our limit or if no new transactions
                if len(filtered_data) == 0 or len(all_data["data"]) >= max_transactions:
                    break
                
                page += 1
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        print(f"Retrieved {len(all_data['data'])} transactions")
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

class BasescanAPI(BaseAPI):
    """Helper class to handle Etherscan/Basescan API interactions"""
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("BASESCAN_API_KEY")
        self.base_url = "https://api.basescan.org/api"
    
    def get_token_transfers(self, address: str) -> Dict:
        """
        Fetch ERC20 token transfers for an Ethereum address from the past 5 days
        """
        # Calculate timestamp for 5 days ago
        five_days_ago = int((datetime.now() - timedelta(days=5)).timestamp())
        
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API-level errors
            if data.get("status") == "0":
                raise ValueError(f"API Error: {data.get('message', 'Unknown error')}")
            
            # Filter transactions from the past 5 days
            if isinstance(data.get("result"), list):
                filtered_result = [
                    tx for tx in data["result"]
                    if int(tx.get("timeStamp", 0)) >= five_days_ago
                ]
                data["result"] = filtered_result
                print(f"Filtered to {len(filtered_result)} transactions from the past 5 days")
            
            return data
            
        except requests.RequestException as e:
            print(f"Error fetching token transfers: {e}")
            raise
            
    def process_transfers(self, raw_data: Dict) -> List[Dict]:
        """Process raw transfer data into standardized format"""
        processed_txs = []
        
        # Validate raw_data structure
        if not isinstance(raw_data.get("result"), list):
            print(f"Invalid result format. Expected list, got: {type(raw_data.get('result'))}")
            return []
            
        for tx in raw_data.get("result", []):
            try:
                # Skip if tx is not a dict
                if not isinstance(tx, dict):
                    print(f"Invalid transaction format: {tx}")
                    continue
                    
                # Debug print
                print(f"\nProcessing transaction: {json.dumps(tx, indent=2)}")
                
                # Validate required fields
                required_fields = ["tokenDecimal", "value", "timeStamp", "hash", 
                                 "tokenSymbol", "contractAddress", "to", "from"]
                missing_fields = [field for field in required_fields if field not in tx]
                
                if missing_fields:
                    print(f"Warning: Missing required fields: {missing_fields}")
                    continue
                
                decimals = int(tx["tokenDecimal"])
                raw_amount = float(tx["value"])
                actual_amount = raw_amount / (10 ** decimals)
                
                # Determine transaction type
                tx_type = "unknown"
                if tx["to"] and tx["from"]:  # Ensure addresses exist
                    if tx["to"].lower() == address.lower():
                        tx_type = "buy"
                    elif tx["from"].lower() == address.lower():
                        tx_type = "sell"
                
                processed_tx = {
                    "id": tx["hash"],
                    "token": tx["tokenSymbol"],
                    "token_address": tx["contractAddress"],
                    "amount": actual_amount,
                    "type": tx_type,
                    "timestamp": datetime.fromtimestamp(int(tx["timeStamp"])).isoformat() + "Z",
                    "usd_value": None
                }
                processed_txs.append(processed_tx)
                
                print(f"Successfully processed transaction: {json.dumps(processed_tx, indent=2)}")
                
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
                print(f"Problematic transaction data: {json.dumps(tx, indent=2)}")
                continue
                
        return processed_txs

    def get_normal_transactions(self, address: str) -> Dict:
        """
        Fetch normal transactions for an Ethereum address from the past 5 days
        """
        five_days_ago = int((datetime.now() - timedelta(days=5)).timestamp())
        
        params = {
            "module": "account",
            "action": "txlist",  # for normal transactions
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 100,  # number of transactions to return
            "sort": "desc",
            "apikey": self.api_key
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "0":
                raise ValueError(f"API Error: {data.get('message', 'Unknown error')}")
            
            # Filter transactions from the past 5 days
            if isinstance(data.get("result"), list):
                filtered_result = [
                    tx for tx in data["result"]
                    if int(tx.get("timeStamp", 0)) >= five_days_ago
                ]
                data["result"] = filtered_result
                print(f"Filtered to {len(filtered_result)} normal transactions from the past 5 days")
            
            return data
            
        except requests.RequestException as e:
            print(f"Error fetching normal transactions: {e}")
            raise

    def process_normal_transactions(self, raw_data: Dict, address: str) -> List[Dict]:
        """Process raw normal transaction data into standardized format"""
        processed_txs = []
        
        if not isinstance(raw_data.get("result"), list):
            print(f"Invalid result format. Expected list, got: {type(raw_data.get('result'))}")
            return []
            
        for tx in raw_data.get("result", []):
            try:
                if not isinstance(tx, dict):
                    continue
                
                # Convert value from Wei to ETH
                value_in_eth = float(tx.get("value", "0")) / (10 ** 18)
                
                # Determine transaction type
                tx_type = "unknown"
                if tx["to"] and tx["from"]:
                    if tx["to"].lower() == address.lower():
                        tx_type = "receive"
                    elif tx["from"].lower() == address.lower():
                        tx_type = "send"
                
                processed_tx = {
                    "id": tx.get("hash"),
                    "token": "ETH",  # These are normal ETH transactions
                    "token_address": None,  # Native ETH doesn't have a contract address
                    "amount": value_in_eth,
                    "type": tx_type,
                    "timestamp": datetime.fromtimestamp(int(tx.get("timeStamp", 0))).isoformat() + "Z",
                    "gas_used": int(tx.get("gasUsed", 0)),
                    "gas_price": float(tx.get("gasPrice", 0)) / (10 ** 9),  # Convert to Gwei
                    "status": tx.get("isError", "0") == "0"  # "0" means success
                }
                processed_txs.append(processed_tx)
                
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
                continue
                
        return processed_txs

class WalletTool:
    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o")
        self.solscan = SolscanAPI()
        self.basescan = BasescanAPI()
        
    def analyze_wallet(self, wallet_address: str) -> dict:
        """Analyze wallet token movements and generate insights"""
        # Detect which chain the address belongs to
        chain = self.solscan.detect_chain(wallet_address)
        
        if chain == Chain.SOLANA:
            raw_data = self.solscan.get_token_balance_changes(wallet_address)
            processed_transactions = self.solscan.process_balance_changes(raw_data)
        else:  # ETHEREUM
            # Get both token transfers and normal transactions
            #token_data = self.basescan.get_token_transfers(wallet_address)
            normal_data = self.basescan.get_normal_transactions(wallet_address)
            
            processed_transactions = (
               # self.basescan.process_transfers(token_data) +
                self.basescan.process_normal_transactions(normal_data, wallet_address)
            )
        
        data = {
            "wallet": wallet_address,
            "chain": chain.value,
            "transactions": processed_transactions
        }

        prompt = (
            f"Analyze the following {chain.value} wallet transactions for wallet {wallet_address}. "
            "Focus on:\n"
            "1. Most frequently traded tokens\n"
            "2. Largest transactions by value\n"
            "3. Trading patterns (buying vs selling)\n"
            "4. Token preferences\n\n"
            f"{json.dumps(data, indent=2)}"
        )

        chat_history = [
            SystemMessage(
                content=f"You are an expert {chain.value} blockchain analyst skilled in interpreting "
                        "wallet transaction data and token movements."
            ),
            HumanMessage(content=prompt)
        ]

        result = self.model.invoke(chat_history)
        
        # Extract structured data from transactions
        tokens_bought = set()
        for tx in processed_transactions:
            if tx.get("type") in ["buy", "receive"]:
                token = tx.get("token")
                if token:
                    tokens_bought.add(token)
        
        return {
            "wallet": wallet_address,
            "chain": chain.value,
            "wallet_insights": result.content,
            "tokens_bought": list(tokens_bought),  # Add structured data
            "raw_data": data
        }