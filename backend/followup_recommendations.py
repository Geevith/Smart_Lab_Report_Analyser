"""
Follow-Up Test Recommendations Module
Provides educational test suggestions based on abnormal lab findings
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class FollowUpRecommendation:
    """Follow-up test recommendation"""
    parameter_name: str
    suggested_tests: List[str]
    rationale: str
    priority: str  # 'low', 'medium', 'high'
    disclaimer: str = "These are educational suggestions based on clinical guidelines. Always consult your healthcare provider for personalized medical advice."

# Comprehensive follow-up test mappings
FOLLOWUP_TESTS = {
    ("Hemoglobin", "LOW"): {
        "tests": [
            "Iron Profile (Serum Iron, TIBC, Ferritin)",
            "Vitamin B12",
            "Folate (Folic Acid)",
            "Reticulocyte Count",
            "Peripheral Blood Smear"
        ],
        "rationale": "To identify the specific cause of anemia and guide appropriate treatment",
        "priority": "medium"
    },
    ("Hemoglobin", "HIGH"): {
        "tests": [
            "Complete Pulmonary Function Tests",
            "Arterial Blood Gas (ABG)",
            "Serum Erythropoietin Level"
        ],
        "rationale": "To evaluate potential causes of elevated hemoglobin such as hypoxia or polycythemia",
        "priority": "medium"
    },
    
    ("WBC Count", "HIGH"): {
        "tests": [
            "Differential White Cell Count",
            "C-Reactive Protein (CRP)",
            "Blood Culture (if infection suspected)"
        ],
        "rationale": "To determine the specific type of white cells elevated and identify potential infection or inflammation",
        "priority": "medium"
    },
    ("WBC Count", "LOW"): {
        "tests": [
            "Differential White Cell Count",
            "Vitamin B12 and Folate",
            "HIV Test (if risk factors present)",
            "Bone Marrow Examination (if persistent)"
        ],
        "rationale": "To investigate causes of decreased white blood cell production",
        "priority": "high"
    },
    
    ("Platelet Count", "LOW"): {
        "tests": [
            "Peripheral Blood Smear",
            "Coagulation Profile (PT, aPTT)",
            "Liver Function Tests",
            "HIV and Hepatitis Screening"
        ],
        "rationale": "To assess bleeding risk and identify underlying causes of thrombocytopenia",
        "priority": "high"
    },
    
    ("Fasting Blood Glucose", "HIGH"): {
        "tests": [
            "HbA1C (if not already done)",
            "Fasting Lipid Panel",
            "Kidney Function Tests (Creatinine, BUN, eGFR)",
            "Liver Function Tests",
            "Urine Albumin/Creatinine Ratio"
        ],
        "rationale": "To assess diabetes control, screen for complications, and evaluate cardiovascular risk",
        "priority": "high"
    },
    ("Fasting Blood Glucose", "LOW"): {
        "tests": [
            "Insulin Level",
            "C-Peptide",
            "Cortisol Level",
            "Growth Hormone Level"
        ],
        "rationale": "To determine the cause of hypoglycemia and rule out hormonal imbalances",
        "priority": "medium"
    },
    
    ("HbA1C", "HIGH"): {
        "tests": [
            "Fasting Lipid Panel",
            "Kidney Function Tests",
            "Liver Function Tests",
            "Urine Microalbumin",
            "Eye Examination (Retinal screening)"
        ],
        "rationale": "To screen for diabetic complications and cardiovascular risk factors",
        "priority": "high"
    },
    
    ("TSH", "HIGH"): {
        "tests": [
            "Free T4 (FT4)",
            "Anti-TPO Antibodies (Thyroid Peroxidase)",
            "Anti-Thyroglobulin Antibodies"
        ],
        "rationale": "To confirm hypothyroidism and check for autoimmune thyroid disease",
        "priority": "high"
    },
    ("TSH", "LOW"): {
        "tests": [
            "Free T4 (FT4)",
            "Free T3 (FT3)",
            "Thyroid Ultrasound",
            "TSH Receptor Antibodies"
        ],
        "rationale": "To confirm hyperthyroidism and identify the underlying cause",
        "priority": "high"
    },
    
    ("FT4", "HIGH"): {
        "tests": [
            "TSH (if not done)",
            "Free T3 (FT3)",
            "Thyroid Ultrasound",
            "Radioactive Iodine Uptake Scan"
        ],
        "rationale": "To evaluate thyroid hormone excess and determine treatment approach",
        "priority": "high"
    },
    ("FT4", "LOW"): {
        "tests": [
            "TSH (if not done)",
            "Anti-TPO Antibodies",
            "Morning Cortisol Level"
        ],
        "rationale": "To confirm hypothyroidism and rule out pituitary or adrenal causes",
        "priority": "high"
    },
    
    ("Creatinine", "HIGH"): {
        "tests": [
            "BUN (if not done)",
            "Estimated GFR (eGFR)",
            "Urine Routine and Microscopy",
            "Urine Protein/Creatinine Ratio",
            "Renal Ultrasound"
        ],
        "rationale": "To assess kidney function comprehensively and identify potential kidney disease",
        "priority": "high"
    },
    
    ("BUN", "HIGH"): {
        "tests": [
            "Creatinine (if not done)",
            "eGFR",
            "Urine Routine Analysis",
            "Electrolytes (Sodium, Potassium)"
        ],
        "rationale": "To evaluate kidney function and hydration status",
        "priority": "high"
    },
    
    ("Total Cholesterol", "HIGH"): {
        "tests": [
            "LDL Cholesterol (if not measured directly)",
            "HDL Cholesterol",
            "Triglycerides",
            "Lipoprotein(a)",
            "ApoB/ApoA1 Ratio",
            "HbA1C or Fasting Glucose"
        ],
        "rationale": "To complete lipid profile and assess cardiovascular risk factors",
        "priority": "medium"
    },
    
    ("LDL Cholesterol", "HIGH"): {
        "tests": [
            "HDL Cholesterol",
            "Triglycerides",
            "ApoB",
            "Lipoprotein(a)",
            "HsCRP (High-Sensitivity C-Reactive Protein)",
            "Coronary Calcium Score (if indicated)"
        ],
        "rationale": "To stratify cardiovascular risk and guide lipid management",
        "priority": "high"
    },
    
    ("HDL Cholesterol", "LOW"): {
        "tests": [
            "LDL Cholesterol",
            "Triglycerides",
            "Fasting Glucose or HbA1C",
            "Liver Function Tests"
        ],
        "rationale": "To assess overall cardiovascular risk profile",
        "priority": "medium"
    },
    
    ("Triglycerides", "HIGH"): {
        "tests": [
            "Fasting Lipid Panel (if not done fasting)",
            "HbA1C or Fasting Glucose",
            "Liver Function Tests",
            "Kidney Function Tests",
            "Thyroid Function Tests (TSH)"
        ],
        "rationale": "To identify secondary causes of hypertriglyceridemia",
        "priority": "medium"
    },
    
    ("SGOT", "HIGH"): {
        "tests": [
            "SGPT (ALT) if not done",
            "Complete Liver Function Tests",
            "Hepatitis Panel (HBsAg, Anti-HCV)",
            "Abdominal Ultrasound",
            "Lipid Profile"
        ],
        "rationale": "To evaluate liver function and identify causes of hepatic enzyme elevation",
        "priority": "high"
    },
    ("SGPT", "HIGH"): {
        "tests": [
            "SGOT (AST) if not done",
            "Complete Liver Function Tests",
            "Hepatitis Screening",
            "Liver Ultrasound",
            "Fasting Glucose or HbA1C"
        ],
        "rationale": "To assess liver health and screen for fatty liver or hepatitis",
        "priority": "high"
    },
    
    ("Uric Acid", "HIGH"): {
        "tests": [
            "Kidney Function Tests",
            "24-Hour Urine Uric Acid",
            "Joint Fluid Analysis (if joint pain present)"
        ],
        "rationale": "To evaluate for gout, kidney stones, and renal uric acid handling",
        "priority": "medium"
    },
    
    ("Vitamin D", "LOW"): {
        "tests": [
            "Calcium Level",
            "Phosphorus Level",
            "Parathyroid Hormone (PTH)",
            "Alkaline Phosphatase"
        ],
        "rationale": "To assess bone health and calcium metabolism",
        "priority": "low"
    },
    
    ("Vitamin B12", "LOW"): {
        "tests": [
            "Complete Blood Count (CBC)",
            "Folate Level",
            "Methylmalonic Acid (MMA)",
            "Homocysteine",
            "Intrinsic Factor Antibodies"
        ],
        "rationale": "To confirm B12 deficiency and identify malabsorption causes",
        "priority": "medium"
    },
}


def get_followup_recommendations(
    parameters_dict: Dict[str, Dict[str, Any]]
) -> List[FollowUpRecommendation]:
    """
    Generate follow-up test recommendations for abnormal parameters
    
    Args:
        parameters_dict: Dict mapping parameter names to their data
                        {name: {value, status, severity, ...}}
    
    Returns:
        List of FollowUpRecommendation objects
    """
    recommendations = []
    
    for param_name, param_data in parameters_dict.items():
        status = param_data.get("status", "NORMAL")
        
        # Only generate recommendations for abnormal parameters
        if status == "NORMAL":
            continue
        
        # Look up recommendation
        key = (param_name, status)
        if key in FOLLOWUP_TESTS:
            rec_data = FOLLOWUP_TESTS[key]
            
            recommendation = FollowUpRecommendation(
                parameter_name=param_name,
                suggested_tests=rec_data["tests"],
                rationale=rec_data["rationale"],
                priority=rec_data["priority"]
            )
            recommendations.append(recommendation)
    
    # Sort by priority (high > medium > low)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
    
    return recommendations
