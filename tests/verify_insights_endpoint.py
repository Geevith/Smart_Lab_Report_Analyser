import requests
import sys

def test_backend_insights():
    try:
        # Dummy TXT content
        filename = "verify_insights.txt"
        with open(filename, "w") as f:
            f.write("Hemoglobin: 10.0") # Low
            
        with open(filename, "rb") as f:
            # MIME type for txt
            files = {'file': (filename, f, 'text/plain')}
            resp = requests.post("http://127.0.0.1:8000/analyze", files=files)
            
        if resp.status_code == 200:
            data = resp.json()
            if "insights" in data and "detailed_insights" in data["insights"]:
                insights = data["insights"]["detailed_insights"]
                print("INSIGHTS FIELD FOUND: SUCCESS")
                # We expect at least one insight for Low Hemoglobin
                if any("Hemoglobin" in i["parameter"] for i in insights):
                     print("HEMOGLOBIN INSIGHT FOUND: SUCCESS")
                else:
                     print("HEMOGLOBIN INSIGHT MISSING: FAILED")
                     print(insights)
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
    test_backend_insights()
