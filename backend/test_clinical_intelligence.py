"""
Unit tests for clinical_intelligence.py module
Tests context-aware insight generation and confidence calculation
"""

import unittest
from backend.clinical_intelligence import (
    generate_contextual_insights,
    calculate_insight_confidence,
    _calculate_deviation_percentage,
    _find_contextual_pattern,
    _create_isolated_insight
)


class TestClinicalIntelligence(unittest.TestCase):
    """Test suite for clinical intelligence module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_params = {
            "Hemoglobin": {
                "value": 12.2,
                "unit": "g/dL",
                "range": "13.0 - 17.0",
                "status": "LOW",
                "severity": "LOW"
            },
            "Platelet Count": {
                "value": 250000,
                "unit": "/µL",
                "range": "150000 - 400000",
                "status": "NORMAL",
                "severity": "LOW"
            },
            "MCV": {
                "value": 78,
                "unit": "fL",
                "range": "80 - 100",
                "status": "LOW",
                "severity": "LOW"
            }
        }
    
    def test_generate_contextual_insights_with_pattern(self):
        """Test that contextual patterns are detected"""
        insights = generate_contextual_insights(self.sample_params)
        
        self.assertGreater(len(insights), 0, "Should generate at least one insight")
        
        # Check for contextual insight (Hgb LOW + Platelet NORMAL)
        hgb_insight = next((i for i in insights if i.parameter == "Hemoglobin"), None)
        self.assertIsNotNone(hgb_insight, "Should generate hemoglobin insight")
        
        # Should be contextual type due to normal platelets
        if hgb_insight.insight_type == "contextual":
            self.assertIn("Platelet Count", hgb_insight.supporting_params,
                         "Should include platelet count as supporting parameter")
    
    def test_generate_contextual_insights_isolated(self):
        """Test isolated insight generation when no pattern matches"""
        isolated_param = {
            "Uric Acid": {
                "value": 8.5,
                "unit": "mg/dL",
                "range": "3.5 - 7.2",
                "status": "HIGH",
                "severity": "MEDIUM"
            }
        }
        
        insights = generate_contextual_insights(isolated_param)
        self.assertEqual(len(insights), 1, "Should generate one insight")
        
        insight = insights[0]
        self.assertEqual(insight.parameter, "Uric Acid")
        self.assertEqual(len(insight.supporting_params), 0,
                        "Isolated insight should have no supporting params")
    
    def test_calculate_insight_confidence_high_deviation(self):
        """Test confidence calculation with high deviation"""
        param_data = {
            "value": 150,
            "range": "70 - 100"
        }
        
        confidence, rationale = calculate_insight_confidence(param_data, supporting_abnormal_count=2)
        
        self.assertGreaterEqual(confidence, 70, "High deviation should give high confidence")
        self.assertLessEqual(confidence, 95, "Confidence should be capped at 95%")
        self.assertIn("50", rationale, "Should mention deviation percentage")
    
    def test_calculate_insight_confidence_low_deviation(self):
        """Test confidence calculation with low deviation"""
        param_data = {
            "value": 102,
            "range": "70 - 100"
        }
        
        confidence, rationale = calculate_insight_confidence(param_data, supporting_abnormal_count=0)
        
        self.assertLess(confidence, 75, "Low deviation should give lower confidence")
        self.assertGreaterEqual(confidence, 50, "Should still have base confidence")
    
    def test_calculate_deviation_percentage_high_value(self):
        """Test deviation calculation for values above range"""
        param_data = {
            "value": 150,
            "range": "70 - 100"
        }
        
        deviation = _calculate_deviation_percentage(param_data)
        
        self.assertIsNotNone(deviation, "Should calculate deviation")
        self.assertAlmostEqual(deviation, 50.0, delta=1.0,
                              msg="150 is 50% above 100")
    
    def test_calculate_deviation_percentage_low_value(self):
        """Test deviation calculation for values below range"""
        param_data = {
            "value": 60,
            "range": "70 - 100"
        }
        
        deviation = _calculate_deviation_percentage(param_data)
        
        self.assertIsNotNone(deviation, "Should calculate deviation")
        self.assertAlmostEqual(deviation, 14.3, delta=1.0,
                              msg="60 is ~14.3% below 70")
    
    def test_calculate_deviation_percentage_invalid_range(self):
        """Test deviation with invalid range format"""
        param_data = {
            "value": 100,
            "range": "Invalid"
        }
        
        deviation = _calculate_deviation_percentage(param_data)
        self.assertIsNone(deviation, "Should return None for invalid range")
    
    def test_contextual_insight_confidence_higher_than_isolated(self):
        """Test that contextual insights have higher confidence than isolated"""
        # Simulate contextual vs isolated
        param_with_support = {
            "value": 120,
            "range": "70 - 100"
        }
        
        conf_contextual, _ = calculate_insight_confidence(param_with_support, supporting_abnormal_count=2)
        conf_isolated, _ = calculate_insight_confidence(param_with_support, supporting_abnormal_count=0)
        
        self.assertGreater(conf_contextual, conf_isolated,
                          "Contextual insight should have higher confidence")
    
    def test_generate_insights_empty_params(self):
        """Test behavior with empty parameters"""
        insights = generate_contextual_insights({})
        self.assertEqual(len(insights), 0, "Should return empty list for no parameters")
    
    def test_generate_insights_normal_params_only(self):
        """Test that normal parameters don't generate insights"""
        normal_params = {
            "Hemoglobin": {
                "value": 15.0,
                "status": "NORMAL",
                "severity": "LOW"
            }
        }
        
        insights = generate_contextual_insights(normal_params)
        self.assertEqual(len(insights), 0,
                        "Should not generate insights for normal parameters")


class TestContextualPatterns(unittest.TestCase):
    """Test specific contextual pattern matching"""
    
    def test_hemoglobin_mcv_pattern(self):
        """Test Hemoglobin + MCV pattern detection"""
        params = {
            "Hemoglobin": {
                "value": 11.5,
                "status": "LOW",
                "severity": "MEDIUM"
            },
            "MCV": {
                "value": 75,
                "status": "LOW",
                "severity": "LOW"
            }
        }
        
        insights = generate_contextual_insights(params)
        hgb_insight = next((i for i in insights if i.parameter == "Hemoglobin"), None)
        
        self.assertIsNotNone(hgb_insight)
        if hgb_insight and hgb_insight.insight_type == "contextual":
            self.assertIn("microcytic", hgb_insight.message.lower(),
                         "Should mention microcytic anemia")
    
    def test_glucose_hba1c_pattern(self):
        """Test Glucose + HbA1C pattern detection"""
        params = {
            "Fasting Blood Glucose": {
                "value": 130,
                "status": "HIGH",
                "severity": "MEDIUM"
            },
            "HbA1C": {
                "value": 7.5,
                "status": "HIGH",
                "severity": "MEDIUM"
            }
        }
        
        insights = generate_contextual_insights(params)
        
        # Should get insights for both
        self.assertGreaterEqual(len(insights), 1,
                               "Should generate insights for diabetic pattern")


if __name__ == '__main__':
    unittest.main()
