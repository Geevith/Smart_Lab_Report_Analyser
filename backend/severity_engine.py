"""
Severity Engine
Calculates severity levels and action priorities for lab abnormalities
"""

from typing import Dict, Any, Tuple, Optional
import re

class SeverityEngine:
    """Manages severity scoring and action level categorization"""
    
    # Severity thresholds based on deviation percentage
    SEVERITY_THRESHOLDS = {
        "CRITICAL": 100,  # >100% deviation
        "HIGH": 50,       # 50-100% deviation
        "MEDIUM": 20,     # 20-50% deviation
        "LOW": 0          # <20% deviation
    }
    
    # Parameters that always require urgent attention when abnormal
    CRITICAL_PARAMETERS = {
        "Potassium": ["High", "Low"],
        "Sodium": ["Low"],  # Severe hyponatremia is dangerous
        "Platelet Count": ["Low"],  # Severe thrombocytopenia 
        "WBC Count": ["Low"],  # Severe leukopenia
        "Creatinine": ["High"]  # Kidney function
    }
    
    def calculate_severity(
        self,
        parameter: str,
        status: str,
        value: Optional[float] = None,
        reference_range: Optional[str] = None,
        deviation_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate severity level for an abnormal parameter
        
        Args:
            parameter: Parameter name
            status: Status (High/Low/Critical)
            value: Actual value
            reference_range: Reference range string
            deviation_pct: Pre-calculated deviation percentage
            
        Returns:
            Dict with severity, action_level, visual_priority, priority_score
        """
        # Calculate deviation if not provided
        if deviation_pct is None and value is not None and reference_range:
            deviation_pct = self._calculate_deviation_percentage(value, reference_range, status)
        
        # Check if this is a critical parameter
        if parameter in self.CRITICAL_PARAMETERS:
            if status in self.CRITICAL_PARAMETERS[parameter]:
                return {
                    "severity": "CRITICAL",
                    "action_level": "URGENT",
                    "visual_priority": 1,
                    "priority_score": 100,
                    "reason": "Critical parameter requiring immediate attention"
                }
        
        # Status-based critical check
        if status == "Critical":
            return {
                "severity": "CRITICAL",
                "action_level": "URGENT",
                "visual_priority": 1,
                "priority_score": 95,
                "reason": "Marked as critical by analysis"
            }
        
        # Deviation-based severity
        if deviation_pct is not None:
            severity = self._severity_from_deviation(deviation_pct)
            action_level = self._action_level_from_severity(severity)
            visual_priority = self._visual_priority_from_severity(severity)
            priority_score = min(100, deviation_pct)
            
            return {
                "severity": severity,
                "action_level": action_level,
                "visual_priority": visual_priority,
                "priority_score": priority_score,
                "reason": f"{deviation_pct:.1f}% deviation from reference range"
            }
        
        # Default medium severity
        return {
            "severity": "MEDIUM",
            "action_level": "MONITOR",
            "visual_priority": 3,
            "priority_score": 50,
            "reason": "Outside reference range"
        }
    
    def get_action_level(self, severity: str) -> str:
        """
        Get action level from severity
        
        Args:
            severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
            
        Returns:
            Action level: URGENT, MONITOR, or INFORMATIONAL
        """
        return self._action_level_from_severity(severity)
    
    def get_visual_hierarchy(self, severity: str) -> Dict[str, Any]:
        """
        Get visual styling information for severity level
        
        Args:
            severity: Severity level
            
        Returns:
            Dict with color, icon, badge_text, etc.
        """
        visual_map = {
            "CRITICAL": {
                "color": "red",
                "bg_color": "#FEE2E2",
                "border_color": "#DC2626",
                "text_color": "#991B1B",
                "dark_bg": "#7F1D1D",
                "dark_border": "#DC2626",
                "dark_text": "#FCA5A5",
                "icon": "error",
                "badge_text": "URGENT",
                "badge_bg": "#DC2626",
                "priority": 1,
                "pulse": True
            },
            "HIGH": {
                "color": "orange",
                "bg_color": "#FED7AA",
                "border_color": "#EA580C",
                "text_color": "#C2410C",
                "dark_bg": "#7C2D12",
                "dark_border": "#EA580C",
                "dark_text": "#FDBA74",
                "icon": "warning",
                "badge_text": "MONITOR",
                "badge_bg": "#EA580C",
                "priority": 2,
                "pulse": False
            },
            "MEDIUM": {
                "color": "yellow",
                "bg_color": "#FEF3C7",
                "border_color": "#D97706",
                "text_color": "#92400E",
                "dark_bg": "#78350F",
                "dark_border": "#D97706",
                "dark_text": "#FCD34D",
                "icon": "info",
                "badge_text": "MONITOR",
                "badge_bg": "#D97706",
                "priority": 3,
                "pulse": False
            },
            "LOW": {
                "color": "blue",
                "bg_color": "#DBEAFE",
                "border_color": "#3B82F6",
                "text_color": "#1E40AF",
                "dark_bg": "#1E3A8A",
                "dark_border": "#3B82F6",
                "dark_text": "#93C5FD",
                "icon": "info",
                "badge_text": "INFO",
                "badge_bg": "#3B82F6",
                "priority": 4,
                "pulse": False
            }
        }
        
        return visual_map.get(severity, visual_map["MEDIUM"])
    
    def _calculate_deviation_percentage(
        self,
        value: float,
        reference_range: str,
        status: str
    ) -> Optional[float]:
        """Calculate percentage deviation from reference range"""
        try:
            # Parse range - expect format like "70-100" or "13.0-17.0"
            range_match = re.search(r'([\d.]+)\s*-\s*([\d.]+)', reference_range)
            
            if range_match:
                min_val = float(range_match.group(1))
                max_val = float(range_match.group(2))
                
                if status == "Low" and value < min_val:
                    return abs((value - min_val) / min_val) * 100
                elif status == "High" and value > max_val:
                    return abs((value - max_val) / max_val) * 100
            
            return None
        except (ValueError, AttributeError):
            return None
    
    def _severity_from_deviation(self, deviation_pct: float) -> str:
        """Map deviation percentage to severity level"""
        if deviation_pct >= self.SEVERITY_THRESHOLDS["CRITICAL"]:
            return "CRITICAL"
        elif deviation_pct >= self.SEVERITY_THRESHOLDS["HIGH"]:
            return "HIGH"
        elif deviation_pct >= self.SEVERITY_THRESHOLDS["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _action_level_from_severity(self, severity: str) -> str:
        """Map severity to action level"""
        action_map = {
            "CRITICAL": "URGENT",
            "HIGH": "MONITOR",
            "MEDIUM": "MONITOR",
            "LOW": "INFORMATIONAL"
        }
        return action_map.get(severity, "MONITOR")
    
    def _visual_priority_from_severity(self, severity: str) -> int:
        """Map severity to visual priority (1=highest)"""
        priority_map = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4
        }
        return priority_map.get(severity, 3)


# Singleton instance
_severity_engine = None

def get_severity_engine() -> SeverityEngine:
    """Get singleton severity engine instance"""
    global _severity_engine
    if _severity_engine is None:
        _severity_engine = SeverityEngine()
    return _severity_engine
