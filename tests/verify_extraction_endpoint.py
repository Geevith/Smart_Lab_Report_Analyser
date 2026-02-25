import requests
import sys

def test_backend_extraction():
    try:
        # Create a dummy text file to act as PDF (it will fail extraction but should pass the endpoint logic)
        with open("verify_dummy.pdf", "w") as f:
            f.write("not a real pdf")
            
        with open("verify_dummy.pdf", "rb") as f:
            files = {'file': ('verify_dummy.pdf', f, 'application/pdf')}
            resp = requests.post("http://127.0.0.1:8000/analyze", files=files)
            
        if resp.status_code == 200:
            data = resp.json()
            if "extracted_text" in data:
                print("EXTRACTION FIELD FOUND: SUCCESS")
                print(f"Extracted Text: {data['extracted_text']}") # Should be empty or error printed in server logs
            else:
                print("EXTRACTION FIELD MISSING: FAILED")
                sys.exit(1)
        else:
            print(f"ANALYZE ENDPOINT: FAILED ({resp.status_code})")
            sys.exit(1)
            
    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_backend_extraction()
