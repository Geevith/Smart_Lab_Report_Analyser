import unittest
from backend.parser import parse_blood_test, PATTERNS, REFERENCE_RANGES

class TestParser(unittest.TestCase):
    def test_hemoglobin_normal(self):
        text = "Hemoglobin: 15.0 g/dL"
        result = parse_blood_test(text)
        self.assertIn("Hemoglobin", result)
        self.assertEqual(result["Hemoglobin"]["value"], 15.0)
        self.assertEqual(result["Hemoglobin"]["status"], "Normal")

    def test_hemoglobin_low(self):
        text = "Hb: 12.0"
        result = parse_blood_test(text)
        self.assertEqual(result["Hemoglobin"]["status"], "Low")

    def test_hemoglobin_high(self):
        text = "Hgb: 18.0"
        result = parse_blood_test(text)
        self.assertEqual(result["Hemoglobin"]["status"], "High")

    def test_multiple_parameters(self):
        text = """
        Hemoglobin 14.5
        WBC Count 8000
        Platelet Count 250000
        """
        result = parse_blood_test(text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result["WBC Count"]["value"], 8000)
        self.assertEqual(result["Platelet Count"]["status"], "Normal")

    def test_noisy_text(self):
        text = "Some random text. Erythrocyte Count: 5.0 million. More text."
        result = parse_blood_test(text)
        self.assertEqual(result["RBC Count"]["value"], 5.0)

    def test_case_insensitive(self):
        text = "plAtElEt cOuNt: 200000"
        result = parse_blood_test(text)
        self.assertIn("Platelet Count", result)

if __name__ == '__main__':
    unittest.main()
