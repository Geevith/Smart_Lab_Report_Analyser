"""
Test comprehensive lab parameter extraction with actual report data
"""
import sys
sys.path.insert(0, 'c:/Users/geevi/Downloads/Smart_Lab_Report_Analyser')

from backend.parser import parse_blood_test
from backend.interpretation import generate_insights

# Sample text from user's comprehensive report
COMPREHENSIVE_REPORT_TEXT = """
RA (Rheumatoid Arthritis) Factor, Serum
(Serum, Immunoturbidimetry)
15.90 IU/mL Non-reactive: < 14

Glucose Fasting
(Fluoride Plasma - F, Hexokinase)
85.3 mg/dL Normal: 70-99

Glucose Post Prandial
(Fluoride Plasma - PP, Hexokinase)
102 mg/dL Normal: 70-140

BUN, Serum
(Serum, Calculated)
9.3 mg/dL 6-20

Creatinine, Serum
(Serum, Jaffes method)
0.99 mg/dL 0.67-1.17

Uric Acid, Serum
(Serum, Uricase)
4.9 mg/dL 3.4-7.0

Calcium, Serum
(Serum, NM-BAPTA)
9.8 mg/dL 8.6-10.0

Phosphorus, Serum
(Serum, Molybdate UV)
4.4 mg/dL 2.5-4.5

Sodium, Serum
(ISE Indirect)
140 mmol/L 136-145

Potassium, Serum
(ISE Indirect)
4.68 mmol/L 3.5-5.1

Chloride, Serum
(ISE Indirect)
104 mmol/L 98-107

Bicarbonate
(Phosphophenolpyruvate (PEP))
21 mmol/L 22-29

Bilirubin Total
(Diazo method)
0.52 mg/dL 0-1.2

Bilirubin Direct
(Diazo method)
0.22 mg/dL 0.0-0.3

Bilirubin- Indirect
(Calculated)
0.30 mg/dL 0.1-1.0

SGOT (AST)
(Serum, Enzymatic IFCC)
27 U/L 0-40

SGPT (ALT)
(Serum, Enzymatic IFCC)
33 IU/L 0-41

Alkaline Phosphatase, Serum
(Serum, p-nitrophenyl phosphate (pNPP) - (IFCC))
88 IU/L 40-129

Gamma GT (GGTP)
(Serum, Gamma-Glutamyl Carboxy Nitroanilide (GGCNA) - IFCC method)
46 U/L < 60

Iron, Serum
(FerroZine)
67.30 ug/dl 33-193

UIBC
(FerroZine)
294.80 µg/dL 125-345

TIBC
(Calculated)
362 µg/dL 250-450

Transferin Saturation
(Calculated)
19 % 14-50

CPK Total
(Serum, CK-NAC IFCC)
86 IU/L < 190

LDH (Lactate Dehydrogenase), Serum
(Serum, Lactate-pyruvate IFCC)
184 IU/L 0-250

HsCRP (High Sensitivity CRP)
(Serum, Immunoturbidimetry)
2.89 mg/L Low: < 1.0

Cholesterol Total, Serum
(Cholesterol oxidase-peroxidase (CHOD-POD))
173 mg/dL Desirable: < 200

Triglycerides, Serum
(Glycerol-3-phosphate peroxidase chromogenic method (GPO-POD))
169 mg/dL Normal: < 150

HDL Cholesterol Direct
(Direct Measure - Polymer Poly Anion PEG method)
41 mg/dL > 40

LDL Cholesterol
(Calculated)
98.2 mg/dL Optimal <100

VLDL Cholesterol
(Calculated)
33.8 mg/dL 6-38

Total Protein
(Biuret test)
7.26 gm/dL 6.4-8.3

Albumin, Serum
(Bromocresol Green (BCG))
4.59 gm/dL 3.5-5.2

Globulin
(Calculated)
2.67 gm/dL 1.8-3.6

Haemoglobin (Hb)
(Sodium lauryl sulfate hemoglobin method (SLS))
16.2 gm/dL 13.0-17.0

Erythrocyte (RBC) Count
(Hydro Dynamic Focusing)
5.57 mill/cu.mm 4.50-5.50

PCV (Packed Cell Volume)
(Automated - Pulse Height Detection)
48.4 % 40.0-50.0

MCV (Mean Corpuscular Volume)
(Calculated)
86.9 fL 83.0-101.0

MCH (Mean Corpuscular Hb)
(Calculated)
29.1 pg 27.0-32.0

MCHC (Mean Corpuscular Hb Concn.)
(Calculated)
33.5 gm/dL 31.5-34.5

RDW (Red Cell Distribution Width)
(Calculated)
13.4 % 11.6-14.0%

Total Leucocytes (WBC) Count
(Automated Cell Counter)
6560 cells/cu.mm 4000-11000

Absolute Neutrophils Count
(Calculated)
4015 cells/cu.mm 2000-7000

Absolute Lymphocyte Count
(Calculated)
1771 cells/cu.mm 1000-3000

Absolute Eosinophil Count
(Calculated)
499 cells/cu.mm 20-500

Platelet count
(Hydro Dynamic Focusing)
216 10^3/µL 150-450

MPV (Mean Platelet Volume)
(Calculated)
10.4 fL 6-9.5

PDW (Platelet Distribution Width)
(Calculated)
12.5 fL 9-17

ESR (Erythrocyte Sedimentation Rate)
(EDTA Whole Blood, Capillary Photometry)
2 mm/hr 5-15

HbA1C- Glycated Haemoglobin
(High-Performance Liquid Chromatography (HPLC))
4.5 % Non-diabetic: <= 5.6

FT3 (Free Triiodothyronine)
(Serum, Electrochemiluminescence immunoassay (ECLIA))
3.16 pg/mL 2.0-4.4

FT4 (Free Thyroxine)
(Serum, Electrochemiluminescence immunoassay (ECLIA))
1.07 ng/dL 0.93-1.7

TSH (Thyroid Stimulating Hormone) - Ultrasensitive, Serum
(Serum, Electrochemiluminescence immunoassay (ECLIA))
7.080 µIU/mL 0.54-5.3

Vitamin D Total - 25 Hydroxy (OH)
(Serum, Electrochemiluminescence immunoassay (ECLIA))
19.70 ng/mL Insufficiency: 20-30

Vitamin B12 (Cyanocobalamin)
(Serum, Electrochemiluminescence immunoassay (ECLIA))
192.00 pg/mL 197-771

Total PSA (Prostate Specific Antigen)
(Serum, Electrochemiluminescence immunoassay (ECLIA))
1.580 ng/mL 0.0-3.1

Homocysteine
(Serum, Enzymatic)
17.80 µmol/L 0-15
"""

