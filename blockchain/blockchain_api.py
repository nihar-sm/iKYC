import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime

# Import blockchain modules (now properly resolved)
from block import Blockchain
from transaction import Transaction
from storage import BlockchainStorage
from zk_proofs import ZKProofGenerator, ZKProofManager

# Keep all the rest of your existing code unchanged\

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="IntelliKYC Blockchain API",
    description="REST API for KYC blockchain operations with zero-knowledge proofs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
blockchain = Blockchain()
storage_manager = BlockchainStorage()
zkp_generator = ZKProofGenerator()
zkp_manager = ZKProofManager()

# Pydantic models for API requests/responses
class TransactionRequest(BaseModel):
    sender: str
    recipient: str
    payload: Dict[str, Any]

class KYCCredentialRequest(BaseModel):
    customer_data: Dict[str, Any]
    verification_level: str
    issuing_institution: str

class ZKProofVerificationRequest(BaseModel):
    proof: Dict[str, Any]
    institution_id: Optional[str] = None

class CrossInstitutionSharingRequest(BaseModel):
    proof_id: str
    requesting_institution: str
    required_verification_level: str = "CDD"

class BlockchainResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# Health check endpoint
@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IntelliKYC Blockchain API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Blockchain endpoints
@app.get("/blockchain/info", tags=["Blockchain"], response_model=Dict[str, Any])
async def get_blockchain_info():
    """Get blockchain information and statistics"""
    try:
        chain_data = []
        for block in blockchain.chain:
            chain_data.append({
                'index': block.index,
                'timestamp': block.timestamp,
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'transaction_count': len(block.transactions),
                'nonce': block.nonce
            })
        
        return {
            "blockchain_length": len(blockchain.chain),
            "difficulty": blockchain.difficulty,
            "pending_transactions": len(blockchain.unconfirmed_transactions),
            "is_valid": blockchain.check_chain_validity(blockchain.chain),
            "last_block_hash": blockchain.last_block.hash if blockchain.chain else None,
            "blocks": chain_data
        }
    except Exception as e:
        logger.error(f"Error getting blockchain info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blockchain/validate", tags=["Blockchain"])
