"""
Unit tests for audit_trail.py module
Tests audit trail generation and rule registry
"""

import unittest
from datetime import datetime
from backend.audit_trail import AuditTrailManager, RuleAuditRecord


class TestAuditTrailManager(unittest.TestCase):
    """Test suite for audit trail manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = AuditTrailManager()
    
    def test_create_audit_record_hemoglobin_low(self):
        """Test creating audit record for low hemoglobin"""
        record = self.manager.create_audit_record(
            parameter_name="Hemoglobin",
            parameter_value=11.5,
            reference_range="13.0 - 17.0",
            status="LOW",
            severity="MEDIUM",
            deviation_pct=11.5,
            confidence=75
        )
        
        self.assertIsInstance(record, RuleAuditRecord)
        self.assertEqual(record.rule_id, "HEMO-LOW-01")
        self.assertIn("Hemoglobin", record.rule_name)
        self.assertIn("11.5", record.trigger_condition)
        self.assertEqual(record.severity_applied, "MEDIUM")
        self.assertEqual(record.confidence_score, 75)
        self.assertEqual(record.deviation_percentage, 11.5)
    
    def test_create_audit_record_glucose_high(self):
        """Test creating audit record for high glucose"""
        record = self.manager.create_audit_record(
            parameter_name="Fasting Blood Glucose",
            parameter_value=140,
            reference_range="< 100",
            status="HIGH",
            severity="MEDIUM",
            deviation_pct=40.0,
            confidence=80
        )
        
        self.assertEqual(record.rule_id, "GLUC-HIGH-01")
        self.assertIn("Glucose", record.rule_name)
        self.assertIn("140", record.trigger_condition)
    
    def test_audit_record_timestamp(self):
        """Test that audit record has valid timestamp"""
        record = self.manager.create_audit_record(
            parameter_name="Hemoglobin",
            parameter_value=11.5,
            reference_range="13.0 - 17.0",
            status="LOW",
            severity="LOW",
            deviation_pct=11.5,
            confidence=70
        )
        
        # Should be valid ISO format
        try:
            dt = datetime.fromisoformat(record.timestamp)
            self.assertIsInstance(dt, datetime)
        except ValueError:
            self.fail("Timestamp should be valid ISO format")
    
    def test_audit_hash_generation(self):
        """Test that audit hash is generated"""
        record = self.manager.create_audit_record(
            parameter_name="Hemoglobin",
            parameter_value=11.5,
            reference_range="13.0 - 17.0",
            status="LOW",
            severity="LOW",
            deviation_pct=11.5,
            confidence=70
        )
        
        self.assertIsNotNone(record.audit_hash)
        self.assertEqual(len(record.audit_hash), 16,
                        "Audit hash should be 16 characters")
    
    def test_audit_hash_uniqueness(self):
        """Test that different records get different hashes"""
        record1 = self.manager.create_audit_record(
            parameter_name="Hemoglobin",
            parameter_value=11.5,
            reference_range="13.0 - 17.0",
            status="LOW",
            severity="LOW",
            deviation_pct=11.5,
            confidence=70
        )
        
        record2 = self.manager.create_audit_record(
            parameter_name="Glucose",
            parameter_value=140,
            reference_range="< 100",
            status="HIGH",
            severity="MEDIUM",
            deviation_pct=40.0,
            confidence=80
        )
        
        self.assertNotEqual(record1.audit_hash, record2.audit_hash,
                           "Different records should have different hashes")
    
    def test_rule_registry_coverage(self):
        """Test that rule registry has good coverage"""
        registry = self.manager.RULE_REGISTRY
        
        # Should have at least 20 rules
        self.assertGreaterEqual(len(registry), 20,
                               "Should have comprehensive rule coverage")
        
        # Check structure of registry entries
        for rule_id, rule_info in registry.items():
            self.assertIn("name", rule_info)
            self.assertIn("category", rule_info)
            self.assertIn("description", rule_info)
    
    def test_generate_rule_id_standard_params(self):
        """Test rule ID generation for standard parameters"""
        rule_id = self.manager._generate_rule_id("Hemoglobin", "LOW", "MEDIUM")
        self.assertTrue(rule_id.startswith("HEMO-"),
                       "Should start with parameter prefix")
        self.assertIn("LOW", rule_id, "Should contain status")
    
    def test_generate_rule_id_critical_severity(self):
        """Test that critical severity gets special rule number"""
        rule_id = self.manager._generate_rule_id("Hemoglobin", "LOW", "CRITICAL")
        self.assertTrue(rule_id.endswith("-99"),
                       "Critical severity should end with -99")
    
    def test_format_trigger_condition_low(self):
        """Test trigger condition formatting for LOW status"""
        condition = self.manager._format_trigger_condition(
            "Hemoglobin",
            11.5,
            "13.0 - 17.0",
            "LOW"
        )
        
        self.assertIn("11.5", condition)
        self.assertIn("<", condition)
        self.assertIn("Minimum", condition)
    
    def test_format_trigger_condition_high(self):
        """Test trigger condition formatting for HIGH status"""
        condition = self.manager._format_trigger_condition(
            "Glucose",
            140,
            "< 100",
            "HIGH"
        )
        
        self.assertIn("140", condition)
        self.assertIn(">", condition)
        self.assertIn("Maximum", condition)
    
    def test_audit_record_to_dict(self):
        """Test converting audit record to dictionary"""
        record = self.manager.create_audit_record(
            parameter_name="Hemoglobin",
            parameter_value=11.5,
            reference_range="13.0 - 17.0",
            status="LOW",
            severity="LOW",
            deviation_pct=11.5,
            confidence=70
        )
        
        record_dict = record.to_dict()
        
        self.assertIsInstance(record_dict, dict)
        self.assertIn("rule_id", record_dict)
        self.assertIn("timestamp", record_dict)
        self.assertIn("audit_hash", record_dict)
        self.assertEqual(record_dict["rule_id"], record.rule_id)


if __name__ == '__main__':
    unittest.main()
