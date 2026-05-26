import logging
from typing import Dict, Any, List
from datetime import datetime
from services.groq_llm_service import groq_analyzer
from core.ai_config import ai_config

logger = logging.getLogger(__name__)


class FraudDetectionOrchestrator:
    """Orchestrates Groq LLM (text + vision) for comprehensive fraud detection."""

    def __init__(self):
        self.groq = groq_analyzer
        self.thresholds = {
            "high": ai_config.fraud_threshold_high,
            "medium": ai_config.fraud_threshold_medium,
            "low": ai_config.fraud_threshold_low,
        }

    def analyze_document_fraud(
        self,
        document_text: str,
        image_path: str,
        document_type: str = "aadhaar",
    ) -> Dict[str, Any]:
        """Run text + vision fraud analysis, combine results."""
        logger.info(f"Starting fraud analysis for {document_type}")
        analyses = []

        text_result = self.groq.analyze_document_text(document_text, document_type)
        analyses.append(text_result)
        logger.info(f"Groq text analysis: {text_result['risk_level']}")

        if image_path:
            try:
                vision_result = self.groq.analyze_document_image(image_path, document_type)
                analyses.append(vision_result)
                logger.info(f"Groq vision analysis: {vision_result['risk_level']}")
            except Exception as e:
                logger.error(f"Groq vision analysis failed: {e}")

        combined = self._combine_analyses(analyses, document_type)
        logger.info(
            f"Combined fraud analysis: {combined['overall_risk_level']} "
            f"(Score: {combined['combined_risk_score']:.2f})"
        )
        return combined

    def _combine_analyses(self, analyses: List[Dict[str, Any]], document_type: str) -> Dict[str, Any]:
        if not analyses:
            return self._create_default_analysis(document_type, "No AI services available")

        successful = [a for a in analyses if a.get("success", False)]
        if not successful:
            return self._create_default_analysis(document_type, "All AI services failed")

        risk_scores = [a["risk_score"] for a in successful]
        confidences = [a["confidence"] for a in successful]

        total_weight = sum(confidences)
        if total_weight > 0:
            combined_risk_score = sum(s * c for s, c in zip(risk_scores, confidences)) / total_weight
        else:
            combined_risk_score = sum(risk_scores) / len(risk_scores)

        overall_risk_level = self._determine_risk_level(combined_risk_score)

        all_indicators: List[str] = []
        for a in successful:
            all_indicators.extend(a.get("fraud_indicators", []))

        return {
            "overall_risk_level": overall_risk_level,
            "combined_risk_score": round(combined_risk_score, 3),
            "average_confidence": round(sum(confidences) / len(confidences), 3),
            "services_used": len(successful),
            "fraud_indicators": list(set(all_indicators)),
            "individual_analyses": successful,
            "recommendation": self._create_recommendation(combined_risk_score, overall_risk_level),
            "analysis_timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "thresholds_used": self.thresholds,
        }

    def _determine_risk_level(self, risk_score: float) -> str:
        if risk_score >= self.thresholds["high"]:
            return "HIGH"
        elif risk_score >= self.thresholds["medium"]:
            return "MEDIUM"
        elif risk_score >= self.thresholds["low"]:
            return "LOW"
        return "MINIMAL"

    def _create_recommendation(self, risk_score: float, risk_level: str) -> Dict[str, Any]:
        recommendations = {
            "HIGH": {
                "action": "REJECT",
                "message": "Document shows high fraud indicators — reject immediately",
                "manual_review": True,
                "additional_verification": ["Request original documents", "Conduct video call verification"],
            },
            "MEDIUM": {
                "action": "MANUAL_REVIEW",
                "message": "Document requires manual review due to suspicious indicators",
                "manual_review": True,
                "additional_verification": ["Enhanced due diligence", "Additional document requests"],
            },
            "LOW": {
                "action": "ADDITIONAL_CHECKS",
                "message": "Document acceptable but recommend additional verification",
                "manual_review": False,
                "additional_verification": ["Cross-reference with database", "Basic verification calls"],
            },
            "MINIMAL": {
                "action": "APPROVE",
                "message": "Document appears authentic — approve with standard processing",
                "manual_review": False,
                "additional_verification": [],
            },
        }
        rec = dict(recommendations.get(risk_level, recommendations["MEDIUM"]))
        rec["risk_score"] = risk_score
        return rec

    def _create_default_analysis(self, document_type: str, reason: str) -> Dict[str, Any]:
        return {
            "overall_risk_level": "UNKNOWN",
            "combined_risk_score": 0.0,
            "average_confidence": 0.0,
            "services_used": 0,
            "fraud_indicators": [reason],
            "individual_analyses": [],
            "recommendation": {
                "action": "MANUAL_REVIEW",
                "message": "AI fraud detection unavailable — manual review required",
                "manual_review": True,
                "additional_verification": ["Full manual document review"],
                "risk_score": 0.0,
            },
            "analysis_timestamp": datetime.now().isoformat(),
            "document_type": document_type,
            "error": reason,
        }


fraud_detector = FraudDetectionOrchestrator()
