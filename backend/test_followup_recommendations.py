"""
Unit tests for followup_recommendations.py module
Tests follow-up test recommendation generation
"""

import unittest
from backend.followup_recommendations import (
    get_followup_recommendations,
    FOLLOWUP_TESTS,
    FollowUpRecommendation
)


class TestFollowUpRecommendations(unittest.TestCase):
    """Test suite for follow-up recommendations module"""
    
    def test_get_recommendations_for_low_hemoglobin(self):
        """Test recommendations for low hemoglobin"""
        params = {
            "Hemoglobin": {
                "value": 11.0,
                "status": "LOW",
                "severity": "MEDIUM"
            }
        }
        
        recs = get_followup_recommendations(params)
        
        self.assertEqual(len(recs), 1, "Should generate one recommendation")
        rec = recs[0]
        
        self.assertEqual(rec.parameter_name, "Hemoglobin")
        self.assertIn("Iron Profile", rec.suggested_tests)
        self.assertIn("Vitamin B12", rec.suggested_tests)
        self.assertEqual(rec.priority, "medium")
        self.assertIn("anemia", rec.rationale.lower())
    
    def test_get_recommendations_for_high_glucose(self):
        """Test recommendations for high glucose"""
        params = {
            "Fasting Blood Glucose": {
                "value": 140,
                "status": "HIGH",
                "severity": "MEDIUM"
            }
        }
        
        recs = get_followup_recommendations(params)
        
        self.assertGreater(len(recs), 0, "Should generate recommendation")
        rec = recs[0]
        
        self.assertEqual(rec.parameter_name, "Fasting Blood Glucose")
        self.assertIn("HbA1C", rec.suggested_tests)
        self.assertEqual(rec.priority, "high")
    
    def test_get_recommendations_multiple_params(self):
        """Test recommendations for multiple abnormal parameters"""
        params = {
            "Hemoglobin": {
                "value": 11.0,
                "status": "LOW",
                "severity": "MEDIUM"
            },
            "TSH": {
                "value": 8.0,
                "status": "HIGH",
                "severity": "HIGH"
            },
            "LDL Cholesterol": {
                "value": 160,
                "status": "HIGH",
                "severity": "MEDIUM"
            }
        }
        
        recs = get_followup_recommendations(params)
        
        self.assertEqual(len(recs), 3, "Should generate 3 recommendations")
        
        # Check they're sorted by priority
        priorities = [rec.priority for rec in recs]
        # Convert to numeric for comparison
        priority_nums = [{"high": 0, "medium": 1, "low": 2}[p] for p in priorities]
        self.assertEqual(priority_nums, sorted(priority_nums),
                        "Should be sorted by priority (high first)")
    
    def test_get_recommendations_normal_params(self):
        """Test that normal parameters don't generate recommendations"""
        params = {
            "Hemoglobin": {
                "value": 15.0,
                "status": "NORMAL",
                "severity": "LOW"
            }
        }
        
        recs = get_followup_recommendations(params)
        self.assertEqual(len(recs), 0,
                        "Should not generate recommendations for normal params")
    
    def test_get_recommendations_empty_params(self):
        """Test behavior with empty parameters"""
        recs = get_followup_recommendations({})
        self.assertEqual(len(recs), 0, "Should return empty list")
    
    def test_recommendation_has_disclaimer(self):
        """Test that all recommendations have disclaimer"""
        params = {
            "Hemoglobin": {
                "value": 11.0,
                "status": "LOW",
                "severity": "MEDIUM"
            }
        }
        
        recs = get_followup_recommendations(params)
        rec = recs[0]
        
        self.assertIsNotNone(rec.disclaimer, "Should have disclaimer")
        self.assertIn("healthcare provider", rec.disclaimer.lower(),
                     "Disclaimer should mention healthcare provider")
    
    def test_priority_ordering(self):
        """Test that high priority comes before medium and low"""
        params = {
            "Vitamin D": {
                "value": 15,
                "status": "LOW",
                "severity": "LOW"
            },
            "Creatinine": {
                "value": 2.5,
                "status": "HIGH",
                "severity": "HIGH"
            },
            "Total Cholesterol": {
                "value": 240,
                "status": "HIGH",
                "severity": "MEDIUM"
            }
        }
        
        recs = get_followup_recommendations(params)
        
        # Creatinine should be first (high priority)
        self.assertEqual(recs[0].priority, "high")
        self.assertEqual(recs[0].parameter_name, "Creatinine")
    
    def test_followup_tests_coverage(self):
        """Test that we have reasonable coverage of parameters"""
        # Count how many parameter+status combinations we support
        covered_params = set()
        for key in FOLLOWUP_TESTS.keys():
            param_name, status = key
            covered_params.add(param_name)
        
        # Should cover at least 15 different parameters
        self.assertGreaterEqual(len(covered_params), 15,
                               "Should have comprehensive parameter coverage")
    
    def test_test_list_not_empty(self):
        """Test that each recommendation has at least one test"""
        for key, data in FOLLOWUP_TESTS.items():
            self.assertGreater(len(data["tests"]), 0,
                             f"Tests list should not be empty for {key}")
    
    def test_rationale_exists(self):
        """Test that each recommendation has a rationale"""
        for key, data in FOLLOWUP_TESTS.items():
            self.assertIsNotNone(data["rationale"],
                               f"Rationale should exist for {key}")
            self.assertGreater(len(data["rationale"]), 10,
                             f"Rationale should be meaningful for {key}")


class TestFollowUpRecommendationDataClass(unittest.TestCase):
    """Test the FollowUpRecommendation dataclass"""
    
    def test_create_recommendation(self):
        """Test creating recommendation instance"""
        rec = FollowUpRecommendation(
            parameter_name="Hemoglobin",
            suggested_tests=["Iron Profile", "Vitamin B12"],
            rationale="To identify cause of anemia",
            priority="medium"
        )
        
        self.assertEqual(rec.parameter_name, "Hemoglobin")
        self.assertEqual(len(rec.suggested_tests), 2)
        self.assertEqual(rec.priority, "medium")
        self.assertIn("healthcare provider", rec.disclaimer.lower())


if __name__ == '__main__':
    unittest.main()
