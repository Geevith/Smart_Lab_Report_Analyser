import requests
import json
import uuid

base_url = "http://localhost:8000"
url_register = f"{base_url}/auth/register"
url_login = f"{base_url}/auth/login"
url_preview = f"{base_url}/preview"

session = requests.Session()

# Register a new user
unique_id = str(uuid.uuid4().hex)[:8]
test_email = f"test{unique_id}@test.com"
test_username = f"testuser{unique_id}"
test_password = "StrongPass123!"

register_res = session.post(url_register, json={
    "email": test_email,
    "username": test_username,
    "password": test_password,
    "confirm_password": test_password,
    "consent": True
})
print("Register:", register_res.status_code)

# Login
login_res = session.post(url_login, json={"username_or_email": test_email, "password": test_password})
print("Login:", login_res.status_code)

csrf_token = session.cookies.get("csrf_token")
headers = {"X-CSRF-Token": csrf_token} if csrf_token else {}

# Preview
with open('temp/test_image.png', 'rb') as f:
    file_bytes = f.read()

files = {
    # Send custom filename so the backend doesn't try to override our exact source file
    'file': ('uploaded_test_image.png', file_bytes, 'image/png')
}
response = session.post(url_preview, files=files, headers=headers)
print("Preview:", response.status_code)

try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)
