import re
from .abnormality_detector import AbnormalityDetector, TestStatus

# --- Normalization Constants ---
# Maps unit variants to their conversion factor against the BASE UNIT.
# Case-insensitive keys will be used in logic.
# UNIT_MULTIPLIERS removed - Logic moved to AbnormalityDetector.UnitNormalizer

# Regex patterns capturing (Value, Unit)
# Format: List of (regex_pattern, base_confidence_level)
# The regex MUST have two capturing groups: 1=Value, 2=Unit (optional)
PATTERNS = {
    # ========== COMPLETE BLOOD COUNT (CBC) ==========
    "Hemoglobin": [
        (r"Hemoglobin\s*\(Hb\)\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "High"),
        (r"Hemoglobin\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "High"),
        (r"Hb\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "Medium"),
        (r"Hgb\s*[:\-]?\s*([\d\.]+)\s*([\w/%µ]+)?", "Medium")
    ],
    "RBC Count": [
        (r"Erythrocyte\s*\(RBC\)\s*Count\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/^%µ]+)?", "High"),
        (r"Red Blood Cell\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/^%µ]+)?", "High"),
        (r"RBC\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/^%µ]+)?", "Medium"),
        (r"Erythrocyte Count\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/^%µ]+)?", "High")
    ],
    "WBC Count": [
        (r"Total Leucocytes?\s*\(WBC\)\s*Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"White Blood Cell\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"WBC\s?Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "Medium"),
        (r"Total Leucocyte Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"TLC\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "Medium")
    ],
    "Platelet Count": [
        (r"Platelet\s*[Cc]ount\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ]+)?", "High"),
        (r"PLT\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ]+)?", "Medium"),
        (r"Platelets\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ]+)?", "High")
    ],
    "Hematocrit": [
        (r"Hematocrit\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"Hct\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium"),
        (r"PCV\s*\(Packed Cell Volume\)\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"PCV\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "MCV": [
        (r"MCV\s*\(Mean Corpuscular Volume\)\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"Mean Corpuscular Volume\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"MCV\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "Medium")
    ],
    "MCH": [
        (r"MCH\s*\(Mean Corpuscular Hb\)\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"Mean Corpuscular Hemoglobin\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"MCH\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "Medium")
    ],
    "MCHC": [
        (r"MCHC\s*\(Mean Corpuscular Hb Concn\.\)\s*[:\-]?\s*([\d\.]+)\s*([\w/%]+)?", "High"),
        (r"Mean Corpuscular Hemoglobin Concentration\s*[:\-]?\s*([\d\.]+)\s*([\w/%]+)?", "High"),
        (r"MCHC\s*[:\-]?\s*([\d\.]+)\s*([\w/%]+)?", "Medium")
    ],
    "RDW": [
        (r"RDW\s*\(Red Cell Distribution Width\)\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"Red Cell Distribution Width\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"RDW\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "MPV": [
        (r"MPV\s*\(Mean Platelet Volume\)\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"Mean Platelet Volume\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"MPV\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "Medium")
    ],
    "PDW": [
        (r"PDW\s*\(Platelet Distribution Width\)\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"Platelet Distribution Width\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "High"),
        (r"PDW\s*[:\-]?\s*([\d\.]+)\s*([\w]+)?", "Medium")
    ],
    "Absolute Neutrophil Count": [
        (r"Absolute Neutrophils Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"ANC\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "Medium")
    ],
    "Absolute Lymphocyte Count": [
        (r"Absolute Lymphocyte Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"ALC\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "Medium")
    ],
    "Absolute Eosinophil Count": [
        (r"Absolute Eosinophil Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "High"),
        (r"AEC\s*[:\-]?\s*([\d\.]+)\s*([\w/^∧%µ\.]+)?", "Medium")
    ],
    "ESR": [
        (r"ESR\s*\(Erythrocyte Sedimentation Rate\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Erythrocyte Sedimentation Rate\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ESR\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== METABOLIC PANEL ==========
    "Fasting Blood Glucose": [
        (r"Glucose\s*Fasting\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "High"),
        (r"Fasting Blood Glucose\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "High"),
        (r"Fasting Blood Sugar\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "High"),
        (r"FBS\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "Medium")
    ],
    "Glucose Post Prandial": [
        (r"Glucose\s*Post\s*Prandial\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "High"),
        (r"Post\s*Prandial\s*Blood\s*Sugar\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "High"),
        (r"PPBS\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "Medium"),
        (r"PP\s*Glucose\s*[:\-]?\s*([\d\.]+)\s*([\w0-9/]+)?", "Medium")
    ],
    "HbA1C": [
        (r"HbA1[Cc]\s*[-\s]*Glycated\s*Haemoglobin\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"Glycated\s*Haemoglobin\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"HbA1[Cc]\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium"),
        (r"A1C\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "BUN": [
        (r"BUN[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Blood Urea Nitrogen\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"BUN\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Creatinine": [
        (r"Creatinine[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Creatinine\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Creatinine\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Uric Acid": [
        (r"Uric Acid[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Uric Acid\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Uric Acid\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== ELECTROLYTES ==========
    "Sodium": [
        (r"Sodium[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Sodium\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Na\+?\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Potassium": [
        (r"Potassium[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Potassium\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"K\+?\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Chloride": [
        (r"Chloride[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Chloride\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Cl\-?\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Bicarbonate": [
        (r"Bicarbonate\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"HCO3\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"CO2\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== MINERALS ==========
    "Calcium": [
        (r"Calcium[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Calcium\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Ca\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Low")
    ],
    "Phosphorus": [
        (r"Phosphorus[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Phosphorus\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Phosphate\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== LIVER FUNCTION TESTS ==========
    "Bilirubin Total": [
        (r"Bilirubin Total\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Total Bilirubin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Bilirubin Direct": [
        (r"Bilirubin Direct\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Direct Bilirubin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Bilirubin Indirect": [
        (r"Bilirubin[-\s]*Indirect\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Indirect Bilirubin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "SGOT": [
        (r"SGOT\s*\(AST\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"AST\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"SGOT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "SGPT": [
        (r"SGPT\s*\(ALT\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ALT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"SGPT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Alkaline Phosphatase": [
        (r"Alkaline Phosphatase[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Alkaline Phosphatase\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ALP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Gamma GT": [
        (r"Gamma GT\s*\(GGTP\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"GGT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"GGTP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== LIPID PROFILE ==========
    "Total Cholesterol": [
        (r"Cholesterol Total[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Total Cholesterol\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Cholesterol\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Triglycerides": [
        (r"Triglycerides[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Triglycerides\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"TG\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "HDL Cholesterol": [
        (r"HDL Cholesterol Direct\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"HDL Cholesterol\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"HDL\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "LDL Cholesterol": [
        (r"LDL Cholesterol\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"LDL\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "VLDL Cholesterol": [
        (r"VLDL Cholesterol\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"VLDL\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== PROTEINS ==========
    "Total Protein": [
        (r"Total Protein\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Protein[,\s]*Total\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Albumin": [
        (r"Albumin[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Albumin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Globulin": [
        (r"Globulin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    
    # ========== IRON STUDIES ==========
    "Serum Iron": [
        (r"Iron[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Iron\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "TIBC": [
        (r"TIBC\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Total Iron Binding Capacity\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "UIBC": [
        (r"UIBC\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Unsaturated Iron Binding Capacity\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Transferrin Saturation": [
        (r"Transferrin Saturation\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High"),
        (r"Transferin Saturation\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "High")
    ],
    
    # ========== CARDIAC ENZYMES ==========
    "CPK Total": [
        (r"CPK Total\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Creatine Phosphokinase\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"CPK\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "LDH": [
        (r"LDH\s*\(Lactate Dehydrogenase\)[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Lactate Dehydrogenase\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"LDH\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== INFLAMMATORY MARKERS ==========
    "HsCRP": [
        (r"HsCRP\s*\(High Sensitivity CRP\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"High Sensitivity CRP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"HsCRP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"hs-CRP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    
    # ========== THYROID FUNCTION ==========
    "FT3": [
        (r"FT3\s*\(Free Triiodothyronine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Free T3\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"FT3\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "FT4": [
        (r"FT4\s*\(Free Thyroxine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Free T4\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"FT4\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "TSH": [
        (r"TSH\s*\(Thyroid Stimulating Hormone\)\s*[-\s]*Ultrasensitive[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/µ]+)?", "High"),
        (r"Thyroid Stimulating Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/µ]+)?", "High"),
        (r"TSH\s*[:\-]?\s*([\d\.]+)\s*([\w/µ]+)?", "Medium")
    ],
    
    # ========== VITAMINS ==========
    "Vitamin D": [
        (r"Vitamin D Total\s*[-\s]*25 Hydroxy\s*\(OH\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"25[-\s]*OH Vitamin D\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Vitamin D\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"25[-\s]*Hydroxy Vitamin D\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Vitamin B12": [
        (r"Vitamin B12\s*\(Cyanocobalamin\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Vitamin B12\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"B12\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium"),
        (r"Cyanocobalamin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    
    # ========== OTHER MARKERS ==========
    "PSA": [
        (r"Total PSA\s*\(Prostate Specific Antigen\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Prostate Specific Antigen\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"PSA\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Homocysteine": [
        (r"Homocysteine\s*[:\-]?\s*([\d\.]+)\s*([\wµ/]+)?", "High")
    ],
    "RA Factor": [
        (r"RA\s*\(Rheumatoid Arthritis\)\s*Factor[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Rheumatoid Factor\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"RA Factor\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"RF\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],

    # ========== IRON / MINERAL EXTRAS ==========
    "Ferritin": [
        (r"Ferritin[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Ferritin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Ferritin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Magnesium": [
        (r"Magnesium[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Serum Magnesium\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Mg\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Zinc": [
        (r"Zinc[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Serum Zinc\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Copper": [
        (r"Copper[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Serum Copper\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Folate": [
        (r"Folate[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Folic Acid\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Folate\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Manganese": [
        (r"Manganese[,\s]*Serum\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== HORMONES ==========
    "Insulin": [
        (r"Insulin\s*\(Fasting\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Serum Insulin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Fasting Insulin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Insulin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "C-Peptide": [
        (r"C[-\s]*Peptide\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Cortisol": [
        (r"Cortisol\s*\(AM\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Serum Cortisol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Cortisol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "Prolactin": [
        (r"Prolactin\s*\(PRL\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Serum Prolactin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Prolactin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "FSH": [
        (r"FSH\s*\(Follicle Stimulating Hormone\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Follicle Stimulating Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"FSH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "LH": [
        (r"LH\s*\(Luteinizing Hormone\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Luteinizing Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"LH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "Estradiol": [
        (r"Estradiol\s*\(E2\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"17[-\s]*Beta Estradiol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Estradiol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "Testosterone": [
        (r"Testosterone\s*\(Total\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Total Testosterone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Testosterone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "DHEA-S": [
        (r"DHEA[-\s]*S(?:ulfate)?\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Dehydroepiandrosterone Sulfate\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Progesterone": [
        (r"Progesterone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "PTH": [
        (r"Parathyroid Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"PTH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Intact PTH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Aldosterone": [
        (r"Aldosterone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Renin": [
        (r"Renin\s*Activity\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Renin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "ACTH": [
        (r"ACTH\s*\(Adrenocorticotropic Hormone\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Adrenocorticotropic Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"ACTH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "Growth Hormone": [
        (r"Growth Hormone\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"GH\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "IGF-1": [
        (r"IGF[-\s]*1\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Insulin[-\s]*like Growth Factor\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== TUMOR MARKERS ==========
    "AFP": [
        (r"AFP\s*\(Alpha Fetoprotein\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Alpha Fetoprotein\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"AFP\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "CEA": [
        (r"CEA\s*\(Carcinoembryonic Antigen\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Carcinoembryonic Antigen\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"CEA\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "CA 125": [
        (r"CA[-\s]*125\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Cancer Antigen 125\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],
    "CA 19-9": [
        (r"CA[-\s]*19[-\s]*9\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],
    "Beta-HCG": [
        (r"Beta[-\s]*HCG\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Human Chorionic Gonadotropin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"HCG\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "Medium")
    ],
    "Free PSA": [
        (r"Free PSA\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "CA 15-3": [
        (r"CA[-\s]*15[-\s]*3\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],

    # ========== ADVANCED CARDIAC ==========
    "Troponin I": [
        (r"Troponin[-\s]*I\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"cTnI\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Troponin T": [
        (r"Troponin[-\s]*T\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"cTnT\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "BNP": [
        (r"BNP\s*\(B[-\s]*type Natriuretic Peptide\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"B[-\s]*type Natriuretic Peptide\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"BNP\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "NT-proBNP": [
        (r"NT[-\s]*proBNP\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "CK-MB": [
        (r"CK[-\s]*MB\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Creatine Kinase MB\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Myoglobin": [
        (r"Myoglobin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== COAGULATION ==========
    "Prothrombin Time": [
        (r"Prothrombin Time\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"PT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "INR": [
        (r"INR\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"International Normalised Ratio\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "APTT": [
        (r"APTT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Activated Partial Thromboplastin Time\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"PTT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "D-Dimer": [
        (r"D[-\s]*Dimer\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Fibrinogen": [
        (r"Fibrinogen\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],

    # ========== ADVANCED LIPIDS ==========
    "ApoB": [
        (r"Apolipoprotein B\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ApoB\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "ApoA1": [
        (r"Apolipoprotein A[-\s]*1\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ApoA[-\s]*1\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Lipoprotein(a)": [
        (r"Lipoprotein\s*\(a\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Lp\s*\(a\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== AUTOIMMUNE / INFLAMMATION ==========
    "CRP": [
        (r"C[-\s]*Reactive Protein\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"CRP\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "ANA": [
        (r"ANA\s*\(Antinuclear Antibody\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Antinuclear Antibody\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"ANA\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Anti-CCP": [
        (r"Anti[-\s]*CCP\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Anti[-\s]*Cyclic Citrullinated Peptide\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Anti-dsDNA": [
        (r"Anti[-\s]*dsDNA\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Anti[-\s]*Double Stranded DNA\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],
    "Complement C3": [
        (r"Complement\s*C3\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"C3\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Complement C4": [
        (r"Complement\s*C4\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"C4\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Anti-TPO": [
        (r"Anti[-\s]*Thyroid Peroxidase\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Anti[-\s]*TPO\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"TPO Antibody\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],
    "Anti-TG": [
        (r"Anti[-\s]*Thyroglobulin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High"),
        (r"Anti[-\s]*TG\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5IU]+)?", "High")
    ],

    # ========== THYROID ADVANCED ==========
    "T3 Total": [
        (r"T3\s*\(Triiodothyronine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Total T3\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"T3\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "T4 Total": [
        (r"T4\s*\(Thyroxine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Total T4\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"T4\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "Thyroglobulin": [
        (r"Thyroglobulin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== DIABETES ADVANCED ==========
    "HOMA-IR": [
        (r"HOMA[-\s]*IR\s*[:\-]?\s*([\d\.]+)\s*", "High"),
        (r"Insulin Resistance Index\s*[:\-]?\s*([\d\.]+)\s*", "High")
    ],
    "Fructosamine": [
        (r"Fructosamine\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],

    # ========== KIDNEY ADVANCED ==========
    "eGFR": [
        (r"eGFR\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Estimated GFR\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Glomerular Filtration Rate\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Cystatin C": [
        (r"Cystatin C\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Urine Creatinine": [
        (r"Urine Creatinine\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Microalbumin": [
        (r"Microalbumin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Urine Microalbumin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Albumin Creatinine Ratio\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Uric Acid Urine": [
        (r"Urine Uric Acid\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],

    # ========== LIVER ADVANCED ==========
    "GGT": [
        (r"GGT\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Gamma Glutamyl Transferase\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "5-Nucleotidase": [
        (r"5[-\s]*Nucleotidase\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Ammonia": [
        (r"Ammonia[,\s]*Plasma\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Serum Ammonia\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Ammonia\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],
    "Prealbumin": [
        (r"Prealbumin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Transthyretin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],

    # ========== INFECTIOUS DISEASE ==========
    "HBsAg": [
        (r"HBsAg\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Hepatitis B Surface Antigen\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Anti-HCV": [
        (r"Anti[-\s]*HCV\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Hepatitis C Antibody\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "VDRL": [
        (r"VDRL\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Rapid Plasma Reagin\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"RPR\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "Medium")
    ],
    "Procalcitonin": [
        (r"Procalcitonin\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"PCT\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "Medium")
    ],

    # ========== CBC DIFFERENTIALS ==========
    "Neutrophils Percent": [
        (r"Neutrophils?\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Lymphocytes Percent": [
        (r"Lymphocytes?\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Monocytes Percent": [
        (r"Monocytes?\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Eosinophils Percent": [
        (r"Eosinophils?\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Basophils Percent": [
        (r"Basophils?\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Absolute Monocyte Count": [
        (r"Absolute Monocyte Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^\u2227%\xb5\.]+)?", "High")
    ],
    "Absolute Basophil Count": [
        (r"Absolute Basophil Count\s*[:\-]?\s*([\d\.]+)\s*([\w/^\u2227%\xb5\.]+)?", "High")
    ],
    "Band Neutrophils": [
        (r"Band Neutrophils\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],
    "Immature Granulocytes": [
        (r"Immature Granulocytes\s*[:\-]?\s*([\d\.]+)\s*([%]+)?", "Medium")
    ],

    # ========== URINE TESTS ==========
    "Urine Protein": [
        (r"Urine Protein\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Protein\s*\(Urine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "Urine Glucose": [
        (r"Urine Glucose\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"Glucose\s*\(Urine\)\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],
    "24h Urine Protein": [
        (r"24[\s]*Hour Urine Protein\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High"),
        (r"24[-\s]*h Urine Protein\s*[:\-]?\s*([\d\.]+)\s*([\w/]+)?", "High")
    ],

    # ========== VITAMINS ADVANCED ==========
    "Vitamin A": [
        (r"Vitamin A\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Retinol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Vitamin E": [
        (r"Vitamin E\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Alpha Tocopherol\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Vitamin C": [
        (r"Vitamin C\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High"),
        (r"Ascorbic Acid\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
    "Vitamin K": [
        (r"Vitamin K\s*[:\-]?\s*([\d\.]+)\s*([\w/\xb5]+)?", "High")
    ],
}


# Reference ranges (Approximate generic adult values)
# Format: (min, max, unit) - These are the TARGET BASE UNITS
REFERENCE_RANGES = {
    # ========== COMPLETE BLOOD COUNT (CBC) ==========
    "Hemoglobin": (13.0, 17.0, "g/dL"),  # Male range; Female: 12.0-15.5
    "RBC Count": (4.5, 5.9, "million/µL"),  # Male; Female: 4.1-5.1
    "WBC Count": (4000, 11000, "cells/µL"),
    "Platelet Count": (150000, 450000, "cells/µL"),
    "Hematocrit": (40, 50, "%"),  # Male; Female: 36-44
    "MCV": (80, 100, "fL"),
    "MCH": (27, 31, "pg"),
    "MCHC": (32, 36, "g/dL"),
    "RDW": (11.6, 14.0, "%"),
    "MPV": (6.0, 9.5, "fL"),
    "PDW": (9.0, 17.0, "fL"),
    "Absolute Neutrophil Count": (2000, 7000, "cells/µL"),
    "Absolute Lymphocyte Count": (1000, 3000, "cells/µL"),
    "Absolute Eosinophil Count": (20, 500, "cells/µL"),
    "ESR": (0, 20, "mm/hr"),  # Male: 0-15; Female: 0-20
    
    # ========== METABOLIC PANEL ==========
    "Fasting Blood Glucose": (70, 100, "mg/dL"),
    "Glucose Post Prandial": (70, 140, "mg/dL"),
    "HbA1C": (4.0, 5.6, "%"),
    "BUN": (6, 20, "mg/dL"),
    "Creatinine": (0.67, 1.17, "mg/dL"),  # Male: 0.74-1.35; Female: 0.59-1.04
    "Uric Acid": (3.4, 7.0, "mg/dL"),  # Male: 3.4-7.0; Female: 2.4-6.0
    
    # ========== ELECTROLYTES ==========
    "Sodium": (136, 145, "mmol/L"),
    "Potassium": (3.5, 5.1, "mmol/L"),
    "Chloride": (98, 107, "mmol/L"),
    "Bicarbonate": (22, 29, "mmol/L"),
    
    # ========== MINERALS ==========
    "Calcium": (8.6, 10.0, "mg/dL"),
    "Phosphorus": (2.5, 4.5, "mg/dL"),
    
    # ========== LIVER FUNCTION TESTS ==========
    "Bilirubin Total": (0.0, 1.2, "mg/dL"),
    "Bilirubin Direct": (0.0, 0.3, "mg/dL"),
    "Bilirubin Indirect": (0.1, 1.0, "mg/dL"),
    "SGOT": (0, 40, "U/L"),
    "SGPT": (0, 41, "U/L"),
    "Alkaline Phosphatase": (40, 129, "U/L"),
    "Gamma GT": (0, 60, "U/L"),
    
    # ========== LIPID PROFILE ==========
    "Total Cholesterol": (0, 200, "mg/dL"),  # Desirable < 200
    "Triglycerides": (0, 150, "mg/dL"),  # Normal < 150
    "HDL Cholesterol": (40, 200, "mg/dL"),  # Higher is better; Low risk > 60
    "LDL Cholesterol": (0, 100, "mg/dL"),  # Optimal < 100
    "VLDL Cholesterol": (6, 38, "mg/dL"),
    
    # ========== PROTEINS ==========
    "Total Protein": (6.4, 8.3, "g/dL"),
    "Albumin": (3.5, 5.2, "g/dL"),
    "Globulin": (1.8, 3.6, "g/dL"),
    
    # ========== IRON STUDIES ==========
    "Serum Iron": (33, 193, "µg/dL"),  # Male: 65-175; Female: 50-170
    "TIBC": (250, 450, "µg/dL"),
    "UIBC": (125, 345, "µg/dL"),
    "Transferrin Saturation": (14, 50, "%"),
    
    # ========== CARDIAC ENZYMES ==========
    "CPK Total": (0, 190, "U/L"),  # Male: 38-174; Female: 26-140
    "LDH": (0, 250, "U/L"),
    
    # ========== INFLAMMATORY MARKERS ==========
    "HsCRP": (0.0, 3.0, "mg/L"),  # Low risk < 1.0; Average: 1.0-3.0; High > 3.0
    
    # ========== THYROID FUNCTION ==========
    "FT3": (2.0, 4.4, "pg/mL"),
    "FT4": (0.93, 1.7, "ng/dL"),
    "TSH": (0.54, 5.3, "µIU/mL"),
    
    # ========== VITAMINS ==========
    "Vitamin D": (30, 100, "ng/mL"),  # Sufficiency: 30-100; Insufficiency: 20-30
    "Vitamin B12": (197, 771, "pg/mL"),
    
    # ========== OTHER MARKERS ==========
    "PSA": (0.0, 4.0, "ng/mL"),  # Age-dependent; this is general
    "Homocysteine": (0, 15, "µmol/L"),
    "RA Factor": (0, 14, "IU/mL"),  # Non-reactive < 14

    # ========== IRON / MINERAL EXTRAS ==========
    "Ferritin": (12, 300, "ng/mL"),  # Male: 12-300; Female: 12-150
    "Magnesium": (1.7, 2.2, "mg/dL"),
    "Zinc": (60, 120, "µg/dL"),
    "Copper": (70, 140, "µg/dL"),
    "Folate": (3.1, 17.5, "ng/mL"),
    "Manganese": (4.7, 18.3, "µg/L"),

    # ========== HORMONES ==========
    "Insulin": (2.6, 24.9, "µIU/mL"),  # Fasting
    "C-Peptide": (0.8, 3.85, "ng/mL"),
    "Cortisol": (6.2, 19.4, "µg/dL"),  # AM: 6.2-19.4; PM: 2.3-11.9
    "Prolactin": (2.5, 17.0, "ng/mL"),  # Male; Female: 1.9-25.0
    "FSH": (1.5, 12.4, "mIU/mL"),  # varies by sex/cycle phase
    "LH": (1.7, 8.6, "mIU/mL"),
    "Estradiol": (7.6, 42.6, "pg/mL"),  # Male; Female varies by cycle
    "Testosterone": (240, 950, "ng/dL"),  # Male; Female: 8-60 ng/dL
    "DHEA-S": (80, 560, "µg/dL"),  # Male; Female: 35-430
    "Progesterone": (0.2, 1.4, "ng/mL"),  # Male; Female varies
    "PTH": (15, 65, "pg/mL"),
    "Aldosterone": (7.5, 30, "ng/dL"),  # Supine
    "Renin": (0.5, 3.4, "ng/mL/hr"),
    "ACTH": (10, 60, "pg/mL"),
    "Growth Hormone": (0.0, 10.0, "ng/mL"),
    "IGF-1": (101, 303, "ng/mL"),  # Age/sex dependent

    # ========== TUMOR MARKERS ==========
    "AFP": (0.0, 8.1, "IU/mL"),
    "CEA": (0.0, 5.0, "ng/mL"),  # Non-smoker; Smoker: < 10
    "CA 125": (0.0, 35.0, "U/mL"),
    "CA 19-9": (0.0, 37.0, "U/mL"),
    "Beta-HCG": (0.0, 5.0, "mIU/mL"),  # Non-pregnant
    "Free PSA": (0.0, 1.5, "ng/mL"),
    "CA 15-3": (0.0, 30.0, "U/mL"),

    # ========== ADVANCED CARDIAC ==========
    "Troponin I": (0.0, 0.04, "ng/mL"),
    "Troponin T": (0.0, 0.014, "ng/mL"),
    "BNP": (0, 100, "pg/mL"),
    "NT-proBNP": (0, 125, "pg/mL"),
    "CK-MB": (0, 25, "U/L"),
    "Myoglobin": (0, 90, "ng/mL"),

    # ========== COAGULATION ==========
    "Prothrombin Time": (11.0, 13.5, "seconds"),
    "INR": (0.8, 1.1, ""),
    "APTT": (25, 35, "seconds"),
    "D-Dimer": (0.0, 0.5, "µg/mL"),
    "Fibrinogen": (200, 400, "mg/dL"),

    # ========== ADVANCED LIPIDS ==========
    "ApoB": (40, 120, "mg/dL"),
    "ApoA1": (101, 199, "mg/dL"),
    "Lipoprotein(a)": (0, 30, "mg/dL"),

    # ========== AUTOIMMUNE / INFLAMMATION ==========
    "CRP": (0.0, 6.0, "mg/L"),
    "ANA": (0, 1, "titer"),  # < 1:80 typically negative
    "Anti-CCP": (0, 17, "U/mL"),
    "Anti-dsDNA": (0, 30, "IU/mL"),
    "Complement C3": (90, 180, "mg/dL"),
    "Complement C4": (16, 47, "mg/dL"),
    "Anti-TPO": (0, 34, "IU/mL"),
    "Anti-TG": (0, 115, "IU/mL"),

    # ========== THYROID ADVANCED ==========
    "T3 Total": (80, 200, "ng/dL"),
    "T4 Total": (5.1, 14.1, "µg/dL"),
    "Thyroglobulin": (1.6, 59.9, "ng/mL"),

    # ========== DIABETES ADVANCED ==========
    "HOMA-IR": (0.0, 2.5, ""),  # < 2.5 normal insulin sensitivity
    "Fructosamine": (200, 285, "µmol/L"),

    # ========== KIDNEY ADVANCED ==========
    "eGFR": (60, 120, "mL/min/1.73m²"),
    "Cystatin C": (0.51, 0.98, "mg/L"),
    "Urine Creatinine": (700, 1800, "mg/day"),
    "Microalbumin": (0, 30, "mg/g"),

    # ========== LIVER ADVANCED ==========
    "GGT": (0, 55, "U/L"),
    "Ammonia": (15, 45, "µg/dL"),
    "Prealbumin": (16, 35, "mg/dL"),

    # ========== INFECTIOUS DISEASE ==========
    "Procalcitonin": (0.0, 0.5, "ng/mL"),  # < 0.5: low risk infection

    # ========== CBC DIFFERENTIALS ==========
    "Neutrophils Percent": (40, 75, "%"),
    "Lymphocytes Percent": (20, 45, "%"),
    "Monocytes Percent": (2, 10, "%"),
    "Eosinophils Percent": (1, 6, "%"),
    "Basophils Percent": (0, 1, "%"),
    "Absolute Monocyte Count": (200, 1000, "cells/µL"),
    "Absolute Basophil Count": (0, 100, "cells/µL"),

    # ========== VITAMINS ADVANCED ==========
    "Vitamin A": (30, 65, "µg/dL"),
    "Vitamin E": (5.5, 17.0, "mg/L"),
    "Vitamin C": (0.4, 2.0, "mg/dL"),
}

# ─────────────────────────────────────────────────────────────────────────────
# Generic fallback: captures any test line not already matched by PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

# Words that look like test names but are NOT lab tests — skip these
_SKIP_WORDS = {
    "name", "date", "age", "sex", "gender", "lab", "doctor", "ref", "report",
    "patient", "page", "test", "result", "sample", "specimen", "time", "unit",
    "method", "hospital", "clinic", "address", "phone", "email", "signature",
    "collected", "reported", "received", "printed", "your", "note", "remarks",
    "interpretation", "value", "normal", "range", "reference", "total",
    "blood", "urine", "serum", "plasma", "whole", "technician", "pathologist",
}

# Generic line pattern: TestName: numeric_value optional_unit optional_(range)
_GENERIC_LINE = re.compile(
    r'^([A-Za-z][A-Za-z0-9 /\-\(\)\.]{1,55}?)'
    r'\s*[:\-|]\s*'
    r'(\d[\d\.]*)'                      # numeric value
    r'\s*([A-Za-z%µ\/\^\*]+)?'          # optional unit
    r'(?:\s+[\(\[<>]?\s*([\d\.]+)\s*[-–]\s*([\d\.]+)\s*[\)\]]?)?',  # optional range
    re.IGNORECASE
)


def _is_likely_test_name(name: str) -> bool:
    """Return True if the candidate string looks like a real lab test name."""
    name_stripped = name.strip()
    if len(name_stripped) < 2 or len(name_stripped) > 60:
        return False
    # Must start with a letter
    if not name_stripped[0].isalpha():
        return False
    # Must contain at least one letter
    if not any(c.isalpha() for c in name_stripped):
        return False
    # Skip purely numeric strings
    try:
        float(name_stripped)
        return False
    except ValueError:
        pass
    # Skip blocklist words
    lower = name_stripped.lower()
    if lower in _SKIP_WORDS:
        return False
    if any(lower == skip for skip in _SKIP_WORDS):
        return False
    return True


def parse_unknown_tests(text: str, already_known: set) -> dict:
    """
    Generic fallback extractor.
    Scans each line looking for 'TestName: value unit (range)' patterns.
    Skips anything already captured by the known PATTERNS.
    Returns results tagged with confidence='Low' and source='auto-detected'.
    """
    unknown_results = {}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = _GENERIC_LINE.match(line)
        if not m:
            continue

        raw_name = m.group(1).strip().rstrip(':- ')
        value_str = m.group(2)
        raw_unit = m.group(3) or ""
        range_min_str = m.group(4)
        range_max_str = m.group(5)

        if not _is_likely_test_name(raw_name):
            continue

        # Skip if already captured by the known patterns
        if raw_name in already_known:
            continue
        # Also skip case-insensitive duplicates
        if any(raw_name.lower() == k.lower() for k in already_known):
            continue

        try:
            value_float = float(value_str)
        except ValueError:
            continue

        # Determine status from printed range if available
        status_str = "Unknown"
        range_str = ""
        if range_min_str and range_max_str:
            try:
                low = float(range_min_str)
                high = float(range_max_str)
                range_str = f"{low} - {high} {raw_unit}".strip()
                if value_float < low:
                    status_str = "Low"
                elif value_float > high:
                    status_str = "High"
                else:
                    status_str = "Normal"
            except ValueError:
                pass

        unknown_results[raw_name] = {
            "value": value_float,
            "unit": raw_unit.strip() if raw_unit else "",
            "original_value": value_str,
            "original_unit": raw_unit.strip() if raw_unit else "",
            "range": range_str,
            "status": status_str,
            "confidence": "Low",
            "severity": "LOW",
            "notes": ["Auto-detected — test not in knowledge base. Verify with your doctor."],
            "source": "auto-detected",
            "range_type": "from_report",
            "range_disclaimer": "Range extracted from the report itself. Always consult your doctor.",
        }

    return unknown_results


def parse_blood_test(text: str) -> dict:
    """
    Parses extracted text for blood test parameters using AbnormalityDetector
    for robust, production-grade analysis.
    After the known-patterns pass, runs a generic fallback to catch any remaining tests.
    """
    results = {}
    detector = AbnormalityDetector()
    
    for param, patterns in PATTERNS.items():
        for pattern, base_confidence in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value_str = match.group(1)
                    raw_unit = match.group(2) if match.lastindex >= 2 else None
                    
                    # Construct reference range string if we have one
                    ref_range_str = ""
                    if param in REFERENCE_RANGES:
                        min_v, max_v, target_unit = REFERENCE_RANGES[param]
                        # Pass unit in string so AbnormalityDetector can extract it for normalization
                        ref_range_str = f"{min_v} - {max_v} {target_unit}"
                        # Note: We rely on AbnormalityDetector to normalize units if raw_unit differs from target_unit
                    
                    # Detect abnormality
                    # We pass the raw value string so detector can handle OCR errors
                    result = detector.detect_abnormality(
                        test_name=param,
                        value=value_str,
                        unit=raw_unit if raw_unit else "",
                        reference_range=ref_range_str
                    )
                    
                    # Convert TestStatus enum to Title Case string
                    status_str = result.status.value.title()
                    
                    # CRITICAL STATUS PRESERVATION
                    # We previously remapped Critical -> High/Low. 
                    # Now we KEEP Critical for the UI to display urgency.
                    if result.status == TestStatus.CRITICAL:
                        status_str = "Critical"

                    # Build result dictionary
                    # Note: We use result.value (float) for values
                    results[param] = {
                        "value": result.value if isinstance(result.value, (int, float)) else 0.0,
                        "unit": result.unit,
                        "original_value": value_str,
                        "original_unit": result.unit, 
                        "range": result.reference_range,
                        "status": status_str,
                        "confidence": "High" if result.confidence_score > 0.8 else ("Medium" if result.confidence_score > 0.5 else "Low"),
                        "severity": result.severity.value,
                        "notes": result.notes,
                        
                        # Range Metadata (Safety & Transparency)
                        "range_type": "generic",  # Future: 'sex_specific', 'age_specific'
                        "range_disclaimer": "General adult range. Individual ranges may vary by age, sex, and health status."
                    }
                    
                    break # Stop after first match
                except Exception as e:
                    # Fallback or log error
                    continue 

    # ── Generic fallback: capture any remaining test lines not already matched ──
    try:
        unknown = parse_unknown_tests(text, already_known=set(results.keys()))
        for name, data in unknown.items():
            if name not in results:  # Never overwrite known tests
                results[name] = data
    except Exception:
        pass  # Fallback must never break the main pipeline

    return results


def deduplicate_parameters(results: dict, source_tracking: bool = True) -> dict:
    """
    Deduplicates repeated parameters, keeping the highest confidence value.
    
    Args:
        results: Dictionary of parsed parameters
        source_tracking: Whether to track which sources/pages contributed
        
    Returns:
        Deduplicated results with merged notes
    """
    # Since results is already a dict with parameter names as keys,
    # duplicates from the same document would have been overwritten.
    # This function is more useful when merging results from multiple pages.
    # For now, we'll add utility for future multi-page merging.
    
    # Group by parameter name (already done by dict structure)
    deduplicated = {}
    
    for param_name, param_data in results.items():
        if param_name in deduplicated:
            # Keep the one with higher confidence
            existing_conf = _conf_to_score(deduplicated[param_name].get('confidence', 'Low'))
            new_conf = _conf_to_score(param_data.get('confidence', 'Low'))
            
            if new_conf > existing_conf:
                # Merge notes from both
                merged_notes = list(set(
                    deduplicated[param_name].get('notes', []) + 
                    param_data.get('notes', [])
                ))
                param_data['notes'] = merged_notes
                deduplicated[param_name] = param_data
            else:
                # Keep existing, but merge notes
                merged_notes = list(set(
                    deduplicated[param_name].get('notes', []) + 
                    param_data.get('notes', [])
                ))
                deduplicated[param_name]['notes'] = merged_notes
        else:
            deduplicated[param_name] = param_data
    
    return deduplicated


def merge_multi_page_results(page_results: list) -> dict:
    """
    Merges parameter results from multiple pages with deduplication.
    
    Args:
        page_results: List of dicts, each containing parsed parameters from a page
        
    Returns:
        Merged and deduplicated results
    """
    merged = {}
    duplicates_removed = 0
    
    for page_idx, page_result in enumerate(page_results, 1):
        for param_name, param_data in page_result.items():
            # Add source page tracking
            param_data['source_page'] = page_idx
            
            if param_name in merged:
                duplicates_removed += 1
                
                # Keep the one with higher confidence
                existing_conf = _conf_to_score(merged[param_name].get('confidence', 'Low'))
                new_conf = _conf_to_score(param_data.get('confidence', 'Low'))
                
                if new_conf > existing_conf:
                    # Merge notes and track sources
                    merged_notes = list(set(
                        merged[param_name].get('notes', []) + 
                        param_data.get('notes', [])
                    ))
                    param_data['notes'] = merged_notes
                    
                    # Track source pages
                    source_pages = merged[param_name].get('source_pages', [merged[param_name].get('source_page', 1)])
                    source_pages.append(page_idx)
                    param_data['source_pages'] = source_pages
                    
                    merged[param_name] = param_data
                else:
                    # Keep existing, but add this page to sources
                    merged_notes = list(set(
                        merged[param_name].get('notes', []) + 
                        param_data.get('notes', [])
                    ))
                    merged[param_name]['notes'] = merged_notes
                    
                    source_pages = merged[param_name].get('source_pages', [merged[param_name].get('source_page', 1)])
                    source_pages.append(page_idx)
                    merged[param_name]['source_pages'] = source_pages
            else:
                merged[param_name] = param_data
    
    return merged, duplicates_removed


def _conf_to_score(confidence: str) -> float:
    """Convert confidence string to numeric score for comparison"""
    confidence_map = {
        'High': 0.9,
        'Medium': 0.6,
        'Low': 0.3
    }
    return confidence_map.get(confidence, 0.5)
