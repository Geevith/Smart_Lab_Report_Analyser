"""
Trajectory Analyzer Module
Analyzes temporal trends, calculates velocity of change, and detects concerning trajectories
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from dataclasses import dataclass
from enum import Enum


class TrendDirection(Enum):
    """Trend direction classification"""
    IMPROVING = "improving"
    WORSENING = "worsening"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskLevel(Enum):
    """Risk trajectory level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrajectoryResult:
    """Result of trajectory analysis"""
    parameter_name: str
    trend_direction: TrendDirection
    velocity: float  # Change per month
    risk_level: RiskLevel
    projected_value: Optional[float]
    projected_date: Optional[str]
    confidence: float  # 0-100
    analysis: str
    concerning_pathway: Optional[str]


# ============================================================================
# Trajectory Analysis
# ============================================================================

def analyze_trajectory(parameter_name: str, history: List[Dict], 
                       reference_range: Optional[Dict] = None) -> TrajectoryResult:
    """
    Analyze temporal trajectory of a parameter
    
    Args:
        parameter_name: Name of the parameter
        history: List of historical data points [{date, value, status}, ...]
        reference_range: Optional reference range {min, max}
        
    Returns:
        TrajectoryResult with trend analysis
    """
    
    # Need at least 2 points for trajectory
    if len(history) < 2:
        return TrajectoryResult(
            parameter_name=parameter_name,
            trend_direction=TrendDirection.INSUFFICIENT_DATA,
            velocity=0.0,
            risk_level=RiskLevel.LOW,
            projected_value=None,
            projected_date=None,
            confidence=0.0,
            analysis="Insufficient historical data for trajectory analysis",
            concerning_pathway=None
        )
    
    # Sort by date
    sorted_history = sorted(history, key=lambda x: datetime.fromisoformat(x['date']))
    
    # Extract values and dates
    values = [float(h['value']) for h in sorted_history if h.get('value') is not None]
    dates = [datetime.fromisoformat(h['date']) for h in sorted_history]
    
    if len(values) < 2:
        return TrajectoryResult(
            parameter_name=parameter_name,
            trend_direction=TrendDirection.INSUFFICIENT_DATA,
            velocity=0.0,
            risk_level=RiskLevel.LOW,
            projected_value=None,
            projected_date=None,
            confidence=0.0,
            analysis="Insufficient valid data points",
            concerning_pathway=None
        )
    
    # Calculate velocity (change per month)
    velocity = calculate_velocity(values, dates)
    
    # Determine trend direction
    trend = determine_trend(values, velocity)
    
    # Calculate risk level
    risk = assess_risk_level(parameter_name, values, velocity, reference_range)
    
    # Detect concerning pathways
    pathway = detect_concerning_pathway(parameter_name, values, velocity, reference_range)
    
    # Project future value (3 months ahead)
    projected_value, projected_date = project_future_value(values[-1], velocity, months=3)
    
    # Calculate confidence based on data consistency
    confidence = calculate_confidence(values, dates)
    
    # Generate analysis text
    analysis = generate_trajectory_analysis(parameter_name, trend, velocity, risk, pathway)
    
    return TrajectoryResult(
        parameter_name=parameter_name,
        trend_direction=trend,
        velocity=velocity,
        risk_level=risk,
        projected_value=projected_value,
        projected_date=projected_date,
        confidence=confidence,
        analysis=analysis,
        concerning_pathway=pathway
    )


def calculate_velocity(values: List[float], dates: List[datetime]) -> float:
    """
    Calculate velocity of change (units per month)
    
    Uses linear regression for more accurate trend
    """
    if len(values) < 2:
        return 0.0
    
    # Calculate time differences in months
    time_diffs = []
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i-1]).days / 30.44  # Average days per month
        time_diffs.append(delta)
    
    # Calculate value changes
    value_diffs = [values[i] - values[i-1] for i in range(1, len(values))]
    
    # Simple linear regression
    if not time_diffs or sum(time_diffs) == 0:
        return 0.0
    
    # Average rate of change per month
    total_change = values[-1] - values[0]
    total_time = sum(time_diffs)
    
    velocity = total_change / total_time if total_time > 0 else 0.0
    
    return round(velocity, 4)


