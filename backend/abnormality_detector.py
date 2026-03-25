"""
Robust Abnormality Detection System for Lab Test Results
Medical Safety-Critical Component - Production Ready

Author: Clinical Data Engineering Team
Version: 2.0
Last Updated: 2026-01-19
"""

import re
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test result status classifications"""
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class Severity(Enum):
    """Clinical severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def get_severity_label(severity: Severity) -> str:
    """
    Get user-friendly severity label
    
    Args:
        severity: Severity enum value
    
    Returns:
        Human-readable severity label
    """
    severity_labels = {
        Severity.LOW: "Mild Deviation",
        Severity.MEDIUM: "Moderate Deviation",
        Severity.HIGH: "Significant Deviation",
        Severity.CRITICAL: "Critical"
    }
    return severity_labels.get(severity, "Normal")


@dataclass
class ReferenceRange:
    """Structured reference range data with demographic context"""
    range_type: str  # 'numeric', 'inequality', 'qualitative'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    operator: Optional[str] = None  # '<', '>', '<=', '>='
    threshold: Optional[float] = None
    qualitative_normal: Optional[List[str]] = None
    gender_specific: bool = False
    age_specific: bool = False
    notes: List[str] = None
    
    # Demographic context fields
    age_group: Optional[str] = None  # e.g., "18-65", "pediatric", "geriatric"
    gender: Optional[str] = None  # "male", "female", "any"
    ethnicity: Optional[str] = None  # "any", "african", "asian", "caucasian", etc.
    pregnancy_status: Optional[bool] = None  # True if pregnancy-adjusted range
    source_note: Optional[str] = None  # Transparency note about range source
    canonical_unit: Optional[str] = None  # The authoritative unit from knowledge base

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


@dataclass
class AbnormalityResult:
    """Complete abnormality detection result"""
    test_name: str
    value: Union[float, str]
    unit: str
    reference_range: str
    status: TestStatus
    confidence_score: float  # 0.0 to 1.0
    notes: List[str]
    severity: Severity
    parsed_range: Optional[ReferenceRange] = None


