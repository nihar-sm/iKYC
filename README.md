# iKYC — Team Vagabond · Hackverse 2025

Team Vagabond's submission for Hackverse 2025 — a 36-hour hackathon hosted by MIT Bengaluru in collaboration with IBM, AWS and 1M1B. The project, a KYC automation platform, secured 2nd place in the Fintech category of the competition.

**Live demo:** [ikyc-demo.streamlit.app](https://ikyc-demo.streamlit.app)  
**GitHub:** [nihar-sm/iKYC](https://github.com/nihar-sm/iKYC)

---

## Project: iKYC — AI-Powered KYC Verification

iKYC automates identity verification using a fully open-source AI stack — no proprietary cloud AI services required. It processes Indian identity documents (Aadhaar, PAN), detects fraud, verifies face liveness, and records each verification immutably on a SHA-256 blockchain.

### Architecture

- **Multi-component system:** Backend (FastAPI), Frontend (Streamlit), Redis session store.
- **Document analysis:** Groq Vision AI (Llama 4 Scout) performs OCR, field extraction, and fraud scoring in a single multimodal API call — replacing IBM Granite and AWS Bedrock Nova.
- **Text & semantic analysis:** Groq LLM (Llama 3.3 70B) for NLU, entity consistency checks, and fraud pattern detection — replacing IBM Watson NLU.
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`) running locally — replacing Amazon Titan Embeddings.
- **OCR fallback:** EasyOCR (offline) with OCR.space as secondary fallback.
- **Face liveness:** MediaPipe FaceMesh — 3-step head movement challenge (left, right, forward) for active liveness detection.
- **Blockchain:** Custom SHA-256 hash chain records each KYC as an immutable transaction with a zero-knowledge proof ID.
- **Validation pipeline:** Personal info → document upload → AI analysis → face liveness → blockchain record → decision.
- **Data managed via Redis:** user sessions, Aadhaar/PAN records, OTPs, blacklists.
- **Dockerized** with separate containers for backend, frontend, and Redis.
- **Privacy-preserving:** Zero-knowledge proof IDs allow third-party verification without exposing customer PII.

### AI Stack (open-source / free-tier)

| Component | Service | Model |
|---|---|---|
| Document vision + OCR | Groq API | `meta-llama/llama-4-scout-17b-16e-instruct` |
| Text analysis + NLU | Groq API | `llama-3.3-70b-versatile` |
| Local embeddings | Sentence Transformers | `all-MiniLM-L6-v2` |
| Face liveness | MediaPipe | FaceMesh |
| OCR | EasyOCR | CRAFT + CRNN |

### System Dependencies

- **Python packages:** `groq`, `sentence-transformers`, `fastapi`, `uvicorn`, `streamlit`, `redis`, `requests`, `pillow`, `numpy`, `opencv-python-headless`, `mediapipe`, `easyocr`, `cryptography`
- **Environment:** `GROQ_API_KEY` (free at [console.groq.com](https://console.groq.com)) — all other dependencies are offline/open-source
- **Redis server** required for full backend (can be dockerized); demo app runs without it
- **Note:** Real-world deployment must include connection to a government database for authoritative document validation

---

*Hackverse 2025 · Team Vagabond · MIT Bengaluru*
