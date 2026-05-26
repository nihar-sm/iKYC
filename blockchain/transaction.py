import json
import hashlib
from time import time
from typing import Dict, Any


class Transaction:
    def __init__(
        self,
        sender: str,
        recipient: str,
        payload: Dict[str, Any],
        timestamp: float = None,
        signature: str = ''
    ):
        """
        Represents a single transaction in the blockchain.

        :param sender: Identifier of the party sending the transaction
        :param recipient: Identifier of the party receiving the transaction
        :param payload: Transaction data; for KYC, this could include credential info
        :param timestamp: Unix timestamp of transaction creation
        :param signature: Digital signature of sender for authenticity (optional here)
        """
        self.sender = sender
        self.recipient = recipient
        self.payload = payload
        self.timestamp = timestamp or time()
        self.signature = signature  # Placeholder for future cryptographic signing
        self.tx_hash = self.compute_hash()

    def compute_hash(self) -> str:
        """
        Returns the SHA-256 hash of the transaction data to ensure immutability.
        """
        tx_dict = {
            'sender': self.sender,
            'recipient': self.recipient,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'signature': self.signature
        }
        tx_string = json.dumps(tx_dict, sort_keys=True).encode()
        return hashlib.sha256(tx_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Return the transaction data as a dictionary.
        """
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'tx_hash': self.tx_hash
        }
