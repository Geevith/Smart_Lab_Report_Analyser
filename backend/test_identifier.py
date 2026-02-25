"""
Intelligent Test Identification System

This module provides automatic test recognition and categorization using a knowledge base approach.
Supports alias mapping, fuzzy matching, and graceful unknown test handling.
"""

import json
import os
import re
from typing import Dict, List, Tuple, Optional
from difflib import get_close_matches


class TestKnowledgeBase:
    """Manages the master test knowledge base"""
    
    def __init__(self, kb_path: str = None):
        if kb_path is None:
            kb_path = os.path.join(os.path.dirname(__file__), 'test_knowledge_base.json')
        
        with open(kb_path, 'r', encoding='utf-8') as f:
            self.kb = json.load(f)
        
        # Build reverse alias mapping for fast lookup
        self.alias_to_test = {}
        for test_id, test_data in self.kb['tests'].items():
            # Add canonical name
            canonical_name = test_data['name'].lower().strip()
            self.alias_to_test[canonical_name] = test_id
            
            # Add all aliases
            for alias in test_data.get('aliases', []):
                alias_key = alias.lower().strip()
                self.alias_to_test[alias_key] = test_id
        
        # Build unit variants mapping
        self.unit_variants = {}
        for canonical_unit, variants in self.kb.get('unit_variants', {}).items():
            for variant in variants:
                self.unit_variants[variant.lower()] = canonical_unit
            # Add canonical form
            self.unit_variants[canonical_unit.lower()] = canonical_unit
    
    def get_test_by_id(self, test_id: str) -> Optional[Dict]:
        """Get test data by test_id"""
        return self.kb['tests'].get(test_id)
    
    def get_test_by_name(self, name: str) -> Optional[Tuple[str, Dict]]:
        """Get test data by name or alias"""
        normalized_name = name.lower().strip()
        test_id = self.alias_to_test.get(normalized_name)
        if test_id:
            return test_id, self.kb['tests'][test_id]
        return None
    
    def get_all_test_names(self) -> List[str]:
        """Get all test canonical names"""
        return [test['name'] for test in self.kb['tests'].values()]
    
    def get_panel(self, panel_name: str) -> Optional[Dict]:
        """Get panel definition"""
        return self.kb['panels'].get(panel_name)
    
    def normalize_unit(self, unit: str) -> Optional[str]:
        """Normalize unit to canonical form"""
        if not unit:
            return None
        return self.unit_variants.get(unit.lower().strip())
    
    def get_tests_by_category(self, category: str) -> List[str]:
        """Get all tests in a category"""
        return [
            test_id for test_id, test_data in self.kb['tests'].items()
            if test_data.get('category') == category
        ]


class IdentifiedTest:
    """Result of test identification"""
    
    def __init__(self, name: str, test_id: str, category: str, unit: str,
                 reference_range: Dict, confidence: str, panel: str = None,
                 related_conditions: List[str] = None, warning: str = None):
        self.name = name
        self.test_id = test_id
        self.category = category
        self.unit = unit
        self.reference_range = reference_range
        self.confidence = confidence
        self.panel = panel
        self.related_conditions = related_conditions or []
        self.warning = warning
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'test_id': self.test_id,
            'category': self.category,
            'unit': self.unit,
            'reference_range': self.reference_range,
            'confidence': self.confidence,
            'panel': self.panel,
            'related_conditions': self.related_conditions,
            'warning': self.warning
        }