class ReferenceRangeParser:
    """
    Parses various reference range formats with medical safety considerations
    """
    
    # OCR error corrections
    OCR_CORRECTIONS = {
        'I': '1',
        'O': '0',
        'l': '1',
        'S': '5',
        'B': '8'
    }
    
    # Qualitative result mappings
    QUALITATIVE_NORMAL = {
        'negative', 'non-reactive', 'normal', 'absent', 'not detected',
        'non-detected', 'undetected', 'reactive (normal)', 'normal range'
    }
    
    QUALITATIVE_ABNORMAL = {
        'positive', 'reactive', 'detected', 'present', 'abnormal',
        'elevated', 'decreased', 'borderline'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def clean_ocr_artifacts(self, text: str) -> str:
        """
        Clean common OCR artifacts from numeric strings
        
        Examples:
            "I5.0" -> "15.0"
            "O.45" -> "0.45"
            "l2.3" -> "12.3"
        """
        if not text:
            return text
        
        cleaned = text.strip()
        
        # Fix common OCR errors in numbers
        # Only replace at beginning for I->1, O->0, l->1
        if len(cleaned) > 0 and cleaned[0] in self.OCR_CORRECTIONS:
            cleaned = self.OCR_CORRECTIONS[cleaned[0]] + cleaned[1:]
        
        # Fix decimal point issues
        cleaned = re.sub(r'([0-9])O([0-9])', r'\g<1>0\g<2>', cleaned)  # 1O.5 -> 10.5
        cleaned = re.sub(r'([0-9])l([0-9])', r'\g<1>1\g<2>', cleaned)  # 1l.5 -> 11.5
        
        return cleaned
    
    def parse(self, range_str: str, test_name: str = "Unknown") -> ReferenceRange:
        """
        Parse a reference range string into structured format
        
        Args:
            range_str: Reference range string
            test_name: Test name for context-specific parsing
            
        Returns:
            ReferenceRange object
        """
        if not range_str or not isinstance(range_str, str):
            return ReferenceRange(
                range_type='insufficient',
                notes=["Missing or invalid reference range"]
            )
        
        range_str = range_str.strip()
        
        # Check for qualitative values
        range_lower = range_str.lower()
        if any(qual in range_lower for qual in self.QUALITATIVE_NORMAL | self.QUALITATIVE_ABNORMAL):
            return self._parse_qualitative(range_str)
        
        # Check for inequality operators
        if any(op in range_str for op in ['<', '>', '≤', '≥', '<=', '>=']):
            return self._parse_inequality(range_str)
        
        # Check for "Up to X" / "Less than X" patterns BEFORE numeric range
        # (to prevent 'Up to 100' from being routed to numeric parser due to '-' check)
        if 'up to' in range_lower or 'less than' in range_lower or 'below' in range_lower:
            return self._parse_upper_limit(range_str)
        
        # Check for numeric range
        if '-' in range_str or ' to ' in range_lower or 'between' in range_lower:
            return self._parse_numeric_range(range_str)
        
        # Fallback: try to parse as single numeric value
        try:
            value = self._extract_number(range_str)
            if value is not None:
                return ReferenceRange(
                    range_type='inequality',
                    operator='<',
                    threshold=value,
                    notes=["Interpreted as upper limit"]
                )
        except:
            pass
        
        return ReferenceRange(
            range_type='unparseable',
            notes=[f"Could not parse reference range: {range_str}"]
        )
    
    def _parse_numeric_range(self, range_str: str) -> ReferenceRange:
        """Parse numeric range like '13.0 - 17.0' or '13-17'"""
        # Clean OCR artifacts
        range_str = self.clean_ocr_artifacts(range_str)
        
        # Pattern: NUMBER - NUMBER or NUMBER to NUMBER (supports negative numbers)
        pattern = r'(-?[\d\.]+)\s*(?:-|to)\s*(-?[\d\.]+)'
        match = re.search(pattern, range_str, re.IGNORECASE)
        
        if match:
            try:
                min_val = float(match.group(1))
                max_val = float(match.group(2))
                
                # Sanity check
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                    note = "Range values were reversed (min > max)"
                else:
                    note = None
                
                return ReferenceRange(
                    range_type='numeric',
                    min_value=min_val,
                    max_value=max_val,
                    notes=[note] if note else []
                )
            except ValueError as e:
                return ReferenceRange(
                    range_type='parse_error',
                    notes=[f"Failed to convert to numbers: {e}"]
                )
        
        return ReferenceRange(
            range_type='parse_error',
            notes=[f"Could not extract numeric range from: {range_str}"]
        )
    
    def _parse_inequality(self, range_str: str) -> ReferenceRange:
        """Parse inequality like '<200', '>=40', '≤150'"""
        range_str = self.clean_ocr_artifacts(range_str)
        
        # Normalize operators
        range_str = range_str.replace('≤', '<=').replace('≥', '>=')
        
        # Pattern: OPERATOR NUMBER or NUMBER OPERATOR
        patterns = [
            (r'([<>]=?)\s*([\d\.]+)', 'prefix'),   # <200
            (r'([\d\.]+)\s*([<>]=?)', 'postfix')   # 200>
        ]
        
        for pattern, pos_type in patterns:
            match = re.search(pattern, range_str)
            if match:
                try:
                    if pos_type == 'prefix':
                        operator = match.group(1)
                        threshold = float(match.group(2))
                    else:
                        threshold = float(match.group(1))
                        operator = match.group(2)
                    
                    return ReferenceRange(
                        range_type='inequality',
                        operator=operator,
                        threshold=threshold
                    )
                except ValueError as e:
                    return ReferenceRange(
                        range_type='parse_error',
                        notes=[f"Failed to parse inequality: {e}"]
                    )
        
        return ReferenceRange(
            range_type='parse_error',
            notes=[f"Could not parse inequality from: {range_str}"]
        )
    
    def _parse_upper_limit(self, range_str: str) -> ReferenceRange:
        """Parse upper limit like 'Up to 150', 'Less than 200'"""
        range_str = self.clean_ocr_artifacts(range_str)
        
        # More aggressive number extraction for 'Up to' patterns
        match = re.search(r'(?:up\s+to|less\s+than|below)\s+([\d\.]+)', range_str, re.IGNORECASE)
        if match:
            try:
                number = float(match.group(1))
                return ReferenceRange(
                    range_type='inequality',
                    operator='<=',  # Changed from < to <= for "up to"
                    threshold=number,
                    notes=["Interpreted as upper limit only"]
                )
            except ValueError:
                pass
        
        # Fallback to generic number extraction
        number = self._extract_number(range_str)
        if number is not None:
            return ReferenceRange(
                range_type='inequality',
                operator='<',
                threshold=number,
                notes=["Interpreted as upper limit only"]
            )
        
        return ReferenceRange(
            range_type='parse_error',
            notes=[f"Could not extract number from: {range_str}"]
        )
    
    def _parse_qualitative(self, range_str: str) -> ReferenceRange:
        """Parse qualitative ranges like 'Negative', 'Positive', 'Non-reactive'"""
        range_lower = range_str.lower()
        
        # Identify normal qualitative values
        normal_values = []
        for qual in self.QUALITATIVE_NORMAL:
            if qual in range_lower:
                normal_values.append(qual)
        
        if normal_values:
            return ReferenceRange(
                range_type='qualitative',
                qualitative_normal=normal_values
            )
        
        # If abnormal indicators are present, still return qualitative type
        abnormal_values = []
        for qual in self.QUALITATIVE_ABNORMAL:
            if qual in range_lower:
                abnormal_values.append(qual)
        
        if abnormal_values:
            return ReferenceRange(
                range_type='qualitative',
                qualitative_normal=[],
                notes=[f"Abnormal indicators: {', '.join(abnormal_values)}"]
            )
        
        return ReferenceRange(
            range_type='qualitative',
            qualitative_normal=[range_str.lower()],
            notes=["Assuming this is the normal value"]
        )
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract first number from text, handling OCR errors"""
        text = self.clean_ocr_artifacts(text)
        match = re.search(r'([\d\.]+)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


class DemographicRangeSelector:
    """
    Selects demographic-specific reference ranges from knowledge base
    Supports age, gender, ethnicity, and pregnancy-based range selection
    """
    
    def __init__(self, knowledge_base_path: str = None):
        """
        Initialize with path to test knowledge base
        
        Args:
            knowledge_base_path: Path to JSON knowledge base file
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.knowledge_base = None
        self.knowledge_base_path = knowledge_base_path or "backend/test_knowledge_base.json"
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load test knowledge base from JSON file"""
        try:
            import json
            import os
            
            # Try multiple possible paths
            possible_paths = [
                self.knowledge_base_path,
                os.path.join(os.path.dirname(__file__), "test_knowledge_base.json"),
                "test_knowledge_base.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self.knowledge_base = json.load(f)
                    self.logger.info(f"Loaded knowledge base from: {path}")
                    return
            
            self.logger.warning(f"Knowledge base not found at any of: {possible_paths}")
            self.knowledge_base = {"tests": {}}
            
        except Exception as e:
            self.logger.error(f"Failed to load knowledge base: {e}")
            self.knowledge_base = {"tests": {}}
    
    def get_demographic_range(
        self,
        test_name: str,
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        patient_ethnicity: Optional[str] = None,
        pregnancy_status: Optional[bool] = None
    ) -> Optional[ReferenceRange]:
        """
        Get demographic-specific reference range for a test
        
        Args:
            test_name: Name of the test
            patient_age: Patient age in years
            patient_gender: "male", "female", or None
            patient_ethnicity: Ethnicity identifier or None
            pregnancy_status: True if pregnant, False/None otherwise
            
        Returns:
            ReferenceRange object if found, None otherwise
        """
        if not self.knowledge_base or "tests" not in self.knowledge_base:
            return None
        
        # Find test in knowledge base (case-insensitive, handle aliases)
        test_data = self._find_test(test_name)
        if not test_data:
            return None
        
        # Check for pregnancy-specific range first (highest priority)
        if pregnancy_status and "conditional_adjustments" in test_data:
            pregnancy_range = test_data["conditional_adjustments"].get("pregnancy")
            if pregnancy_range:
                return self._build_range_from_dict(
                    pregnancy_range, test_data,
                    age_group="pregnancy", gender="female", 
                    pregnancy_status=True,
                    source_note="Pregnancy-adjusted reference range"
                )
        
        # Check for demographic-specific ranges
        if "demographic_ranges" in test_data:
            best_match = self._find_best_demographic_match(
                test_data["demographic_ranges"],
                patient_age, patient_gender, patient_ethnicity
            )
            if best_match:
                return self._build_range_from_dict(
                    best_match, test_data,
                    source_note=self._get_demographic_note(best_match)
                )
        
        # Fallback to generic reference range
        if "reference_range" in test_data:
            ref_range = test_data["reference_range"]
            note = ref_range.get("note", "Generic reference range")
            if "Male:" in note or "Female:" in note:
                # Parse gender-specific from note
                return self._parse_gender_specific_note(ref_range, patient_gender, test_data)
            
            return self._build_range_from_dict(
                ref_range, test_data,
                source_note="Generic reference range (no demographic specificity)"
            )
        
        return None
    
    def _find_test(self, test_name: str) -> Optional[Dict]:
        """Find test in knowledge base by name or alias"""
        test_lower = test_name.lower().strip()
        
        for test_id, test_data in self.knowledge_base["tests"].items():
            # Check canonical name
            if test_data.get("name", "").lower() == test_lower:
                return test_data
            
            # Check aliases
            aliases = test_data.get("aliases", [])
            if any(alias.lower() == test_lower for alias in aliases):
                return test_data
        
        return None
    
    def _find_best_demographic_match(
        self,
        demographic_ranges: List[Dict],
        patient_age: Optional[int],
        patient_gender: Optional[str],
        patient_ethnicity: Optional[str]
    ) -> Optional[Dict]:
        """
        Find best matching demographic range based on patient data
        
        Scoring system:
        - Age match: +3 points
        - Gender match: +2 points
        - Ethnicity match: +1 point
        """
        best_score = -1
        best_match = None
        
        for range_spec in demographic_ranges:
            score = 0
            
            # Age matching
            age_min = range_spec.get("age_min", 0)
            age_max = range_spec.get("age_max", 999)
            if patient_age and age_min <= patient_age <= age_max:
                score += 3
            elif patient_age is None and range_spec.get("age_min") is None:
                score += 1  # Generic age range
            
            # Gender matching
            range_gender = range_spec.get("gender", "any")
            if patient_gender and range_gender.lower() == patient_gender.lower():
                score += 2
            elif range_gender.lower() == "any":
                score += 1
            
            # Ethnicity matching
            range_ethnicity = range_spec.get("ethnicity", "any")
            if patient_ethnicity and range_ethnicity.lower() == patient_ethnicity.lower():
                score += 1
            elif range_ethnicity == "any":
                score += 0.5
            
            # Update best match if this is better
            if score > best_score:
                best_score = score
                best_match = range_spec
        
        return best_match if best_score > 0 else None
    
    def _build_range_from_dict(
        self, 
        range_dict: Dict, 
        test_data: Dict,
        age_group: str = None,
        gender: str = None,
        ethnicity: str = None,
        pregnancy_status: bool = None,
        source_note: str = None
    ) -> ReferenceRange:
        """Build ReferenceRange object from dictionary, preserving canonical unit."""
        min_val = range_dict.get("min")
        max_val = range_dict.get("max")
        
        # Extract demographic info from range_dict if not provided
        if age_group is None:
            age_min = range_dict.get("age_min")
            age_max = range_dict.get("age_max")
            if age_min is not None and age_max is not None:
                age_group = f"{age_min}-{age_max}"
        
        if gender is None:
            gender = range_dict.get("gender", "any")
        
        if ethnicity is None:
            ethnicity = range_dict.get("ethnicity", "any")
        
        # Canonical unit: prefer range_dict unit, then fall back to top-level test unit
        canonical_unit = (
            range_dict.get("unit")
            or test_data.get("unit")
        )

        # Build notes
        notes = []
        if range_dict.get("note"):
            notes.append(range_dict["note"])
        
        return ReferenceRange(
            range_type='numeric',
            min_value=float(min_val) if min_val is not None else None,
            max_value=float(max_val) if max_val is not None else None,
            age_group=age_group,
            gender=gender,
            ethnicity=ethnicity,
            pregnancy_status=pregnancy_status,
            source_note=source_note,
            notes=notes,
            canonical_unit=canonical_unit,
        )
    
    def _parse_gender_specific_note(
        self, 
        ref_range: Dict, 
        patient_gender: Optional[str],
        test_data: Dict
    ) -> ReferenceRange:
        """Parse gender-specific ranges from note field (legacy format)"""
        import re
        note = ref_range.get("note", "")
        
        # Try to extract gender-specific values from note
        # Example: "Male: 13-17; Female: 12-15.5"
        if patient_gender and patient_gender.lower() in ["male", "female"]:
            pattern = rf"{patient_gender.capitalize()}:\s*([0-9.]+)\s*-\s*([0-9.]+)"
            match = re.search(pattern, note)
            if match:
                return ReferenceRange(
                    range_type='numeric',
                    min_value=float(match.group(1)),
                    max_value=float(match.group(2)),
                    gender=patient_gender.lower(),
                    source_note=f"Gender-specific range for {patient_gender}",
                    notes=[note]
                )
        
        # Fallback to generic range
        return ReferenceRange(
            range_type='numeric',
            min_value=float(ref_range.get("min")) if ref_range.get("min") else None,
            max_value=float(ref_range.get("max")) if ref_range.get("max") else None,
            source_note="Generic range (gender not specified)",
            notes=[note] if note else []
        )
    
    def _get_demographic_note(self, range_spec: Dict) -> str:
        """Generate human-readable note about demographic specificity"""
        parts = []
        
        if "age_min" in range_spec and "age_max" in range_spec:
            parts.append(f"Age {range_spec['age_min']}-{range_spec['age_max']}")
        
        if range_spec.get("gender") and range_spec["gender"] != "any":
            parts.append(f"{range_spec['gender'].capitalize()}")
        
        if range_spec.get("ethnicity") and range_spec["ethnicity"] != "any":
            parts.append(f"{range_spec['ethnicity'].capitalize()} population")
        
        if parts:
            return f"Demographic-specific range: {', '.join(parts)}"
        else:
            return "Generic reference range"




class UnitNormalizer:
    """
    Normalize and convert units with safety checks.
    
    Design: CONVERSIONS[canonical_unit][input_unit] = factor_to_multiply_input_by
    i.e. canonical_value = input_value * factor
    """
    
    # Unit conversion factors: CONVERSIONS[target_unit][source_unit] = factor
    # canonical_value = reported_value * factor
    CONVERSIONS = {
        # ── Hemoglobin / Protein mass concentration ──────────────────────────
        'g/dL': {
            'g/dl': 1.0,
            'gm/dl': 1.0,
            'gm/dL': 1.0,
            'g/L':   0.1,        # 1 g/L = 0.1 g/dL
            'mg/dL': 0.001,      # rarely used but safe fallback
        },

        # ── Glucose / Cholesterol / most biochemistry ─────────────────────────
        'mg/dL': {
            'mg/dl': 1.0,
            'mg/L':  0.1,
            # mmol/L conversions are analyte-specific; handled via context below
        },

        # ── Counts per microlitre (CBC) ───────────────────────────────────────
        # reports may use /uL, 10^3/µL, K/µL, lakh/µL, ×10³/µL …
        'cells/µL': {
            'cells/ul':    1.0,
            'cells/uL':    1.0,
            '/µL':         1.0,
            '/ul':         1.0,
            '/uL':         1.0,
            'µL':          1.0,  # bare unit sometimes seen in OCR
            'uL':          1.0,
            '10^3/µL':     1000.0,
            '10^3/uL':     1000.0,
            '10³/µL':      1000.0,
            'x10^3/µL':    1000.0,
            'x10^3/uL':    1000.0,
            '×10³/µL':     1000.0,
            '×10^3/µL':    1000.0,
            'k/µL':        1000.0,
            'k/uL':        1000.0,
            'K/µL':        1000.0,
            'K/uL':        1000.0,
            'thou/µL':     1000.0,
            'thou/uL':     1000.0,
            'cmm':         1.0,   # cells per cubic mm = cells/µL
            '/cmm':        1.0,
            'lakh/µL':     100000.0,
            'lakh/uL':     100000.0,
            '10^6/µL':     1000000.0,
            '10^6/uL':     1000000.0,
            'million/µL':  1000000.0,
            'million/uL':  1000000.0,
            'mill/cmm':    1000000.0,
            'mill/µL':     1000000.0,
        },

        # ── RBC Count (million/µL) ────────────────────────────────────────────
        'million/µL': {
            'million/uL':  1.0,
            'mill/cmm':    1.0,
            '10^6/µL':     1.0,
            '10^6/uL':     1.0,
            '10⁶/µL':      1.0,
            'x10^6/µL':    1.0,
            '×10⁶/µL':     1.0,
            '10^3/µL':     0.001, # 10^3 cells → ÷1000 → millions
            'k/µL':        0.001,
            'K/µL':        0.001,
            '/µL':         0.000001,
            '/uL':         0.000001,
            'cells/µL':    0.000001,
            'cells/uL':    0.000001,
            'cmm':         0.000001,
        },

        # ── milli/micro moles per litre ───────────────────────────────────────
        'mmol/L': {
            'mmol/l':      1.0,
            'mEq/L':       1.0,   # for monovalent electrolytes (Na, K, Cl, HCO3)
            'meq/L':       1.0,
            'mEq/l':       1.0,
            'mg/dL': None,        # requires molar mass — handled via analyte context
        },
        'µmol/L': {
            'umol/L':      1.0,
            'umol/l':      1.0,
            'µmol/l':      1.0,
            'nmol/L':      0.001,
            'mg/dL': None,        # requires molar mass — handled via analyte context
        },

        # ── Thyroid / hormones ────────────────────────────────────────────────
        'µIU/mL': {
            'uIU/mL':      1.0,
            'uIU/ml':      1.0,
            'µIU/ml':      1.0,
            'mIU/L':       1.0,   # mIU/L == µIU/mL numerically
            'miu/L':       1.0,
            'mIU/mL':      1000.0, # milli vs micro
        },
        'mIU/mL': {
            'miu/mL':      1.0,
            'miu/ml':      1.0,
            'IU/mL':       1000.0,
            'µIU/mL':      0.001,
        },
        'pg/mL': {
            'pg/ml':       1.0,
            'ng/L':        1.0,   # 1 ng/L = 1 pg/mL
            'ng/dL':       10.0,  # 1 ng/dL = 10 pg/mL
        },
        'ng/mL': {
            'ng/ml':       1.0,
            'µg/L':        1.0,   # 1 µg/L = 1 ng/mL
            'ug/L':        1.0,
            'mcg/L':       1.0,
            'ng/dL':       0.01,
            'µg/dL':       0.01,  # 1 µg/dL = 0.01 µg/mL = 0.01 ng/mL
        },
        'ng/dL': {
            'ng/dl':       1.0,
            'pg/mL':       0.1,
            'ng/mL':       100.0,
        },
        # µg/dL (cortisol, trace minerals, DHEA-S, vitamins A/C ...)
        'µg/dL': {
            'ug/dL':       1.0,
            'mcg/dL':      1.0,
            'µg/dl':       1.0,
            'ng/dL':       0.001, # 1 ng/dL = 0.001 µg/dL
            'ng/mL':       0.1,
            'µg/L':        0.1,
            'ug/L':        0.1,
        },
        'µg/L': {
            'ug/L':        1.0,
            'mcg/L':       1.0,
            'ng/mL':       1.0,
            'µg/dL':       10.0,
        },

        # ── Enzyme U/L ─────────────────────────────────────────────────────
        'U/L': {
            'u/L':         1.0,
            'u/l':         1.0,
            'IU/L':        1.0,
            'iu/L':        1.0,
            'mU/mL':       1.0,   # mU/mL == U/L
            'U/mL':        1000.0,
        },
        'IU/mL': {
            'iu/mL':       1.0,
            'U/mL':        1.0,
            'IU/L':        0.001,
            'U/L':         0.001,
        },

        # ── Percentages ──────────────────────────────────────────────────────
        '%': {
            'percent':     1.0,
            'pct':         1.0,
        },

        # ── Time-based ───────────────────────────────────────────────────────
        'mm/hr': {
            'mm/h':        1.0,
            'mm per hour': 1.0,
        },
        'seconds': {
            'sec':         1.0,
            's':           1.0,
        },

        # ── Volume ───────────────────────────────────────────────────────────
        'fL': {
            'fl':          1.0,
            'femtolitre':  1.0,
        },
        'pg': {
            'picogram':    1.0,
        },

        # ── Lipids / coagulation (mg/dL family already handled) ───────────────
        'mg/g': {
            'mg/g creatinine': 1.0,
        },
        'µg/mL': {
            'ug/mL':       1.0,
            'mcg/mL':      1.0,
            'mg/L':        1.0,   # 1 mg/L = 1 µg/mL
        },
        'ng/mL/hr': {
            'ng/ml/hr':    1.0,
        },
    }

    # Analyte-specific mmol/L → mg/dL molar mass factors
    # canonical_value_mg_dL = reported_mmol_L * factor
    MMOL_TO_MGDL: Dict[str, float] = {
        'glucose':         18.0182,
        'fasting blood glucose': 18.0182,
        'glucose post prandial': 18.0182,
        'cholesterol':     38.67,
        'total cholesterol': 38.67,
        'hdl cholesterol': 38.67,
        'ldl cholesterol': 38.67,
        'vldl cholesterol': 38.67,
        'triglycerides':   88.57,
        'urea':            6.006,
        'bun':             2.8,   # BUN = urea × 0.4667
        'creatinine':      88.42,
        'uric acid':       16.81,
        'calcium':         4.008,
        'phosphorus':      3.097,
        'magnesium':       2.431,
        'bilirubin total': 17.10,
        'bilirubin direct':17.10,
        'albumin':         10.0,  # approximate
    }
    
    def normalize(self, value: float, unit: str, target_unit: str, test_context: str = "") -> Tuple[float, str, bool]:
        """
        Convert value from `unit` to `target_unit`.
        Returns (converted_value, final_unit, was_converted).
        """
        if not unit or not target_unit:
            return value, unit or "Unknown", False

        unit_clean   = unit.strip()
        target_clean = target_unit.strip()
        context_low  = test_context.lower()

        # ── Already in target unit (case-insensitive) ────────────────────────
        if unit_clean.lower() == target_clean.lower():
            return value, target_clean, False

        # ── Analyte-specific mmol/L → mg/dL ─────────────────────────────────
        if unit_clean.lower() in ('mmol/l', 'mmol/L'.lower()) and target_clean.lower() == 'mg/dl':
            factor = None
            for analyte_key, f in self.MMOL_TO_MGDL.items():
                if analyte_key in context_low:
                    factor = f
                    break
            if factor is not None:
                return value * factor, 'mg/dL', True
            # Cannot safely convert without molar mass
            logger.warning(f"mmol/L→mg/dL: no molar mass for '{test_context}', skipping conversion")
            return value, unit_clean, False

        # ── General conversion table lookup ──────────────────────────────────
        # Try exact target unit match first
        for tgt_key, conversion_map in self.CONVERSIONS.items():
            if tgt_key.lower() != target_clean.lower():
                continue
            for src_variant, factor in conversion_map.items():
                if factor is None:
                    continue  # placeholder entry
                if src_variant.lower() == unit_clean.lower():
                    converted = value * factor
                    logger.info(
                        f"[UnitNorm] {test_context}: {value} {unit_clean} → {converted:.4g} {tgt_key}"
                    )
                    return converted, tgt_key, True

        # ── Reverse lookup: maybe target→source exists as inverse ─────────────
        for src_key, conversion_map in self.CONVERSIONS.items():
            if src_key.lower() != unit_clean.lower():
                continue
            for candidate_target, factor in conversion_map.items():
                if factor is None or factor == 0:
                    continue
                if candidate_target.lower() == target_clean.lower():
                    converted = value / factor
                    logger.info(
                        f"[UnitNorm] {test_context} (reverse): {value} {unit_clean} → {converted:.4g} {target_clean}"
                    )
                    return converted, target_clean, True

        logger.warning(
            f"[UnitNorm] Cannot convert '{unit_clean}' → '{target_clean}' for '{test_context}'"
        )
        return value, unit_clean, False


class AbnormalityDetector:
    """
    Main abnormality detection engine with medical safety focus
    """
    
    # Critical thresholds that override normal classification
    CRITICAL_THRESHOLDS = {
        "Potassium": {"low": 2.5, "high": 6.0},
        "Sodium": {"low": 120, "high": 160},
        "Glucose Fasting": {"low": 40, "high": 400},
        "Creatinine": {"high": 5.0},
        "Hemoglobin": {"low": 7.0, "high": 20.0},
        "WBC Count": {"low": 2000, "high": 30000},
        "Platelet Count": {"low": 50000, "high": 1000000}
    }
    
    def __init__(self):
        self.range_parser = ReferenceRangeParser()
        self.unit_normalizer = UnitNormalizer()
        self.demographic_selector = DemographicRangeSelector()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def detect_abnormality(
        self,
        test_name: str,
        value: Union[float, str],
        unit: str,
        reference_range: str,
        patient_gender: Optional[str] = None,
        patient_age: Optional[int] = None,
        patient_ethnicity: Optional[str] = None,
        pregnancy_status: Optional[bool] = None
    ) -> AbnormalityResult:
        """
        Detect abnormality with comprehensive safety checks
        
        Args:
            test_name: Name of the test
            value: Test value (numeric or qualitative)
            unit: Unit of measurement
            reference_range: Reference range string (OCR-extracted)
            patient_gender: Optional patient gender ("male" or "female")
            patient_age: Optional patient age in years
            patient_ethnicity: Optional patient ethnicity
            pregnancy_status: Optional pregnancy status (True if pregnant)
            
        Returns:
            AbnormalityResult with classification and confidence
        """
        notes = []
        confidence = 1.0
        
        # ── Step 1: Get reference range from knowledge base ─────────────────
        # KB-derived range takes priority over whatever the OCR captured,
        # because the KB stores clinically validated canonical values and units.
        parsed_range = self.demographic_selector.get_demographic_range(
            test_name,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_ethnicity=patient_ethnicity,
            pregnancy_status=pregnancy_status
        )

        if parsed_range:
            if parsed_range.source_note:
                notes.append(parsed_range.source_note)
            notes.extend(parsed_range.notes)
            # Build display range string preserving the canonical unit
            if parsed_range.min_value is not None and parsed_range.max_value is not None:
                unit_suffix = f" {parsed_range.canonical_unit}" if parsed_range.canonical_unit else ""
                reference_range = f"{parsed_range.min_value} - {parsed_range.max_value}{unit_suffix}"
            self.logger.info(f"[KB] Range for '{test_name}': {reference_range}")
        else:
            # Fallback: parse whatever is in the OCR-supplied reference_range string
            parsed_range = self.range_parser.parse(reference_range, test_name)
            notes.extend(parsed_range.notes)
            notes.append("Using OCR-extracted range (test not in knowledge base)")
            confidence *= 0.90  # OCR ranges are less reliable

        # ── Step 2: Handle qualitative values ───────────────────────────────
        if isinstance(value, str) and not value.replace('.', '').replace('-', '').isdigit():
            return self._classify_qualitative(test_name, value, parsed_range, notes)

        # ── Step 3: Parse numeric value (with OCR correction) ───────────────
        numeric_value: Optional[float] = None
        try:
            if isinstance(value, str):
                value_clean = self.range_parser.clean_ocr_artifacts(value)
                numeric_value = float(value_clean)
                if value != value_clean:
                    notes.append(f"Corrected OCR artifact: '{value}' → '{value_clean}'")
                    confidence *= 0.9
            else:
                numeric_value = float(value)
        except (ValueError, TypeError):
            return AbnormalityResult(
                test_name=test_name,
                value=value,
                unit=unit,
                reference_range=reference_range,
                status=TestStatus.REVIEW_REQUIRED,
                confidence_score=0.0,
                notes=[f"Cannot parse numeric value: '{value}'"],
                severity=Severity.MEDIUM,
                parsed_range=parsed_range,
            )

        # ── Step 4: Unit Normalisation ───────────────────────────────────────
        # Determine the authoritative target unit using a priority chain:
        #   1. canonical_unit stored in the KB-derived ReferenceRange
        #   2. Unit embedded at the end of the reference_range display string
        #   3. Give up — compare as-is and penalise confidence
        target_unit: Optional[str] = None

        # Priority 1: canonical unit from knowledge base
        if parsed_range and getattr(parsed_range, 'canonical_unit', None):
            target_unit = parsed_range.canonical_unit

        # Priority 2: extract unit from tail of reference_range string
        if not target_unit:
            # Matches units like: cells/µL  g/dL  mg/dL  µIU/mL  mm/hr  %  fL  pg
            tail_match = re.search(
                r'[\d\.]+\s+([a-zA-Z][a-zA-Z0-9/%µ^·×\-]*)$',
                reference_range.strip()
            )
            if tail_match:
                target_unit = tail_match.group(1).strip()

        # Perform conversion when units differ
        if (
            numeric_value is not None
            and target_unit
            and unit
            and unit.strip().lower() != target_unit.strip().lower()
        ):
            converted_val, final_unit, was_converted = self.unit_normalizer.normalize(
                numeric_value, unit, target_unit, test_context=test_name
            )
            if was_converted:
                notes.append(
                    f"Unit conversion: {value} {unit} → {converted_val:.4g} {final_unit}"
                )
                numeric_value = converted_val
                unit = final_unit

                # Post-conversion physiological sanity check
                PHYS_BOUNDS = {
                    "Hemoglobin":      (3.0,    25.0),     # g/dL
                    "WBC Count":       (100,    500_000),  # cells/µL
                    "Platelet Count":  (1_000,  2_000_000),# cells/µL
                    "Potassium":       (1.0,    10.0),     # mmol/L
                    "Sodium":          (100,    180),      # mmol/L
                    "Fasting Blood Glucose": (20, 1_000),  # mg/dL
                }
                if test_name in PHYS_BOUNDS:
                    lo, hi = PHYS_BOUNDS[test_name]
                    if not (lo <= numeric_value <= hi):
                        notes.append(
                            f"⚠️ Post-conversion value {numeric_value:.2g} "
                            f"outside physiological bounds ({lo}–{hi}). "
                            "Verify report units."
                        )
                        confidence *= 0.5
            else:
                # Conversion table doesn't cover this pair — flag it
                notes.append(
                    f"Unit mismatch: report gives '{unit}', expected '{target_unit}'. "
                    "Could not auto-convert — comparing as-is."
                )
                confidence *= 0.75

        # ── Step 4b: Scale-rescue for CBC abbreviated notations ─────────────
        # Many Indian labs print "370 /uL" to mean "370 × 10³/µL" (370,000).
        # After extraction the OCR unit may be empty, "/uL", "uL", or anything
        # else. We therefore trigger the rescue on *test name + magnitude*
        # rather than unit string.
        #
        # Trigger: the numeric value is ≥100× below the expected minimum AND
        # the test is a known large-scale count parameter.
        _LARGE_COUNT_TESTS = {
            'platelet count', 'wbc count', 'wbc', 'white blood cell',
            'total leucocyte count', 'total wbc', 'tlc',
            'platelet', 'plt', 'thrombocyte',
        }
        if (
            parsed_range.range_type == 'numeric'
            and parsed_range.min_value is not None
            and numeric_value is not None
            and numeric_value > 0
            and parsed_range.min_value > 0
            and test_name.strip().lower() in _LARGE_COUNT_TESTS
        ):
            ratio = parsed_range.min_value / numeric_value
            if ratio >= 100:                       # value is 100× or more below min
                for scale_factor in (1000, 1_000_000):
                    candidate = numeric_value * scale_factor
                    # Accept if scaled value lands within 10× of the expected range
                    if candidate >= parsed_range.min_value / 10:
                        notes.append(
                            f"Scale rescue: report uses abbreviated notation "
                            f"({value} {unit} interpreted as "
                            f"{candidate:.4g} {unit} via x{scale_factor:,}). "
                            "Common in labs that omit the x10^3 prefix."
                        )
                        numeric_value = candidate
                        confidence *= 0.92  # small confidence penalty
                        break

        # ── Step 5: Classify ─────────────────────────────────────────────────
        if parsed_range.range_type == 'numeric':
            return self._classify_numeric(
                test_name, numeric_value, unit, parsed_range, notes, confidence
            )
        elif parsed_range.range_type == 'inequality':
            return self._classify_inequality(
                test_name, numeric_value, unit, parsed_range, notes, confidence
            )
        else:
            return self._classify_unknown(
                test_name, numeric_value, unit, reference_range, notes
            )
    
    def _classify_numeric(
        self,
        test_name: str,
        value: float,
        unit: str,
        parsed_range: ReferenceRange,
        notes: List[str],
        confidence: float
    ) -> AbnormalityResult:
        """Classify against numeric range (min-max)"""
        min_val = parsed_range.min_value
        max_val = parsed_range.max_value
        
        # Determine status
        if value < min_val:
            status = TestStatus.LOW
            severity = self._determine_severity(
                test_name, value, min_val, "low"
            )
        elif value > max_val:
            status = TestStatus.HIGH
            severity = self._determine_severity(
                test_name, value, max_val, "high"
            )
        else:
            status = TestStatus.NORMAL
            severity = Severity.LOW
        
        # Check for critical override
        if test_name in self.CRITICAL_THRESHOLDS:
            critical = self.CRITICAL_THRESHOLDS[test_name]
            if 'low' in critical and value < critical['low']:
                status = TestStatus.CRITICAL
                severity = Severity.CRITICAL
                notes.append(f"Value below critical threshold ({critical['low']})")
            elif 'high' in critical and value > critical['high']:
                status = TestStatus.CRITICAL
                severity = Severity.CRITICAL
                notes.append(f"Value above critical threshold ({critical['high']})")
        
        return AbnormalityResult(
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=f"{min_val} - {max_val}",
            status=status,
            confidence_score=confidence,
            notes=notes,
            severity=severity,
            parsed_range=parsed_range
        )
    
    def _classify_inequality(
        self,
        test_name: str,
        value: float,
        unit: str,
        parsed_range: ReferenceRange,
        notes: List[str],
        confidence: float
    ) -> AbnormalityResult:
        """Classify against inequality (< or > threshold)"""
        operator = parsed_range.operator
        threshold = parsed_range.threshold
        
        # Determine status based on operator
        if operator in ['<', '<=']:
            # Normal is below threshold
            if value < threshold or (operator == '<=' and value == threshold):
                status = TestStatus.NORMAL
                severity = Severity.LOW
            else:
                status = TestStatus.HIGH
                severity = self._determine_severity(
                    test_name, value, threshold, "high"
                )
        elif operator in ['>', '>=']:
            # Normal is above threshold
            if value > threshold or (operator == '>=' and value == threshold):
                status = TestStatus.NORMAL
                severity = Severity.LOW
            else:
                status = TestStatus.LOW
                severity = self._determine_severity(
                    test_name, value, threshold, "low"
                )
        else:
            return self._classify_unknown(test_name, value, unit, str(threshold), notes)
        
        # Check for critical override
        if test_name in self.CRITICAL_THRESHOLDS:
            critical = self.CRITICAL_THRESHOLDS[test_name]
            if 'low' in critical and value < critical['low']:
                status = TestStatus.CRITICAL
                severity = Severity.CRITICAL
            elif 'high' in critical and value > critical['high']:
                status = TestStatus.CRITICAL
                severity = Severity.CRITICAL
        
        return AbnormalityResult(
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=f"{operator} {threshold}",
            status=status,
            confidence_score=confidence,
            notes=notes,
            severity=severity,
            parsed_range=parsed_range
        )
    
    def _classify_qualitative(
        self,
        test_name: str,
        value: str,
        parsed_range: ReferenceRange,
        notes: List[str]
    ) -> AbnormalityResult:
        """Classify qualitative results (Positive/Negative, etc.)"""
        value_lower = value.lower().strip()
        
        if parsed_range.range_type != 'qualitative':
            notes.append("Qualitative value but range is not qualitative")
            return AbnormalityResult(
                test_name=test_name,
                value=value,
                unit="N/A",
                reference_range=str(parsed_range.qualitative_normal),
                status=TestStatus.REVIEW_REQUIRED,
                confidence_score=0.5,
                notes=notes,
                severity=Severity.MEDIUM,
                parsed_range=parsed_range
            )
        
        # Check if value matches normal qualitative values
        normal_values = parsed_range.qualitative_normal or []
        if any(normal in value_lower for normal in normal_values):
            status = TestStatus.NORMAL
            severity = Severity.LOW
            confidence = 0.95
        elif value_lower in ReferenceRangeParser.QUALITATIVE_NORMAL:
            status = TestStatus.NORMAL
            severity = Severity.LOW
            confidence = 0.9
        elif value_lower in ReferenceRangeParser.QUALITATIVE_ABNORMAL:
            status = TestStatus.HIGH
            severity = Severity.MEDIUM
            confidence = 0.9
            notes.append("Qualitative abnormal result detected")
        else:
            status = TestStatus.REVIEW_REQUIRED
            severity = Severity.MEDIUM
            confidence = 0.6
            notes.append(f"Uncertain qualitative classification for: {value}")
        
        return AbnormalityResult(
            test_name=test_name,
            value=value,
            unit="N/A",
            reference_range=str(normal_values),
            status=status,
            confidence_score=confidence,
            notes=notes,
            severity=severity,
            parsed_range=parsed_range
        )
    
    def _classify_unknown(
        self,
        test_name: str,
        value: Union[float, str],
        unit: str,
        reference_range: str,
        notes: List[str]
    ) -> AbnormalityResult:
        """Fallback classification when range cannot be parsed"""
        notes.append("Reference range could not be reliably parsed")
        
        return AbnormalityResult(
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=reference_range,
            status=TestStatus.REVIEW_REQUIRED,
            confidence_score=0.0,
            notes=notes,
            severity=Severity.MEDIUM,
            parsed_range=None
        )
    
    def _determine_severity(
        self,
        test_name: str,
        value: float,
        boundary: float,
        direction: str
    ) -> Severity:
        """
        Determine severity based on how far value is from boundary
        
        Args:
            test_name: Test name
            value: Actual value
            boundary: Reference boundary (min or max)
            direction: "low" or "high"
        """
        if boundary == 0:
            return Severity.MEDIUM
        
        # Calculate percentage deviation
        deviation = abs((value - boundary) / boundary) * 100
        
        if deviation < 10:
            return Severity.LOW
        elif deviation < 25:
            return Severity.MEDIUM
        elif deviation < 50:
            return Severity.HIGH
        else:
            return Severity.CRITICAL


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example usage of the abnormality detection system"""
    detector = AbnormalityDetector()
    
    # Test cases
    test_cases = [
        {
            "test_name": "Hemoglobin",
            "value": "I5.2",  # OCR error: should be 15.2
            "unit": "g/dL",
            "reference_range": "13.0 - 17.0"
        },
        {
            "test_name": "Glucose Fasting",
            "value": 250.0,
            "unit": "mg/dL",
            "reference_range": "<100"
        },
        {
            "test_name": "TSH",
            "value": 7.5,
            "unit": "µIU/mL",
            "reference_range": "0.4 - 4.0"
        },
        {
            "test_name": "HIV Test",
            "value": "Negative",
            "unit": "",
            "reference_range": "Negative"
        },
        {
            "test_name": "Vitamin D",
            "value": 18.0,
            "unit": "ng/mL",
            "reference_range": "Up to 100"  # Should be >=30 ideally
        }
    ]
    
    print("="*80)
    print("ABNORMALITY DETECTION RESULTS")
    print("="*80)
    
    for test in test_cases:
        result = detector.detect_abnormality(**test)
        
        print(f"\nTest: {result.test_name}")
        print(f"  Value: {result.value} {result.unit}")
        print(f"  Reference: {result.reference_range}")
        print(f"  Status: {result.status.value}")
        print(f"  Severity: {result.severity.value}")
        print(f"  Confidence: {result.confidence_score:.2f}")
        if result.notes:
            print(f"  Notes: {', '.join(result.notes)}")
        print("-" * 80)


if __name__ == "__main__":
    example_usage()
