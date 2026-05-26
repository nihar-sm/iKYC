"""
Groq LLM integration for semantic analysis and fraud detection.
Class name GraniteAIProcessor preserved for interface compatibility.
"""

import json
import re
import sys
import os
from typing import Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ai_config import AIConfig


class GraniteAIProcessor:
    """Groq LLM for semantic analysis and fraud detection (replaces IBM Granite)."""

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

    def analyze_document_semantics(self, document_text: str, document_type: str) -> Dict:
        """Analyse document semantics using Groq LLM."""
        if not self.is_available:
            return self._mock_semantic_analysis(document_text, document_type)

        try:
            prompt = f"""Analyse this {document_type} document for semantic validity.

Document text: {document_text}

Return ONLY valid JSON:
{{
    "document_type_confidence": <0.0-1.0>,
    "language_detected": "english",
    "content_validity": <0.0-1.0>,
    "structure_compliance": true
}}"""
            completion = self.client.chat.completions.create(
                model=AIConfig.GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            data = self._parse_json(completion.choices[0].message.content)
            return {
                "success": True,
                "semantic_analysis": {
                    "document_type_confidence": float(data.get("document_type_confidence", 0.85)),
                    "language_detected": data.get("language_detected", "english"),
                    "content_validity": float(data.get("content_validity", 0.80)),
                    "structure_compliance": bool(data.get("structure_compliance", True)),
                },
                "ai_model": "Groq_Llama",
            }
        except Exception as e:
            return {"success": False, "error": f"Groq semantic analysis failed: {str(e)}"}

    def detect_fraud_patterns(self, document_text: str, field_extractions: Dict) -> Dict:
        """Detect fraud patterns using Groq LLM."""
        if not self.is_available:
            return self._mock_fraud_detection(document_text, field_extractions)

        try:
            prompt = f"""Analyse this document text for fraud patterns.

Text: {document_text}
Extracted fields: {json.dumps(field_extractions)}

Return ONLY valid JSON:
{{
    "fraud_score": <0.0-1.0>,
    "confidence": <0.0-1.0>,
    "patterns_detected": ["list"],
    "anomaly_score": <0.0-1.0>,
    "overall_risk": "LOW|MEDIUM|HIGH"
}}"""
            completion = self.client.chat.completions.create(
                model=AIConfig.GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            data = self._parse_json(completion.choices[0].message.content)
            fraud_score = float(data.get("fraud_score", 0.1))
            return {
                "success": True,
                "fraud_score": fraud_score,
                "ai_analysis": {
                    "confidence": float(data.get("confidence", 0.85)),
                    "patterns_detected": data.get("patterns_detected", ["none"]),
                    "anomaly_score": float(data.get("anomaly_score", fraud_score)),
                },
                "overall_risk": data.get("overall_risk", "LOW"),
                "ai_model": "Groq_Llama",
            }
        except Exception as e:
            return {"success": False, "error": f"Groq fraud detection failed: {str(e)}"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json(self, text: str) -> Dict:
        try:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return {}

    def _mock_semantic_analysis(self, document_text: str, document_type: str) -> Dict:
        return {
            "success": True,
            "semantic_analysis": {
                "document_type_confidence": 0.85,
                "language_detected": "english",
                "content_validity": 0.80,
                "structure_compliance": True,
            },
            "ai_model": "Mock_Groq",
        }

    def _mock_fraud_detection(self, document_text: str, field_extractions: Dict) -> Dict:
        fraud_score = 0.2 if len(field_extractions) < 3 else 0.1
        return {
            "success": True,
            "fraud_score": fraud_score,
            "ai_analysis": {
                "confidence": 0.85,
                "patterns_detected": ["insufficient_data"] if fraud_score > 0.15 else ["none"],
                "anomaly_score": fraud_score,
            },
            "overall_risk": "MEDIUM" if fraud_score > 0.15 else "LOW",
            "ai_model": "Mock_Groq",
        }