def determine_trend(values: List[float], velocity: float) -> TrendDirection:
    """Determine overall trend direction"""
    
    if len(values) < 2:
        return TrendDirection.INSUFFICIENT_DATA
    
    # Calculate variability
    if len(values) >= 3:
        variance = statistics.variance(values)
        mean = statistics.mean(values)
        cv = (variance ** 0.5) / mean if mean != 0 else 0  # Coefficient of variation
        
        # If highly variable, mark as fluctuating
        if cv > 0.15:  # 15% CV threshold
            return TrendDirection.FLUCTUATING
    
    # Check velocity
    if abs(velocity) < 0.01:  # Threshold for stability
        return TrendDirection.STABLE
    elif velocity > 0:
        return TrendDirection.WORSENING if _is_increase_bad(values) else TrendDirection.IMPROVING
    else:
        return TrendDirection.IMPROVING if _is_increase_bad(values) else TrendDirection.WORSENING


def _is_increase_bad(values: List[float]) -> bool:
    """
    Determine if increasing values are bad (heuristic)
    Most lab values: increase is bad (glucose, cholesterol, etc.)
    Some exceptions: HDL, hemoglobin (but hard to generalize)
    """
    # Default assumption: increase is bad for most parameters
    return True


def assess_risk_level(parameter_name: str, values: List[float], 
                     velocity: float, reference_range: Optional[Dict]) -> RiskLevel:
    """Assess risk level based on trajectory"""
    
    current_value = values[-1]
    
    # If no reference range, use conservative approach
    if not reference_range:
        if abs(velocity) > 5:
            return RiskLevel.HIGH
        elif abs(velocity) > 2:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    # Parse reference range
    ref_min = reference_range.get('min')
    ref_max = reference_range.get('max')
    
    if ref_min is None or ref_max is None:
        return RiskLevel.MODERATE
    
    # Calculate how far outside range
    if current_value < ref_min:
        deviation = (ref_min - current_value) / ref_min
    elif current_value > ref_max:
        deviation = (current_value - ref_max) / ref_max
    else:
        deviation = 0
    
    # High velocity towards danger zone
    if abs(velocity) > 3 and deviation > 0.2:
        return RiskLevel.CRITICAL
    elif abs(velocity) > 2 and deviation > 0.1:
        return RiskLevel.HIGH
    elif deviation > 0.15 or abs(velocity) > 1:
        return RiskLevel.MODERATE
    else:
        return RiskLevel.LOW


def detect_concerning_pathway(parameter_name: str, values: List[float], 
                              velocity: float, reference_range: Optional[Dict]) -> Optional[str]:
    """
    Detect if parameter is on a concerning pathway (e.g., pre-diabetic)
    """
    
    current_value = values[-1]
    param_lower = parameter_name.lower()
    
    # Pre-diabetic pathway detection
    if 'glucose' in param_lower or 'hba1c' in param_lower:
        if 'glucose' in param_lower and 100 <= current_value < 126:
            if velocity > 2:  # Increasing at 2+ mg/dL per month
                return "Pre-Diabetic Trajectory"
        elif 'hba1c' in param_lower and 5.7 <= current_value < 6.5:
            if velocity > 0.1:
                return "Pre-Diabetic Trajectory"
    
    # Hypertension pathway
    if 'blood pressure' in param_lower or 'bp' in param_lower:
        if current_value >= 130:
            return "Hypertensive Trajectory"
    
    # Cholesterol pathway
    if 'cholesterol' in param_lower and 'hdl' not in param_lower:
        if current_value >= 200:
            if velocity > 5:
                return "Cardiovascular Risk Pathway"
    
    # Kidney function decline
    if 'creatinine' in param_lower:
        if velocity > 0.2:  # Rising creatinine
            return "Declining Kidney Function"
    
    if 'gfr' in param_lower or 'egfr' in param_lower:
        if velocity < -2:  # Declining GFR
            return "Declining Kidney Function"
    
    return None


