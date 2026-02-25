"""
Missing Tests Suggester - Intelligent system for suggesting follow-up tests
based on detected abnormalities in lab reports.
"""

from typing import List, Dict, Any


class TestSuggestion:
    """Represents a suggested follow-up test."""
    def __init__(self, test_name: str, rationale: str, priority: str = "Medium"):
        self.test_name = test_name
        self.rationale = rationale
        self.priority = priority  # High, Medium, Low
    
    def to_dict(self):
        return {
            "test_name": self.test_name,
            "rationale": self.rationale,
            "priority": self.priority
        }


# Knowledge base of test suggestions based on abnormal parameters
SUGGESTION_RULES = {
    # Glucose/Diabetes markers
    "glucose": {
        "high": [
            TestSuggestion("HbA1c (Glycated Hemoglobin)", "Elevated glucose detected. HbA1c provides 3-month average blood sugar levels.", "High"),
            TestSuggestion("Fasting Insulin", "High glucose may indicate insulin resistance. Fasting insulin helps assess pancreatic function.", "Medium"),
            TestSuggestion("C-Peptide", "Helps distinguish between Type 1 and Type 2 diabetes by measuring insulin production.", "Medium"),
        ]
    },
    
    # Anemia markers
    "hemoglobin": {
        "low": [
            TestSuggestion("Iron Studies (Serum Iron, TIBC, Ferritin)", "Low hemoglobin suggests anemia. Iron studies identify iron-deficiency anemia.", "High"),
            TestSuggestion("Vitamin B12", "B12 deficiency can cause megaloblastic anemia.", "High"),
            TestSuggestion("Folate (Folic Acid)", "Folate deficiency is another cause of megaloblastic anemia.", "High"),
            TestSuggestion("Reticulocyte Count", "Measures bone marrow's response to anemia.", "Medium"),
        ]
    },
    
    # Liver function
    "alt": {
        "high": [
            TestSuggestion("Hepatitis Panel (A, B, C)", "Elevated liver enzymes may indicate viral hepatitis.", "High"),
            TestSuggestion("Liver Ultrasound", "Imaging to assess liver structure and detect fatty liver disease.", "Medium"),
            TestSuggestion("GGT (Gamma-Glutamyl Transferase)", "Helps distinguish liver vs. bone-related ALP elevation.", "Medium"),
        ]
    },
    
    "ast": {
        "high": [
            TestSuggestion("Hepatitis Panel (A, B, C)", "Elevated liver enzymes may indicate viral hepatitis.", "High"),
            TestSuggestion("Liver Ultrasound", "Imaging to assess liver structure and detect cirrhosis or fatty liver.", "Medium"),
            TestSuggestion("AST/ALT Ratio", "Ratio analysis helps identify alcoholic vs. non-alcoholic liver disease.", "Low"),
        ]
    },
    
    # Cholesterol/Lipid markers
    "cholesterol": {
        "high": [
            TestSuggestion("Apolipoprotein B (ApoB)", "More accurate cardiovascular risk marker than LDL cholesterol.", "Medium"),
            TestSuggestion("Lipoprotein(a) [Lp(a)]", "Genetic risk factor for cardiovascular disease not affected by lifestyle.", "Medium"),
            TestSuggestion("hs-CRP (High-Sensitivity C-Reactive Protein)", "Measures inflammation, a key cardiovascular risk factor.", "Low"),
        ]
    },
    
    "ldl": {
        "high": [
            TestSuggestion("Apolipoprotein B (ApoB)", "Superior marker for assessing cardiovascular risk.", "Medium"),
            TestSuggestion("Coronary Calcium Score (CT Scan)", "Imaging to quantify arterial plaque buildup.", "Medium"),
        ]
    },
    
    # Kidney function
    "creatinine": {
        "high": [
            TestSuggestion("Cystatin C", "More accurate kidney function marker, especially in early disease.", "High"),
            TestSuggestion("Urine Microalbumin/Creatinine Ratio", "Detects early kidney damage.", "High"),
            TestSuggestion("Kidney Ultrasound", "Imaging to assess kidney structure and size.", "Medium"),
        ]
    },
    
    "bun": {
        "high": [
            TestSuggestion("Urine Analysis", "Comprehensive kidney function assessment.", "High"),
            TestSuggestion("Electrolyte Panel", "Monitors sodium, potassium, and other minerals affected by kidney function.", "Medium"),
        ]
    },
    
    # Thyroid
    "tsh": {
        "high": [
            TestSuggestion("Free T4", "Confirms hypothyroidism and assesses severity.", "High"),
            TestSuggestion("TPO Antibodies (Anti-Thyroid Peroxidase)", "Detects autoimmune thyroid disease (Hashimoto's).", "Medium"),
        ],
        "low": [
            TestSuggestion("Free T4 and Free T3", "Confirms hyperthyroidism and identifies type.", "High"),
            TestSuggestion("Thyroid Ultrasound", "Imaging to detect nodules or goiter.", "Medium"),
        ]
    },
    
    # White blood cells
    "wbc": {
        "high": [
            TestSuggestion("Differential WBC Count", "Identifies which white blood cells are elevated (neutrophils, lymphocytes, etc.).", "High"),
            TestSuggestion("CRP (C-Reactive Protein)", "Measures inflammation or infection severity.", "Medium"),
        ],
        "low": [
            TestSuggestion("Differential WBC Count", "Identifies which white blood cells are low.", "High"),
            TestSuggestion("Bone Marrow Biopsy", "For severe or unexplained leukopenia.", "Medium"),
        ]
    },
}


