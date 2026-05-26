"""
IntelliKYC Blockchain Module
Privacy-preserving KYC verification system using zero-knowledge proofs
"""

from .block import Block, Blockchain
from .transaction import Transaction
from .storage import BlockchainStorage
from .zk_proofs import ZKProofGenerator, ZKProofManager

__version__ = "1.0.0"
__all__ = ["Block", "Blockchain", "Transaction", "BlockchainStorage", 
           "ZKProofGenerator", "ZKProofManager"]