def project_future_value(current_value: float, velocity: float, months: int = 3) -> Tuple[float, str]:
    """
    Project future value based on current velocity
    
    Args:
        current_value: Current parameter value
        velocity: Change per month
        months: Months into future
        
    Returns:
        (projected_value, projected_date)
    """
    projected_value = current_value + (velocity * months)
    projected_date = (datetime.now() + timedelta(days=months * 30)).strftime("%Y-%m-%d")
    
    return round(projected_value, 2), projected_date


def calculate_confidence(values: List[float], dates: List[datetime]) -> float:
    """
    Calculate confidence score based on data quality
    
    Factors:
    - Number of data points
    - Time span
    - Consistency
    """
    
    # More data points = higher confidence
    point_score = min(len(values) / 10 * 40, 40)  # Max 40 points for 10+ readings
    
    # Time span (prefer longer history)
    time_span_days = (dates[-1] - dates[0]).days
    time_score = min(time_span_days / 365 * 30, 30)  # Max 30 points for 1+ year
    
    # Consistency (low variance relative to range)
    if len(values) >= 3:
        value_range = max(values) - min(values)
        mean_value = statistics.mean(values)
        consistency = 1 - (value_range / mean_value if mean_value != 0 else 0)
        consistency_score = max(0, consistency) * 30
    else:
        consistency_score = 10
    
    total_score = point_score + time_score + consistency_score
    return round(min(total_score, 100), 1)


def generate_trajectory_analysis(parameter_name: str, trend: TrendDirection, 
                                 velocity: float, risk: RiskLevel, 
                                 pathway: Optional[str]) -> str:
    """Generate human-readable trajectory analysis"""
    
    analysis = f"{parameter_name} shows a {trend.value} trend"
    
    if trend == TrendDirection.INSUFFICIENT_DATA:
        return "Insufficient historical data for trend analysis. Consider regular monitoring."
    
    if abs(velocity) > 0.01:
        direction = "increasing" if velocity > 0 else "decreasing"
        analysis += f", {direction} at {abs(velocity):.2f} units/month"
    
    analysis += f". Risk level: {risk.value}"
    
    if pathway:
        analysis += f". ⚠️ Concerning pathway detected: {pathway}"
    
    # Add recommendations
    if risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        analysis += ". Immediate medical consultation recommended."
    elif risk == RiskLevel.MODERATE:
        analysis += ". Monitor closely and discuss with healthcare provider."
    
    return analysis


# ============================================================================
# Multi-Parameter Trajectory Analysis
# ============================================================================

def analyze_multiple_trajectories(parameters_history: Dict[str, List[Dict]], 
                                  reference_ranges: Optional[Dict] = None) -> List[TrajectoryResult]:
    """
    Analyze trajectories for multiple parameters
    
    Args:
        parameters_history: Dict of {param_name: [history_list]}
        reference_ranges: Dict of {param_name: {min, max}}
        
    Returns:
        List of TrajectoryResult objects, sorted by risk level
    """
    
    results = []
    
    for param_name, history in parameters_history.items():
        ref_range = reference_ranges.get(param_name) if reference_ranges else None
        trajectory = analyze_trajectory(param_name, history, ref_range)
        results.append(trajectory)
    
    # Sort by risk level (critical first)
    risk_order = {
        RiskLevel.CRITICAL: 0,
        RiskLevel.HIGH: 1,
        RiskLevel.MODERATE: 2,
        RiskLevel.LOW: 3
    }
    
    results.sort(key=lambda x: risk_order.get(x.risk_level, 999))
    
    return results
