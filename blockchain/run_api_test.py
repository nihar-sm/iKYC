import subprocess
import time
import sys
import os

def run_api_and_test():
    print("Starting IntelliKYC Blockchain API server...")
    
    # Start API server in background
    api_process = subprocess.Popen([
        sys.executable, "blockchain_api.py"
    ], cwd=os.getcwd())
    
    try:
        # Wait for server to start
        print("Waiting 5 seconds for server to start...")
        time.sleep(5)
        
        # Run the test
        print("Running API tests...")
        test_process = subprocess.run([
            sys.executable, "test_blockchain_api.py"
        ], cwd=os.getcwd())
        
    finally:
        # Clean up: stop the API server
        print("Stopping API server...")
        api_process.terminate()
        api_process.wait()
        print("Done!")

if __name__ == "__main__":
    run_api_and_test()
