"""
Clinical Intelligence Module
Generates context-aware insights by analyzing parameter relationships
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ContextualInsight:
    """Context-aware clinical insight"""
    parameter: str
    insight_type: str  # 'contextual', 'isolated', 'pattern'
    message: str
    supporting_params: List[str]
    severity: str
    confidence: int  # 0-95

# Parameter relationship mapping
CLINICAL_RELATIONSHIPS = {
    "Hemoglobin": {
        "supporting": ["RBC Count", "Hematocrit", "MCV", "MCH", "MCHC"],
        "conflicting": ["Platelet Count", "WBC Count"],
        "related_organs": ["Bone Marrow", "Kidneys", "Spleen"]
    },
    "Fasting Blood Glucose": {
        "supporting": ["HbA1C", "Glucose Post Prandial"],
        "conflicting": [],
        "related_organs": ["Pancreas", "Liver"]
    },
    "Glucose Post Prandial": {
        "supporting": ["HbA1C", "Fasting Blood Glucose"],
        "conflicting": [],
        "related_organs": ["Pancreas"]
    },
    "HbA1C": {
        "supporting": ["Fasting Blood Glucose", "Glucose Post Prandial"],
        "conflicting": [],
        "related_organs": ["Pancreas", "Blood"]
    },
    "TSH": {
        "supporting": ["FT3", "FT4"],
        "conflicting": [],
        "related_organs": ["Thyroid", "Pituitary"]
    },
    "FT4": {
        "supporting": ["TSH", "FT3"],
        "conflicting": [],
        "related_organs": ["Thyroid"]
    },
    "FT3": {
        "supporting": ["TSH", "FT4"],
        "conflicting": [],
        "related_organs": ["Thyroid"]
    },
    "Creatinine": {
        "supporting": ["BUN"],
        "conflicting": [],
        "related_organs": ["Kidneys"]
    },
    "BUN": {
        "supporting": ["Creatinine"],
        "conflicting": [],
        "related_organs": ["Kidneys"]
    },
    "Total Cholesterol": {
        "supporting": ["LDL Cholesterol", "HDL Cholesterol", "Triglycerides"],
        "conflicting": [],
        "related_organs": ["Liver", "Heart"]
    },
    "LDL Cholesterol": {
        "supporting": ["Total Cholesterol", "HDL Cholesterol", "Triglycerides"],
        "conflicting": [],
        "related_organs": ["Heart", "Arteries"]
    },
    "HDL Cholesterol": {
        "supporting": ["Total Cholesterol", "LDL Cholesterol"],
        "conflicting": [],
        "related_organs": ["Heart", "Liver"]
    },
    "Triglycerides": {
        "supporting": ["Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol", "Fasting Blood Glucose"],
        "conflicting": [],
        "related_organs": ["Liver", "Pancreas"]
    },
    # Iron panel relationships
    "Serum Iron": {
        "supporting": ["TIBC", "Transferrin Saturation", "Hemoglobin", "MCV"],
        "conflicting": [],
        "related_organs": ["Bone Marrow", "Liver"]
    },
    "TIBC": {
        "supporting": ["Serum Iron", "Transferrin Saturation"],
        "conflicting": [],
        "related_organs": ["Liver"]
    },
    "Transferrin Saturation": {
        "supporting": ["Serum Iron", "TIBC"],
        "conflicting": [],
        "related_organs": ["Liver"]
    },
    # CBC extended relationships
    "MCV": {
        "supporting": ["Hemoglobin", "RBC Count", "MCH", "MCHC"],
        "conflicting": [],
        "related_organs": ["Bone Marrow"]
    },
    "MCH": {
        "supporting": ["Hemoglobin", "MCV", "MCHC"],
        "conflicting": [],
        "related_organs": ["Bone Marrow"]
    },
    "MCHC": {
        "supporting": ["Hemoglobin", "MCV", "MCH"],
        "conflicting": [],
        "related_organs": ["Bone Marrow"]
    },
    "RBC Count": {
        "supporting": ["Hemoglobin", "Hematocrit", "MCV"],
        "conflicting": [],
        "related_organs": ["Bone Marrow"]
    },
    "Hematocrit": {
        "supporting": ["Hemoglobin", "RBC Count"],
        "conflicting": [],
        "related_organs": ["Blood"]
    },
    # Liver function relationships  
    "SGPT": {
        "supporting": ["SGOT", "Bilirubin Total", "Alkaline Phosphatase"],
        "conflicting": [],
        "related_organs": ["Liver"]
    },
    "SGOT": {
        "supporting": ["SGPT", "Bilirubin Total"],
        "conflicting": [],
        "related_organs": ["Liver", "Heart", "Muscle"]
    }
}

# Contextual insight templates
CONTEXTUAL_INSIGHTS = {
    # Hematological patterns
    ("Hemoglobin", "LOW", "Platelet Count", "NORMAL"): {
        "template": "{severity} reduced hemoglobin with normal platelet count suggests nutritional deficiency (iron, B12, or folate) rather than bone marrow dysfunction.",
        "confidence": 75
    },
    ("Hemoglobin", "LOW", "MCV", "LOW"): {
        "template": "{severity} reduced hemoglobin with low MCV indicates microcytic anemia, commonly associated with iron deficiency.",
        "confidence": 80
    },
    ("Hemoglobin", "LOW", "MCV", "HIGH"): {
        "template": "{severity} reduced hemoglobin with elevated MCV suggests macrocytic anemia, possibly related to Vitamin B12 or folate deficiency.",
        "confidence": 80
    },
    ("Hemoglobin", "LOW", "RBC Count", "LOW"): {
        "template": "{severity} reduced hemoglobin accompanied by low RBC count indicates anemia with reduced red blood cell production.",
        "confidence": 75
    },
    
    # Metabolic patterns
    ("Fasting Blood Glucose", "HIGH", "HbA1C", "HIGH"): {
        "template": "Sustained elevation in both fasting glucose and HbA1C indicates chronic poor glycemic control over the past 2-3 months.",
        "confidence": 85
    },
    ("Fasting Blood Glucose", "HIGH", "HbA1C", "NORMAL"): {
        "template": "Elevated fasting glucose with normal HbA1C may indicate recent glycemic variability or early glucose intolerance.",
        "confidence": 70
    },
    ("HbA1C", "HIGH", "Glucose Post Prandial", "HIGH"): {
        "template": "Elevated HbA1C with high post-meal glucose suggests persistent hyperglycemia requiring glycemic management.",
        "confidence": 80
    },
    
    # Thyroid patterns
    ("TSH", "HIGH", "FT4", "LOW"): {
        "template": "Elevated TSH with low FT4 is a pattern consistent with primary hypothyroidism.",
        "confidence": 90
    },
    ("TSH", "LOW", "FT4", "HIGH"): {
        "template": "Suppressed TSH with elevated FT4 is a pattern consistent with hyperthyroidism.",
        "confidence": 90
    },
    ("TSH", "HIGH", "FT4", "NORMAL"): {
        "template": "Elevated TSH with normal FT4 may indicate subclinical hypothyroidism or early thyroid dysfunction.",
        "confidence": 75
    },
    ("TSH", "LOW", "FT4", "NORMAL"): {
        "template": "Suppressed TSH with normal FT4 may indicate subclinical hyperthyroidism or excessive thyroid hormone replacement.",
        "confidence": 75
    },
    
    # Renal patterns
    ("Creatinine", "HIGH", "BUN", "HIGH"): {
        "template": "Elevated creatinine and BUN together suggest reduced kidney function requiring medical evaluation.",
        "confidence": 85
    },
    ("Creatinine", "HIGH", "BUN", "NORMAL"): {
        "template": "Elevated creatinine with normal BUN may indicate muscle-related elevation or early kidney changes.",
        "confidence": 65
    },
    
    # Lipid patterns
    ("LDL Cholesterol", "HIGH", "HDL Cholesterol", "LOW"): {
        "template": "Elevated LDL with low HDL is an unfavorable lipid profile associated with increased cardiovascular risk.",
        "confidence": 85
    },
    ("Total Cholesterol", "HIGH", "LDL Cholesterol", "HIGH"): {
        "template": "Elevated total cholesterol primarily driven by elevated LDL cholesterol suggests need for lipid management.",
        "confidence": 80
    },
    
    # Iron deficiency patterns
    ("Serum Iron", "LOW", "TIBC", "HIGH"): {
        "template": "Low serum iron with elevated TIBC is a classic pattern indicating iron deficiency - the body increases transferrin production to capture available iron.",
        "confidence": 90
    },
    ("Serum Iron", "LOW", "Transferrin Saturation", "LOW"): {
        "template": "Low serum iron with reduced transferrin saturation confirms iron deficiency state.",
        "confidence": 85
    },
    ("MCV", "LOW", "MCH", "LOW"): {
        "template": "Low MCV and MCH together indicate microcytic hypochromic anemia, typically from iron deficiency.",
        "confidence": 80
    },
    
    # Metabolic syndrome cluster
    ("Fasting Blood Glucose", "HIGH", "Triglycerides", "HIGH"): {
        "template": "Elevated fasting glucose with high triglycerides suggests insulin resistance and increased cardiovascular risk.",
        "confidence": 80
    },
    ("Triglycerides", "HIGH", "HDL Cholesterol", "LOW"): {
        "template": "High triglycerides with low HDL is an atherogenic dyslipidemia pattern associated with metabolic syndrome.",
        "confidence": 85
    },
    
    # Dehydration pattern
    ("Hemoglobin", "HIGH", "Hematocrit", "HIGH"): {
        "template": "Elevated hemoglobin and hematocrit together suggest hemoconcentration, possibly from dehydration.",
        "confidence": 75
    },
    ("Creatinine", "HIGH", "Hematocrit", "HIGH"): {
        "template": "Elevated creatinine with high hematocrit may indicate dehydration-induced pre-renal azotemia.",
        "confidence": 70
    },
    
    # Liver damage patterns
    ("SGPT", "HIGH", "SGOT", "HIGH"): {
        "template": "Elevated SGPT (ALT) and SGOT (AST) together indicate hepatocellular injury. SGPT is more liver-specific.",
        "confidence": 85
    },
    ("Bilirubin Total", "HIGH", "SGPT", "HIGH"): {
        "template": "Elevated bilirubin with raised SGPT suggests hepatocellular disease affecting both liver function and enzyme levels.",
        "confidence": 80
    }
}


def generate_contextual_insights(
    parameters_dict: Dict[str, Dict[str, Any]]
) -> List[ContextualInsight]:
    """
    Generate context-aware insights by analyzing parameter relationships
    
    Args:
        parameters_dict: Dict mapping parameter names to their data
                        {name: {value, status, severity, ...}}
    
    Returns:
        List of ContextualInsight objects
    """
    insights = []
    processed_params = set()
    
    # Iterate through abnormal parameters
    for param_name, param_data in parameters_dict.items():
        status = param_data.get("status", "NORMAL")
        
        if status == "NORMAL" or param_name in processed_params:
            continue
        
        # Check for contextual patterns with supporting parameters
        contextual_insight = _find_contextual_pattern(
            param_name, param_data, parameters_dict
        )
        
        if contextual_insight:
            insights.append(contextual_insight)
            processed_params.add(param_name)
        else:
            # Fallback to isolated insight
            isolated_insight = _create_isolated_insight(param_name, param_data)
            insights.append(isolated_insight)
            processed_params.add(param_name)
    
    return insights


def _find_contextual_pattern(
    param_name: str,
    param_data: Dict[str, Any],
    all_params: Dict[str, Dict[str, Any]]
) -> Optional[ContextualInsight]:
    """Find contextual insight based on parameter relationships"""
    
    status = param_data.get("status", "NORMAL")
    severity = param_data.get("severity", "MEDIUM")
    
    # Get relationship map
    relationships = CLINICAL_RELATIONSHIPS.get(param_name, {})
    supporting_params = relationships.get("supporting", [])
    
    # Check each supporting parameter for pattern match
    for support_param in supporting_params:
        if support_param in all_params:
            support_data = all_params[support_param]
            support_status = support_data.get("status", "NORMAL")
            
            # Build pattern key
            pattern_key = (param_name, status, support_param, support_status)
            
            if pattern_key in CONTEXTUAL_INSIGHTS:
                template_data = CONTEXTUAL_INSIGHTS[pattern_key]
                
                # Format severity label
                severity_label = {
                    "LOW": "Mildly",
                    "MEDIUM": "Moderately",
                    "HIGH": "Significantly",
                    "CRITICAL": "Critically"
                }.get(severity, "")
                
                message = template_data["template"].format(severity=severity_label)
                
                return ContextualInsight(
                    parameter=param_name,
                    insight_type="contextual",
                    message=message,
                    supporting_params=[support_param],
                    severity=severity,
                    confidence=template_data["confidence"]
                )
    
    return None


def _create_isolated_insight(
    param_name: str,
    param_data: Dict[str, Any]
) -> ContextualInsight:
    """Create basic insight for isolated parameter"""
    
    # Import here to avoid circular dependency
    from backend.interpretation import ANALYSIS_RULES
    
    status = param_data.get("status", "NORMAL")
    severity = param_data.get("severity", "MEDIUM")
    
    # Get insight from existing rules
    insight_text = ANALYSIS_RULES.get(
        (param_name, status.capitalize()),
        f"{status.capitalize()} {param_name} detected. Consult healthcare provider for interpretation."
    )
    
    return ContextualInsight(
        parameter=param_name,
        insight_type="isolated",
        message=insight_text,
        supporting_params=[],
        severity=severity,
        confidence=60  # Lower confidence for isolated insights
    )


def calculate_insight_confidence(
    param_data: Dict[str, Any],
    supporting_abnormal_count: int = 0
) -> Tuple[int, str]:
    """
    Calculate confidence score for an insight
    
    Args:
        param_data: Parameter data with value, range, status
        supporting_abnormal_count: Number of related abnormal parameters
    
    Returns:
        Tuple of (confidence_score, rationale_text)
    """
    confidence = 50  # Base confidence
    rationale_parts = []
    
    # Factor 1: Deviation strength
    deviation = _calculate_deviation_percentage(param_data)
    if deviation:
        if deviation > 50:
            confidence += 25
            rationale_parts.append(f"{deviation:.0f}% deviation")
        elif deviation > 25:
            confidence += 15
            rationale_parts.append(f"{deviation:.0f}% deviation")
        else:
            confidence += 5
            rationale_parts.append(f"{deviation:.0f}% deviation")
    
    # Factor 2: Supporting parameters
    if supporting_abnormal_count > 2:
        confidence += 20
        rationale_parts.append(f"{supporting_abnormal_count} supporting params")
    elif supporting_abnormal_count > 0:
        confidence += 10
        rationale_parts.append(f"{supporting_abnormal_count} supporting param(s)")
    
    # Cap at 95%
    confidence = min(confidence, 95)
    
    rationale = "Based on: " + ", ".join(rationale_parts) if rationale_parts else "Limited data available"
    
    return confidence, rationale


def _calculate_deviation_percentage(param_data: Dict[str, Any]) -> Optional[float]:
    """Calculate percentage deviation from reference range"""
    try:
        value = float(param_data.get("value", 0))
        ref_range = param_data.get("range", "")
        
        # Simple numeric range parsing
        import re
        range_match = re.search(r'([\d.]+)\s*-\s*([\d.]+)', ref_range)
        
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            
            if value < min_val:
                return abs((value - min_val) / min_val) * 100
            elif value > max_val:
                return abs((value - max_val) / max_val) * 100
        
        return None
    except:
        return None
