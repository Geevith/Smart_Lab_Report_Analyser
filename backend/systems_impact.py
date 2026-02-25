"""
Systems Impact Calculator
Aggregates analyzed lab parameters into physiological system groupings.
This is an organizational grouping, NOT a medical diagnosis.
"""

from typing import Dict, List, Any

# System groupings based on existing parser.py parameters
# These are organizational categories, not medical conclusions
SYSTEM_GROUPINGS = {
    "Hematological": [
        "Hemoglobin", "RBC Count", "WBC Count", "Platelet Count", "Hematocrit",
        "MCV", "MCH", "MCHC", "RDW", "MPV", "PDW",
        "Absolute Neutrophil Count", "Absolute Lymphocyte Count", 
        "Absolute Eosinophil Count", "ESR"
    ],
    "Cardiovascular": [
        "Total Cholesterol", "Triglycerides", "HDL Cholesterol", "LDL Cholesterol",
        "VLDL Cholesterol", "HsCRP", "CPK Total", "LDH", "Homocysteine"
    ],
    "Metabolic": [
        "Fasting Blood Glucose", "Glucose Post Prandial", "HbA1C", "Uric Acid"
    ],
    "Renal": [
        "BUN", "Creatinine"
    ],
    "Hepatic": [
        "Bilirubin Total", "Bilirubin Direct", "Bilirubin Indirect",
        "SGOT", "SGPT", "Alkaline Phosphatase", "Gamma GT",
        "Total Protein", "Albumin", "Globulin"
    ],
    "Electrolyte Balance": [
        "Sodium", "Potassium", "Chloride", "Bicarbonate", "Calcium", "Phosphorus"
    ],
    "Thyroid Function": [
        "FT3", "FT4", "TSH"
    ],
    "Nutritional": [
        "Vitamin D", "Vitamin B12", "Serum Iron", "TIBC", "UIBC", "Transferrin Saturation"
    ]
}

# Parameter importance weights for scoring
# Critical biomarkers = 3.0, Standard = 2.0, Supporting = 1.0
PARAMETER_WEIGHTS = {
    # Hematological - Critical markers
    "Hemoglobin": 3.0,
    "RBC Count": 2.5,
    "WBC Count": 3.0,
    "Platelet Count": 3.0,
    "Hematocrit": 2.0,
    "MCV": 1.5,
    "MCH": 1.0,
    "MCHC": 1.0,
    "RDW": 1.0,
    "MPV": 1.0,
    "PDW": 0.5,
    "Absolute Neutrophil Count": 2.5,
    "Absolute Lymphocyte Count": 2.0,
    "Absolute Eosinophil Count": 1.5,
    "ESR": 1.5,
    
    # Cardiovascular - High importance
    "Total Cholesterol": 2.5,
    "Triglycerides": 2.5,
    "HDL Cholesterol": 3.0,
    "LDL Cholesterol": 3.0,
    "VLDL Cholesterol": 2.0,
    "HsCRP": 2.5,
    "CPK Total": 2.0,
    "LDH": 2.0,
    "Homocysteine": 2.0,
    
    # Metabolic - Critical for diabetes
    "Fasting Blood Glucose": 3.0,
    "Glucose Post Prandial": 3.0,
    "HbA1C": 3.0,
    "Uric Acid": 2.0,
    
    # Renal - Critical kidney function
    "BUN": 3.0,
    "Creatinine": 3.0,
    
    # Hepatic - Liver function markers
    "Bilirubin Total": 2.5,
    "Bilirubin Direct": 2.0,
    "Bilirubin Indirect": 1.5,
    "SGOT": 2.5,
    "SGPT": 2.5,
    "Alkaline Phosphatase": 2.5,
    "Gamma GT": 2.0,
    "Total Protein": 2.0,
    "Albumin": 2.5,
    "Globulin": 1.5,
    
    # Electrolyte Balance - Critical for homeostasis
    "Sodium": 3.0,
    "Potassium": 3.0,
    "Chloride": 2.5,
    "Bicarbonate": 2.5,
    "Calcium": 2.5,
    "Phosphorus": 2.0,
    
    # Thyroid Function - Hormonal regulation
    "FT3": 2.5,
    "FT4": 2.5,
    "TSH": 3.0,
    
    # Nutritional - Important for wellness
    "Vitamin D": 2.0,
    "Vitamin B12": 2.5,
    "Serum Iron": 2.0,
    "TIBC": 1.5,
    "UIBC": 1.0,
    "Transferrin Saturation": 2.0
}

