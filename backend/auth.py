"""
Authentication and Authorization Module
Handles password hashing, session management, and user validation
"""

import secrets
import hashlib
import hashlib
from typing import Optional
from .database import (
    create_user, get_user_by_username, get_user_by_email, get_user_by_id,
    update_last_login, create_session, validate_session as db_validate_session,
    invalidate_session as db_invalidate_session, log_activity
)

# Password hashing context with bcrypt
import bcrypt

# ============================================================================
# Password Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt (pre-hashed with SHA256 to support long passwords)"""
    # Pre-hash to handle passwords > 72 chars (bcrypt limit)
    pre_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # Use bcrypt directly to avoid passlib compatibility issues
    return bcrypt.hashpw(pre_hash.encode('ascii'), bcrypt.gensalt()).decode('ascii')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Pre-hash to handle passwords > 72 chars
    pre_hash = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    try:
        return bcrypt.checkpw(pre_hash.encode('ascii'), hashed_password.encode('ascii'))
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets minimum security requirements
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 1000:
        return False, "Password is too long (max 1000 characters)"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    
    return True, ""


# ============================================================================
# Session Token Functions
# ============================================================================

def generate_session_token() -> str:
    """Generate a secure random session token"""
    return secrets.token_urlsafe(32)


# ============================================================================
# User Registration & Login
# ============================================================================

def register_user(email: str, username: str, password: str, full_name: str = None, 
                 date_of_birth: str = None, gender: str = None, age: int = None, ethnicity: str = None) -> dict:
    """
    Register a new user
    
    Returns:
        dict with user info (without password hash)
    
    Raises:
        ValueError: if validation fails or user already exists
    """
    # Validate email format
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ValueError("Invalid email format")
    
    # Validate username (alphanumeric, 3-20 chars)
    if not username.isalnum() or len(username) < 3 or len(username) > 20:
        raise ValueError("Username must be 3-20 alphanumeric characters")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        raise ValueError(error_msg)
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create user in database
    try:
        user_id = create_user(
            email=email.lower(),  # Store email in lowercase
            username=username.lower(),  # Store username in lowercase
            password_hash=password_hash,
            full_name=full_name,
            date_of_birth=date_of_birth,
            gender=gender,
            age=age,
            ethnicity=ethnicity
        )
        
        # Return user info
        return {
            "id": user_id,
            "email": email.lower(),
            "username": username.lower(),
            "full_name": full_name
        }
    except ValueError as e:
        # Re-raise database errors (duplicate email/username)
        raise e


def login_user(username_or_email: str, password: str, ip_address: str = None, 
              user_agent: str = None) -> tuple[dict, str]:
    """
    Authenticate user and create session
    
    Returns:
        (user_dict, session_token)
    
    Raises:
        ValueError: if credentials are invalid
    """
    # Try to find user by username or email
    user = get_user_by_username(username_or_email.lower())
    if not user:
        user = get_user_by_email(username_or_email.lower())
    
    if not user:
        raise ValueError("Invalid username/email or password")
    
    # Verify password
    if not verify_password(password, user['password_hash']):
        raise ValueError("Invalid username/email or password")
    
    # Check if user is active
    if not user['is_active']:
        raise ValueError("Account is inactive. Please contact support.")
    
    # Generate session token
    session_token = generate_session_token()
    
    # Create session in database
    create_session(
        user_id=user['id'],
        session_token=session_token,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_in_hours=24
    )
    
    # Update last login
    update_last_login(user['id'])
    
    # Log activity
    log_activity(user['id'], "login", ip_address=ip_address)
    
    # Return user info (without password_hash) and session token
    user_info = {
        "id": user['id'],
        "email": user['email'],
        "username": user['username'],
        "full_name": user['full_name'],
        "date_of_birth": user['date_of_birth'],
        "gender": user['gender'],
        "age": user.get('age'),
        "ethnicity": user.get('ethnicity')
    }
    
    return user_info, session_token


def logout_user(session_token: str, user_id: int = None):
    """
    Logout user by invalidating session
    """
    db_invalidate_session(session_token)
    
    if user_id:
        log_activity(user_id, "logout")


# ============================================================================
# Session Validation
# ============================================================================

def validate_session(session_token: str) -> Optional[dict]:
    """
    Validate session token and return user info if valid
    
    Returns:
        user dict if session is valid, None otherwise
    """
    user_id = db_validate_session(session_token)
    
    if not user_id:
        return None
    
    # Get user info
    user = get_user_by_id(user_id)
    
    # Check if user is still active
    if not user or not user['is_active']:
        return None
    
    return user


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user_from_session(session_token: str) -> Optional[dict]:
    """
    Get current user from session token
    Alias for validate_session for clarity in endpoints
    """
    return validate_session(session_token)
