from tools.wallet_tool import BasescanAPI
import json

def test_basescan():
    api = BasescanAPI()
    test_address = "0xe9825fd47c5d863b1aecba3707abcc7c8b49b88d" # Your test address
    
    try:
        # Get raw data
        raw_data = api.get_normal_transactions(test_address)
        print("\nRaw API Response:")
        print(json.dumps(raw_data, indent=2))
        
        # Process transfers
        processed = api.process_transfers(raw_data)
        print("\nProcessed Transactions:")
        print(json.dumps(processed, indent=2))
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_basescan() 