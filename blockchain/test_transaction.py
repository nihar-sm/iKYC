from transaction import Transaction
import time

def main():
    tx = Transaction(
        sender="Bank_A",
        recipient="Customer_123",
        payload={
            "kyc_id": "kyc_001",
            "verification_level": "CDD",
            "status": "APPROVED",
            "details": "Basic KYC verification completed."
        }
    )
    print("Transaction hash:", tx.tx_hash)
    print("Transaction dict:", tx.to_dict())

if __name__ == "__main__":
    main()
