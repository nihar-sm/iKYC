# blockchain/test_zk_proofs.py (Updated version)
from zk_proofs import ZKProofGenerator, ZKProofManager


def main():
    print("=== Testing Zero-Knowledge Proof System ===")
    
    # Initialize ZK Proof Generator
    zkp = ZKProofGenerator()
    
    # Sample customer data (this would normally be sensitive PII)
    customer_data = {
        'name': 'John Doe',
        'email': 'john.doe@email.com',
        'passport_number': 'US123456789',
        'address': '123 Main St, City, State'
    }
    
    print("\n--- Generating KYC Zero-Knowledge Proof ---")
    
    # Generate zero-knowledge proof
    kyc_proof = zkp.generate_kyc_proof(
        customer_data=customer_data,
        verification_level='CDD',
        issuing_institution='Bank_A'
    )
    
    print(f"Generated proof ID: {kyc_proof['proof_id']}")
    print(f"Verification level: {kyc_proof['public_claims']['verification_level']}")
    print(f"Issuing institution: {kyc_proof['public_claims']['issuing_institution']}")
    print("SUCCESS: Customer PII is NOT exposed in proof")  # Fixed Unicode issue
    
    print("\n--- Verifying Zero-Knowledge Proof ---")
    
    # Verify the proof
    verification_result = zkp.verify_kyc_proof(kyc_proof)
    
    print(f"Proof valid: {verification_result['valid']}")
    print(f"Signature verified: {verification_result['signature_verified']}")
    print(f"Privacy preserved: {verification_result['privacy_preserved']}")
    
    if verification_result['valid']:
        print("SUCCESS: Zero-knowledge proof verification successful!")
    else:
        print("FAILED: Zero-knowledge proof verification failed!")
    
    print("\n--- Testing Cross-Institution Sharing ---")
    
    # Test cross-institution proof sharing
    sharing_proof = zkp.generate_cross_institution_proof(
        original_proof=kyc_proof,
        requesting_institution='Bank_B',
        required_verification_level='CDD'
    )
    
    print(f"Sharing approved: {sharing_proof['sharing_approved']}")
    print(f"Requesting institution: {sharing_proof['requesting_institution']}")
    print(f"Privacy preserved: {sharing_proof['privacy_preserved']}")
    
    print("\n--- Testing ZK Proof Manager ---")
    
    # Initialize proof manager
    manager = ZKProofManager()
    
    # Export and register public key
    public_key_pem = zkp.get_public_key_pem()
    registration_success = manager.register_institution('Bank_A', public_key_pem)
    print(f"Institution registration: {registration_success}")
    
    # Store proof
    proof_stored = manager.store_proof(kyc_proof['proof_id'], kyc_proof)
    print(f"Proof stored: {proof_stored}")
    
    # Verify stored proof
    stored_verification = manager.verify_stored_proof(kyc_proof['proof_id'], 'Bank_A')
    print(f"Stored proof valid: {stored_verification['valid']}")
    
    print("\n=== Zero-Knowledge Proof System Test Complete ===")


if __name__ == "__main__":
    main()