class TestIdentifier:
    """Intelligent test identification engine"""
    
    def __init__(self, kb_path: str = None):
        self.kb = TestKnowledgeBase(kb_path)
    
    def identify(self, test_name: str, value: float = None, unit: str = None) -> IdentifiedTest:
        """
        Identify a test using multi-step logic:
        1. Direct name/alias matching
        2. Fuzzy matching
        3. Unit-based inference
        4. Unknown test handling
        """
        
        # Step 1: Direct matching
        result = self.kb.get_test_by_name(test_name)
        if result:
            test_id, test_data = result
            return self._create_identified_test(test_id, test_data, "High", unit)
        
        # Step 2: Fuzzy matching
        fuzzy_result = self._fuzzy_match(test_name)
        if fuzzy_result:
            test_id, test_data, match_score = fuzzy_result
            confidence = "High" if match_score > 0.9 else "Medium"
            
            # Verify unit if provided
            if unit:
                expected_unit = test_data.get('unit')
                normalized_unit = self.kb.normalize_unit(unit)
                normalized_expected = self.kb.normalize_unit(expected_unit)
                
                if normalized_unit and normalized_expected and normalized_unit != normalized_expected:
                    # Unit mismatch - downgrade confidence
                    confidence = "Low"
            
            return self._create_identified_test(test_id, test_data, confidence, unit)
        
        # Step 3: Unit-based inference
        inferred_category = self._infer_category(test_name, unit)
        
        # Step 4: Unknown test handling
        return IdentifiedTest(
            name=test_name,
            test_id=f"unknown_{test_name.lower().replace(' ', '_')}",
            category=inferred_category,
            unit=unit or "Unknown",
            reference_range={},
            confidence="Low",
            warning=f"Test '{test_name}' not found in knowledge base. Category inferred as '{inferred_category}'."
        )
    
    def _create_identified_test(self, test_id: str, test_data: Dict, 
                                confidence: str, provided_unit: str = None) -> IdentifiedTest:
        """Create IdentifiedTest from test data"""
        return IdentifiedTest(
            name=test_data['name'],
            test_id=test_id,
            category=test_data.get('category', 'Unknown'),
            unit=provided_unit or test_data.get('unit', 'Unknown'),
            reference_range=test_data.get('reference_range', {}),
            confidence=confidence,
            panel=test_data.get('panel'),
            related_conditions=test_data.get('related_conditions', [])
        )
    
    def _fuzzy_match(self, test_name: str, cutoff: float = 0.6) -> Optional[Tuple[str, Dict, float]]:
        """Fuzzy match test name against knowledge base"""
        all_names = []
        name_to_test_id = {}
        
        # Collect all names and aliases
        for test_id, test_data in self.kb.kb['tests'].items():
            canonical = test_data['name']
            all_names.append(canonical)
            name_to_test_id[canonical] = test_id
            
            for alias in test_data.get('aliases', []):
                all_names.append(alias)
                name_to_test_id[alias] = test_id
        
        # Find close matches
        matches = get_close_matches(test_name, all_names, n=1, cutoff=cutoff)
        
        if matches:
            matched_name = matches[0]
            test_id = name_to_test_id[matched_name]
            test_data = self.kb.get_test_by_id(test_id)
            
            # Calculate match score (similarity ratio)
            from difflib import SequenceMatcher
            score = SequenceMatcher(None, test_name.lower(), matched_name.lower()).ratio()
            
            return test_id, test_data, score
        
        return None
    
    def _infer_category(self, test_name: str, unit: str = None) -> str:
        """Infer test category from name and unit"""
        name_lower = test_name.lower()
        
        # Keyword-based inference
        category_keywords = {
            'Blood': ['blood', 'hemoglobin', 'hb', 'rbc', 'wbc', 'platelet'],
            'Liver': ['bilirubin', 'sgot', 'sgpt', 'alt', 'ast', 'liver', 'alp', 'ggt'],
            'Kidney': ['creatinine', 'bun', 'urea', 'kidney', 'renal'],
            'Diabetes': ['glucose', 'sugar', 'hba1c', 'a1c', 'diabetes'],
            'Lipids': ['cholesterol', 'triglyceride', 'hdl', 'ldl', 'lipid'],
            'Thyroid': ['thyroid', 'tsh', 'ft3', 'ft4', 't3', 't4'],
            'Electrolytes': ['sodium', 'potassium', 'chloride', 'electrolyte'],
            'Vitamins': ['vitamin', 'b12', 'vitamin d'],
            'Cardiac': ['cpk', 'ldh', 'troponin', 'cardiac', 'heart'],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return category
        
        # Unit-based inference
        if unit:
            normalized_unit = self.kb.normalize_unit(unit)
            unit_categories = {
                'g/dL': 'Blood',
                'mg/dL': 'Chemistry',
                'cells/µL': 'Blood',
                'U/L': 'Enzymes',
                'mmol/L': 'Electrolytes',
                'ng/mL': 'Hormones',
                '%': 'Blood'
            }
            if normalized_unit in unit_categories:
                return unit_categories[normalized_unit]
        
        return 'Unknown'


class PanelGrouper:
    """Groups identified tests into medical panels"""
    
    def __init__(self, kb: TestKnowledgeBase):
        self.kb = kb
    
    def group_tests(self, identified_tests: List[IdentifiedTest]) -> Dict[str, Dict]:
        """Group tests into panels and detect completeness"""
        panel_results = {}
        
        # Get all panels
        for panel_name, panel_data in self.kb.kb['panels'].items():
            expected_tests = set(panel_data['tests'])
            
            # Find detected tests in this panel
            detected_tests = [
                test for test in identified_tests
                if test.test_id in expected_tests
            ]
            
            if detected_tests:
                detected_ids = set(test.test_id for test in detected_tests)
                missing_ids = expected_tests - detected_ids
                
                # Get missing test names
                missing_names = [
                    self.kb.get_test_by_id(test_id)['name']
                    for test_id in missing_ids
                    if self.kb.get_test_by_id(test_id)
                ]
                
                panel_results[panel_name] = {
                    'name': panel_data['name'],
                    'detected': [test.name for test in detected_tests],
                    'missing': missing_names,
                    'completeness': len(detected_ids) / len(expected_tests),
                    'description': panel_data.get('description', '')
                }
        
        return panel_results


def identify_tests_from_text(text: str) -> Dict:
    """
    High-level function to identify all tests from extracted text
    
    Args:
        text: Extracted lab report text
    
    Returns:
        Dictionary with identified tests and panel groupings
    """
    identifier = TestIdentifier()
    
    # This is a placeholder - actual implementation would parse the text
    # For now, return the identifier for integration with parser
    return {
        'identifier': identifier,
        'message': 'Use identifier.identify(test_name, value, unit) to identify each test'
    }


# Example usage
if __name__ == "__main__":
    # Initialize identifier
    identifier = TestIdentifier()
    
    # Test direct matching
    print("=== Direct Matching ===")
    test1 = identifier.identify("Hemoglobin", 14.5, "g/dL")
    print(f"{test1.name}: {test1.category}, Confidence: {test1.confidence}")
    
    # Test alias matching
    print("\n=== Alias Matching ===")
    test2 = identifier.identify("Hb", 14.5, "g/dL")
    print(f"{test2.name}: {test2.category}, Confidence: {test2.confidence}")
    
    # Test fuzzy matching
    print("\n=== Fuzzy Matching ===")
    test3 = identifier.identify("Haemoglobin", 14.5, "g/dL")
    print(f"{test3.name}: {test3.category}, Confidence: {test3.confidence}")
    
    # Test unknown test
    print("\n=== Unknown Test Handling ===")
    test4 = identifier.identify("Random Unknown Test", 100, "mg/dL")
    print(f"{test4.name}: {test4.category}, Confidence: {test4.confidence}")
    if test4.warning:
        print(f"Warning: {test4.warning}")
    
    # Test panel grouping
    print("\n=== Panel Grouping ===")
    kb = TestKnowledgeBase()
    grouper = PanelGrouper(kb)
    
    tests = [
        identifier.identify("Hemoglobin"),
        identifier.identify("WBC"),
        identifier.identify("Platelet Count")
    ]
    
    panels = grouper.group_tests(tests)
    for panel_name, panel_data in panels.items():
        print(f"\n{panel_data['name']}:")
        print(f"  Detected: {', '.join(panel_data['detected'])}")
        print(f"  Missing: {', '.join(panel_data['missing'])}")
        print(f"  Completeness: {panel_data['completeness']*100:.1f}%")
