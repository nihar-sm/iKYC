import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from block import Blockchain, Block
from transaction import Transaction


class BlockchainStorage:
    """
    Handles persistent storage for the blockchain using JSON files.
    Provides save/load functionality and backup management.
    """
    
    def __init__(self, storage_path: str = "blockchain_data"):
        """
        Initialize storage manager with specified directory.
        
        :param storage_path: Directory path where blockchain files will be stored
        """
        self.storage_path = storage_path
        self.chain_file = os.path.join(storage_path, "blockchain.json")
        self.backup_dir = os.path.join(storage_path, "backups")
        self.metadata_file = os.path.join(storage_path, "metadata.json")
        
        # Create directories if they don't exist
        os.makedirs(storage_path, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def save_blockchain(self, blockchain: Blockchain) -> bool:
        """
        Save entire blockchain to JSON file.
        
        :param blockchain: Blockchain instance to save
        :return: True if successful, False otherwise
        """
        try:
            # Prepare blockchain data for JSON serialization
            blockchain_data = {
                "chain": [],
                "metadata": {
                    "total_blocks": len(blockchain.chain),
                    "difficulty": blockchain.difficulty,
                    "saved_at": datetime.now().isoformat(),
                    "last_block_hash": blockchain.last_block.hash if blockchain.chain else None
                }
            }
            
            # Convert each block to dictionary
            for block in blockchain.chain:
                block_data = {
                    "index": block.index,
                    "timestamp": block.timestamp,
                    "previous_hash": block.previous_hash,
                    "nonce": block.nonce,
                    "hash": block.hash,
                    "transactions": [tx.to_dict() for tx in block.transactions]
                }
                blockchain_data["chain"].append(block_data)
            
            # Save to file
            with open(self.chain_file, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            
            # Save metadata separately
            self._save_metadata(blockchain_data["metadata"])
            
            print(f"Blockchain saved successfully to {self.chain_file}")
            return True
            
        except Exception as e:
            print(f"Error saving blockchain: {str(e)}")
            return False

    def load_blockchain(self) -> Optional[Blockchain]:
        """
        Load blockchain from JSON file.
        
        :return: Blockchain instance if successful, None otherwise
        """
        try:
            if not os.path.exists(self.chain_file):
                print("No saved blockchain found. Creating new blockchain.")
                return Blockchain()
            
            with open(self.chain_file, 'r') as f:
                blockchain_data = json.load(f)
            
            # Create new blockchain instance
            blockchain = Blockchain.__new__(Blockchain)
            blockchain.unconfirmed_transactions = []
            blockchain.chain = []
            
            # Set difficulty from saved metadata
            if "metadata" in blockchain_data:
                blockchain.difficulty = blockchain_data["metadata"].get("difficulty", 2)
            else:
                blockchain.difficulty = 2
            
            # Reconstruct blocks and transactions
            for block_data in blockchain_data["chain"]:
                transactions = []
                
                # Reconstruct transactions
                for tx_data in block_data["transactions"]:
                    transaction = Transaction(
                        sender=tx_data["sender"],
                        recipient=tx_data["recipient"],
                        payload=tx_data["payload"],
                        timestamp=tx_data["timestamp"],
                        signature=tx_data["signature"]
                    )
                    # Set the original hash
                    transaction.tx_hash = tx_data["tx_hash"]
                    transactions.append(transaction)
                
                # Reconstruct block
                block = Block(
                    index=block_data["index"],
                    transactions=transactions,
                    timestamp=block_data["timestamp"],
                    previous_hash=block_data["previous_hash"],
                    nonce=block_data["nonce"]
                )
                # Set the original hash
                block.hash = block_data["hash"]
                
                blockchain.chain.append(block)
            
            print(f"Blockchain loaded successfully from {self.chain_file}")
            print(f"Total blocks: {len(blockchain.chain)}")
            
            # Validate loaded blockchain
            if blockchain.check_chain_validity(blockchain.chain):
                print("Loaded blockchain is valid.")
                return blockchain
            else:
                print("WARNING: Loaded blockchain failed validation!")
                return blockchain  # Return anyway, but with warning
                
        except Exception as e:
            print(f"Error loading blockchain: {str(e)}")
            return None

    def create_backup(self, blockchain: Blockchain, backup_name: str = None) -> bool:
        """
        Create a backup copy of the blockchain.
        
        :param blockchain: Blockchain to backup
        :param backup_name: Custom backup name, auto-generated if None
        :return: True if successful, False otherwise
        """
        try:
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"blockchain_backup_{timestamp}.json"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Use the same format as save_blockchain
            blockchain_data = {
                "chain": [],
                "metadata": {
                    "total_blocks": len(blockchain.chain),
                    "difficulty": blockchain.difficulty,
                    "backup_created_at": datetime.now().isoformat(),
                    "last_block_hash": blockchain.last_block.hash if blockchain.chain else None
                }
            }
            
            for block in blockchain.chain:
                block_data = {
                    "index": block.index,
                    "timestamp": block.timestamp,
                    "previous_hash": block.previous_hash,
                    "nonce": block.nonce,
                    "hash": block.hash,
                    "transactions": [tx.to_dict() for tx in block.transactions]
                }
                blockchain_data["chain"].append(block_data)
            
            with open(backup_path, 'w') as f:
                json.dump(blockchain_data, f, indent=2)
            
            print(f"Backup created: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False

    def list_backups(self) -> List[str]:
        """
        List all available backup files.
        
        :return: List of backup filenames
        """
        try:
            backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.json')]
            backups.sort(reverse=True)  # Most recent first
            return backups
        except Exception as e:
            print(f"Error listing backups: {str(e)}")
            return []

    def load_from_backup(self, backup_filename: str) -> Optional[Blockchain]:
        """
        Load blockchain from a specific backup file.
        
        :param backup_filename: Name of backup file to load
        :return: Blockchain instance if successful, None otherwise
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_filename}")
                return None
            
            # Temporarily change chain_file to backup path
            original_chain_file = self.chain_file
            self.chain_file = backup_path
            
            # Load using existing method
            blockchain = self.load_blockchain()
            
            # Restore original chain_file
            self.chain_file = original_chain_file
            
            if blockchain:
                print(f"Blockchain restored from backup: {backup_filename}")
            
            return blockchain
            
        except Exception as e:
            print(f"Error loading from backup: {str(e)}")
            return None

    def _save_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Save blockchain metadata separately.
        
        :param metadata: Metadata dictionary to save
        :return: True if successful, False otherwise
        """
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")
            return False

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about stored blockchain files.
        
        :return: Dictionary containing storage information
        """
        info = {
            "storage_path": self.storage_path,
            "chain_file_exists": os.path.exists(self.chain_file),
            "metadata_file_exists": os.path.exists(self.metadata_file),
            "backups_count": len(self.list_backups()),
            "backups": self.list_backups()
        }
        
        if info["chain_file_exists"]:
            try:
                stat = os.stat(self.chain_file)
                info["chain_file_size"] = stat.st_size
                info["chain_file_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except:
                pass
        
        return info
