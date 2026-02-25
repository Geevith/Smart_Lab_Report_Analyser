"""
Audit Trail System for Explainability & Traceability
Tracks rule application, trigger conditions, and decision paths
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

@dataclass
class RuleAuditRecord:
    """Single rule application audit record"""
    rule_id: str
    rule_name: str
    trigger_condition: str
    trigger_description: str
    input_parameters: List[Dict[str, Any]]
    deviation_percentage: Optional[float]
    severity_applied: str
    confidence_score: int
    timestamp: str
    audit_hash: str = ""
    
    def to_dict(self):
        return asdict(self)


class AuditTrailManager:
    """Manages audit trail creation and retrieval"""
    
    # Comprehensive rule registry
    RULE_REGISTRY = {
        # Hematological rules
        "HEMO-LOW-01": {
            "name": "Hemoglobin Below Reference Minimum",
            "category": "Hematological",
            "description": "Triggered when hemoglobin value falls below reference range minimum"
        },
        "HEMO-HIGH-01": {
            "name": "Hemoglobin Above Reference Maximum",
            "category": "Hematological",
            "description": "Triggered when hemoglobin exceeds reference range maximum"
        },
        "HEMO-CRIT-01": {
            "name": "Critical Hemoglobin Deficiency",
            "category": "Hematological",
            "description": "Triggered when hemoglobin drops below critical threshold"
        },
        "WBC-HIGH-01": {
            "name": "Elevated White Blood Cell Count",
            "category": "Hematological",
            "description": "Triggered when WBC count exceeds reference maximum"
        },
        "WBC-LOW-01": {
            "name": "Decreased White Blood Cell Count",
            "category": "Hematological",
            "description": "Triggered when WBC count falls below reference minimum"
        },
        "PLAT-LOW-01": {
            "name": "Low Platelet Count",
            "category": "Hematological",
            "description": "Triggered when platelet count is below reference minimum"
        },
        "PLAT-HIGH-01": {
            "name": "Elevated Platelet Count",
            "category": "Hematological",
            "description": "Triggered when platelet count exceeds reference maximum"
        },
        
        # Metabolic rules
        "GLUC-HIGH-01": {
            "name": "Elevated Fasting Glucose",
            "category": "Metabolic",
            "description": "Triggered when fasting glucose exceeds reference maximum"
        },
        "GLUC-LOW-01": {
            "name": "Low Fasting Glucose",
            "category": "Metabolic",
            "description": "Triggered when fasting glucose falls below reference minimum"
        },
        "GLUC-CRIT-01": {
            "name": "Critical Glucose Level",
            "category": "Metabolic",
            "description": "Triggered when glucose reaches critical threshold"
        },
        "HBA1-HIGH-01": {
            "name": "Elevated Glycated Hemoglobin",
            "category": "Metabolic",
            "description": "Triggered when HbA1C exceeds reference maximum"
        },
        
        # Thyroid rules
        "TSH-HIGH-01": {
            "name": "Elevated TSH (Hypothyroid Pattern)",
            "category": "Thyroid Function",
            "description": "Triggered when TSH exceeds upper reference limit"
        },
        "TSH-LOW-01": {
            "name": "Suppressed TSH (Hyperthyroid Pattern)",
            "category": "Thyroid Function",
            "description": "Triggered when TSH falls below lower reference limit"
        },
        "FT4-HIGH-01": {
            "name": "Elevated Free T4",
            "category": "Thyroid Function",
            "description": "Triggered when FT4 exceeds reference maximum"
        },
        "FT4-LOW-01": {
            "name": "Low Free T4",
            "category": "Thyroid Function",
            "description": "Triggered when FT4 falls below reference minimum"
        },
        
        # Renal rules
        "CREA-HIGH-01": {
            "name": "Elevated Creatinine",
            "category": "Renal Function",
            "description": "Triggered when creatinine exceeds reference maximum"
        },
        "CREA-CRIT-01": {
            "name": "Critical Creatinine Elevation",
            "category": "Renal Function",
            "description": "Triggered when creatinine reaches critical threshold"
        },
        "BUN-HIGH-01": {
            "name": "Elevated Blood Urea Nitrogen",
            "category": "Renal Function",
            "description": "Triggered when BUN exceeds reference maximum"
        },
        
        # Lipid rules
        "CHOL-HIGH-01": {
            "name": "Elevated Total Cholesterol",
            "category": "Cardiovascular",
            "description": "Triggered when total cholesterol exceeds reference maximum"
        },
        "LDL-HIGH-01": {
            "name": "Elevated LDL Cholesterol",
            "category": "Cardiovascular",
            "description": "Triggered when LDL cholesterol exceeds reference maximum"
        },
        "HDL-LOW-01": {
            "name": "Low HDL Cholesterol",
            "category": "Cardiovascular",
            "description": "Triggered when HDL cholesterol falls below reference minimum"
        },
        "TRIG-HIGH-01": {
            "name": "Elevated Triglycerides",
            "category": "Cardiovascular",
            "description": "Triggered when triglycerides exceed reference maximum"
        },
        
        # Liver rules
        "SGOT-HIGH-01": {
            "name": "Elevated SGOT/AST",
            "category": "Hepatic",
            "description": "Triggered when SGOT/AST exceeds reference maximum"
        },
        "SGPT-HIGH-01": {
            "name": "Elevated SGPT/ALT",
            "category": "Hepatic",
            "description": "Triggered when SGPT/ALT exceeds reference maximum"
        },
    }
    
    def create_audit_record(
        self,
        parameter_name: str,
        parameter_value: Any,
        reference_range: str,
        status: str,
        severity: str,
        deviation_pct: Optional[float],
        confidence: int
    ) -> RuleAuditRecord:
        """
        Create an audit record for a parameter classification
        """
        # Generate rule ID
        rule_id = self._generate_rule_id(parameter_name, status, severity)
        
        # Get rule info from registry
        rule_info = self.RULE_REGISTRY.get(rule_id, {
            "name": f"{parameter_name} {status}",
            "category": "General",
            "description": f"Standard {status} classification for {parameter_name}"
        })
        
        # Format trigger condition
        trigger_condition = self._format_trigger_condition(
            parameter_name, parameter_value, reference_range, status
        )
        
        # Create input parameters list
        input_params = [{
            "name": parameter_name,
            "value": parameter_value,
            "reference_range": reference_range,
            "status": status
        }]
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Create audit hash for integrity
        audit_hash = self._generate_audit_hash(
            rule_id, parameter_name, str(parameter_value), timestamp
        )
        
        # Create record
        return RuleAuditRecord(
            rule_id=rule_id,
            rule_name=rule_info["name"],
            trigger_condition=trigger_condition,
            trigger_description=rule_info["description"],
            input_parameters=input_params,
            deviation_percentage=deviation_pct,
            severity_applied=severity,
            confidence_score=confidence,
            timestamp=timestamp,
            audit_hash=audit_hash
        )
    
    def _generate_rule_id(self, param: str, status: str, severity: str) -> str:
        """Generate standardized rule ID"""
        # Parameter prefix mapping
        prefix_map = {
            "Hemoglobin": "HEMO",
            "WBC Count": "WBC",
            "Platelet Count": "PLAT",
            "RBC Count": "RBC",
            "Fasting Blood Glucose": "GLUC",
            "Glucose Post Prandial": "GLUC",
            "HbA1C": "HBA1",
            "TSH": "TSH",
            "FT4": "FT4",
            "FT3": "FT3",
            "Creatinine": "CREA",
            "BUN": "BUN",
            "Total Cholesterol": "CHOL",
            "LDL Cholesterol": "LDL",
            "HDL Cholesterol": "HDL",
            "Triglycerides": "TRIG",
            "SGOT": "SGOT",
            "SGPT": "SGPT",
        }
        
        prefix = prefix_map.get(param, param[:4].upper().replace(" ", ""))
        
        # Status code
        status_code = status[:4].upper()
        
        # Severity number
        severity_num = "01"
        if severity == "CRITICAL":
            severity_num = "99"
        elif severity == "HIGH":
            severity_num = "02"
        
        return f"{prefix}-{status_code}-{severity_num}"
    
    def _format_trigger_condition(
        self, param: str, value: Any, ref_range: str, status: str
    ) -> str:
        """Format human-readable trigger condition"""
        if status == "LOW":
            return f"{param} ({value}) < Reference Minimum"
        elif status == "HIGH":
            return f"{param} ({value}) > Reference Maximum"
        elif status == "CRITICAL":
            return f"{param} ({value}) exceeds Critical Threshold"
        else:
            return f"{param} ({value}) within expected range"
    
    def _generate_audit_hash(self, *components) -> str:
        """Generate integrity hash for audit record"""
        combined = "|".join(str(c) for c in components)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
