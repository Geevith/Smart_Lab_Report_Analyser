# Medical insights rules
# Mapping: (Parameter, Status) -> Insight
# Using safe, non-diagnostic language.

# NOTE: This legacy dict is kept for backwards compatibility
# Primary insights now loaded from knowledge_base.json
ANALYSIS_RULES = {
    # ========== COMPLETE BLOOD COUNT (CBC) ==========
    ("Hemoglobin", "Low"): "Low hemoglobin levels can be associated with anemia, which may result from iron deficiency, vitamin deficiencies, or other factors. Consult a healthcare provider for proper evaluation.",
    ("Hemoglobin", "High"): "Elevated hemoglobin levels can occur due to dehydration, smoking, living at high altitudes, or other underlying conditions. Using this result for self-diagnosis is not recommended.",
    ("WBC Count", "High"): "A high white blood cell count (Leukocytosis) is often a sign of the body reacting to an infection or inflammation, but can have other causes.",
    ("WBC Count", "Low"): "A low white blood cell count (Leukopenia) can be seen in various conditions, including viral infections or bone marrow issues. Medical advice is recommended.",
    ("Platelet Count", "Low"): "Low platelet count (Thrombocytopenia) may affect blood clotting. Common causes include viral infections, nutrient deficiencies, or medication side effects.",
    ("Platelet Count", "High"): "High platelet count (Thrombocytosis) can satisfy a normal reaction to inflammation or infection, but persistent elevation should be evaluated by a doctor.",
    ("RBC Count", "Low"): "A lower than normal Red Blood Cell count is frequently seen in anemia.",
    ("RBC Count", "High"): "A higher than normal Red Blood Cell count (Erythrocytosis) can be related to low oxygen levels, pulmonary issues, or dehydration.",
    ("Hematocrit", "Low"): "Low hematocrit indicates a lower percentage of red blood cells, commonly seen in anemia.",
    ("Hematocrit", "High"): "High hematocrit often typically suggests dehydration or an increased production of red blood cells.",
    ("MCV", "Low"): "Low MCV (Microcytosis) often indicates smaller than average red blood cells, which is commonly associated with iron deficiency.",
    ("MCV", "High"): "High MCV (Macrocytosis) indicates larger than average red blood cells, which can be seen in Vitamin B12 or Folate deficiency.",
    ("MCH", "Low"): "Low MCH suggests decreased hemoglobin content in red blood cells, often seen in iron deficiency anemia.",
    ("MCH", "High"): "High MCH may be associated with macrocytic anemias or vitamin B12/folate deficiency.",
    ("MCHC", "Low"): "Low MCHC indicates lower hemoglobin concentration in red blood cells, commonly seen in iron deficiency anemia.",
    ("MCHC", "High"): "High MCHC is uncommon but may be seen in conditions like hereditary spherocytosis.",
    ("RDW", "High"): "Elevated RDW indicates high variation in red blood cell size, which can be seen in various types of anemia, nutritional deficiencies, or mixed conditions.",
    ("MPV", "Low"): "Low MPV may indicate bone marrow disorders or certain types of anemia.",
    ("MPV", "High"): "High MPV can suggest increased platelet production, which may be seen in conditions like thrombocytopenia or after bleeding.",
    ("Absolute Neutrophil Count", "Low"): "Low neutrophil count (Neutropenia) can increase infection risk and may be caused by medications, infections, or bone marrow disorders.",
    ("Absolute Neutrophil Count", "High"): "High neutrophil count can indicate bacterial infection, inflammation, or stress response.",
    ("Absolute Lymphocyte Count", "Low"): "Low lymphocyte count can be associated with viral infections, certain medications, or immune system disorders.",
    ("Absolute Lymphocyte Count", "High"): "High lymphocyte count may indicate viral infections, chronic infections, or lymphoproliferative disorders.",
    ("Absolute Eosinophil Count", "High"): "Elevated eosinophils can be associated with allergic conditions, parasitic infections, or certain skin disorders.",
    ("ESR", "High"): "Elevated ESR may indicate inflammation, infection, autoimmune disorders, or other underlying conditions.",
    ("ESR", "Low"): "Generally not clinically significant but can be seen in conditions like sickle cell anemia or polycythemia.",
    
    # ========== METABOLIC PANEL ==========
    ("Fasting Blood Glucose", "High"): "Elevated fasting glucose levels can be associated with insulin resistance, pre-diabetes, or diabetes mellitus. Lifestyle modification and medical consultation are recommended.",
    ("Fasting Blood Glucose", "Low"): "Low fasting glucose (hypoglycemia) may be caused by medication, prolonged fasting, or hormonal imbalances. Please discuss with your healthcare provider.",
    ("Glucose Post Prandial", "High"): "Elevated post-meal glucose can indicate impaired glucose tolerance or diabetes. Regular monitoring and dietary modifications may be beneficial.",
    ("Glucose Post Prandial", "Low"): "Low post-meal glucose is uncommon but can occur with certain medications or reactive hypoglycemia.",
    ("HbA1C", "High"): "Elevated HbA1C indicates poor long-term blood sugar control and may suggest pre-diabetes or diabetes. This marker reflects average glucose levels over the past 2-3 months.",
    ("HbA1C", "Low"): "Very low HbA1C may be seen in conditions with rapid red blood cell turnover or certain anemias. Clinical correlation is recommended.",
    ("BUN", "High"): "Elevated BUN (Blood Urea Nitrogen) can indicate reduced kidney function, dehydration, high protein diet, or other conditions. Follow up with your healthcare provider.",
    ("BUN", "Low"): "Low BUN is generally not concerning and can occur with low protein diet, over-hydration, or liver disease.",
    ("Creatinine", "High"): "Elevated creatinine levels may indicate reduced kidney function or dehydration. This is an important marker for kidney health and warrants medical evaluation.",
    ("Creatinine", "Low"): "Low creatinine is uncommon and may be seen with low muscle mass, malnutrition, or certain muscle diseases.",
    ("Uric Acid", "High"): "Elevated uric acid (Hyperuricemia) can be associated with gout, kidney stones, or kidney disease. Dietary modifications may be recommended.",
    ("Uric Acid", "Low"): "Low uric acid is generally not concerning but can be seen with certain medications or genetic conditions.",
    
    # ========== ELECTROLYTES ==========
    ("Sodium", "High"): "Elevated sodium (Hypernatremia) can result from dehydration, excessive salt intake, or certain medical conditions. Adequate hydration is important.",
    ("Sodium", "Low"): "Low sodium (Hyponatremia) can be caused by excessive fluid intake, certain medications, or underlying conditions. This requires medical evaluation.",
    ("Potassium", "High"): "Elevated potassium (Hyperkalemia) can be serious and may result from kidney issues, certain medications, or metabolic disturbances. Immediate medical attention may be needed.",
    ("Potassium", "Low"): "Low potassium (Hypokalemia) can affect heart rhythm and muscle function. Causes include diuretics, vomiting, diarrhea, or inadequate dietary intake.",
    ("Chloride", "High"): "Elevated chloride can be associated with dehydration, kidney disease, or certain metabolic conditions.",
    ("Chloride", "Low"): "Low chloride can result from prolonged vomiting, certain medications, or metabolic alkalosis.",
    ("Bicarbonate", "High"): "Elevated bicarbonate may indicate metabolic alkalosis, which can result from various conditions including excessive vomiting or certain medications.",
    ("Bicarbonate", "Low"): "Low bicarbonate may suggest metabolic acidosis, which can be associated with kidney disease, diabetes, or other metabolic conditions.",
    
    # ========== MINERALS ==========
    ("Calcium", "High"): "Elevated calcium (Hypercalcemia) can be associated with parathyroid disorders, certain cancers, or excessive vitamin D intake. Medical evaluation is recommended.",
    ("Calcium", "Low"): "Low calcium (Hypocalcemia) can result from vitamin D deficiency, parathyroid disorders, or kidney disease. May affect bone health and muscle function.",
    ("Phosphorus", "High"): "Elevated phosphorus can be associated with kidney disease, hypoparathyroidism, or excessive dietary intake.",
    ("Phosphorus", "Low"): "Low phosphorus can result from malnutrition, vitamin D deficiency, or certain medications. May affect bone health and energy metabolism.",
    
    # ========== LIVER FUNCTION TESTS ==========
    ("Bilirubin Total", "High"): "Elevated total bilirubin can indicate liver disease, bile duct obstruction, or increased red blood cell breakdown (hemolysis). Medical evaluation is important.",
    ("Bilirubin Direct", "High"): "Elevated direct bilirubin suggests liver or bile duct problems and requires medical investigation.",
    ("Bilirubin Indirect", "High"): "Elevated indirect bilirubin can indicate increased red blood cell breakdown (hemolysis) or certain genetic conditions like Gilbert's syndrome.",
    ("SGOT", "High"): "Elevated SGOT (AST) can indicate liver damage, muscle injury, or heart problems. Further evaluation is needed to determine the cause.",
    ("SGPT", "High"): "Elevated SGPT (ALT) is more specific to liver damage and can be caused by hepatitis, fatty liver disease, medications, or alcohol use.",
    ("Alkaline Phosphatase", "High"): "Elevated alkaline phosphatase can indicate liver disease, bone disorders, or bile duct obstruction. Context and additional tests help determine the cause.",
    ("Gamma GT", "High"): "Elevated GGT is often associated with liver disease, bile duct problems, or alcohol consumption. It can help differentiate the source of elevated alkaline phosphatase.",
    
    # ========== LIPID PROFILE ==========
    ("Total Cholesterol", "High"): "Elevated total cholesterol is a risk factor for cardiovascular disease. Lifestyle modifications including diet and exercise, along with medical guidance, are recommended.",
    ("Triglycerides", "High"): "Elevated triglycerides increase cardiovascular risk and can be associated with obesity, diabetes, or metabolic syndrome. Dietary changes and weight loss may help.",
    ("HDL Cholesterol", "Low"): "Low HDL (good cholesterol) is a risk factor for heart disease. Regular exercise and healthy fats can help increase HDL levels.",
    ("LDL Cholesterol", "High"): "Elevated LDL (bad cholesterol) is a major risk factor for atherosclerosis and cardiovascular disease. Diet, exercise, and possibly medication may be recommended.",
    ("VLDL Cholesterol", "High"): "Elevated VLDL cholesterol can contribute to atherosclerosis and is often associated with high triglycerides.",
    
    # ========== PROTEINS ==========
    ("Total Protein", "Low"): "Low total protein can indicate liver disease, kidney disease, malnutrition, or malabsorption disorders.",
    ("Total Protein", "High"): "Elevated total protein can be seen with dehydration, chronic inflammation, or certain blood disorders.",
    ("Albumin", "Low"): "Low albumin can indicate liver disease, kidney disease, malnutrition, or chronic inflammation. Albumin is important for maintaining fluid balance.",
    ("Albumin", "High"): "Elevated albumin is usually due to dehydration.",
    ("Globulin", "Low"): "Low globulin can suggest immune deficiency or liver disease.",
    ("Globulin", "High"): "Elevated globulin can be associated with chronic infections, inflammation, or certain blood disorders.",
    
    # ========== IRON STUDIES ==========
    ("Serum Iron", "Low"): "Low serum iron can indicate iron deficiency anemia, chronic inflammation, or malabsorption. Iron supplementation may be needed.",
    ("Serum Iron", "High"): "Elevated serum iron can be seen with hemochromatosis (iron overload), certain anemias, or excessive supplementation.",
    ("TIBC", "High"): "Elevated TIBC often indicates iron deficiency, as the body produces more transferrin to capture available iron.",
    ("TIBC", "Low"): "Low TIBC can be seen with iron overload, chronic illness, or malnutrition.",
    ("Transferrin Saturation", "Low"): "Low transferrin saturation suggests iron deficiency and indicates that available iron is insufficient.",
    ("Transferrin Saturation", "High"): "High transferrin saturation can indicate iron overload conditions like hemochromatosis.",
    
    # ========== CARDIAC ENZYMES ==========
    ("CPK Total", "High"): "Elevated CPK can indicate muscle damage from heart attack, skeletal muscle injury, intense exercise, or muscle diseases.",
    ("LDH", "High"): "Elevated LDH can be seen with tissue damage including heart attack, liver disease, hemolysis, or certain cancers. Additional tests help determine the source.",
    
    # ========== INFLAMMATORY MARKERS ==========
    ("HsCRP", "High"): "Elevated high-sensitivity CRP indicates inflammation and is associated with increased cardiovascular risk. Lifestyle modifications and risk factor management are important.",
    
    # ========== THYROID FUNCTION ==========
    ("FT3", "High"): "Elevated Free T3 can indicate hyperthyroidism (overactive thyroid), which can cause symptoms like weight loss, rapid heartbeat, and anxiety.",
    ("FT3", "Low"): "Low Free T3 can be seen in hypothyroidism, severe illness, or certain medications.",
    ("FT4", "High"): "Elevated Free T4 can indicate hyperthyroidism, thyroiditis, or excessive thyroid medication.",
    ("FT4", "Low"): "Low Free T4 suggests hypothyroidism (underactive thyroid), which can cause fatigue, weight gain, and cold intolerance.",
    ("TSH", "High"): "Elevated TSH indicates hypothyroidism (underactive thyroid). The pituitary gland increases TSH to stimulate the thyroid. Thyroid hormone replacement may be needed.",
    ("TSH", "Low"): "Low TSH can indicate hyperthyroidism (overactive thyroid) or excessive thyroid hormone replacement. The pituitary reduces TSH when thyroid hormone levels are high.",
    
    # ========== VITAMINS ==========
    ("Vitamin D", "Low"): "Vitamin D deficiency can affect bone health, immune function, and overall well-being. Supplementation and sun exposure may be recommended.",
    ("Vitamin D", "High"): "Very high vitamin D levels can result from excessive supplementation and may cause hypercalcemia. Reduce supplementation and consult your doctor.",
    ("Vitamin B12", "Low"): "Vitamin B12 deficiency can cause anemia, neurological symptoms, and fatigue. Common in vegetarians, elderly, or those with absorption issues. Supplementation is often effective.",
    ("Vitamin B12", "High"): "Elevated B12 is usually due to recent supplementation and is generally not concerning.",
    
    # ========== OTHER MARKERS ==========
    ("PSA", "High"): "Elevated PSA can be associated with prostate enlargement, prostatitis, or prostate cancer. Further evaluation by a urologist is recommended. Note that PSA can also be elevated after certain procedures or activities.",
    ("Homocysteine", "High"): "Elevated homocysteine is a risk factor for cardiovascular disease and stroke. Vitamin B6, B12, and folate supplementation may help reduce levels.",
    ("RA Factor", "High"): "Positive or elevated Rheumatoid Factor can indicate rheumatoid arthritis or other autoimmune conditions. Clinical correlation with symptoms is important.",

    # ========== IRON / MINERAL EXTRAS ==========
    ("Ferritin", "Low"): "Low ferritin indicates depleted iron stores, the most common cause of iron deficiency anemia. Dietary changes or iron supplementation may be recommended by your doctor.",
    ("Ferritin", "High"): "Elevated ferritin can indicate iron overload (hemochromatosis), liver disease, chronic inflammation, or infections. Further evaluation is recommended.",
    ("Magnesium", "Low"): "Low magnesium can cause muscle cramps, irregular heartbeat, and fatigue. Common causes include poor diet, alcohol use, or certain medications.",
    ("Magnesium", "High"): "Elevated magnesium usually results from excessive supplementation or kidney disease.",
    ("Zinc", "Low"): "Zinc deficiency can impair immune function, wound healing, and growth.",
    ("Folate", "Low"): "Low folate can lead to megaloblastic anemia and is especially important during pregnancy. Supplementation is often recommended.",

    # ========== HORMONES ==========
    ("Insulin", "High"): "Elevated fasting insulin suggests insulin resistance, a risk factor for type 2 diabetes and metabolic syndrome. Lifestyle changes (diet and exercise) are the primary intervention.",
    ("Insulin", "Low"): "Low insulin can be seen in type 1 diabetes or very early type 2 diabetes. Discuss with your endocrinologist.",
    ("Cortisol", "High"): "Elevated cortisol may suggest Cushing's syndrome, chronic stress, or steroid medication use. Symptoms can include weight gain, fatigue, and high blood pressure.",
    ("Cortisol", "Low"): "Low cortisol may indicate adrenal insufficiency (Addison's disease), which can cause fatigue, weight loss, and low blood pressure.",
    ("Prolactin", "High"): "Elevated prolactin can be caused by a pituitary tumor (prolactinoma), certain medications, hypothyroidism, or stress. It can affect fertility.",
    ("FSH", "High"): "Elevated FSH in women may indicate reduced ovarian reserve or menopause. In men, it can suggest primary testicular failure.",
    ("FSH", "Low"): "Low FSH may indicate pituitary or hypothalamic dysfunction, affecting reproductive function.",
    ("LH", "High"): "Elevated LH in women can indicate PCOS or menopause. In men, it may suggest primary hypogonadism.",
    ("LH", "Low"): "Low LH can indicate pituitary or hypothalamic disorders affecting fertility and hormone balance.",
    ("Estradiol", "High"): "Elevated estradiol in women can occur with ovarian cysts. In men, it may indicate liver disease.",
    ("Estradiol", "Low"): "Low estradiol in women can indicate menopause or premature ovarian failure, leading to bone loss.",
    ("Testosterone", "Low"): "Low testosterone can cause fatigue, reduced libido, muscle loss, and mood changes.",
    ("Testosterone", "High"): "Elevated testosterone in women may suggest PCOS or adrenal tumors. Discuss with your doctor.",
    ("DHEA-S", "High"): "Elevated DHEA-S may indicate adrenal overactivity. In women, it can contribute to androgen excess symptoms.",
    ("PTH", "High"): "Elevated PTH (hyperparathyroidism) causes calcium release from bones, leading to kidney stones, bone pain, and fatigue.",
    ("PTH", "Low"): "Low PTH (hypoparathyroidism) can cause low calcium, leading to muscle cramps and tingling.",
    ("IGF-1", "High"): "Elevated IGF-1 may indicate acromegaly (excess growth hormone in adults). Specialist evaluation is recommended.",
    ("IGF-1", "Low"): "Low IGF-1 can indicate growth hormone deficiency, malnutrition, or liver disease.",

    # ========== TUMOR MARKERS ==========
    ("AFP", "High"): "Elevated AFP can be associated with liver cancer, testicular cancer, or elevated during pregnancy. Further evaluation is essential — this marker requires clinical context.",
    ("CEA", "High"): "Elevated CEA is associated with colorectal and other cancers, as well as smoking or inflammatory bowel disease. Further evaluation is essential.",
    ("CA 125", "High"): "Elevated CA 125 can indicate ovarian cancer, but also endometriosis, fibroids, or pelvic conditions. Clinical evaluation is important.",
    ("CA 19-9", "High"): "Elevated CA 19-9 can be associated with pancreatic, gallbladder, or bile duct cancers, or pancreatitis. Requires further investigation.",
    ("Beta-HCG", "High"): "Elevated beta-HCG may indicate pregnancy, gestational trophoblastic disease, or certain testicular cancers in men.",
    ("CA 15-3", "High"): "Elevated CA 15-3 is used to monitor breast cancer. Elevation may indicate progression or recurrence.",

    # ========== ADVANCED CARDIAC ==========
    ("Troponin I", "High"): "Elevated Troponin I indicates heart muscle damage, most commonly from a heart attack. This requires immediate medical evaluation.",
    ("Troponin T", "High"): "Elevated Troponin T indicates heart muscle injury from a heart attack. Seek immediate emergency care.",
    ("BNP", "High"): "Elevated BNP is a key marker of heart failure. Higher levels indicate more severe heart failure. Immediate medical evaluation is recommended.",
    ("NT-proBNP", "High"): "Elevated NT-proBNP is a sensitive heart failure marker. This warrants urgent medical evaluation.",
    ("CK-MB", "High"): "Elevated CK-MB indicates heart muscle damage. Seek immediate medical evaluation.",
    ("Myoglobin", "High"): "Elevated myoglobin can indicate muscle injury including heart attack. Requires immediate clinical evaluation.",

    # ========== COAGULATION ==========
    ("Prothrombin Time", "High"): "Prolonged prothrombin time means blood takes longer to clot, which can indicate liver disease, vitamin K deficiency, or anticoagulant medications.",
    ("INR", "High"): "Elevated INR means blood takes longer than normal to clot, common with warfarin therapy or liver disease. Discuss your target range with your doctor.",
    ("INR", "Low"): "Low INR suggests faster-than-normal clotting, which may increase the risk of blood clots. Evaluation may be needed.",
    ("APTT", "High"): "Prolonged APTT can indicate clotting factor deficiencies, liver disease, or anticoagulants. Medical evaluation is needed.",
    ("D-Dimer", "High"): "Elevated D-Dimer can indicate blood clot formation as in DVT or pulmonary embolism. Requires immediate medical evaluation.",
    ("Fibrinogen", "Low"): "Low fibrinogen can impair clotting and may indicate DIC, liver disease, or bleeding risk.",
    ("Fibrinogen", "High"): "Elevated fibrinogen indicates inflammation and is a cardiovascular risk marker.",

    # ========== ADVANCED LIPIDS ==========
    ("ApoB", "High"): "Elevated ApoB is a strong predictor of cardiovascular disease risk. Lifestyle modifications and possibly medication may be recommended.",
    ("ApoA1", "Low"): "Low ApoA1 (the main HDL protein) is associated with increased cardiovascular risk.",
    ("Lipoprotein(a)", "High"): "Elevated Lp(a) is a genetically determined cardiovascular risk factor. Specialist consultation is recommended.",

    # ========== AUTOIMMUNE / INFLAMMATION ==========
    ("CRP", "High"): "Elevated CRP indicates active inflammation from infections, autoimmune conditions, or cardiovascular disease risk. The source should be identified.",
    ("ANA", "High"): "A positive ANA test can be seen in autoimmune conditions like lupus or rheumatoid arthritis. A positive result requires further specialist evaluation.",
    ("Anti-CCP", "High"): "Elevated Anti-CCP antibodies are highly specific for rheumatoid arthritis (RA). A rheumatologist consultation is recommended.",
    ("Anti-dsDNA", "High"): "Elevated Anti-dsDNA antibodies are highly specific for systemic lupus erythematosus (SLE). Specialist evaluation is recommended.",
    ("Complement C3", "Low"): "Low C3 can indicate active autoimmune disease (especially lupus), complement deficiency, or liver disease.",
    ("Complement C4", "Low"): "Low C4 can be seen in lupus, hereditary angioedema, or complement deficiency.",
    ("Anti-TPO", "High"): "Elevated Anti-TPO antibodies indicate autoimmune thyroid disease, such as Hashimoto's thyroiditis or Graves' disease.",
    ("Anti-TG", "High"): "Elevated Anti-Thyroglobulin antibodies indicate autoimmune thyroid disease or are used in thyroid cancer monitoring.",

    # ========== THYROID ADVANCED ==========
    ("T3 Total", "High"): "Elevated total T3 indicates hyperthyroidism, causing weight loss, rapid heartbeat, and tremors.",
    ("T3 Total", "Low"): "Low total T3 can indicate hypothyroidism or 'sick euthyroid syndrome' during serious illness.",
    ("T4 Total", "High"): "Elevated total T4 suggests hyperthyroidism.",
    ("T4 Total", "Low"): "Low total T4 suggests hypothyroidism. Thyroid hormone replacement may be needed.",

    # ========== DIABETES ADVANCED ==========
    ("HOMA-IR", "High"): "Elevated HOMA-IR indicates insulin resistance, a key risk factor for type 2 diabetes. Diet, exercise, and weight loss are the primary interventions.",
    ("Fructosamine", "High"): "Elevated fructosamine reflects poor short-term blood sugar control over the past 2-3 weeks.",

    # ========== KIDNEY ADVANCED ==========
    ("eGFR", "Low"): "Low eGFR indicates reduced kidney filtration function. Chronic kidney disease is staged by eGFR level. Nephrology referral may be needed.",
    ("Microalbumin", "High"): "Elevated microalbumin is an early marker of kidney damage, particularly in diabetes and hypertension.",
    ("Cystatin C", "High"): "Elevated Cystatin C is an early, sensitive marker of reduced kidney function.",

    # ========== LIVER ADVANCED ==========
    ("GGT", "High"): "Elevated GGT is associated with liver disease, bile duct problems, or alcohol consumption.",
    ("Ammonia", "High"): "Elevated ammonia can indicate liver failure. Severe elevation can cause confusion (hepatic encephalopathy). Seek immediate medical care.",
    ("Prealbumin", "Low"): "Low prealbumin is a sensitive marker for malnutrition or liver disease.",

    # ========== INFECTIOUS DISEASE ==========
    ("Procalcitonin", "High"): "Elevated procalcitonin is a specific marker for bacterial infection and sepsis. Higher levels indicate more serious infection. Immediate evaluation is needed.",

    # ========== VITAMINS ADVANCED ==========
    ("Vitamin A", "Low"): "Vitamin A deficiency can cause night blindness, increased infection risk, and skin problems.",
    ("Vitamin A", "High"): "Elevated Vitamin A (hypervitaminosis A) can be toxic, causing headaches and liver damage. Usually from excessive supplementation.",
    ("Vitamin E", "Low"): "Vitamin E deficiency can cause nerve damage and muscle weakness, especially with fat malabsorption disorders.",
    ("Vitamin C", "Low"): "Low Vitamin C can lead to scurvy, causing fatigue, gum disease, and poor wound healing.",
}


