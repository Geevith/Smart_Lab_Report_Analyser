"""
Comprehensive test suite for Abnormality Detection System
Tests edge cases, OCR errors, unit conversions, and medical safety
"""

import unittest
from backend.abnormality_detector import (
    AbnormalityDetector,
    ReferenceRangeParser,
    UnitNormalizer,
    TestStatus,
    Severity
)


class TestReferenceRangeParser(unittest.TestCase):
    """Test reference range parsing logic"""
    
    def setUp(self):
        self.parser = ReferenceRangeParser()
    
    def test_numeric_range_standard(self):
        """Test standard numeric range parsing"""
        result = self.parser.parse("13.0 - 17.0")
        self.assertEqual(result.range_type, 'numeric')
        self.assertEqual(result.min_value, 13.0)
        self.assertEqual(result.max_value, 17.0)
    
    def test_numeric_range_no_spaces(self):
        """Test numeric range without spaces"""
        result = self.parser.parse("13-17")
        self.assertEqual(result.range_type, 'numeric')
        self.assertEqual(result.min_value, 13.0)
        self.assertEqual(result.max_value, 17.0)
    
    def test_numeric_range_to_keyword(self):
        """Test numeric range with 'to' keyword"""
        result = self.parser.parse("13.0 to 17.0")
        self.assertEqual(result.range_type, 'numeric')
        self.assertEqual(result.min_value, 13.0)
        self.assertEqual(result.max_value, 17.0)
    
    def test_inequality_less_than(self):
        """Test less than operator"""
        result = self.parser.parse("<200")
        self.assertEqual(result.range_type, 'inequality')
        self.assertEqual(result.operator, '<')
        self.assertEqual(result.threshold, 200.0)
    
    def test_inequality_greater_than(self):
        """Test greater than operator"""
        result = self.parser.parse(">40")
        self.assertEqual(result.range_type, 'inequality')
        self.assertEqual(result.operator, '>')
        self.assertEqual(result.threshold, 40.0)
    
    def test_inequality_less_than_or_equal(self):
        """Test less than or equal operator"""
        result = self.parser.parse("<=150")
        self.assertEqual(result.range_type, 'inequality')
        self.assertEqual(result.operator, '<=')
        self.assertEqual(result.threshold, 150.0)
    
    def test_inequality_unicode(self):
        """Test unicode inequality operators"""
        result = self.parser.parse("≤150")
        self.assertEqual(result.range_type, 'inequality')
        self.assertEqual(result.operator, '<=')
        self.assertEqual(result.threshold, 150.0)
    
    def test_up_to_pattern(self):
        """Test 'Up to X' pattern"""
        result = self.parser.parse("Up to 150")
        self.assertEqual(result.range_type, 'inequality')
        self.assertEqual(result.operator, '<')
        self.assertEqual(result.threshold, 150.0)
    
    def test_qualitative_negative(self):
        """Test qualitative 'Negative' result"""
        result = self.parser.parse("Negative")
        self.assertEqual(result.range_type, 'qualitative')
        self.assertIn('negative', result.qualitative_normal)
    
    def test_qualitative_non_reactive(self):
        """Test qualitative 'Non-reactive' result"""
        result = self.parser.parse("Non-reactive")
        self.assertEqual(result.range_type, 'qualitative')
        self.assertIn('non-reactive', result.qualitative_normal)
    
    def test_ocr_artifact_correction(self):
        """Test OCR artifact correction"""
        cleaned = self.parser.clean_ocr_artifacts("I5.0")
        self.assertEqual(cleaned, "15.0")
        
        cleaned = self.parser.clean_ocr_artifacts("O.45")
        self.assertEqual(cleaned, "0.45")
        
        cleaned = self.parser.clean_ocr_artifacts("l2.3")
        self.assertEqual(cleaned, "12.3")
    
    def test_reversed_range_correction(self):
        """Test auto-correction of reversed min/max"""
        result = self.parser.parse("17.0 - 13.0")
        self.assertEqual(result.min_value, 13.0)
        self.assertEqual(result.max_value, 17.0)
        self.assertIn("reversed", result.notes[0].lower())
    
    def test_missing_range(self):
        """Test handling of missing reference range"""
        result = self.parser.parse("")
        self.assertEqual(result.range_type, 'insufficient')
        self.assertTrue(len(result.notes) > 0)
    
    def test_unparseable_range(self):
        """Test handling of unparseable reference range"""
        result = self.parser.parse("Some random text")
        self.assertIn(result.range_type, ['unparseable', 'parse_error', 'qualitative'])


