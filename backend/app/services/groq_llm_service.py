import base64
import json
import re
import logging
from typing import Dict, Any
from core.ai_config import ai_config

logger = logging.getLogger(__name__)


class GroqLLMService:
    """Unified Groq LLM service — replaces IBM Granite (text) + AWS Bedrock Nova (vision)."""

    def __init__(self):
        api_key = ai_config.groq_api_key
        if not api_key:
            logger.warning("GROQ_API_KEY not set — running in mock mode")
            self.client = None
        else:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
                logger.info("Groq LLM service initialized")
            except ImportError:
                logger.error("groq package not installed — pip install groq")
                self.client = None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_document_text(self, text: str, document_type: str = "aadhaar") -> Dict[str, Any]:
        """Text-based fraud analysis (replaces IBM Granite)."""
        if not self.enabled:
            return self._mock_analysis("GroqLLM_Text")

        prompt = f"""You are a document fraud detection specialist analysing {document_type} identity documents.

Analyse the following document text for fraud indicators:

{text}

Check for:
1. Inconsistent formatting or unusual characters
2. Suspicious ID number patterns
3. Unrealistic personal information
4. Missing standard document elements
5. Inconsistent name/date formatting

Respond with ONLY valid JSON:
{{
    "risk_score": <0.0-1.0>,
    "risk_level": "LOW|MEDIUM|HIGH",
    "fraud_indicators": ["list of issues"],
    "confidence": <0.0-1.0>,
    "explanation": "brief explanation"
}}"""
        try:
            resp = self.client.chat.completions.create(
                model=ai_config.groq_text_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            return self._parse_response(resp.choices[0].message.content, "GroqLLM_Text")
        except Exception as e:
            logger.error(f"Groq text analysis failed: {e}")
            return self._mock_analysis("GroqLLM_Text", error=True)

    def analyze_document_image(self, image_path: str, document_type: str = "aadhaar") -> Dict[str, Any]:
        """Vision-based fraud analysis (replaces AWS Bedrock Nova vision)."""
        if not self.enabled:
            return self._mock_analysis("GroqLLM_Vision")

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            ext = image_path.rsplit(".", 1)[-1].lower()
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            b64 = base64.b64encode(image_bytes).decode()

            prompt = f"""You are an expert in document fraud detection. Analyse this {document_type} document image.

Look for:
1. Image quality inconsistencies or digital manipulation
2. Misaligned text or formatting irregularities
3. Colour or font inconsistencies
4. Signs of photo editing or overlays
5. Missing security features
6. Text that appears pasted or artificially added

Respond with ONLY valid JSON:
{{
    "risk_score": <0.0-1.0>,
    "risk_level": "LOW|MEDIUM|HIGH",
    "fraud_indicators": ["list of visual issues"],
    "confidence": <0.0-1.0>,
    "explanation": "detailed explanation",
    "authenticity_score": <0.0-1.0>
}}"""

            resp = self.client.chat.completions.create(
                model=ai_config.groq_vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }],
                temperature=0.1,
                max_tokens=600,
            )
            result = self._parse_response(resp.choices[0].message.content, "GroqLLM_Vision")
            result.setdefault("authenticity_score", round(1.0 - result.get("risk_score", 0.0), 3))
            return result
        except Exception as e:
            logger.error(f"Groq vision analysis failed: {e}")
            return self._mock_analysis("GroqLLM_Vision", error=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, text: str, service: str) -> Dict[str, Any]:
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                data = json.loads(m.group())
                return {
                    "service": service,
                    "risk_score": float(data.get("risk_score", 0.0)),
                    "risk_level": data.get("risk_level", "LOW"),
                    "fraud_indicators": data.get("fraud_indicators", []),
                    "confidence": float(data.get("confidence", 0.8)),
                    "explanation": data.get("explanation", ""),
                    "authenticity_score": float(data.get("authenticity_score", 1.0)),
                    "success": True,
                }
        except Exception:
            pass
        risk_keywords = ["fraud", "fake", "tampered", "suspicious", "inconsistent", "invalid"]
        score = min(sum(1 for k in risk_keywords if k in text.lower()) / len(risk_keywords), 1.0)
        return {
            "service": service,
            "risk_score": score,
            "risk_level": "HIGH" if score > 0.6 else "MEDIUM" if score > 0.3 else "LOW",
            "fraud_indicators": ["Fallback analysis — manual review recommended"],
            "confidence": 0.5,
            "explanation": "Parsed from unstructured response",
            "authenticity_score": round(1.0 - score, 3),
            "success": True,
        }

    def _mock_analysis(self, service: str, error: bool = False) -> Dict[str, Any]:
        if error:
            return {
                "service": service, "risk_score": 0.0, "risk_level": "UNKNOWN",
                "fraud_indicators": ["Service unavailable"], "confidence": 0.0,
                "explanation": "AI service error — manual review required",
                "authenticity_score": 0.0, "success": False,
            }
        return {
            "service": service, "risk_score": 0.1, "risk_level": "LOW",
            "fraud_indicators": ["No obvious fraud indicators"],
            "confidence": 0.7,
            "explanation": "Mock analysis (GROQ_API_KEY not configured)",
            "authenticity_score": 0.9, "success": True, "mock": True,
        }


groq_analyzer = GroqLLMService()
