"""
Pattern Detection Module
Statistical and rule-based pattern detection for lab reports without ML training overhead
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of patterns that can be detected"""
    TREND_RISING = "TREND_RISING"
    TREND_FALLING = "TREND_FALLING"
    TREND_ACCELERATING = "TREND_ACCELERATING"
    CLINICAL_TRAJECTORY = "CLINICAL_TRAJECTORY"
    STABILITY = "STABILITY"


@dataclass
class TrendPattern:
    """Detected trend pattern in lab results"""
    pattern_name: str
    pattern_type: PatternType
    affected_parameters: List[str]
    description: str
    confidence: float  # 0.0 to 1.0
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    timeframe: Optional[str] = None  # e.g., "3 months", "6 reports"
    rate_of_change: Optional[float] = None  # Units per timeframe
    recommendation: Optional[str] = None


class ClinicalPatternRules:
    """
    Pre-defined clinical pattern rules library
    These are evidence-based patterns that don't require ML training
    """
    
    # Clinical trajectory patterns (parameter moving toward diagnosis threshold)
    CLINICAL_TRAJECTORIES = {
        "pre_diabetic_trajectory": {
            "parameters": ["Fasting Blood Glucose", "HbA1C", "Glucose Post Prandial"],
            "thresholds": {
                "Fasting Blood Glucose": {"normal_max": 100, "prediabetic": 126, "diabetic": 126},
                "HbA1C": {"normal_max": 5.6, "pre diabetic": 6.5, "diabetic": 6.5},
                "Glucose Post Prandial": {"normal_max": 140, "prediabetic": 200, "diabetic": 200}
            },
            "pattern_name": "Pre-diabetic Trajectory",
            "description_template": "{param} has been trending upward from {start_val} to {end_val} over {timeframe}, approaching pre-diabetic range ({threshold}).",
            "severity": "MEDIUM"
        },
        "worsening_renal_function": {
            "parameters": ["Creatinine", "BUN"],
            "thresholds": {
                "Creatinine": {"normal_max": 1.2, "warning": 1.5, "concerning": 2.0},
                "BUN": {"normal_max": 20, "warning": 30, "concerning": 40}
            },
            "pattern_name": "Declining Renal Function",
            "description_template": "{param} shows progressive elevation from {start_val} to {end_val} over {timeframe}, suggesting declining kidney function.",
            "severity": "HIGH"
        },
        "progressive_anemia": {
            "parameters": ["Hemoglobin", "Hematocrit", "RBC Count"],
            "thresholds": {
                "Hemoglobin": {"normal_min_male": 13.0, "normal_min_female": 12.0, "mild_anemia": 11.0, "moderate_anemia": 9.0},
                "Hematocrit": {"normal_min_male": 40, "normal_min_female": 36, "mild_anemia": 33},
                "RBC Count": {"normal_min_male": 4.7, "normal_min_female": 4.2, "low": 4.0}
            },
            "pattern_name": "Progressive Anemia",
            "description_template": "{param} has been declining from {start_val} to {end_val} over {timeframe}, indicating worsening anemia.",
            "severity": "MEDIUM"
        },
        "lipid_deterioration": {
            "parameters": ["Total Cholesterol", "LDL Cholesterol", "Triglycerides"],
            "thresholds": {
                "Total Cholesterol": {"desirable": 200, "borderline": 240, "high": 240},
                "LDL Cholesterol": {"optimal": 100, "near_optimal": 130, "borderline": 160, "high": 190},
                "Triglycerides": {"normal": 150, "borderline": 200, "high": 500}
            },
            "pattern_name": "Worsening Lipid Profile",
            "description_template": "{param} trend from {start_val} to {end_val} over {timeframe} shows progressive increase in cardiovascular risk.",
            "severity": "MEDIUM"
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def match_patterns(
        self, 
        current_params: Dict[str, Any],
        historical_params: List[Dict[str, Any]]
    ) -> List[TrendPattern]:
        """
        Match clinical trajectory patterns based on current and historical data
        
        Args:
            current_params: Current lab results {param_name: {value, unit, status, ...}}
            historical_params: List of historical results, ordered oldest to newest
                              Each item: {param_name: {value, unit, timestamp, ...}}
        
        Returns:
            List of detected TrendPattern objects
        """
        detected_patterns = []
        
        if not historical_params or len(historical_params) < 2:
            #self.logger.info("Insufficient historical data for pattern matching (need at least 2 reports)")
            return []
        
        # Check each clinical trajectory
        for trajectory_id, trajectory_def in self.CLINICAL_TRAJECTORIES.items():
            for param in trajectory_def["parameters"]:
                pattern = self._check_trajectory(
                    param, current_params, historical_params, trajectory_def
                )
                if pattern:
                    detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _check_trajectory(
        self,
        param_name: str,
        current_params: Dict[str, Any],
        historical_params: List[Dict[str, Any]],
        trajectory_def: Dict
    ) -> Optional[TrendPattern]:
        """Check if parameter matches a clinical trajectory pattern"""
        
        # Extract historical values for this parameter
        historical_values = []
        for hist_report in historical_params:
            if param_name in hist_report:
                try:
                    val = float(hist_report[param_name].get("value", 0))
                    historical_values.append(val)
                except (ValueError, TypeError, AttributeError):
                    continue
        
        # Get current value
        current_val = None
        if param_name in current_params:
            try:
                current_val = float(current_params[param_name].get("value", 0))
            except (ValueError, TypeError, AttributeError):
                return None
        
        if not historical_values or current_val is None:
            return None
        
        # Need at least 2 historical points + current
        if len(historical_values) < 2:
            return None
        
        # Calculate trend
        start_val = historical_values[0]
        end_val = current_val
        
        # Check if trending in concerning direction
        thresholds = trajectory_def["thresholds"].get(param_name, {})
        
        # Determine if upward or downward trend is concerning
        is_upward_trend = end_val > start_val
        change_pct = abs((end_val - start_val) / start_val * 100) if start_val != 0 else 0
        
       # Minimum 5% change to be considered a trend
        if change_pct < 5:
            return None
        
        # Check if trend is clinically significant based on trajectory type
        is_significant = False
        severity = trajectory_def.get("severity", "MEDIUM")
        
        if "diabetic" in trajectory_def["pattern_name"].lower():
            # For diabetes: upward trend toward threshold is concerning
            normal_max = thresholds.get("normal_max", 0)
            if is_upward_trend and end_val > normal_max * 0.9:  # Approaching threshold
                is_significant = True
                if end_val > normal_max:
                    severity = "HIGH"
        
        elif "renal" in trajectory_def["pattern_name"].lower():
            # For renal: any upward trend is concerning
            if is_upward_trend and change_pct > 10:
                is_significant = True
                warning_threshold = thresholds.get("warning", float('inf'))
                if end_val > warning_threshold:
                    severity = "HIGH"
        
        elif "anemia" in trajectory_def["pattern_name"].lower():
            # For anemia: downward trend is concerning
            if not is_upward_trend and change_pct > 10:
                is_significant = True
                # Gender-aware threshold checking would go here
                min_threshold = min(thresholds.get("normal_min_male", 0), 
                                   thresholds.get("normal_min_female", 0))
                if end_val < min_threshold:
                    severity = "HIGH"
        
        elif "lipid" in trajectory_def["pattern_name"].lower():
            # For lipids: upward trend is concerning
            if is_upward_trend and change_pct > 10:
                is_significant = True
                borderline = thresholds.get("borderline", float('inf'))
                if end_val > borderline:
                    severity = "HIGH"
        
        if not is_significant:
            return None
        
        # Calculate confidence based on:
        # 1. Number of historical points
        # 2. Consistency of trend
        # 3. Magnitude of change
        confidence = min(0.5 + (len(historical_values) * 0.1) + (change_pct / 100), 0.95)
        
        # Generate description
        timeframe = f"{len(historical_params)} reports"
        direction = "increasing" if is_upward_trend else "decreasing"
        
        description = trajectory_def["description_template"].format(
            param=param_name,
            start_val=f"{start_val:.1f}",
            end_val=f"{end_val:.1f}",
            timeframe=timeframe,
            threshold=thresholds.get("normal_max", "") or thresholds.get("normal_min_male", "")
        )
        
        # Add recommendation
        recommendation = f"Monitor {param_name} closely and discuss trending pattern with healthcare provider."
        if severity == "HIGH":
            recommendation = f"Urgent medical consultation recommended due to {direction} {param_name}."
        
        return TrendPattern(
            pattern_name=trajectory_def["pattern_name"],
            pattern_type=PatternType.CLINICAL_TRAJECTORY,
            affected_parameters=[param_name],
            description=description,
            confidence=confidence,
            severity=severity,
            timeframe=timeframe,
            rate_of_change=(end_val - start_val) / len(historical_params),
            recommendation=recommendation
        )


class StatisticalPatternDetector:
    """
   Statistical pattern detection using simple statistical methods
    No ML training required
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.clinical_rules = ClinicalPatternRules()
    
    def detect_trend_patterns(
        self,
        current_params: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[TrendPattern]:
        """
        Detect trending patterns in lab results
        
        Args:
            current_params: Current lab results
            historical_data: List of previous lab results (oldest to newest)
        
        Returns:
            List of detected TrendPattern objects
        """
        patterns = []
        
        # Use clinical rules for pattern matching
        clinical_patterns = self.clinical_rules.match_patterns(
            current_params, historical_data
        )
        patterns.extend(clinical_patterns)
        
        return patterns


def detect_patterns_for_user(
    user_id: str,
    current_results: Dict[str, Any],
    historical_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main entry point for pattern detection
    
    Args:
        user_id: User identifier
        current_results: Current lab test results
        historical_results: Historical lab results (list of dicts)
    
    Returns:
        Dictionary with pattern detection results
    """
    detector = StatisticalPatternDetector()
    
    patterns = detector.detect_trend_patterns(current_results, historical_results)
    
    if not patterns:
        return {
            "has_patterns": False,
            "patterns": [],
            "summary": "No significant trending patterns detected at this time."
        }
    
    return {
        "has_patterns": True,
        "patterns": [
            {
                "name": p.pattern_name,
                "type": p.pattern_type.value,
                "parameters": p.affected_parameters,
                "description": p.description,
                "confidence": round(p.confidence * 100, 1),
                "severity": p.severity,
                "timeframe": p.timeframe,
                "recommendation": p.recommendation
            }
            for p in patterns
        ],
        "summary": f"Detected {len(patterns)} trending pattern(s) requiring attention."
    }
