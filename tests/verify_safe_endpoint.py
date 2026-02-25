import requests
import sys

def test_backend_disclaimer():
    try:
        # Dummy PDF content (text based for extractor)
        filename = "verify_safe.txt"
        with open(filename, "w") as f:
            f.write("Hemoglobin: 10.0") # Low
            
        with open(filename, "rb") as f:
            files = {'file': (filename, f, 'text/plain')}
            resp = requests.post("http://127.0.0.1:8000/analyze", files=files)
            
        if resp.status_code == 200:
            data = resp.json()
            if "insights" in data:
                insights = data["insights"]
                #Check disclaimer
                if "disclaimer" in insights and "informational purposes only" in insights["disclaimer"]:
                    print("DISCLAIMER FOUND: SUCCESS")
                else:
                    print("DISCLAIMER MISSING OR INCORRECT: FAILED")
                    
                # Check safe language in detailed insights
                if "detailed_insights" in insights and len(insights["detailed_insights"]) > 0:
                    insight_text = insights["detailed_insights"][0]["insight"]
                    if "associated with" in insight_text or "Common causes" in insight_text or "Consult a healthcare" in insight_text:
                         print("SAFE LANGUAGE DETECTED: SUCCESS")
                    else:
                         print(f"SAFE LANGUAGE NOT DETECTED: FAILED. Got: {insight_text}")
                else:
                    print("NO DETAILED INSIGHTS FOUND: FAILED")
            else:
                print("INSIGHTS FIELD MISSING: FAILED")
                sys.exit(1)
        else:
            print(f"ANALYZE ENDPOINT: FAILED ({resp.status_code})")
            sys.exit(1)
            
    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_backend_disclaimer()
