import requests
import random
import string

BASE_URL = "http://localhost:8000"

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def test_auth_flow():
    username = f"user{generate_random_string()}" # Removed underscore
    email = f"{username}@example.com"
    password = "Password123!"
    
    print(f"Testing with User: {username} / {email}")

    # 1. Register New User
    print("\n[1] Register New User...")
    payload = {
        "email": email,
        "username": username,
        "password": password,
        "confirm_password": password,
        "consent": True
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    if response.status_code == 200:
        data = response.json()
        print("✅ Success:", data.get("message"))
        if data.get("auto_login") is False:
             print("✅ Correctly identified as new user (auto_login=False)")
        else:
             print("❌ Error: Should not auto-login new user")
    else:
        print("❌ Failed:", response.text)
        return

    # 2. Register Existing User (Same Password) -> Should Auto-Login
    print("\n[2] Register Existing User (Same Password)...")
    session = requests.Session()
    response = session.post(f"{BASE_URL}/auth/register", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Success:", data.get("message"))
        if data.get("auto_login") is True:
             print("✅ Correctly auto-logged in (auto_login=True)")
             if "session_token" in response.cookies or session.cookies.get("session_token"):
                 print("✅ Session cookie received")
             else:
                 print("❌ Error: No session cookie received")
        else:
             print("❌ Error: Did not auto-login existing user")
    else:
        print("❌ Failed:", response.text)

    # 3. Register Existing User (Wrong Password) -> Should Fail
    print("\n[3] Register Existing User (Wrong Password)...")
    payload_wrong = payload.copy()
    payload_wrong["password"] = "WrongPass123!"
    payload_wrong["confirm_password"] = "WrongPass123!"
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload_wrong)
    
    if response.status_code == 400:
        print("✅ Correctly rejected:", response.json().get("detail"))
    else:
        print("❌ Error: Should have failed but got:", response.status_code, response.text)

    # 4. Long Password Test (> 72 bytes)
    print("\n[4] Long Password Test...")
    long_user = f"long{generate_random_string()}"
    long_pass = "A" * 80 + "1a!" # 83 chars
    
    payload_long = {
        "email": f"{long_user}@example.com",
        "username": long_user,
        "password": long_pass,
        "confirm_password": long_pass,
        "consent": True
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload_long)
    if response.status_code == 200:
        print("✅ Long password registration successful")
    else:
        print("❌ Long password failed:", response.text)

if __name__ == "__main__":
    test_auth_flow()