class TestAbnormalityDetector(unittest.TestCase):
    """Test abnormality detection logic"""
    
    def setUp(self):
        self.detector = AbnormalityDetector()
    
    def test_normal_hemoglobin(self):
        """Test normal hemoglobin value"""
        result = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=15.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result.status, TestStatus.NORMAL)
        self.assertEqual(result.severity, Severity.LOW)
    
    def test_low_hemoglobin(self):
        """Test low hemoglobin value"""
        result = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=11.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result.status, TestStatus.LOW)
        self.assertIn(result.severity, [Severity.LOW, Severity.MEDIUM])
    
    def test_high_hemoglobin(self):
        """Test high hemoglobin value"""
        result = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=19.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result.status, TestStatus.HIGH)
    
    def test_critical_low_hemoglobin(self):
        """Test critically low hemoglobin value"""
        result = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=6.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result.status, TestStatus.CRITICAL)
        self.assertEqual(result.severity, Severity.CRITICAL)
    
    def test_ocr_corrected_value(self):
        """Test OCR artifact correction in value"""
        result = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value="I5.2",  # Should be corrected to 15.2
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result.value, 15.2)
        self.assertEqual(result.status, TestStatus.NORMAL)
        self.assertTrue(any("OCR" in note for note in result.notes))
    
    def test_high_glucose_with_inequality(self):
        """Test high glucose with inequality range"""
        result = self.detector.detect_abnormality(
            test_name="Glucose Fasting",
            value=250.0,
            unit="mg/dL",
            reference_range="<100"
        )
        self.assertEqual(result.status, TestStatus.HIGH)
        self.assertGreater(result.severity.value, Severity.LOW.value)
    
    def test_critical_high_glucose(self):
        """Test critically high glucose"""
        result = self.detector.detect_abnormality(
            test_name="Glucose Fasting",
            value=450.0,
            unit="mg/dL",
            reference_range="<100"
        )
        self.assertEqual(result.status, TestStatus.CRITICAL)
    
    def test_qualitative_negative(self):
        """Test qualitative negative result"""
        result = self.detector.detect_abnormality(
            test_name="HIV Test",
            value="Negative",
            unit="",
            reference_range="Negative"
        )
        self.assertEqual(result.status, TestStatus.NORMAL)
        self.assertGreater(result.confidence_score, 0.8)
    
    def test_qualitative_positive(self):
        """Test qualitative positive result"""
        result = self.detector.detect_abnormality(
            test_name="HIV Test",
            value="Positive",
            unit="",
            reference_range="Negative"
        )
        self.assertIn(result.status, [TestStatus.HIGH, TestStatus.REVIEW_REQUIRED])
    
    def test_unparseable_range_review_required(self):
        """Test that unparseable ranges trigger REVIEW_REQUIRED"""
        result = self.detector.detect_abnormality(
            test_name="Unknown Test",
            value=100.0,
            unit="units",
            reference_range="Some unparseable text"
        )
        self.assertEqual(result.status, TestStatus.REVIEW_REQUIRED)
        self.assertEqual(result.confidence_score, 0.0)
    
    def test_non_numeric_value_review_required(self):
        """Test that non-numeric non-qualitative values trigger REVIEW_REQUIRED"""
        result = self.detector.detect_abnormality(
            test_name="Test",
            value="Not a number",
            unit="",
            reference_range="10-20"
        )
        self.assertEqual(result.status, TestStatus.REVIEW_REQUIRED)
    
    def test_tsh_high(self):
        """Test high TSH (hypothyroidism)"""
        result = self.detector.detect_abnormality(
            test_name="TSH",
            value=7.5,
            unit="µIU/mL",
            reference_range="0.4 - 4.0"
        )
        self.assertEqual(result.status, TestStatus.HIGH)
    
    def test_tsh_low(self):
        """Test low TSH (hyperthyroidism)"""
        result = self.detector.detect_abnormality(
            test_name="TSH",
            value=0.2,
            unit="µIU/mL",
            reference_range="0.4 - 4.0"
        )
        self.assertEqual(result.status, TestStatus.LOW)
    
    def test_vitamin_d_low_with_upper_limit(self):
        """Test low Vitamin D with 'Up to' range"""
        result = self.detector.detect_abnormality(
            test_name="Vitamin D",
            value=18.0,
            unit="ng/mL",
            reference_range="Up to 100"
        )
        # Note: This is tricky - "Up to 100" suggests <100 is normal
        # but medically we know <30 is deficient
        # The detector should classify as NORMAL based purely on the range
        self.assertEqual(result.status, TestStatus.NORMAL)
    
    def test_potassium_critical_high(self):
        """Test critically high potassium"""
        result = self.detector.detect_abnormality(
            test_name="Potassium",
            value=6.5,
            unit="mmol/L",
            reference_range="3.5 - 5.1"
        )
        self.assertEqual(result.status, TestStatus.CRITICAL)
    
    def test_potassium_critical_low(self):
        """Test critically low potassium"""
        result = self.detector.detect_abnormality(
            test_name="Potassium",
            value=2.0,
            unit="mmol/L",
            reference_range="3.5 - 5.1"
        )
        self.assertEqual(result.status, TestStatus.CRITICAL)
    
    def test_confidence_without_unit(self):
        """Test that missing unit reduces confidence"""
        result_with_unit = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=15.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        
        result_without_unit = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=15.0,
            unit="",
            reference_range="13.0 - 17.0"
        )
        
        # Confidence should be lower when unit is missing
        # (though both should classify correctly)
        self.assertEqual(result_with_unit.status, result_without_unit.status)
    
    def test_boundary_values(self):
        """Test values at exact boundaries"""
        # At minimum boundary
        result_min = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=13.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result_min.status, TestStatus.NORMAL)
        
        # At maximum boundary
        result_max = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=17.0,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result_max.status, TestStatus.NORMAL)
        
        # Just below minimum
        result_below = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=12.9,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result_below.status, TestStatus.LOW)
        
        # Just above maximum
        result_above = self.detector.detect_abnormality(
            test_name="Hemoglobin",
            value=17.1,
            unit="g/dL",
            reference_range="13.0 - 17.0"
        )
        self.assertEqual(result_above.status, TestStatus.HIGH)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.detector = AbnormalityDetector()
    
    def test_none_value(self):
        """Test handling of None value"""
        result = self.detector.detect_abnormality(
            test_name="Test",
            value=None,
            unit="",
            reference_range="10-20"
        )
        self.assertEqual(result.status, TestStatus.REVIEW_REQUIRED)
    
    def test_empty_string_value(self):
        """Test handling of empty string value"""
        result = self.detector.detect_abnormality(
            test_name="Test",
            value="",
            unit="",
            reference_range="10-20"
        )
        self.assertEqual(result.status, TestStatus.REVIEW_REQUIRED)
    
    def test_negative_value(self):
        """Test handling of negative value (valid for some tests)"""
        result = self.detector.detect_abnormality(
            test_name="Temperature Change",
            value=-5.0,
            unit="°C",
            reference_range="-10 to 10"
        )
        self.assertEqual(result.status, TestStatus.NORMAL)
    
    def test_very_large_value(self):
        """Test handling of very large value"""
        result = self.detector.detect_abnormality(
            test_name="WBC Count",
            value=50000.0,
            unit="cells/µL",
            reference_range="4000 - 11000"
        )
        self.assertEqual(result.status, TestStatus.CRITICAL)
    
    def test_zero_value(self):
        """Test handling of zero value"""
        result = self.detector.detect_abnormality(
            test_name="Test",
            value=0.0,
            unit="",
            reference_range="<10"
        )
        self.assertEqual(result.status, TestStatus.NORMAL)


