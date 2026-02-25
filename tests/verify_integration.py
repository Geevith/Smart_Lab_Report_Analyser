import requests
import json

def test_analyze_endpoint():
    url = "http://localhost:8000/analyze"
    
    # Create a dummy file in memory
    files = {
        'file': ('test_report.pdf', b'Hemoglobin: 12.5 g/dL\nRBC Count: 4.8 million/uL\nPotassium: 6.2 mmol/L', 'application/pdf')
    }
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Response received.")
            
            # Check for new keys
            if "parameters" in data:
                print(f"✅ 'parameters' key present with {len(data['parameters'])} items.")
                # Verify content
                hemo = next((p for p in data['parameters'] if p['name'] == 'Hemoglobin'), None)
                if hemo:
                    print(f"   - Hemoglobin detected: {hemo['value']} {hemo['unit']} ({hemo['status']})")
                
                potassium = next((p for p in data['parameters'] if p['name'] == 'Potassium'), None)
                if potassium:
                    print(f"   - Potassium detected: {potassium['value']} {potassium['unit']} ({potassium['status']})")
                    if potassium['status'] == 'High':
                         print("   ✅ Abnormality Detection Working (High Potassium)")
                    else:
                         print(f"   ⚠️ Abnormality Detection check: Status is {potassium['status']}")

            else:
                print("❌ 'parameters' key MISSING.")
                
            if "summary" in data:
                print("✅ 'summary' key present.")
                print(f"   - Stats: {data['summary']}")
            else:
                print("❌ 'summary' key MISSING.")
                
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Ensure 'backend/main.py' is running on port 8000.")

if __name__ == "__main__":
    test_analyze_endpoint()
