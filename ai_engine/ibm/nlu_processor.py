"""
Groq-based NLU processor for enhanced document content analysis.
Class IBMNLUProcessor preserved for interface compatibility.
"""

import json
import re
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.ai_config import AIConfig


class IBMNLUProcessor:
    """Groq LLM NLU for enhanced document understanding and fraud detection (replaces IBM Watson NLU)."""

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

    def analyze_document_content(self, document_text: str, document_type: str) -> Dict:
        """Enhanced NLU analysis for KYC documents using Groq LLM."""
        if not self.is_available:
            return self._mock_nlu_analysis(document_text, document_type)

        try:
            prompt = f"""Perform NLU analysis on this {document_type} identity document text.

Text: {document_text}

Return ONLY valid JSON:
{{
    "sentiment_analysis": {{
        "label": "neutral|positive|negative",
        "score": <-1.0 to 1.0>,
        "is_suspicious": false
    }},
    "entity_consistency": {{
        "person_entities": [{{"text": "name", "confidence": 0.9}}],
        "location_entities": [{{"text": "city", "confidence": 0.8}}],
        "organization_entities": [],
        "inconsistency_score": <0.0-1.0>,
        "potential_issues": []
    }},
    "fraud_indicators": [],
    "document_quality_score": <0.0-1.0>,
    "suspicious_patterns": []
}}"""

            completion = self.client.chat.completions.create(
                model=AIConfig.GROQ_TEXT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            data = self._parse_json(completion.choices[0].message.content)
            return {
                "success": True,
                "nlu_analysis": data or self._default_nlu_analysis(),
                "ai_service": "Groq_Llama_NLU",
                "document_type": document_type,
            }
        except Exception as e:
            return {"success": False, "error": f"NLU analysis failed: {str(e)}"}

    def cross_validate_with_granite(self, granite_results: Dict, nlu_results: Dict) -> Dict:
        """Cross-validate text fraud detection and NLU results."""
        try:
            granite_fraud_score = granite_results.get("fraud_score", 0.5)
            nlu_quality_score = nlu_results.get("nlu_analysis", {}).get("document_quality_score", 0.5)
            nlu_fraud_indicators = nlu_results.get("nlu_analysis", {}).get("fraud_indicators", [])
            nlu_fraud_score = min(len(nlu_fraud_indicators) * 0.2, 1.0)

            consensus_fraud_score = (granite_fraud_score + nlu_fraud_score + (1.0 - nlu_quality_score)) / 3
            diff = abs(granite_fraud_score - nlu_fraud_score)
            agreement_level = "HIGH" if diff < 0.2 else "MEDIUM" if diff < 0.4 else "LOW"

            return {
                "success": True,
                "consensus_analysis": {
                    "granite_fraud_score": granite_fraud_score,
                    "nlu_fraud_score": nlu_fraud_score,
                    "nlu_quality_score": nlu_quality_score,
                    "consensus_fraud_score": consensus_fraud_score,
                    "agreement_level": agreement_level,
                    "combined_indicators": (
                        granite_results.get("fraud_indicators", []) + nlu_fraud_indicators
                    ),
                },
                "validation_enhanced": True,
            }
        except Exception as e:
            return {"success": False, "error": f"Cross-validation failed: {str(e)}"}

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

    def _default_nlu_analysis(self) -> Dict:
        return {
            "sentiment_analysis": {"label": "neutral", "score": 0.0, "is_suspicious": False},
            "entity_consistency": {
                "person_entities": [], "location_entities": [], "organization_entities": [],
                "inconsistency_score": 0.0, "potential_issues": [],
            },
            "fraud_indicators": [],
            "document_quality_score": 0.75,
            "suspicious_patterns": [],
        }

    def _mock_nlu_analysis(self, document_text: str, document_type: str) -> Dict:
        return {
            "success": True,
            "nlu_analysis": {
                "sentiment_analysis": {"label": "neutral", "score": 0.1, "is_suspicious": False},
                "entity_consistency": {
                    "person_entities": [{"text": "Sample Name", "confidence": 0.9}],
                    "location_entities": [],
                    "organization_entities": [],
                    "inconsistency_score": 0.0,
                    "potential_issues": [],
                },
                "fraud_indicators": [],
                "document_quality_score": 0.9,
                "suspicious_patterns": [],
            },
            "ai_service": "Mock_Groq_NLU",
        }
