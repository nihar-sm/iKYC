# blockchain/test_blockchain_api.py
import requests
import json
import time
import threading
import subprocess

# API base URL
BASE_URL = "http://localhost:8001"

def test_api():
    print("=== Testing IntelliKYC Blockchain API ===")
    
    try:
        # 1. Health check
        print("\n--- Health Check ---")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print(f"Health check: {response.json()}")
        else:
            print(f"Health check failed: {response.status_code}")
            return
        
        # 2. Get blockchain info
        print("\n--- Blockchain Info ---")
        response = requests.get(f"{BASE_URL}/blockchain/info")
        if response.status_code == 200:
            blockchain_info = response.json()
            print(f"Blockchain length: {blockchain_info['blockchain_length']}")
            print(f"Is valid: {blockchain_info['is_valid']}")
        
        # 3. Add KYC credential transaction
        print("\n--- Issue KYC Credential ---")
        kyc_request = {
            "customer_data": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "passport": "US123456789"
            },
            "verification_level": "CDD",
            "issuing_institution": "Bank_A"
        }
        
        response = requests.post(f"{BASE_URL}/kyc/credentials", json=kyc_request)
        if response.status_code == 200:
            kyc_result = response.json()
            print(f"KYC credential issued: {kyc_result.get('success', False)}")
        else:
            print(f"KYC credential failed: {response.status_code}")
        
        # 4. Add regular transaction
        print("\n--- Add Transaction ---")
        transaction_request = {
            "sender": "Bank_B",
            "recipient": "Customer_456",
            "payload": {
                "type": "ACCOUNT_OPENING",
                "account_type": "SAVINGS",
                "initial_deposit": 1000
            }
        }
        
        response = requests.post(f"{BASE_URL}/transactions", json=transaction_request)
        if response.status_code == 200:
            tx_result = response.json()
            print(f"Transaction added: {tx_result.get('success', False)}")
        
        # 5. Mine a block
        print("\n--- Mine Block ---")
        response = requests.post(f"{BASE_URL}/mine")
        if response.status_code == 200:
            mine_result = response.json()
            print(f"Mining result: {mine_result.get('success', False)}")
        
        # 6. Validate blockchain
        print("\n--- Validate Blockchain ---")
        response = requests.get(f"{BASE_URL}/blockchain/validate")
        if response.status_code == 200:
            validation = response.json()
            print(f"Validation: {validation.get('valid', False)}")
        
        print("\n=== API Test Complete ===")
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API server. Make sure the server is running at http://localhost:8001")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_api()
