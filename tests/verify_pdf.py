import requests

def test_generate_pdf():
    # Mock analysis data matching the structure expected by generate_report_endpoint
    payload = {
        "analysis": {
            "Hemoglobin": {
                "value": 11.5,
                "unit": "g/dL",
                "range": "13.0 - 17.0",
                "status": "Low"
            },
            "WBC Count": {
                "value": 8000,
                "unit": "cells/µL",
                "range": "4000 - 11000",
                "status": "Normal"
            }
        },
        "insights": {
            "summary": "Flagged 1 parameter(s).",
            "detailed_insights": [
                {
                    "parameter": "Hemoglobin (Low)",
                    "status": "Low",
                    "insight": "Low hemoglobin levels can be associated with anemia."
                }
            ],
            "disclaimer": "This is a test disclaimer."
        }
    }
    
    try:
        url = "http://127.0.0.1:8000/generate_report"
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type")
            if "application/pdf" in content_type:
                print("PDF GENERATION: SUCCESS")
                with open("test_report.pdf", "wb") as f:
                    f.write(response.content)
                print("PDF saved as 'test_report.pdf'")
            else:
                print(f"WRONG CONTENT TYPE: {content_type}")
        else:
            print(f"ENDPOINT FAILED: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"CONNECTION ERROR: {e}")

if __name__ == "__main__":
    test_generate_pdf()
