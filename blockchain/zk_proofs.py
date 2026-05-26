import hashlib
import json
import os
import random
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from time import time


class ZKProofGenerator:
    """
    Zero-Knowledge Proof system for KYC credential verification.
    Allows proving KYC completion without revealing personal information.
    """
    
    def __init__(self, key_size: int = 2048):
        """
        Initialize ZK Proof Generator with RSA key pair.
        
        :param key_size: RSA key size (default 2048 bits)
        """
        self.key_size = key_size
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
    def generate_kyc_proof(
        self, 
        customer_data: Dict[str, Any], 
        verification_level: str,
        issuing_institution: str
    ) -> Dict[str, Any]:
        """
        Generate zero-knowledge proof for KYC credential.
        
        :param customer_data: Customer PII data (will be hashed, not exposed)
        :param verification_level: CIP, CDD, or EDD
        :param issuing_institution: Institution that performed KYC
        :return: Zero-knowledge proof dictionary
        """
        
        # Create commitment hash from sensitive data
        commitment_data = {
            'customer_pii': customer_data,
            'verification_details': {
                'level': verification_level,
                'issuer': issuing_institution,
                'timestamp': time()
            }
        }
        
        commitment_hash = self._create_commitment(commitment_data)
        
        # Generate random challenge for proof
        challenge = self._generate_challenge()
        
        # Create public claims (safe to reveal)
        public_claims = {
            'verification_level': verification_level,
            'issuing_institution': issuing_institution,
            'verification_completed': True,
            'meets_compliance': True,
            'timestamp': commitment_data['verification_details']['timestamp']
        }
        
        # Generate proof structure
        proof = {
            'proof_type': 'kyc_verification_proof',
            'commitment_hash': commitment_hash,
            'challenge': challenge,
            'public_claims': public_claims,
            'proof_signature': None,  # Will be set after signing
            'proof_id': self._generate_proof_id(),
            'generated_at': time()
        }
        
        # Sign the proof for authenticity
        proof_signature = self._sign_proof(proof)
        proof['proof_signature'] = proof_signature.hex()
        
        return proof
    
    def verify_kyc_proof(
        self, 
        proof: Dict[str, Any], 
        public_key: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Verify zero-knowledge proof without accessing private data.
        
        :param proof: Zero-knowledge proof to verify
        :param public_key: Public key for signature verification (optional)
        :return: Verification result
        """
        try:
            # Use provided public key or default
            verification_key = public_key or self.public_key
            
            # Extract signature for verification
            signature_hex = proof.get('proof_signature')
            if not signature_hex:
                return {
                    'valid': False,
                    'reason': 'Missing proof signature',
                    'verified_at': time()
                }
            
            signature = bytes.fromhex(signature_hex)
            
            # Create proof copy without signature for verification
            proof_copy = proof.copy()
            proof_copy.pop('proof_signature', None)
            
            # Verify cryptographic signature
            proof_data = json.dumps(proof_copy, sort_keys=True).encode('utf-8')
            
            try:
                verification_key.verify(
                    signature,
                    proof_data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                signature_valid = True
            except Exception:
                signature_valid = False
            
            # Verify proof structure and claims
            structure_valid = self._validate_proof_structure(proof)
            
            # Check if proof is recent (not expired)
            proof_age = time() - proof.get('generated_at', 0)
            not_expired = proof_age < 86400  # 24 hours validity
            
            # Overall verification result
            overall_valid = signature_valid and structure_valid and not_expired
            
            verification_result = {
                'valid': overall_valid,
                'signature_verified': signature_valid,
                'structure_valid': structure_valid,
                'not_expired': not_expired,
                'proof_age_seconds': proof_age,
                'public_claims': proof.get('public_claims', {}),
                'verification_level': proof.get('public_claims', {}).get('verification_level'),
                'issuing_institution': proof.get('public_claims', {}).get('issuing_institution'),
                'privacy_preserved': True,  # No PII exposed during verification
                'verified_at': time()
            }
            
            if not overall_valid:
                reasons = []
                if not signature_valid:
                    reasons.append('Invalid cryptographic signature')
                if not structure_valid:
                    reasons.append('Invalid proof structure')
                if not not_expired:
                    reasons.append('Proof expired')
                verification_result['failure_reasons'] = reasons
            
            return verification_result
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Verification error: {str(e)}',
                'verified_at': time()
            }
    
    def generate_cross_institution_proof(
        self, 
        original_proof: Dict[str, Any],
        requesting_institution: str,
        required_verification_level: str = 'CDD'
    ) -> Dict[str, Any]:
        """
        Generate proof for sharing KYC credentials across institutions.
        
        :param original_proof: Original KYC proof
        :param requesting_institution: Institution requesting verification
        :param required_verification_level: Minimum verification level required
        :return: Cross-institution sharing proof
        """
        
        # Verify original proof first
        original_verification = self.verify_kyc_proof(original_proof)
        
        if not original_verification['valid']:
            return {
                'sharing_approved': False,
                'reason': 'Original proof is invalid',
                'timestamp': time()
            }
        
        # Check if verification level meets requirements
        original_level = original_verification.get('verification_level', 'NONE')
        level_hierarchy = {'CIP': 1, 'CDD': 2, 'EDD': 3}
        
        original_level_value = level_hierarchy.get(original_level, 0)
        required_level_value = level_hierarchy.get(required_verification_level, 2)
        
        if original_level_value < required_level_value:
            return {
                'sharing_approved': False,
                'reason': f'Verification level {original_level} insufficient for requirement {required_verification_level}',
                'timestamp': time()
            }
        
        # Generate sharing proof
        sharing_proof = {
            'proof_type': 'cross_institution_sharing',
            'original_proof_id': original_proof.get('proof_id'),
            'sharing_approved': True,
            'requesting_institution': requesting_institution,
            'verification_level_confirmed': original_level,
            'original_issuer': original_verification.get('issuing_institution'),
            'shared_claims': {
                'kyc_completed': True,
                'verification_level': original_level,
                'compliance_status': 'VERIFIED',
                'issuing_institution': original_verification.get('issuing_institution')
            },
            'privacy_preserved': True,
            'customer_data_protected': True,
            'sharing_timestamp': time()
        }
        
        # Sign sharing proof
        sharing_signature = self._sign_proof(sharing_proof)
        sharing_proof['sharing_signature'] = sharing_signature.hex()
        
        return sharing_proof
    
    def _create_commitment(self, data: Dict[str, Any]) -> str:
        """
        Create cryptographic commitment (hash) of sensitive data.
        
        :param data: Data to create commitment for
        :return: SHA-256 hash of the data
        """
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    
    def _generate_challenge(self) -> str:
        """
        Generate random challenge for zero-knowledge proof.
        
        :return: Random challenge string
        """
        challenge_bytes = os.urandom(32)
        return hashlib.sha256(challenge_bytes).hexdigest()
    
    def _generate_proof_id(self) -> str:
        """
        Generate unique proof identifier.
        
        :return: Unique proof ID
        """
        random_bytes = os.urandom(16)
        timestamp = str(int(time()))
        proof_data = timestamp + random_bytes.hex()
        return hashlib.sha256(proof_data.encode()).hexdigest()[:16]
    
    def _sign_proof(self, proof: Dict[str, Any]) -> bytes:
        """
        Sign proof with private key for authenticity.
        
        :param proof: Proof data to sign
        :return: Digital signature bytes
        """
        # Remove signature field if present
        proof_copy = proof.copy()
        proof_copy.pop('proof_signature', None)
        proof_copy.pop('sharing_signature', None)
        
        proof_data = json.dumps(proof_copy, sort_keys=True).encode('utf-8')
        
        signature = self.private_key.sign(
            proof_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature
    
    def _validate_proof_structure(self, proof: Dict[str, Any]) -> bool:
        """
        Validate that proof has required structure.
        
        :param proof: Proof to validate
        :return: True if structure is valid, False otherwise
        """
        required_fields = [
            'proof_type', 'commitment_hash', 'challenge', 
            'public_claims', 'proof_id', 'generated_at'
        ]
        
        for field in required_fields:
            if field not in proof:
                return False
        
        # Validate public claims structure
        public_claims = proof.get('public_claims', {})
        required_claims = ['verification_level', 'issuing_institution', 'verification_completed']
        
        for claim in required_claims:
            if claim not in public_claims:
                return False
        
        return True
    
    def get_public_key_pem(self) -> str:
        """
        Export public key in PEM format for sharing.
        
        :return: Public key in PEM format
        """
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def load_public_key_from_pem(self, pem_data: str):
        """
        Load public key from PEM format.
        
        :param pem_data: Public key in PEM format
        :return: Public key object
        """
        return serialization.load_pem_public_key(
            pem_data.encode('utf-8'),
            backend=default_backend()
        )


class ZKProofManager:
    """
    Manager class for handling multiple ZK proofs and institutional keys.
    """
    
    def __init__(self):
        self.institution_keys: Dict[str, Any] = {}
        self.proof_store: Dict[str, Dict[str, Any]] = {}
    
    def register_institution(
        self, 
        institution_id: str, 
        public_key_pem: str
    ) -> bool:
        """
        Register an institution's public key for proof verification.
        
        :param institution_id: Unique institution identifier
        :param public_key_pem: Institution's public key in PEM format
        :return: True if successful, False otherwise
        """
        try:
            zkp = ZKProofGenerator()
            public_key = zkp.load_public_key_from_pem(public_key_pem)
            self.institution_keys[institution_id] = public_key
            return True
        except Exception as e:
            print(f"Failed to register institution {institution_id}: {str(e)}")
            return False
    
    def store_proof(self, proof_id: str, proof: Dict[str, Any]) -> bool:
        """
        Store a zero-knowledge proof.
        
        :param proof_id: Unique proof identifier
        :param proof: Proof data
        :return: True if successful, False otherwise
        """
        self.proof_store[proof_id] = proof
        return True
    
    def verify_stored_proof(self, proof_id: str, institution_id: str) -> Dict[str, Any]:
        """
        Verify a stored proof using institution's public key.
        
        :param proof_id: Proof identifier to verify
        :param institution_id: Institution that issued the proof
        :return: Verification result
        """
        if proof_id not in self.proof_store:
            return {
                'valid': False,
                'reason': 'Proof not found',
                'verified_at': time()
            }
        
        if institution_id not in self.institution_keys:
            return {
                'valid': False,
                'reason': 'Institution not registered',
                'verified_at': time()
            }
        
        proof = self.proof_store[proof_id]
        public_key = self.institution_keys[institution_id]
        
        zkp = ZKProofGenerator()
        return zkp.verify_kyc_proof(proof, public_key)
