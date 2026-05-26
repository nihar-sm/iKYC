"""
Groq Vision integration for multimodal document analysis.
Class name BedrockTitanProcessor preserved for interface compatibility.
"""

import json
import re
import base64
from typing import Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ai_config import AIConfig


class BedrockTitanProcessor:
    """Groq Vision for document risk analysis and multimodal fraud detection (replaces AWS Bedrock Nova)."""

    def __init__(self):
        try:
            from groq import Groq
            api_key = AIConfig.GROQ_API_KEY
            if not api_key:
                print("Warning: GROQ_API_KEY not set — running in mock mode")
                self.client = None
            else:
                self.client = Groq(api_key=api_key)
            self.is_available = self.client is not None
        except ImportError:
            print("Warning: groq package not installed — pip install groq")
            self.client = None
            self.is_available = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def analyze_document_risk(self, document_text: str, ocr_confidence: float,
                               document_type: str = "document") -> Dict:
        """Document risk analysis using Groq LLM."""
        if not self.is_available:
            return self._mock_risk_analysis(document_text, ocr_confidence)

        try:
            prompt = AIConfig.GROQ_FRAUD_DETECTION_PROMPT.format(
                document_text=document_text,
                ocr_confidence=ocr_confidence,
                document_type=document_type,
            )
            resp = self._call_groq_text(prompt)
            if resp["success"]:
                return {
                    "success": True,
                    "risk_analysis": self._parse_risk_response(resp["response_text"]),
                    "ai_model": "Groq_Llama",
                }
            return self._mock_risk_analysis(document_text, ocr_confidence)
        except Exception:
            return self._mock_risk_analysis(document_text, ocr_confidence)

    def validate_document_authenticity(self, document_data: Dict) -> Dict:
        """Document authenticity validation using Groq LLM."""
        if not self.is_available:
            return self._mock_authenticity_validation(document_data)

        try:
            prompt = f"""Validate the authenticity of this identity document.

Extracted Text: {document_data.get('extracted_text', '')}
OCR Confidence: {document_data.get('ocr_confidence', 0.0)}
Extracted Fields: {document_data.get('field_extractions', {})}

Return ONLY valid JSON:
{{
    "authenticity_score": <0.0-1.0>,
    "format_compliance": true,
    "data_consistency": true,
    "forgery_indicators": [],
    "confidence_level": "HIGH|MEDIUM|LOW"
}}"""
            resp = self._call_groq_text(prompt)
            if resp["success"]:
                return {
                    "success": True,
                    "authenticity_analysis": self._parse_json(resp["response_text"]) or {
                        "authenticity_score": 0.75, "format_compliance": True,
                        "data_consistency": True, "forgery_indicators": [],
                        "confidence_level": "MEDIUM",
                    },
                    "ai_model": "Groq_Llama",
                }
            return self._mock_authenticity_validation(document_data)
        except Exception:
            return self._mock_authenticity_validation(document_data)

    def analyze_document_multimodal(self, document_text: str, image_data: bytes = None) -> Dict:
        """Multimodal analysis using Groq Vision."""
        if not self.is_available or not image_data:
            return {"success": False, "error": "Groq Vision not available or no image provided"}

        try:
            b64 = base64.b64encode(image_data).decode()
            prompt = f"""Analyse this identity document image alongside the extracted text.

Extracted text: {document_text}

Check for visual authenticity, text-image consistency, security features, and fraud indicators.
Return JSON with risk_score, fraud_indicators, authenticity_score, and confidence."""

            completion = self.client.chat.completions.create(
                model=AIConfig.GROQ_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
                temperature=0.1,
                max_tokens=600,
            )
            return {
                "success": True,
                "multimodal_analysis": self._parse_json(completion.choices[0].message.content),
                "ai_model": "Groq_Llama4_Vision",
                "capabilities_used": ["text_analysis", "image_analysis", "cross_modal_validation"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_document_embeddings(self, text: str, dimensions: int = None) -> Dict:
        """Generate text embeddings using sentence-transformers (local, open-source)."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(AIConfig.EMBEDDINGS_MODEL)
            embedding = model.encode(text).tolist()
            return {
                "success": True,
                "embeddings": embedding,
                "dimensions": len(embedding),
                "model": f"sentence-transformers/{AIConfig.EMBEDDINGS_MODEL}",
            }
        except ImportError:
            return {"success": False, "error": "sentence-transformers not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cross_validate_with_ibm(self, ibm_results: Dict, bedrock_analysis: Dict) -> Dict:
        """Cross-validate text and vision analysis results."""
        try:
            ibm_fraud_score = ibm_results.get("fraud_score", 0.5)
            ibm_confidence = ibm_results.get("ai_analysis", {}).get("confidence", 0.5)
            bedrock_risk_score = bedrock_analysis.get("risk_analysis", {}).get("overall_risk_score", 0.5)
            bedrock_authenticity = bedrock_analysis.get("authenticity_analysis", {}).get("authenticity_score", 0.5)

            consensus_fraud_score = (ibm_fraud_score + bedrock_risk_score) / 2
            consensus_authenticity = (ibm_confidence + bedrock_authenticity) / 2
            diff = abs(ibm_fraud_score - bedrock_risk_score)
            agreement_level = "HIGH" if diff < 0.2 else "MEDIUM" if diff < 0.4 else "LOW"

            if agreement_level == "HIGH":
                final_decision = (
                    "APPROVED" if consensus_fraud_score < 0.3
                    else "REJECTED" if consensus_fraud_score > 0.7
                    else "MANUAL_REVIEW"
                )
            else:
                final_decision = "MANUAL_REVIEW"

            return {
                "success": True,
                "consensus_analysis": {
                    "fraud_score": consensus_fraud_score,
                    "authenticity_score": consensus_authenticity,
                    "agreement_level": agreement_level,
                    "final_decision": final_decision,
                },
                "cross_validation": "completed",
            }
        except Exception as e:
            return {"success": False, "error": f"Cross-validation failed: {str(e)}"}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_groq_text(self, prompt: str) -> Dict:
        if not self.is_available:
            return {"success": False, "error": "Groq not available"}
        try:
            completion = self.client.chat.completions.create(
                model=AIConfig.GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
            )
            return {"success": True, "response_text": completion.choices[0].message.content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _parse_json(self, text: str) -> Dict:
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return {}

    def _parse_risk_response(self, text: str) -> Dict:
        data = self._parse_json(text)
        defaults = {
            "document_authenticity_risk": 0.2,
            "information_consistency_risk": 0.15,
            "fraud_probability": 0.1,
            "overall_risk_score": 0.15,
            "risk_factors": ["none_identified"],
            "recommendations": ["proceed_with_standard_verification"],
            "confidence_level": "MEDIUM",
        }
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data

    def _mock_risk_analysis(self, document_text: str, ocr_confidence: float) -> Dict:
        base_risk = max(0.1, 1.0 - ocr_confidence)
        return {
            "success": True,
            "risk_analysis": {
                "document_authenticity_risk": base_risk,
                "information_consistency_risk": base_risk * 0.8,
                "fraud_probability": base_risk * 0.6,
                "overall_risk_score": base_risk,
                "risk_factors": ["low_ocr_confidence"] if ocr_confidence < 0.7 else ["none_identified"],
                "recommendations": ["manual_review"] if base_risk > 0.5 else ["proceed_with_verification"],
                "confidence_level": "HIGH" if base_risk < 0.3 else "MEDIUM",
            },
            "ai_model": "Mock_Groq",
            "mock_mode": True,
        }

    def _mock_authenticity_validation(self, document_data: Dict) -> Dict:
        has_fields = bool(document_data.get("field_extractions"))
        good_quality = document_data.get("image_quality", {}).get("quality_score", 0.5) > 0.7
        score = 0.9 if has_fields and good_quality else 0.6
        return {
            "success": True,
            "authenticity_analysis": {
                "authenticity_score": score,
                "format_compliance": has_fields,
                "data_consistency": good_quality,
                "forgery_indicators": [] if score > 0.7 else ["quality_issues"],
                "confidence_level": "HIGH" if score > 0.8 else "MEDIUM",
            },
            "ai_model": "Mock_Groq",
            "mock_mode": True,
        }

    # Legacy alias
    def _call_bedrock_titan(self, prompt: str) -> Dict:
        return self._call_groq_text(prompt)

    # Legacy alias — same logic, kept for orchestrator compatibility
    def _call_nova_text(self, prompt: str, use_lite: bool = False) -> Dict:
        return self._call_groq_text(prompt)