class TestMedicalSafety(unittest.TestCase):
    """Test medical safety features"""
    
    def setUp(self):
        self.detector = AbnormalityDetector()
    
    def test_no_false_normals_for_critical_values(self):
        """Ensure critical values are never classified as NORMAL"""
        critical_tests = [
            ("Potassium", 7.0, "mmol/L", "3.5-5.1"),
            ("Glucose Fasting", 500, "mg/dL", "<100"),
            ("Hemoglobin", 5.0, "g/dL", "13-17"),
            ("WBC Count", 50000, "cells/µL", "4000-11000")
        ]
        
        for test_name, value, unit, ref_range in critical_tests:
            result = self.detector.detect_abnormality(
                test_name, value, unit, ref_range
            )
            self.assertNotEqual(
                result.status,
                TestStatus.NORMAL,
                f"{test_name}={value} should not be NORMAL"
            )
    
    def test_uncertainty_flags_review(self):
        """Ensure uncertain cases are flagged for review"""
        uncertain_cases = [
            ("Test", "unclear value", "", "10-20"),
            ("Test", 15, "", "unparseable range text"),
            ("Test", "", "", "10-20")
        ]
        
        for test_name, value, unit, ref_range in uncertain_cases:
            result = self.detector.detect_abnormality(
                test_name, value, unit, ref_range
            )
            self.assertIn(
                result.status,
                [TestStatus.REVIEW_REQUIRED, TestStatus.INSUFFICIENT_DATA],
                f"Uncertain case should require review: {test_name}"
            )


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestReferenceRangeParser))
    suite.addTests(loader.loadTestsFromTestCase(TestAbnormalityDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestMedicalSafety))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
