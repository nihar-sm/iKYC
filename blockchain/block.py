import hashlib
import json
from time import time
from typing import List, Optional, Any
from transaction import Transaction  # Import the Transaction class


class Block:
    def __init__(
        self,
        index: int,
        transactions: List[Transaction],
        timestamp: Optional[float] = None,
        previous_hash: str = '',
        nonce: int = 0
    ):
        self.index = index                          # Position of block in chain
        self.transactions = transactions            # List of Transaction objects
        self.timestamp = timestamp or time()        # Creation time (epoch)
        self.previous_hash = previous_hash          # Hash of previous block
        self.nonce = nonce                          # Proof of Work nonce
        self.hash = self.compute_hash()             # SHA256 hash of block contents

    def compute_hash(self) -> str:
        """
        Compute SHA-256 hash of block contents: index, transactions, timestamp, previous_hash, nonce.
        Transactions serialized via their to_dict method for consistency.
        """
        block_data = {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],  # serialize transactions
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }

        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


class Blockchain:
    difficulty = 2  # Number of leading zeros required in hash for PoW

    def __init__(self):
        self.unconfirmed_transactions: List[Transaction] = []  # Transactions waiting to be mined
        self.chain: List[Block] = []
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Creates genesis block with empty transactions and mine it.
        """
        genesis_block = Block(0, [], time(), previous_hash="0")
        proof = self.proof_of_work(genesis_block)
        genesis_block.hash = proof
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def proof_of_work(self, block: Block) -> str:
        """
        Simple Proof of Work algorithm:
        Increment nonce until hash starts with `difficulty` zeros.
        """
        block.nonce = 0
        computed_hash = block.compute_hash()

        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    def add_block(self, block: Block, proof: str) -> bool:
        """
        Adds block after verification:
        - previous_hash matches
        - proof is valid
        """
        if block.previous_hash != self.last_block.hash:
            print("Previous hash mismatch.")
            return False

        if not self.is_valid_proof(block, proof):
            print("Invalid proof of work.")
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def is_valid_proof(self, block: Block, block_hash: str) -> bool:
        """
        Validates hash and difficulty.
        """
        return block_hash.startswith('0' * Blockchain.difficulty) and block_hash == block.compute_hash()

    def add_new_transaction(self, transaction: Transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self) -> Optional[Block]:
        """
        Create new block with current unconfirmed transactions and mine it.
        """
        if not self.unconfirmed_transactions:
            print("No transactions to mine.")
            return None

        new_block = Block(
            index=self.last_block.index + 1,
            transactions=self.unconfirmed_transactions.copy(),
            timestamp=time(),
            previous_hash=self.last_block.hash
        )

        proof = self.proof_of_work(new_block)
        added = self.add_block(new_block, proof)

        if added:
            self.unconfirmed_transactions = []
            print(f"Block #{new_block.index} mined with hash: {new_block.hash}")
            return new_block
        else:
            print("Failed to add block after mining.")
            return None

    def check_chain_validity(self, chain: List[Block]) -> bool:
        previous_hash = "0"
        for block in chain:
            if block.previous_hash != previous_hash:
                print(f"Previous hash mismatch at block {block.index}")
                return False

            computed_hash = block.compute_hash()
            if block.hash != computed_hash:
                print(f"Hash mismatch at block {block.index}")
                return False

            if block.index != 0 and not block.hash.startswith('0' * Blockchain.difficulty):
                print(f"Proof of work not satisfied at block {block.index}")
                return False

            previous_hash = block.hash
        return True
