from block import Blockchain
from transaction import Transaction


def main():
    blockchain = Blockchain()

    # Create a sample transaction
    tx1 = Transaction(
        sender="Bank_A",
        recipient="Customer_123",
        payload={
            "kyc_id": "kyc_001",
            "verification_level": "CDD",
            "status": "APPROVED",
            "details": "Basic KYC verification completed."
        }
    )

    # Add the transaction
    blockchain.add_new_transaction(tx1)

    # Mine a block containing the transaction
    mined_block = blockchain.mine()
    if mined_block:
        print(f"Mined block #{mined_block.index} with hash: {mined_block.hash}")

    # Validate blockchain integrity
    is_valid = blockchain.check_chain_validity(blockchain.chain)
    print(f"Blockchain valid? {is_valid}")


if __name__ == "__main__":
    main()