async def validate_blockchain():
    """Validate entire blockchain integrity"""
    try:
        is_valid = blockchain.check_chain_validity(blockchain.chain)
        return {
            "valid": is_valid,
            "message": "Blockchain is valid" if is_valid else "Blockchain validation failed",
            "validated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error validating blockchain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Transaction endpoints
@app.post("/transactions", tags=["Transactions"], response_model=BlockchainResponse)
async def add_transaction(request: TransactionRequest):
    """Add a new transaction to the blockchain"""
    try:
        # Create transaction
        transaction = Transaction(
            sender=request.sender,
            recipient=request.recipient,
            payload=request.payload
        )
        
        # Add to blockchain
        blockchain.add_new_transaction(transaction)
        
        logger.info(f"Transaction added: {transaction.tx_hash}")
        
        return BlockchainResponse(
            success=True,
            message="Transaction added successfully",
            data={
                "transaction_hash": transaction.tx_hash,
                "sender": transaction.sender,
                "recipient": transaction.recipient,
                "timestamp": transaction.timestamp
            }
        )
    except Exception as e:
        logger.error(f"Error adding transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transactions/pending", tags=["Transactions"])
async def get_pending_transactions():
    """Get all pending transactions"""
    try:
        pending = []
        for tx in blockchain.unconfirmed_transactions:
            pending.append(tx.to_dict())
        
        return {
            "pending_count": len(pending),
            "transactions": pending
        }
    except Exception as e:
        logger.error(f"Error getting pending transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Mining endpoints
@app.post("/mine", tags=["Mining"], response_model=BlockchainResponse)
async def mine_block():
    """Mine a new block with pending transactions"""
    try:
        if not blockchain.unconfirmed_transactions:
            return BlockchainResponse(
                success=False,
                message="No transactions to mine"
            )
        
        # Mine the block
        mined_block = blockchain.mine()
        
        if mined_block:
            logger.info(f"Block #{mined_block.index} mined successfully")
            
            return BlockchainResponse(
                success=True,
                message=f"Block #{mined_block.index} mined successfully",
                data={
                    "block_index": mined_block.index,
                    "block_hash": mined_block.hash,
                    "transaction_count": len(mined_block.transactions),
                    "nonce": mined_block.nonce,
                    "timestamp": mined_block.timestamp
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Mining failed")
            
    except Exception as e:
        logger.error(f"Error mining block: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# KYC-specific endpoints
@app.post("/kyc/credentials", tags=["KYC"], response_model=BlockchainResponse)
async def issue_kyc_credential(request: KYCCredentialRequest):
    """Issue a KYC credential and store on blockchain"""
    try:
        # Generate zero-knowledge proof
        zkp_proof = zkp_generator.generate_kyc_proof(
            customer_data=request.customer_data,
            verification_level=request.verification_level,
            issuing_institution=request.issuing_institution
        )
        
        # Create transaction with KYC credential
        kyc_transaction = Transaction(
            sender=request.issuing_institution,
            recipient="KYC_REGISTRY",
            payload={
                "type": "KYC_CREDENTIAL",
                "verification_level": request.verification_level,
                "proof_id": zkp_proof["proof_id"],
                "commitment_hash": zkp_proof["commitment_hash"],
                "public_claims": zkp_proof["public_claims"]
            }
        )
        
        # Add to blockchain
        blockchain.add_new_transaction(kyc_transaction)
        
        # Store ZK proof
        zkp_manager.store_proof(zkp_proof["proof_id"], zkp_proof)
        
        logger.info(f"KYC credential issued: {zkp_proof['proof_id']}")
        
        return BlockchainResponse(
            success=True,
            message="KYC credential issued successfully",
            data={
                "credential_id": zkp_proof["proof_id"],
                "transaction_hash": kyc_transaction.tx_hash,
                "verification_level": request.verification_level,
                "zk_proof_generated": True,
                "privacy_preserved": True
            }
        )
    except Exception as e:
        logger.error(f"Error issuing KYC credential: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/kyc/verify", tags=["KYC"])
async def verify_kyc_credential(request: ZKProofVerificationRequest):
    """Verify a KYC credential using zero-knowledge proof"""
    try:
        # Verify the proof
        verification_result = zkp_generator.verify_kyc_proof(request.proof)
        
        logger.info(f"KYC verification completed: {verification_result['valid']}")
        
        return {
            "verification_successful": verification_result["valid"],
            "verification_details": verification_result,
            "privacy_preserved": True,
            "verified_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error verifying KYC credential: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/kyc/share", tags=["KYC"])
async def share_kyc_credential(request: CrossInstitutionSharingRequest):
    """Share KYC credential across institutions"""
    try:
        # Get the original proof
        original_proof = zkp_manager.proof_store.get(request.proof_id)
        
        if not original_proof:
            raise HTTPException(status_code=404, detail="KYC credential not found")
        
        # Generate sharing proof
        sharing_proof = zkp_generator.generate_cross_institution_proof(
            original_proof=original_proof,
            requesting_institution=request.requesting_institution,
            required_verification_level=request.required_verification_level
        )
        
        logger.info(f"KYC credential shared: {request.proof_id}")
        
        return {
            "sharing_approved": sharing_proof["sharing_approved"],
            "sharing_proof": sharing_proof,
            "privacy_preserved": True,
            "shared_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error sharing KYC credential: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Storage endpoints
@app.post("/blockchain/save", tags=["Storage"])
async def save_blockchain():
    """Save blockchain to persistent storage"""
    try:
        success = storage_manager.save_blockchain(blockchain)
        
        if success:
            return {
                "success": True,
                "message": "Blockchain saved successfully",
                "saved_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save blockchain")
            
    except Exception as e:
        logger.error(f"Error saving blockchain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/blockchain/load", tags=["Storage"])
async def load_blockchain():
    """Load blockchain from persistent storage"""
    try:
        global blockchain
        loaded_blockchain = storage_manager.load_blockchain()
        
        if loaded_blockchain:
            blockchain = loaded_blockchain
            return {
                "success": True,
                "message": "Blockchain loaded successfully",
                "blocks_loaded": len(blockchain.chain),
                "loaded_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load blockchain")
            
    except Exception as e:
        logger.error(f"Error loading blockchain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage/info", tags=["Storage"])
async def get_storage_info():
    """Get storage information"""
    try:
        storage_info = storage_manager.get_storage_info()
        return storage_info
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for auto-mining
async def auto_mine_task():
    """Background task to automatically mine blocks when transactions are pending"""
    while True:
        try:
            if len(blockchain.unconfirmed_transactions) >= 1:  # Mine when 1+ transactions pending
                mined_block = blockchain.mine()
                if mined_block:
                    logger.info(f"Auto-mined block #{mined_block.index}")
            await asyncio.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Auto-mining error: {str(e)}")
            await asyncio.sleep(30)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("IntelliKYC Blockchain API starting up...")
    
    # Load existing blockchain if available
    try:
        loaded_blockchain = storage_manager.load_blockchain()
        if loaded_blockchain and len(loaded_blockchain.chain) > 1:  # More than genesis block
            global blockchain
            blockchain = loaded_blockchain
            logger.info(f"Loaded existing blockchain with {len(blockchain.chain)} blocks")
    except Exception as e:
        logger.warning(f"Could not load existing blockchain: {str(e)}")
    
    # Start auto-mining task
    asyncio.create_task(auto_mine_task())
    logger.info("Auto-mining background task started")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("IntelliKYC Blockchain API shutting down...")
    
    # Save blockchain before shutdown
    try:
        storage_manager.save_blockchain(blockchain)
        logger.info("Blockchain saved during shutdown")
    except Exception as e:
        logger.error(f"Failed to save blockchain during shutdown: {str(e)}")

# Run the API server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_level="info"
    )