DISCLAIMER = "IMPORTANT: This analysis is generated by an AI system and is for informational purposes only. It is NOT a medical diagnosis. Always consult a qualified healthcare professional for interpretation of your lab results and medical advice."

def generate_insights(analysis_result, user_demographics=None):
    """
    Generate comprehensive insights with contextual analysis, audit trails, 
    confidence scores, follow-up recommendations, personalization, and lifestyle advice.
    
    Enhanced with:
    - Knowledge Base Migration (JSON-based rules)
    - Personalization (age, gender, ethnicity)
    - Severity Prioritization (4-tier system)
    - Lifestyle Recommendations & External Resources
    
    Args:
        analysis_result: Dict of parameter analysis results
        user_demographics: Optional dict with 'age', 'gender', 'ethnicity' keys
    """
    # Import all enhancement modules
    try:
        from backend.clinical_intelligence import (
            generate_contextual_insights, 
            calculate_insight_confidence,
            _calculate_deviation_percentage
        )
        from backend.audit_trail import AuditTrailManager
        from backend.followup_recommendations import get_followup_recommendations
        from backend.knowledge_base_loader import get_knowledge_base_loader
        from backend.personalization_engine import get_personalization_engine
        from backend.severity_engine import get_severity_engine
        from backend.lifestyle_recommendations import get_lifestyle_recommendations
        use_enhanced_features = True
    except ImportError as e:
        print(f"Import warning - using fallback mode: {e}")
        use_enhanced_features = False
    
    insights = []
    abnormal_count = 0
    summary = "All parameters within normal ranges."
    
    # Convert analysis_result to parameters dict
    parameters_dict = {}
    for param_name, param_data in analysis_result.items():
        if isinstance(param_data, dict):
            status = param_data.get("status", "Normal")
            if status in ["High", "Low", "Critical"]:
                abnormal_count += 1
            
            parameters_dict[param_name] = {
                "value": param_data.get("value"),
                "unit": param_data.get("unit", ""),
                "range": param_data.get("range", ""),
                "status": status.upper() if status != "Normal" else "NORMAL",
                "severity": param_data.get("severity", "MEDIUM")
            }
    
    if use_enhanced_features and abnormal_count > 0:
        # Initialize enhancement modules
        kb_loader = get_knowledge_base_loader()
        personalization_engine = get_personalization_engine()
        severity_engine = get_severity_engine()
        lifestyle_module = get_lifestyle_recommendations()
        audit_manager = AuditTrailManager()
        
        # Use contextual insights
        contextual_insights = generate_contextual_insights(parameters_dict)
        
        for ctx_insight in contextual_insights:
            param_data = parameters_dict.get(ctx_insight.parameter, {})
            
            # Get knowledge base insight
            kb_insight = kb_loader.get_insight(
                ctx_insight.parameter,
                ctx_insight.severity,
                user_age=user_demographics.get("age") if user_demographics else None,
                user_gender=user_demographics.get("gender") if user_demographics else None
            )
            
            # Use KB insight if available, otherwise use contextual
            base_insight_text = kb_insight.get("insight") if kb_insight else ctx_insight.message
            
            # Apply personalization
            personalized = personalization_engine.personalize_insight(
                base_insight_text,
                ctx_insight.parameter,
                param_data.get("status", "NORMAL"),
                user_demographics
            )
            
            # Calculate severity
            severity_info = severity_engine.calculate_severity(
                ctx_insight.parameter,
                param_data.get("status", "NORMAL"),
                value=param_data.get("value"),
                reference_range=param_data.get("range")
            )
            
            # Get lifestyle recommendations
            lifestyle = lifestyle_module.get_lifestyle_advice(
                ctx_insight.parameter,
                param_data.get("status"),
                kb_insight
            )
            
            # Get symptom questions
            symptom_questions = lifestyle_module.get_symptom_questions(
                ctx_insight.parameter,
                param_data.get("status"),
                kb_insight
            )
            
            # Get external resources
            external_resources = lifestyle_module.get_external_resources(
                ctx_insight.parameter,
                param_data.get("status"),
                kb_insight
            )
            
            # Calculate deviation and confidence
            deviation = _calculate_deviation_percentage(param_data)
            supporting_count = len(ctx_insight.supporting_params)
            confidence_score, confidence_rationale = calculate_insight_confidence(
                param_data, supporting_count
            )
            
            # Create audit trail
            audit_record = audit_manager.create_audit_record(
                parameter_name=ctx_insight.parameter,
                parameter_value=param_data.get("value"),
                reference_range=param_data.get("range"),
                status=param_data.get("status", "NORMAL"),
                severity=severity_info["severity"],
                deviation_pct=deviation,
                confidence=confidence_score
            )
            
            # Get visual styling
            visual_hierarchy = severity_engine.get_visual_hierarchy(severity_info["severity"])
            
            insights.append({
                "parameter": ctx_insight.parameter,
                "status": param_data.get("status"),
                "insight_type": ctx_insight.insight_type,
                "insight": personalized["insight"],
                "personalization_applied": personalized["personalization_applied"],
                "personalization_context": personalized["context"],
                "supporting_params": ctx_insight.supporting_params,
                "severity": severity_info["severity"],
                "severity_label": {
                    "CRITICAL": "Critical - Urgent Attention Required",
                    "HIGH": "Significant Deviation",
                    "MEDIUM": "Moderate Deviation",
                    "LOW": "Mild Deviation"
                }.get(severity_info["severity"], "Normal"),
                "action_level": severity_info["action_level"],
                "priority_score": severity_info["priority_score"],
                "visual_hierarchy": visual_hierarchy,
                "confidence_score": confidence_score,
                "confidence_rationale": confidence_rationale,
                "lifestyle_recommendations": lifestyle,
                "symptom_questions": symptom_questions,
                "external_resources": external_resources,
                "audit_trail": audit_record.to_dict()
            })
        
        # Generate follow-up recommendations
        followup_recs = get_followup_recommendations(parameters_dict)
        
        # Sort insights by priority score (highest first)
        insights.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Update summary
        summary = f"Flagged {abnormal_count} parameter(s) outside standard reference ranges. See details below."
        
        return {
            "summary": summary,
            "detailed_insights": insights,
            "followup_recommendations": [
                {
                    "parameter": rec.parameter_name,
                    "tests": rec.suggested_tests,
                    "rationale": rec.rationale,
                    "priority": rec.priority,
                    "disclaimer": rec.disclaimer
                }
                for rec in followup_recs
            ],
            "disclaimer": DISCLAIMER,
            "total_abnormal": abnormal_count,
            "knowledge_base_version": kb_loader.get_version(),
            "personalization_enabled": user_demographics is not None
        }
    
    else:
        # Fallback to original simple insights
        for param, data in analysis_result.items():
            if not isinstance(data, dict):
                continue
            
            status = data.get("status", "Normal")
            if status != "Normal":
                key = (param, status.capitalize())
                if key in ANALYSIS_RULES:
                    insights.append({
                        "parameter": param,
                        "status": status,
                        "insight": ANALYSIS_RULES[key],
                        "severity": data.get("severity", "MEDIUM"),
                        "severity_label": "Moderate Deviation"
                    })
                else:
                    insights.append({
                        "parameter": param,
                        "status": status,
                        "insight": f"{param} is {status}. Please discuss this result with your doctor.",
                        "severity": "MEDIUM",
                        "severity_label": "Moderate Deviation"
                    })
    
        if abnormal_count > 0:
            summary = f"Flagged {abnormal_count} parameter(s) outside standard reference ranges. See details below."
    
        return {
            "summary": summary,
            "detailed_insights": insights,
            "disclaimer": DISCLAIMER
        }
