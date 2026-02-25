# -*- coding: utf-8 -*-
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.parser import parse_blood_test

# Simple test text
test_text = """
Glucose Fasting
85.3 mg/dL

Hemoglobin (Hb)
16.2 gm/dL

Total Cholesterol, Serum
173 mg/dL

TSH (Thyroid Stimulating Hormone) - Ultrasensitive, Serum
7.080 µIU/mL
"""

print("Simple Extraction Test")
print("=" * 60)

results = parse_blood_test(test_text)

print(f"Extracted {len(results)} parameters:")
for param, data in results.items():
    print(f"  - {param}: {data.get('value')} {data.get('unit')} [{data.get('status')}]")

print("\nDone!")
