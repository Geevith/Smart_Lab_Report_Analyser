"""
AI-Powered Medical Report Analyzer

Uses Google Gemini API to analyze narrative medical reports (CT, MRI, X-ray, 
pathology, cardiology, etc.) that cannot be processed by the regex-based parser.

Returns structured data in the same schema as parse_blood_test() so the
existing frontend and insights engine work without changes.
"""

import os
import json
import logging
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
# Gemini client setup (lazy initialization)
# ────────────────────────────────────────────────────────────────────────────

_gemini_client = None
_gemini_model = None

def _get_gemini_model():
    """Lazy-initialize the Gemini model."""
    global _gemini_client, _gemini_model
    if _gemini_model is not None:
        return _gemini_model

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.2,       # Low temperature for factual accuracy
                "top_p": 0.95,
                "response_mime_type": "application/json",  # Force JSON output
            }
        )
        log.info("Gemini model initialized successfully")
        return _gemini_model
    except Exception as e:
        log.warning(f"Failed to initialize Gemini: {e}")
        return None


# ────────────────────────────────────────────────────────────────────────────
# Prompt templates per report type
# ────────────────────────────────────────────────────────────────────────────

BASE_SYSTEM_PROMPT = """You are MedLab AI, a medical report analysis assistant.
Your role is to help patients understand their medical reports in simple, clear language.

CRITICAL RULES:
1. Never provide a diagnosis. Always recommend consulting a doctor.
2. Use simple, patient-friendly language. Avoid excessive medical jargon.
3. When you use a medical term, briefly explain it in parentheses.
4. Be kind, clear, and reassuring without downplaying genuine concerns.
5. You MUST return valid JSON matching the exact schema provided.
"""

ANALYSIS_PROMPT_TEMPLATE = """
{system_prompt}

You are analyzing a {report_type_label}.

Report text:
---
{report_text}
---

Extract ALL findings mentioned in this report and return them as JSON matching this exact schema:

{{
  "report_summary": "2-3 sentence plain-English summary of the overall report",
  "report_type_detected": "specific type detected e.g. CT Chest, MRI Brain, Biopsy Colon",
  "overall_status": "Normal | Borderline | Abnormal | Critical",
  "findings": [
    {{
      "name": "Finding name (e.g. Right Pleural Effusion, Liver Size, Bone Density)",
      "value": "What was found (e.g. Mild, 15cm, Reduced, Normal, Absent)",
      "status": "Normal | Borderline | Abnormal | Critical",
      "severity": "LOW | MEDIUM | HIGH | CRITICAL",
      "body_region": "Where in the body (e.g. Right Lung, Liver, Spine)",
      "simple_explanation": "1-2 sentence plain-English explanation for a patient",
      "is_actionable": true or false
    }}
  ],
  "patient_summary_bullets": [
    "Key point 1 in simple language",
    "Key point 2 in simple language"
  ],
  "questions_for_doctor": [
    "What does finding X mean for me?",
    "Do I need a follow-up test?"
  ],
  "urgency_note": "None | Schedule routine appointment | Schedule appointment soon | Seek medical attention promptly | Seek immediate medical attention",
  "disclaimer": "This AI analysis is for informational purposes only and does not constitute medical advice. Please consult your doctor."
}}

IMPORTANT:
- Include EVERY finding mentioned, including normal ones
- If the report says something is "normal" or "unremarkable", still include it as a Normal finding
- For radiology reports, include both the Findings section AND the Impression/Conclusion
- If the report has an overall impression/conclusion, base the overall_status on that
"""

def _build_prompt(report_text: str, report_type_label: str) -> str:
    """Build the analysis prompt from the template."""
    # Truncate very long reports (Gemini has context limits, but 1.5-flash handles 1M tokens)
    truncated_text = report_text[:50000] if len(report_text) > 50000 else report_text
    return ANALYSIS_PROMPT_TEMPLATE.format(
        system_prompt=BASE_SYSTEM_PROMPT,
        report_type_label=report_type_label,
        report_text=truncated_text,
    )


# ────────────────────────────────────────────────────────────────────────────
# Core AI analysis function
# ────────────────────────────────────────────────────────────────────────────

def analyze_with_ai(report_text: str, report_type_label: str = "Medical Report") -> Dict:
    """
    Analyze a narrative medical report using Gemini AI.

    Returns a dict that mirrors the structure used by parse_blood_test() so the
    rest of the pipeline (insights, summary, database) works transparently.
    """
    model = _get_gemini_model()

    if model is None:
        log.warning("Gemini API not available — returning structured fallback")
        return _no_api_fallback(report_text, report_type_label)

    try:
        prompt = _build_prompt(report_text, report_type_label)
        response = model.generate_content(prompt)
        raw_json = response.text.strip()

        # Clean response if Gemini wraps in markdown code blocks
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
        raw_json = raw_json.strip()

        ai_data = json.loads(raw_json)
        return _convert_ai_response_to_analysis(ai_data)

    except json.JSONDecodeError as e:
        log.error(f"Gemini returned invalid JSON: {e}")
        return _no_api_fallback(report_text, report_type_label)
    except Exception as e:
        log.error(f"Gemini analysis failed: {e}")
        return _no_api_fallback(report_text, report_type_label)