def test_comprehensive_extraction():
    """Test that we extract a wide variety of parameters from comprehensive report"""
    print("=" * 80)
    print("COMPREHENSIVE LAB PARAMETER EXTRACTION TEST")
    print("=" * 80)
    
    # Parse the report
    results = parse_blood_test(COMPREHENSIVE_REPORT_TEXT)
    
    print(f"\n[+] Successfully extracted {len(results)} parameters\n")
    
    # Expected categories and counts
    expected_categories = {
        "CBC": ["Hemoglobin", "RBC Count", "WBC Count", "Platelet Count", "Hematocrit", "MCV", "MCH", "MCHC", "RDW", "MPV", "PDW", "ESR"],
        "Metabolic Panel": ["Fasting Blood Glucose", "Glucose Post Prandial", "HbA1C", "BUN", "Creatinine", "Uric Acid"],
        "Electrolytes": ["Sodium", "Potassium", "Chloride", "Bicarbonate"],
        "Minerals": ["Calcium", "Phosphorus"],
        "Liver Function": ["Bilirubin Total", "Bilirubin Direct", "Bilirubin Indirect", "SGOT", "SGPT", "Alkaline Phosphatase", "Gamma GT"],
        "Lipid Profile": ["Total Cholesterol", "Triglycerides", "HDL Cholesterol", "LDL Cholesterol", "VLDL Cholesterol"],
        "Proteins": ["Total Protein", "Albumin", "Globulin"],
        "Iron Studies": ["Serum Iron", "TIBC", "UIBC", "Transferrin Saturation"],
        "Cardiac Enzymes": ["CPK Total", "LDH"],
        "Inflammatory": ["HsCRP"],
        "Thyroid": ["FT3", "FT4", "TSH"],
        "Vitamins": ["Vitamin D", "Vitamin B12"],
        "Other": ["PSA", "Homocysteine", "RA Factor"]
    }
    
    # Check each category
    total_expected = 0
    total_found = 0
    
    for category, params in expected_categories.items():
        found_params = [p for p in params if p in results]
        total_expected += len(params)
        total_found += len(found_params)
        
        print(f"\n{category}:")
        print(f"  Expected: {len(params)} | Found: {len(found_params)}")
        
        if found_params:
            print(f"  [+] Extracted: {', '.join(found_params)}")
        
        # Show missing parameters
        missing = [p for p in params if p not in results]
        if missing:
            print(f"  [-] Missing: {', '.join(missing)}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Extracted {total_found}/{total_expected} expected parameters ({total_found/total_expected*100:.1f}%)")
    print("=" * 80)
    
    # Show sample detailed results
    print("\n\n" + "=" * 80)
    print("SAMPLE DETAILED RESULTS (first 10 parameters)")
    print("=" * 80)
    
    for i, (param, data) in enumerate(list(results.items())[:10]):
        print(f"\n{i+1}. {param}:")
        print(f"   Value: {data.get('value')} {data.get('unit')}")
        print(f"   Status: {data.get('status')}")
        print(f"   Confidence: {data.get('confidence')}")
        print(f"   Reference: {data.get('range')}")
    
    # Generate insights for abnormal values
    insights = generate_insights(results)
    
    print("\n\n" + "=" * 80)
    print("INSIGHTS FOR ABNORMAL VALUES")
    print("=" * 80)
    print(f"\nSummary: {insights['summary']}\n")
    
    if insights['detailed_insights']:
        for insight in insights['detailed_insights']:
            print(f"\n* {insight['parameter']} ({insight['status']}):")
            print(f"  {insight['insight']}")
    else:
        print("\nNo abnormal values detected.")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    return len(results), total_found, total_expected

if __name__ == "__main__":
    extracted, found, expected = test_comprehensive_extraction()
    print(f"\n[+] Test successful: Analyzed {extracted} total parameters")
    print(f"[+] Coverage: {found}/{expected} documented parameters extracted")
