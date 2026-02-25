"""
Historical Context & Trend Analysis
Provides temporal context for parameter interpretation
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

class TrendDirection(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    trend_direction: str
    previous_values: List[Dict[str, Any]]
    context_message: str
    display_chart: bool
    disclaimer: str = "Historical comparison is contextual support, not clinical conclusion"


def calculate_trend(
    current_value: float,
    previous_values: List[Dict[str, Any]],
    parameter_name: str,
    current_status: str
) -> TrendAnalysis:
    """
    Calculate trend direction and impact on current insight
    
    Args:
        current_value: Latest parameter value
        previous_values: List of historical values with timestamps
                        [{"date": "2025-12-15", "value": 12.8}, ...]
        parameter_name: Name of the parameter
        current_status: Current classification (HIGH, LOW, NORMAL)
    
    Returns:
        TrendAnalysis object with direction, impact, and context
    """
    if not previous_values or len(previous_values) < 1:
        return TrendAnalysis(
            trend_direction=TrendDirection.INSUFFICIENT_DATA.value,
            previous_values=[],
            context_message="No historical data available for comparison",
            display_chart=False
        )
    
    # Sort by date (oldest first)
    sorted_values = sorted(previous_values, key=lambda x: x.get("date", ""))
    
    if len(sorted_values) < 2:
        # Only one previous value - simple comparison
        prev_val = sorted_values[0]["value"]
        direction = _determine_direction_simple(
            current_value, prev_val, current_status
        )
    else:
        # Multiple values - calculate trend
        direction = _determine_direction_trend(
            current_value, sorted_values, current_status
        )
    
    # Generate context message
    context_message = _generate_context_message(
        parameter_name, current_value, sorted_values, direction, current_status
    )
    
    return TrendAnalysis(
        trend_direction=direction.value,
        previous_values=sorted_values,
        context_message=context_message,
        display_chart=len(sorted_values) >= 2
    )


def _determine_direction_simple(
    current: float, previous: float, status: str
) -> TrendDirection:
    """Determine direction from simple comparison"""
    if abs(current - previous) < 0.01:  # Essentially stable
        return TrendDirection.STABLE
    
    if status in ["HIGH", "CRITICAL"]:
        # For HIGH values, decreasing is improving
        if current < previous:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.WORSENING
    elif status == "LOW":
        # For LOW values, increasing is improving
        if current > previous:
            return TrendDirection.IMPROVING
        else:
            return TrendDirection.WORSENING
    else:
        return TrendDirection.STABLE


def _determine_direction_trend(
    current: float, history: List[Dict], status: str
) -> TrendDirection:
    """Determine direction from historical trend"""
    # Calculate average movement
    values = [h["value"] for h in history] + [current]
    
    # Simple linear regression slope
    n = len(values)
    x = list(range(n))
    y = values
    
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return TrendDirection.STABLE
    
    slope = numerator / denominator
    
    # Determine direction based on status and slope
    if abs(slope) < 0.1:  # Relatively flat
        return TrendDirection.STABLE
    
    if status in ["HIGH", "CRITICAL"]:
        # For HIGH values, negative slope is improving
        return TrendDirection.IMPROVING if slope < 0 else TrendDirection.WORSENING
    elif status == "LOW":
        # For LOW values, positive slope is improving
        return TrendDirection.IMPROVING if slope > 0 else TrendDirection.WORSENING
    else:
        return TrendDirection.STABLE


def _generate_context_message(
    param: str, current: float, history: List, direction: TrendDirection, status: str
) -> str:
    """Generate plain-language trend context"""
    if direction == TrendDirection.IMPROVING:
        return f"{param} is moving toward the reference range compared to previous results"
    elif direction == TrendDirection.WORSENING:
        return f"{param} has deviated further from the reference range since last measurement"
    elif direction == TrendDirection.STABLE:
        return f"{param} has remained relatively stable compared to previous results"
    else:
        return "No trend analysis available due to insufficient historical data"


def format_historical_values_for_display(
    history: List[Dict[str, Any]],
    current_value: float,
    current_date: str = None
) -> List[Dict[str, str]]:
    """
    Format historical values for UI display
    
    Returns:
        List of formatted records for display
        [{"date": "2025-12-15", "value": "12.8 g/dL", "formatted_date": "Dec 15, 2025"}, ...]
    """
    formatted = []
    
    for record in sorted(history, key=lambda x: x.get("date", ""), reverse=True):
        date_str = record.get("date", "Unknown")
        value = record.get("value", 0)
        unit = record.get("unit", "")
        
        # Format date nicely
        try:
            date_obj = datetime.fromisoformat(date_str)
            formatted_date = date_obj.strftime("%b %d, %Y")
        except:
            formatted_date = date_str
        
        formatted.append({
            "date": date_str,
            "value": f"{value} {unit}".strip(),
            "formatted_date": formatted_date
        })
    
    # Add current value
    if current_date is None:
        current_date = datetime.now().isoformat()
    
    try:
        current_date_obj = datetime.fromisoformat(current_date)
        current_formatted_date = current_date_obj.strftime("%b %d, %Y")
    except:
        current_formatted_date = "Current"
    
    formatted.insert(0, {
        "date": current_date,
        "value": f"{current_value}",
        "formatted_date": f"{current_formatted_date} (Current)"
    })
    
    return formatted
