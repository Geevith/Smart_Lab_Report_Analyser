
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from backend.report_generator import generate_pdf

def create_sample():
    # Mock Data
    analysis_data = {
        "Hemoglobin": {"value": 14.5, "unit": "g/dL", "status": "Normal", "range": "13.0 - 17.0"},
        "WBC": {"value": 7.8, "unit": "K/uL", "status": "Normal", "range": "4.0 - 10.0"},
        "RBC": {"value": 4.9, "unit": "M/uL", "status": "Normal", "range": "4.5 - 5.9"},
        "Platelets": {"value": 250, "unit": "K/uL", "status": "Normal", "range": "150 - 450"},
        "Glucose": {"value": 95, "unit": "mg/dL", "status": "Normal", "range": "70 - 99"},
        "Total Cholesterol": {"value": 185, "unit": "mg/dL", "status": "Normal", "range": "< 200"},
        "LDL Cholesterol": {"value": 110, "unit": "mg/dL", "status": "High", "range": "< 100"},
        "HDL Cholesterol": {"value": 55, "unit": "mg/dL", "status": "Normal", "range": "> 40"},
        "Triglycerides": {"value": 140, "unit": "mg/dL", "status": "Normal", "range": "< 150"},
        "TSH": {"value": 2.5, "unit": "uIU/mL", "status": "Normal", "range": "0.4 - 4.0"},
        "Vitamin D": {"value": 25, "unit": "ng/mL", "status": "Low", "range": "30 - 100"}
    }

    insights_data = {
        "detailed_insights": [
            {
                "parameter": "LDL Cholesterol",
                "status": "High",
                "insight": "Elevated LDL cholesterol increases the risk of plaque accumulation in arteries (atherosclerosis). Dietary modifications lowering saturated fat intake are recommended.",
                "severity": "MEDIUM",
                "confidence_score": 92
            },
            {
                "parameter": "Vitamin D",
                "status": "Low",
                "insight": "Vitamin D deficiency may impact bone density and immune function. Consider increased sun exposure or supplementation as advised by a physician.",
                "severity": "LOW",
                "confidence_score": 88
            }
        ],
        "summary": "Patient shows generally good health but has elevated LDL cholesterol and mild Vitamin D deficiency.",
        "systems_impact": {
            "Cardiovascular": {"status": "Attention", "abnormal_count": 1, "total_count": 4},
            "Immune System": {"status": "Normal", "abnormal_count": 0, "total_count": 2},
            "Metabolism": {"status": "Attention", "abnormal_count": 1, "total_count": 3}
        }
    }
    
    systems_impact = {
         "Cardiovascular": {"status": "Attention", "abnormal_count": 1, "total_count": 4, "abnormal_parameters": [{"name": "LDL Cholesterol"}]},
         "Skeletal": {"status": "Attention", "abnormal_count": 1, "total_count": 1, "abnormal_parameters": [{"name": "Vitamin D"}]}
    }

    user_info = {
        "full_name": "Sample User",
        "date_of_birth": "1990-01-01",
        "gender": "Male",
        "email": "sample@example.com"
    }

    print("Generating PDF...")
    pdf_buffer = generate_pdf(analysis_data, insights_data, systems_impact, "Reference_Lab_Report.pdf", user_info)
    
    # Ensure directory exists
    os.makedirs("frontend/assets", exist_ok=True)
    
    output_path = "frontend/assets/sample_report.pdf"
    with open(output_path, "wb") as f:
        f.write(pdf_buffer.getvalue())
    
    print(f"Sample report created at: {output_path}")

if __name__ == "__main__":
    create_sample()
