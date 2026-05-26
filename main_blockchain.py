"""
IntelliKYC Blockchain API - Main Application Runner
"""
import sys
import os
from pathlib import Path

def main():
    """Main application entry point"""
    
    # Add blockchain directory to Python path
    blockchain_dir = Path(__file__).parent / "blockchain"
    sys.path.insert(0, str(blockchain_dir))
    
    print("🚀 Starting IntelliKYC Blockchain API...")
    print("📊 API Documentation: http://localhost:8001/docs")
    print("🔐 Privacy-preserving KYC system ready!")
    print("=" * 50)
    
    try:
        import uvicorn
        
        # Use import string format for reload to work properly
        uvicorn.run(
            "blockchain.blockchain_api:app",  # Import string format
            host="0.0.0.0",
            port=8001,
            log_level="info",
            reload=True
        )
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all blockchain files are present")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
