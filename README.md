# iKYC-TeamVagabond-Hackverse2025
Team Vagabond's submission for Hackverse 2025 - a 36 hour hackathon hosted by MIT Bengaluru in collaboration with IBM, AWS and 1M1B. 
The project, a KYC automation, secured 2nd place in the Fintech category of the competition.

NOTE: Keys of IBM and AWS services have expired; real-world implementation must include connection to govt. database for validation

Project: IntelliKYC - AI Powered KYC Verification
- Multi-component system: Backend (FastAPI), Frontend (Streamlit), Redis backend.
- Uses multi-engine OCR: EasyOCR, OCR.space, Mock OCR as fallback.
- Integrates IBM Granite AI for semantic and fraud evaluations.
- Uses IBM NLU for advanced document content analysis.
- Uses AWS Bedrock Nova models for document authenticity and risk.
- Features include document digitization, fraud detection, and face liveness verification.
- Validation pipeline (personal info, document, contact, face) with multi-step sequential processing.
- Data managed via Redis including user, Aadhaar, PAN, sessions, OTPs, blacklists.
- Dockerized with separate containers for backend, frontend, and Redis.
- Capable to integrate multi-modal AI including image + text processing.
- Immutably records KYC verifications—each verification is stored as a transaction on the blockchain.
- Preserves privacy with zero-knowledge proofs—all customer attestations are validated and shared across banks without revealing any personal data.

System Dependencies:
- Python packages: fastapi, uvicorn, streamlit, redis, requests, pillow, numpy, opencv, mediapipe, easyocr, boto3, ibm-watson.
- Requires Redis server running (can be dockerized).
