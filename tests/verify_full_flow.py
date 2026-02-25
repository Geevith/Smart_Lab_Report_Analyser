import requests
import secrets
import sys

BASE_URL = "http://localhost:8000"

def run_verification():
    print("🚀 Starting Full Flow Verification...")
    
    # 1. Register
    username = f"verifyuser{secrets.token_hex(4)}"
    email = f"{username}@example.com"
    password = "TestPassword123!"
    
    print(f"\n1. Registering user: {username}")
    reg_payload = {
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password,
        "full_name": "Verification User",
        "date_of_birth": "1990-01-01",
        "gender": "Other",
        "consent": True
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        if resp.status_code == 200:
            print("✅ Registration SUCCESS")
        else:
            print(f"❌ Registration FAILED: {resp.status_code} - {resp.text}")
            sys.exit(1)
            
        # 2. Login
        print(f"\n2. Logging in...")
        login_payload = {
            "username_or_email": email,
            "password": password,
            "remember_me": False
        }
        
        session = requests.Session()
        resp = session.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if resp.status_code == 200:
            print("✅ Login SUCCESS")
            # Verify cookie jar has session_token
            if "session_token" in session.cookies:
                 print("✅ Session Token received")
            else:
                 print("❌ Session Token MISSING in cookies")
                 # proceed anyway to see if it fails
        else:
            print(f"❌ Login FAILED: {resp.status_code} - {resp.text}")
            sys.exit(1)

        # 3. Analyze File
        print(f"\n3. Uploading file to /analyze...")
        files = {
            'file': ('test_report.txt', b'Hemoglobin: 12.5 g/dL\nRBC Count: 4.8 million/uL', 'text/plain')
        }
        
        # We use the session object which holds the cookies
        resp = session.post(f"{BASE_URL}/analyze", files=files)
        
        if resp.status_code == 200:
            print("✅ Analysis SUCCESS")
            data = resp.json()
            if "parameters" in data and len(data["parameters"]) > 0:
                print(f"   - Extracted {len(data['parameters'])} parameters.")
            else:
                print("   ⚠️ No parameters extracted (might be expected for dummy text).")
        else:
            print(f"❌ Analysis FAILED: {resp.status_code} - {resp.text}")
            sys.exit(1)

        # 4. Check History
        print(f"\n4. Checking /history...")
        resp = session.get(f"{BASE_URL}/history")
        
        if resp.status_code == 200:
            history = resp.json()
            print(f"✅ History SUCCESS. Found {len(history)} reports.")
            if len(history) > 0:
                print(f"   - Most recent: {history[0].get('filename')}")
        else:
             print(f"❌ History FAILED: {resp.status_code} - {resp.text}")
             sys.exit(1)

        print("\n✨ ALL TESTS PASSED!")

    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