# System-to-system physiological relationships
# These represent known medical connections, not diagnostic assertions
SYSTEM_RELATIONSHIPS = {
    "Thyroid Function": [
        {"target": "Cardiovascular", "type": "hormonal", "description": "Thyroid hormones regulate heart rate and cardiac output"},
        {"target": "Metabolic", "type": "metabolic", "description": "Thyroid affects basal metabolic rate"}
    ],
    "Renal": [
        {"target": "Electrolyte Balance", "type": "regulatory", "description": "Kidneys regulate electrolyte homeostasis"},
        {"target": "Cardiovascular", "type": "regulatory", "description": "Kidney function affects blood pressure"},
        {"target": "Hematological", "type": "hormonal", "description": "Kidneys produce erythropoietin for RBC production"}
    ],
    "Hepatic": [
        {"target": "Metabolic", "type": "metabolic", "description": "Liver regulates glucose and lipid metabolism"},
        {"target": "Nutritional", "type": "metabolic", "description": "Liver processes and stores vitamins"},
        {"target": "Hematological", "type": "synthetic", "description": "Liver produces clotting factors"}
    ],
    "Metabolic": [
        {"target": "Cardiovascular", "type": "pathological", "description": "Metabolic disorders affect cardiovascular health"},
        {"target": "Renal", "type": "pathological", "description": "Diabetes can lead to kidney damage"}
    ],
    "Cardiovascular": [
        {"target": "Renal", "type": "hemodynamic", "description": "Blood pressure affects kidney perfusion"}
    ],
    "Hematological": [
        {"target": "Cardiovascular", "type": "transport", "description": "Blood transports oxygen to heart"}
    ],
    "Nutritional": [
        {"target": "Hematological", "type": "substrate", "description": "Vitamins and iron needed for blood cell production"}
    ]
}

# Status labels - descriptive, not clinical
STATUS_LABELS = {
    "normal": "Within Expected Range",
    "minor": "Minor Variation Detected", 
    "multiple": "Multiple Variations Observed",
    "critical": "Significant Deviation Noted"
}

# Icons for each system (Material Icons)
SYSTEM_ICONS = {
    "Hematological": "water_drop",
    "Cardiovascular": "favorite",
    "Metabolic": "local_fire_department",
    "Renal": "science",
    "Hepatic": "healing",
    "Electrolyte Balance": "bolt",
    "Thyroid Function": "psychology",
    "Nutritional": "nutrition"
}

# Severity levels for frontend visualization (non-diagnostic)
SEVERITY_LEVELS = {
    "normal": "none",
    "minor": "mild",
    "multiple": "moderate",
    "critical": "high"
}

# Body region mapping for figure visualization (visual association only, not anatomical)
BODY_REGION_MAP = {
    "Hematological": {"region": "core", "x": 50, "y": 110, "label": "Blood Core"},
    "Cardiovascular": {"region": "chest", "x": 48, "y": 85, "label": "Chest"},
    "Metabolic": {"region": "abdomen", "x": 50, "y": 130, "label": "Abdomen"},
    "Renal": {"region": "lower_torso", "x": 50, "y": 145, "label": "Lower Torso"},
    "Hepatic": {"region": "right_abdomen", "x": 42, "y": 115, "label": "Right Abdomen"},
    "Electrolyte Balance": {"region": "limbs", "x": 25, "y": 100, "label": "Limbs"},
    "Thyroid Function": {"region": "neck", "x": 50, "y": 55, "label": "Neck"},
    "Nutritional": {"region": "head", "x": 50, "y": 30, "label": "Head"}
}


def calculate_weighted_score(abnormal_params: List[Dict[str, Any]]) -> float:
    """
    Calculate weighted abnormality score based on parameter importance.
    
    Args:
        abnormal_params: List of abnormal parameter dictionaries
        
    Returns:
        Weighted score (higher = more severe abnormalities)
    """
    weighted_sum = 0.0
    
    for param in abnormal_params:
        param_name = param.get("name", "")
        status = param.get("status", "")
        
        # Get weight (default to 1.0 if not found)
        weight = PARAMETER_WEIGHTS.get(param_name, 1.0)
        
        # Apply severity multiplier
        if status == "Critical":
            severity_multiplier = 3.0
        elif status in ["High", "Low"]:
            severity_multiplier = 1.5
        else:
            severity_multiplier = 1.0
        
        weighted_sum += weight * severity_multiplier
    
    return weighted_sum