def _convert_ai_response_to_analysis(ai_data: Dict) -> Dict:
    """
    Convert the Gemini JSON response into the standard analysis format
    used by the rest of the pipeline.

    Returns:
        {
          'analysis_result': dict  ← same shape as parse_blood_test()
          'ai_metadata': dict      ← extra AI-specific fields for the frontend
        }
    """
    analysis_result = {}
    findings = ai_data.get("findings", [])

    for finding in findings:
        name = finding.get("name", "Unknown Finding")
        value_str = finding.get("value", "See report")
        status = finding.get("status", "Normal")
        severity = finding.get("severity", "MEDIUM")
        body_region = finding.get("body_region", "")
        explanation = finding.get("simple_explanation", "")
        is_actionable = finding.get("is_actionable", False)

        # Normalize status to match existing system
        status_map = {
            "Normal": "Normal",
            "Borderline": "Borderline",
            "Abnormal": "High",   # Frontend shows High/Low/Normal
            "Critical": "Critical",
        }
        normalized_status = status_map.get(status, "Normal")

        # Try to extract a numeric value if the value looks numeric
        numeric_value = None
        try:
            # Handle values like "15 cm", "Mild (grade 1)", "3.2"
            import re
            num_match = re.search(r"[\d\.]+", str(value_str))
            if num_match:
                numeric_value = float(num_match.group())
        except Exception:
            pass

        analysis_result[name] = {
            "value": numeric_value if numeric_value is not None else 0.0,
            "value_display": value_str,        # Human-readable value for frontend
            "unit": body_region,               # Repurpose unit field for body region
            "range": "See report",
            "status": normalized_status,
            "confidence": "High",              # Gemini-extracted findings are high confidence
            "severity": severity,
            "notes": [explanation] if explanation else [],
            "source": "ai_analyzed",           # Tag so pipeline knows this came from AI
            "range_disclaimer": "AI-extracted finding from narrative report. Consult your doctor.",
            "is_actionable": is_actionable,
        }

    return {
        "analysis_result": analysis_result,
        "ai_metadata": {
            "report_summary": ai_data.get("report_summary", ""),
            "report_type_detected": ai_data.get("report_type_detected", ""),
            "overall_status": ai_data.get("overall_status", "Unknown"),
            "patient_summary_bullets": ai_data.get("patient_summary_bullets", []),
            "questions_for_doctor": ai_data.get("questions_for_doctor", []),
            "urgency_note": ai_data.get("urgency_note", "None"),
            "disclaimer": ai_data.get("disclaimer", ""),
        }
    }


def _no_api_fallback(report_text: str, report_type_label: str) -> Dict:
    """
    Returns a structured error response when the Gemini API is unavailable.
    The frontend can detect this and show a helpful message.
    """
    return {
        "analysis_result": {},
        "ai_metadata": {
            "report_summary": f"This appears to be a {report_type_label}. AI analysis is currently unavailable.",
            "report_type_detected": report_type_label,
            "overall_status": "Unknown",
            "patient_summary_bullets": [
                "The AI analyzer could not process this report automatically.",
                "Please review the extracted text below and discuss with your doctor.",
            ],
            "questions_for_doctor": [
                "Can you walk me through the key findings in this report?",
                "Are there any results I should be concerned about?",
            ],
            "urgency_note": "Schedule routine appointment",
            "disclaimer": "AI analysis unavailable. Please configure GEMINI_API_KEY in .env to enable AI analysis for non-blood-test reports.",
            "api_unavailable": True,
        }
    }


def generate_ai_insight_for_finding(finding_name: str, status: str, 
                                     explanation: str, severity: str) -> Dict:
    """
    Convert an AI-analyzed finding into the insight format used by generate_insights().
    Called by interpretation.py for ai_analyzed parameters.
    """
    severity_labels = {
        "LOW": "Mild Deviation",
        "MEDIUM": "Moderate Deviation",
        "HIGH": "Significant Deviation",
        "CRITICAL": "Critical - Urgent Attention Required",
    }
    return {
        "parameter": finding_name,
        "status": status,
        "insight": explanation if explanation else f"{finding_name} was noted in the report. Please discuss with your doctor.",
        "severity": severity,
        "severity_label": severity_labels.get(severity, "Moderate Deviation"),
        "source": "ai_analyzed",
        "confidence_score": 0.85,
        "confidence_rationale": "AI-extracted from narrative report",
    }
