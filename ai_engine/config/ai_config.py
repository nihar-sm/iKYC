"""
AI Engine Configuration for iKYC
Open-source stack: Groq API (LLM + Vision) + EasyOCR + sentence-transformers
"""

import os


class AIConfig:
    """Configuration for AI services."""

    # ------------------------------------------------------------------
    # Groq Configuration (replaces IBM Granite + AWS Bedrock)
    # ------------------------------------------------------------------
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
    GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

    # Groq inference parameters
    GROQ_MAX_TOKENS = 1000
    GROQ_TEMPERATURE = 0.1
    GROQ_TOP_P = 0.9

    # ------------------------------------------------------------------
    # Embeddings (local, open-source — replaces Amazon Titan Embeddings)
    # ------------------------------------------------------------------
    EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"   # sentence-transformers
    EMBEDDINGS_DIMENSIONS = 384

    # ------------------------------------------------------------------
    # OCR Engine Configuration
    # ------------------------------------------------------------------
    OCR_ENGINES = ["easyocr", "ocr_space", "mock"]
    OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY", "")
    OCR_SPACE_URL = "https://api.ocr.space/parse/image"
    OCR_MAX_IMAGE_SIZE_MB = 5
    OCR_SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "pdf", "bmp", "gif"]
    OCR_DEFAULT_LANGUAGE = "eng"
    OCR_CONFIDENCE_THRESHOLD = 0.7

    # ------------------------------------------------------------------
    # Document Processing
    # ------------------------------------------------------------------
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "pdf"]
    MAX_FILE_SIZE_MB = 10
    FRAUD_DETECTION_THRESHOLD = 0.6

    FRAUD_INDICATORS = {
        "low_ocr_confidence": 0.5,
        "inconsistent_fonts": 0.7,
        "image_quality_issues": 0.6,
        "suspicious_patterns": 0.8,
    }

    AADHAAR_FIELDS = ["aadhaar_number", "name", "date_of_birth", "gender", "address", "father_name", "issue_date"]
    PAN_FIELDS = ["pan_number", "name", "father_name", "date_of_birth", "signature", "issue_date"]

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------
    GROQ_FRAUD_DETECTION_PROMPT = """You are an expert document fraud detection AI. Analyse this document for potential fraud indicators.

Document Text: {document_text}
OCR Confidence: {ocr_confidence}
Document Type: {document_type}

Return ONLY valid JSON:
{{
    "document_authenticity_risk": <float 0-1>,
    "information_consistency_risk": <float 0-1>,
    "fraud_probability": <float 0-1>,
    "overall_risk_score": <float 0-1>,
    "risk_factors": ["list"],
    "recommendations": ["list"],
    "confidence_level": "HIGH|MEDIUM|LOW",
    "analysis_reasoning": "brief explanation"
}}"""

    # Alias used by legacy orchestrator code
    NOVA_FRAUD_DETECTION_PROMPT = GROQ_FRAUD_DETECTION_PROMPT
    FRAUD_DETECTION_PROMPT = GROQ_FRAUD_DETECTION_PROMPT

    FIELD_EXTRACTION_PROMPT = """Extract structured information from this {document_type} document.

DOCUMENT TEXT: {document_text}
REQUIRED FIELDS: {required_fields}

Return ONLY valid JSON with extracted fields. Use null for missing fields."""

    GROQ_MULTIMODAL_ANALYSIS_PROMPT = """Analyse this document using BOTH the extracted text and the document image.

EXTRACTED TEXT: {document_text}
DOCUMENT TYPE: {document_type}

Provide comprehensive analysis including visual authenticity, text-image consistency,
document quality, fraud indicators, and overall risk assessment.

Return JSON with the same structure as the fraud detection prompt."""

    # Alias used by legacy orchestrator code
    NOVA_MULTIMODAL_ANALYSIS_PROMPT = GROQ_MULTIMODAL_ANALYSIS_PROMPT