def calculate_health_score(abnormal_params: List[Dict[str, Any]], total_params: int) -> Dict[str, Any]:
    """
    Calculate 0-100 health score for a system.
    
    Score logic:
    - Start with 100 (perfect health)
    - Deduct points based on abnormality severity and importance
    - Critical params: -15 points (weighted)
    - High/Low params: -8 points (weighted)
    - Minimum score: 0
    
    Args:
        abnormal_params: List of abnormal parameters
        total_params: Total parameter count in system
        
    Returns:
        Dictionary with score breakdown
    """
    base_score = 100
    deductions = []
    total_deduction = 0.0
    
    for param in abnormal_params:
        param_name = param.get("name", "")
        status = param.get("status", "")
        weight = PARAMETER_WEIGHTS.get(param_name, 1.0)
        
        # Calculate deduction based on status and weight
        if status == "Critical":
            deduction = 15.0 * (weight / 2.5)  # Normalize by average weight
        elif status in ["High", "Low"]:
            deduction = 8.0 * (weight / 2.5)
        else:
            deduction = 3.0 * (weight / 2.5)
        
        deductions.append({
            "parameter": param_name,
            "status": status,
            "deduction": round(deduction, 1)
        })
        total_deduction += deduction
    
    # Calculate final score (ensure it stays in 0-100 range)
    final_score = max(0, min(100, base_score - total_deduction))
    
    return {
        "score": int(final_score),
        "base": base_score,
        "total_deduction": round(total_deduction, 1),
        "deductions": deductions
    }


def get_related_systems(system_name: str) -> List[Dict[str, str]]:
    """
    Get systems related to the given system.
    
    Args:
        system_name: Name of the system
        
    Returns:
        List of related system dictionaries with target, type, and description
    """
    return SYSTEM_RELATIONSHIPS.get(system_name, [])


def compute_systems_impact(analyzed_parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute system-level impact summary from analyzed parameters.
    
    Args:
        analyzed_parameters: List of parameter dicts with keys:
            - name: str
            - value: str
            - unit: str
            - range: str
            - status: str (Normal, High, Low, Critical)
    
    Returns:
        Dict with system names as keys, each containing:
            - status: str (descriptive label)
            - abnormal_count: int
            - critical: bool
            - total_count: int
            - parameters: list of contributing parameter details
            - icon: str (Material Icon name)
    """
    # Build lookup by parameter name
    param_lookup = {p["name"]: p for p in analyzed_parameters}
    
    systems_result = {}
    
    for system_name, param_names in SYSTEM_GROUPINGS.items():
        # Find parameters belonging to this system
        system_params = []
        abnormal_params = []
        has_critical = False
        
        for param_name in param_names:
            if param_name in param_lookup:
                param = param_lookup[param_name]
                system_params.append({
                    "name": param.get("name"),
                    "value": param.get("value"),
                    "unit": param.get("unit", ""),
                    "range": param.get("range", ""),
                    "status": param.get("status", "Normal")
                })
                
                status = param.get("status", "Normal")
                if status in ["High", "Low"]:
                    abnormal_params.append(param)
                elif status == "Critical":
                    abnormal_params.append(param)
                    has_critical = True
        
        # Skip systems with no parameters found
        if not system_params:
            continue
        
        # Determine system status based on deterministic rules
        abnormal_count = len(abnormal_params)
        
        if has_critical:
            status_key = "critical"
        elif abnormal_count >= 2:
            status_key = "multiple"
        elif abnormal_count == 1:
            status_key = "minor"
        else:
            status_key = "normal"
        
        # Calculate weighted score and health score
        weighted_score = calculate_weighted_score(abnormal_params)
        health_score_data = calculate_health_score(abnormal_params, len(system_params))
        
        # Get related systems
        related_systems = get_related_systems(system_name)
        
        systems_result[system_name] = {
            "status": STATUS_LABELS[status_key],
            "status_key": status_key,
            "severity_level": SEVERITY_LEVELS[status_key],
            "abnormal_count": abnormal_count,
            "critical": has_critical,
            "total_count": len(system_params),
            "icon": SYSTEM_ICONS.get(system_name, "science"),
            "body_region": BODY_REGION_MAP.get(system_name, {"region": "unknown", "x": 50, "y": 100, "label": "Unknown"}),
            "parameters": system_params,
            "abnormal_parameters": [
                {
                    "name": p.get("name"),
                    "value": p.get("value"),
                    "unit": p.get("unit", ""),
                    "status": p.get("status")
                }
                for p in abnormal_params
            ],
            # New enhanced data
            "weighted_score": round(weighted_score, 2),
            "health_score": health_score_data["score"],
            "score_breakdown": health_score_data,
            "related_systems": related_systems,
            # Placeholder for trends (will be calculated when historical data available)
            "trend_vs_previous": None
        }
    
    return systems_result

