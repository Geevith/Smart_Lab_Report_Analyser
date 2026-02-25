import unittest
from backend.interpretation import generate_insights, DISCLAIMER

class TestInterpretation(unittest.TestCase):
    def test_normal_insights(self):
        analysis_results = {
            "Hemoglobin": {"value": 14.0, "status": "Normal"},
            "WBC Count": {"value": 6000, "status": "Normal"}
        }
        result = generate_insights(analysis_results)
        self.assertEqual(result["summary"], "Blood test parameters appear within standard reference ranges.")
        self.assertEqual(len(result["detailed_insights"]), 0)
        self.assertIn("disclaimer", result)
        self.assertEqual(result["disclaimer"], DISCLAIMER)

    def test_abnormal_insights(self):
        analysis_results = {
            "Hemoglobin": {"value": 11.0, "status": "Low"},
            "WBC Count": {"value": 15000, "status": "High"}
        }
        result = generate_insights(analysis_results)
        self.assertTrue("Flagged 2 parameter(s)" in result["summary"])
        self.assertEqual(len(result["detailed_insights"]), 2)
        
        # Check content
        insights_text = [item["insight"] for item in result["detailed_insights"]]
        # Check for safe language
        self.assertTrue(any("associated with anemia" in t for t in insights_text))
        self.assertTrue(any("sign of the body reacting" in t for t in insights_text))
        
        # Check disclaimer
        self.assertIn(DISCLAIMER, result["disclaimer"])

    def test_unknown_abnormality(self):
        analysis_results = {
            "RandomParam": {"value": 100, "status": "High"}
        }
        result = generate_insights(analysis_results)
        self.assertTrue("Flagged 1 parameter(s)" in result["summary"])
        self.assertTrue("discuss this result with your doctor" in result["detailed_insights"][0]["insight"])

if __name__ == '__main__':
    unittest.main()
