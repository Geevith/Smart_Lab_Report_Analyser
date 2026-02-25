import sys
import os
sys.path.append(os.getcwd())

from backend.auth import hash_password, verify_password

def test_hashing():
    print("Testing DIRECT bcrypt...")
    import bcrypt
    try:
        # Hex digest is 64 bytes
        hex_digest = b"d9d8e7ee4e92681edbb144557bbf512c15e51582ed8f4a03dac98e88d1065674"
        print(f"Direct bcrypt hash on 64 bytes: {len(hex_digest)}")
        hashed = bcrypt.hashpw(hex_digest, bcrypt.gensalt())
        print(f"✅ Direct bcrypt success: {hashed[:10]}")
    except Exception as e:
        print(f"❌ Direct bcrypt failed: {e}")

    print("Testing hash_password...")
    password = "StrongPassword123!"
    try:
        hashed = hash_password(password)
        print(f"✅ Hashed successfully: {hashed[:10]}...")
    except Exception as e:
        print(f"❌ Hashing failed: {e}")
        return

    print("Testing verify_password...")
    try:
        is_valid = verify_password(password, hashed)
        if is_valid:
            print("✅ Verification successful")
        else:
            print("❌ Verification failed")
    except Exception as e:
        print(f"❌ Verification error: {e}")

    print("Testing Verify...")
    # ... existing verify code ...

    print("Testing DIRECT bcrypt...")
    import bcrypt
    try:
        pw_bytes = b"test_password"
        # Hex digest is 64 bytes
        hex_digest = b"d9d8e7ee4e92681edbb144557bbf512c15e51582ed8f4a03dac98e88d1065674"
        print(f"Direct bcrypt hash on 64 bytes: {len(hex_digest)}")
        hashed = bcrypt.hashpw(hex_digest, bcrypt.gensalt())
        print(f"✅ Direct bcrypt success: {hashed[:10]}")
    except Exception as e:
        print(f"❌ Direct bcrypt failed: {e}")


if __name__ == "__main__":
    test_hashing()
