import requests
import json
import secrets

BASE_URL = "http://localhost:8000"

def test_registration_and_login():
    print("🚀 Starting Authentication Test...")
    
    # 1. Test with a Long Password (150 chars)
    username = f"testuser{secrets.token_hex(4)}"
    email = f"{username}@example.com"
    long_password = "LongPassword_" + "A"*100 + "123!"
    
    print(f"\nExample 1: Testing Long Password (Len: {len(long_password)})")
    print(f"Username: {username}")
    
    # Register
    register_payload = {
        "email": email,
        "username": username,
        "password": long_password,
        "confirm_password": long_password,
        "consent": True
    }
    
    try:
        reg_response = requests.post(f"{BASE_URL}/auth/register", json=register_payload)
        print(f"Registration Status: {reg_response.status_code}")
        if reg_response.status_code == 200:
            print("✅ Registration SUCCESS")
        else:
            print(f"❌ Registration FAILED: {reg_response.text}")
            return

        # Login
        login_payload = {
            "username_or_email": email,
            "password": long_password,
            "remember_me": False
        }
        
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        print(f"Login Status: {login_response.status_code}")
        if login_response.status_code == 200:
            print("✅ Login SUCCESS")
            token = login_response.cookies.get("session_token")
            print(f"Session Token received: {token[:10]}...")
        else:
            print(f"❌ Login FAILED: {login_response.text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("Ensure the backend server is running on localhost:8000")

if __name__ == "__main__":
    test_registration_and_login()
