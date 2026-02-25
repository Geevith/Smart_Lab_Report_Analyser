"""
Unit tests for historical_context.py module
Tests trend analysis and historical context generation
"""

import unittest
from backend.historical_context import (
    calculate_trend,
    format_historical_values_for_display,
    TrendAnalysis,
    TrendDirection
)


class TestHistoricalContext(unittest.TestCase):
    """Test suite for historical context module"""
    
    def test_calculate_trend_improving(self):
        """Test trend analysis for improving values (LOW status increasing)"""
        historical_values = [
            {"value": 11.0, "date": "2026-01-01"},
            {"value": 11.5, "date": "2026-01-15"}
        ]
        
        trend = calculate_trend(
            current_value=12.2,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="LOW"
        )
        
        self.assertIsInstance(trend, TrendAnalysis)
        self.assertEqual(trend.trend_direction, TrendDirection.IMPROVING.value)
        self.assertTrue(trend.display_chart)
    
    def test_calculate_trend_worsening(self):
        """Test trend analysis for worsening values (HIGH status increasing)"""
        historical_values = [
            {"value": 100, "date": "2026-01-01"},
            {"value": 110, "date": "2026-01-15"}
        ]
        
        trend = calculate_trend(
            current_value=125,
            previous_values=historical_values,
            parameter_name="Glucose",
            current_status="HIGH"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.WORSENING.value)
        self.assertTrue(trend.display_chart)
    
    def test_calculate_trend_stable(self):
        """Test trend analysis for stable values"""
        historical_values = [
            {"value": 100, "date": "2026-01-01"}
        ]
        
        trend = calculate_trend(
            current_value=101,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="NORMAL"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.STABLE.value)
    
    def test_calculate_trend_insufficient_data(self):
        """Test that insufficient data returns appropriate status"""
        trend = calculate_trend(
            current_value=100,
            previous_values=[],
            parameter_name="Hemoglobin",
            current_status="NORMAL"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.INSUFFICIENT_DATA.value)
        self.assertFalse(trend.display_chart)
    
    def test_format_historical_values(self):
        """Test formatting of historical values for display"""
        history = [
            {"value": 12.0, "unit": "g/dL", "date": "2026-01-01"},
            {"value": 11.5, "unit": "g/dL", "date": "2025-12-15"}
        ]
        
        formatted = format_historical_values_for_display(
            history=history,
            current_value=12.5,
            current_date="2026-02-01"
        )
        
        # Should include current + history
        self.assertGreaterEqual(len(formatted), 3)
        
        # First entry should be current
        self.assertIn("Current", formatted[0]["formatted_date"])
    
    def test_context_message_generation(self):
        """Test that context messages are generated"""
        historical_values = [
            {"value": 11.0, "date": "2026-01-01"}
        ]
        
        trend = calculate_trend(
            current_value=12.2,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="LOW"
        )
        
        self.assertIsNotNone(trend.context_message)
        self.assertGreater(len(trend.context_message), 10)
        self.assertIn("Hemoglobin", trend.context_message)
    
    def test_improving_direction_for_low_values(self):
        """Test that increasing values are improving when status is LOW"""
        historical_values = [
            {"value": 10.0, "date": "2026-01-01"}
        ]
        
        trend = calculate_trend(
            current_value=11.5,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="LOW"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.IMPROVING.value)
    
    def test_worsening_direction_for_low_values(self):
        """Test that decreasing values are worsening when status is LOW"""
        historical_values = [
            {"value": 11.5, "date": "2026-01-01"}
        ]
        
        trend = calculate_trend(
            current_value=10.0,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="LOW"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.WORSENING.value)
    
    def test_improving_direction_for_high_values(self):
        """Test that decreasing values are improving when status is HIGH"""
        historical_values = [
            {"value": 140, "date": "2026-01-01"}
        ]
        
        trend = calculate_trend(
            current_value=130,
            previous_values=historical_values,
            parameter_name="Glucose",
            current_status="HIGH"
        )
        
        self.assertEqual(trend.trend_direction, TrendDirection.IMPROVING.value)
    
    def test_multiple_historical_points(self):
        """Test trend calculation with multiple historical data points"""
        historical_values = [
            {"value": 11.0, "date": "2026-01-01"},
            {"value": 11.3, "date": "2026-01-10"},
            {"value": 11.7, "date": "2026-01-20"}
        ]
        
        trend = calculate_trend(
            current_value=12.2,
            previous_values=historical_values,
            parameter_name="Hemoglobin",
            current_status="LOW"
        )
        
        # Should use trend analysis with multiple points
        self.assertEqual(len(trend.previous_values), 3)
        self.assertTrue(trend.display_chart)


class TestTrendDirection(unittest.TestCase):
    """Test TrendDirection enum"""
    
    def test_trend_direction_values(self):
        """Test that TrendDirection has all expected values"""
        self.assertEqual(TrendDirection.IMPROVING.value, "improving")
        self.assertEqual(TrendDirection.STABLE.value, "stable")
        self.assertEqual(TrendDirection.WORSENING.value, "worsening")
        self.assertEqual(TrendDirection.INSUFFICIENT_DATA.value, "insufficient_data")


if __name__ == '__main__':
    unittest.main()