def suggest_missing_tests(parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze parameters and suggest missing follow-up tests.
    
    Args:
        parameters: List of parameter dictionaries with name, value, status, etc.
    
    Returns:
        List of test suggestions
    """
    suggestions = []
    seen_tests = set()  # Avoid duplicate suggestions
    
    for param in parameters:
        param_name = param.get("name", "").lower()
        status = param.get("status", "Normal").lower()
        
        # Check if parameter has abnormal status
        if status in ["high", "low", "critical"]:
            # Search for matching rules
            for rule_key, rule_data in SUGGESTION_RULES.items():
                if rule_key in param_name:
                    # Get suggestions for this status
                    status_suggestions = rule_data.get(status, [])
                    
                    for suggestion in status_suggestions:
                        # Avoid duplicates
                        if suggestion.test_name not in seen_tests:
                            seen_tests.add(suggestion.test_name)
                            suggestions.append(suggestion.to_dict())
    
    # Sort by priority: High > Medium > Low
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return suggestions


def get_demographic_specific_suggestions(parameters: List[Dict[str, Any]], user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get test suggestions based on demographics (age, gender, etc.).
    
    Args:
        parameters: List of parameters
        user_data: User demographic data (age, gender, etc.)
    
    Returns:
        List of demographic-specific suggestions
    """
    suggestions = []
    age = user_data.get("age")
    gender = user_data.get("gender", "").lower()
    
    # Age-based suggestions
    if age and age >= 40:
        suggestions.append(TestSuggestion(
            "Coronary Calcium Score",
            "Recommended for adults over 40 to assess cardiovascular risk.",
            "Medium"
        ).to_dict())
    
    if age and age >= 50:
        suggestions.append(TestSuggestion(
            "Colonoscopy Screening",
            "Colorectal cancer screening recommended starting at age 50.",
            "High"
        ).to_dict())
    
    # Gender-based suggestions
    if gender == "female" and age and age >= 40:
        suggestions.append(TestSuggestion(
            "Mammogram",
            "Breast cancer screening recommended for women over 40.",
            "High"
        ).to_dict())
    
    if gender == "male" and age and age >= 50:
        suggestions.append(TestSuggestion(
            "PSA (Prostate-Specific Antigen)",
            "Prostate cancer screening for men over 50.",
            "Medium"
        ).to_dict())
    
    return suggestions
