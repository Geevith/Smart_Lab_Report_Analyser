import requests
import json

url = "http://localhost:8000/generate_report"
data = {
    "analysis": {
        "Hemoglobin": {
            "value": 14.5,
            "unit": "g/dL",
            "status": "Normal"
        }
    },
    "insights": {
        "detailed_insights": []
    },
    "filename": "TestReport"
}

try:
    response = requests.post(url, json=data)
    if response.status_code == 200:
        with open("test_report.pdf", "wb") as f:
            f.write(response.content)
        print("SUCCESS: PDF generated and saved as test_report.pdf")
    else:
        print(f"FAILED: {response.status_code} - {response.text}")
except Exception as e:
    print(f"ERROR: {str(e)}")
