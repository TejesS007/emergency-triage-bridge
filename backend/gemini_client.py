import json
import logging
import os
from typing import Optional

from google import genai
from google.genai import types

from backend.schema import TriageAssessment

logger = logging.getLogger(__name__)

FALLBACK_ASSESSMENT = TriageAssessment(
    severity="medium",
    condition_summary="Unable to analyze — manual review needed",
    medications=[],
    allergies=[],
    recommended_action="Consult a medical professional immediately",
)

SYSTEM_INSTRUCTION = (
    "You are an Emergency Medical Triage AI Assistant. "
    "Your objective is to rapidly evaluate patient symptoms or uploaded medical/injury photos "
    "and provide a structured triage assessment.\n"
    "You must output ONLY valid JSON matching the following schema:\n"
    "{\n"
    '  "severity": "low" | "medium" | "high" | "critical",\n'
    '  "condition_summary": string,\n'
    '  "medications": string[],\n'
    '  "allergies": string[],\n'
    '  "recommended_action": string\n'
    "}\n"
    "Guidelines:\n"
    "- 'severity' MUST be one of: 'low', 'medium', 'high', 'critical'.\n"
    "- 'condition_summary': concise description of apparent condition or trauma.\n"
    "- 'medications': any medications mentioned or visually identified (empty array if none).\n"
    "- 'allergies': any patient allergies mentioned (empty array if none).\n"
    "- 'recommended_action': immediate first aid step or hospital guidance."
)


def get_gemini_client() -> Optional[genai.Client]:
    """Instantiate the Gemini client using the GEMINI_API_KEY environment variable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set.")
        return None
    return genai.Client(api_key=api_key)


def analyze_triage(
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    text: Optional[str] = None,
) -> TriageAssessment:
    """
    Analyzes patient image and/or text description using Gemini 2.5 Flash.
    Returns a validated TriageAssessment.
    If an error occurs or invalid JSON is returned, gracefully returns the fallback assessment.
    """
    try:
        client = get_gemini_client()
        if not client:
            logger.warning("No Gemini client available; using fallback.")
            return FALLBACK_ASSESSMENT

        contents = []

        if image_bytes and mime_type:
            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            )

        if text:
            contents.append(text)

        if not contents:
            logger.warning("No input content provided to analyze_triage.")
            return FALLBACK_ASSESSMENT

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=TriageAssessment,
            temperature=0.1,
        )

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=config,
        )

        if not response or not response.text:
            logger.warning("Empty response received from Gemini model.")
            return FALLBACK_ASSESSMENT

        # Parse JSON into validated Pydantic model
        raw_text = response.text.strip()
        data = json.loads(raw_text)
        return TriageAssessment.model_validate(data)

    except Exception as exc:
        logger.error(f"Gemini triage analysis failed: {exc}", exc_info=True)
        return FALLBACK_ASSESSMENT
