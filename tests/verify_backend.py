import requests
import sys

def test_backend():
    try:
        # Test Root
        resp = requests.get("http://127.0.0.1:8000/")
        if resp.status_code == 200:
            print("ROOT ENDPOINT: SUCCESS")
        else:
            print(f"ROOT ENDPOINT: FAILED ({resp.status_code})")
            sys.exit(1)

        # Test Analyze (Mock)
        # We need a dummy file
        with open("test_dummy.txt", "w") as f:
            f.write("dummy content")
            
        with open("test_dummy.txt", "rb") as f:
            files = {'file': ('test_dummy.txt', f, 'text/plain')}
            resp = requests.post("http://127.0.0.1:8000/analyze", files=files)
            
        if resp.status_code == 200:
            print("ANALYZE ENDPOINT: SUCCESS")
            print(resp.json())
        else:
            print(f"ANALYZE ENDPOINT: FAILED ({resp.status_code})")
            print(resp.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_backend()
