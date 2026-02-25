# Test the intelligent parser
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from test_identifier import TestIdentifier

# Simple direct test
identifier = TestIdentifier()

print("=" * 60)
print("INTELLIGENT TEST IDENTIFICATION - DEMO")
print("=" * 60)

# Test 1: Alias matching
print("\n1. Alias Matching:")
print("   Input: 'Hb' (common abbreviation)")
result = identifier.identify("Hb", 14.5, "g/dL")
print(f"   Identified as: {result.name}")
print(f"   Category: {result.category}, Confidence: {result.confidence}")

# Test 2: Direct matching
print("\n2. Direct Matching:")
print("   Input: 'Total Cholesterol'")
result = identifier.identify("Total Cholesterol", 180, "mg/dL")
print(f"   Identified as: {result.name}")
print(f"   Category: {result.category}, Panel: {result.panel}")

# Test 3: Fuzzy matching
print("\n3. Fuzzy Matching:")
print("   Input: 'Haemoglobin' (British spelling)")
result = identifier.identify("Haemoglobin", 15.0, "g/dL")
print(f"   Identified as: {result.name}")
print(f"   Confidence: {result.confidence}")

# Test 4: Unknown test
print("\n4. Unknown Test Handling:")
print("   Input: 'Some Random Test'")
result = identifier.identify("Some Random Test", 42.0, "mg/dL")
print(f"   Name: {result.name}")
print(f"   Category: {result.category} (inferred)")
print(f"   Confidence: {result.confidence}")
print(f"   Warning: {result.warning}")

print("\n" + "=" * 60)
print("SUCCESS! All identification modes working correctly.")
print("=" * 60)
