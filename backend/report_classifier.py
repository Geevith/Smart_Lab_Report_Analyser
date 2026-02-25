"""
Medical Report Type Classifier

Detects the type of medical report from extracted text using keyword scoring.
No ML model needed — purely text-based, runs offline, zero cost.
"""

import re
from typing import Dict, Tuple


# Keywords for each report category with their weights
REPORT_SIGNALS: Dict[str, Dict[str, int]] = {
    "blood_test": {
        # Strong signals
        "hemoglobin": 10, "hematocrit": 10, "platelet": 10, "leukocyte": 10,
        "erythrocyte": 10, "wbc": 8, "rbc": 8, "hb": 6,
        "blood count": 10, "complete blood": 10, "cbc": 10,
        # Lab panels
        "lipid profile": 10, "liver function": 10, "kidney function": 10,
        "thyroid function": 10, "fasting glucose": 8, "hba1c": 10,
        "creatinine": 8, "cholesterol": 8, "triglyceride": 8,
        "sgot": 10, "sgpt": 10, "bilirubin": 8, "albumin": 6,
        "ferritin": 6, "insulin": 6, "tsh": 8, "vitamin": 6,
        # Structural signals (numeric lab results have these patterns)
        "reference range": 10, "normal range": 10, "bio reference": 8,
        "units": 4, "g/dl": 8, "mg/dl": 8, "iu/l": 8, "iu/ml": 6,
        "cells/ul": 8, "mmol/l": 8, "nmol/l": 6, "pmol/l": 6,
    },

    "radiology": {
        # Modality names
        "ct scan": 15, "computed tomography": 15, "mri": 10,
        "magnetic resonance": 12, "x-ray": 10, "chest x": 10,
        "ultrasound": 10, "sonography": 10, "mammography": 10,
        "pet scan": 12, "nuclear medicine": 10, "fluoroscopy": 10,
        "echocardiography": 8, "doppler": 8,
        # Radiologist language
        "impression": 10, "findings": 8, "contrast": 6, "enhancement": 6,
        "opacity": 10, "density": 6, "lesion": 8, "mass": 6,
        "nodule": 10, "effusion": 10, "consolidation": 10, "infiltrate": 10,
        "atelectasis": 12, "pneumothorax": 12, "pleural": 10,
        "parenchyma": 10, "cortex": 6, "medulla": 6,
        "lobe": 6, "bilateral": 8, "unilateral": 6,
        "hypodense": 12, "hyperdense": 12, "isodense": 10,
        "radiolucent": 10, "radioopaque": 10,
        "mm in size": 8, "cm lesion": 8, "enhancement": 6,
        "scan shows": 10, "scan reveals": 10, "review shows": 8,
    },

    "pathology": {
        "biopsy": 15, "histopathology": 15, "histology": 12,
        "cytology": 12, "specimen": 10, "tissue": 8,
        "malignant": 12, "benign": 10, "carcinoma": 12, "adenocarcinoma": 12,
        "sarcoma": 12, "lymphoma": 12, "melanoma": 12,
        "metastasis": 12, "neoplasm": 10, "tumor": 8,
        "grade": 8, "stage": 8, "margin": 8, "mitosis": 10,
        "necrosis": 10, "inflammation": 8, "fibrosis": 8,
        "pathological": 10, "microscopic": 8, "macroscopic": 8,
        "staining": 8, "immunohistochemistry": 12, "ihc": 10,
    },

    "cardiology": {
        "ecg": 12, "electrocardiogram": 12, "electrocardiograph": 12,
        "ekg": 12, "cardiac": 8, "ejection fraction": 15,
        "left ventricle": 10, "right ventricle": 10,
        "atrium": 8, "ventricle": 8, "aorta": 8, "mitral": 8,
        "sinus rhythm": 12, "atrial fibrillation": 12, "arrhythmia": 12,
        "st segment": 10, "t wave": 8, "qt interval": 10, "pr interval": 8,
        "heart rate": 6, "bpm": 6, "troponin": 8,
        "echocardiogram": 12, "echo": 6, "systolic": 8, "diastolic": 8,
        "bnp": 10, "nt-probnp": 10, "coronary": 8, "ischemia": 10,
    },

    "ophthalmology": {
        "intraocular pressure": 15, "iop": 10, "retina": 10,
        "fundus": 12, "optic disc": 12, "macula": 12,
        "visual acuity": 12, "visual field": 10,
        "cornea": 8, "lens": 6, "vitreous": 8, "glaucoma": 12,
        "diabetic retinopathy": 12, "macular degeneration": 12,
        "tonometry": 10, "slit lamp": 10,
    },

    "neurology": {
        "eeg": 12, "electroencephalogram": 12, "nerve conduction": 12,
        "emg": 10, "electromyography": 12, "brain mri": 12,
        "cerebrospinal": 12, "csf": 10, "lumbar puncture": 10,
        "seizure": 8, "epilepsy": 8, "neuropathy": 10,
    },
}

# Report type display names
REPORT_TYPE_LABELS = {
    "blood_test": "Blood / Lab Report",
    "radiology": "Radiology Report",
    "pathology": "Pathology / Biopsy Report",
    "cardiology": "Cardiology Report",
    "ophthalmology": "Ophthalmology Report",
    "neurology": "Neurology Report",
    "general": "Medical Report",
}

# Report type icons
REPORT_TYPE_ICONS = {
    "blood_test": "🔬",
    "radiology": "🫁",
    "pathology": "🧬",
    "cardiology": "❤️",
    "ophthalmology": "👁️",
    "neurology": "🧠",
    "general": "📋",
}

# Whether each type requires the AI analyzer (True) or the existing parser (False)
REQUIRES_AI = {
    "blood_test": False,
    "radiology": True,
    "pathology": True,
    "cardiology": True,
    "ophthalmology": True,
    "neurology": True,
    "general": True,
}


def classify_report(text: str) -> Dict:
    """
    Classify the type of medical report from extracted text.

    Returns:
        {
            'type': 'blood_test' | 'radiology' | 'pathology' | 'cardiology' | ...,
            'label': 'Blood / Lab Report',
            'icon': '🔬',
            'confidence': 0.85,
            'requires_ai': False,
            'scores': {...}  # debug: per-type scores
        }
    """
    text_lower = text.lower()
    scores: Dict[str, float] = {}

    for report_type, signals in REPORT_SIGNALS.items():
        score = 0.0
        for keyword, weight in signals.items():
            if keyword in text_lower:
                # Count occurrences, cap at 3 to avoid single-term dominance
                count = min(text_lower.count(keyword), 3)
                score += weight * count
        scores[report_type] = score

    # Find best match
    if not scores or max(scores.values()) == 0:
        best_type = "general"
        confidence = 0.0
    else:
        best_type = max(scores, key=lambda k: scores[k])
        total_score = sum(scores.values())
        confidence = scores[best_type] / total_score if total_score > 0 else 0.0

        # Fallback to general if confidence too low
        if confidence < 0.25:
            best_type = "general"
            confidence = 0.0

    return {
        "type": best_type,
        "label": REPORT_TYPE_LABELS.get(best_type, "Medical Report"),
        "icon": REPORT_TYPE_ICONS.get(best_type, "📋"),
        "confidence": round(confidence, 3),
        "requires_ai": REQUIRES_AI.get(best_type, True),
        "scores": {k: round(v, 1) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
    }


def is_narrative_report(text: str) -> bool:
    """Quick check: does this text look like narrative prose vs. a numeric table?"""
    classification = classify_report(text)
    return classification["requires_ai"]
