from block import Blockchain
from transaction import Transaction
from storage import BlockchainStorage


def main():
    print("=== Testing Blockchain Storage ===")
    
    # Initialize storage manager
    storage = BlockchainStorage()
    
    # Create a blockchain with some transactions
    blockchain = Blockchain()
    
    # Add a few transactions and mine blocks
    tx1 = Transaction(
        sender="Bank_A",
        recipient="Customer_123",
        payload={"kyc_id": "kyc_001", "status": "APPROVED"}
    )
    
    tx2 = Transaction(
        sender="Bank_B", 
        recipient="Customer_456",
        payload={"kyc_id": "kyc_002", "status": "PENDING"}
    )
    
    blockchain.add_new_transaction(tx1)
    blockchain.add_new_transaction(tx2)
    blockchain.mine()
    
    print(f"Created blockchain with {len(blockchain.chain)} blocks")
    
    # Save blockchain
    print("\n--- Saving blockchain ---")
    save_success = storage.save_blockchain(blockchain)
    print(f"Save successful: {save_success}")
    
    # Create backup
    print("\n--- Creating backup ---")
    backup_success = storage.create_backup(blockchain)
    print(f"Backup successful: {backup_success}")
    
    # Load blockchain
    print("\n--- Loading blockchain ---")
    loaded_blockchain = storage.load_blockchain()
    
    if loaded_blockchain:
        print(f"Loaded blockchain with {len(loaded_blockchain.chain)} blocks")
        print(f"Chain valid: {loaded_blockchain.check_chain_validity(loaded_blockchain.chain)}")
    
    # Display storage info
    print("\n--- Storage Information ---")
    info = storage.get_storage_info()
    for key, value in info.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
