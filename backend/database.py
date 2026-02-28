import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e

def init_db():
    """Initializes the database. Tables are typically managed via Admin/Migration tools."""
    # Since we are using Supabase, table creation is handled via Migrations.
    # This function checks connectivity.
    try:
        conn = get_db_connection()
        conn.close()
        print("Database connection successful.")
    except Exception as e:
        print(f"Failed to connect to database: {e}")

# ============================================================================
# Report Functions
# ============================================================================

def save_report(user_id, filename, summary_status, original_filename=None, file_hash=None, report_type=None, lab_name=None, lab_date=None):
    """Saves a report record to the database."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO reports (user_id, filename, original_filename, file_hash, timestamp, summary_status, report_type, lab_name, lab_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, filename, original_filename or filename, file_hash, timestamp, summary_status, report_type, lab_name, lab_date))
        report_id = cursor.fetchone()[0]
        conn.commit()
        return report_id
    finally:
        cursor.close()
        conn.close()

def save_parameters(user_id, report_id, parameters_dict):
    """Save parameters for a report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        for param_name, param_data in parameters_dict.items():
            cursor.execute('''
                INSERT INTO historical_parameters 
                (user_id, report_id, parameter_name, value, unit, reference_range, status, severity, confidence_score, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                report_id,
                param_name,
                float(param_data.get('value', 0)),
                param_data.get('unit'),
                param_data.get('range'),
                param_data.get('status', 'NORMAL'),
                param_data.get('severity'),
                param_data.get('confidence_score'),
                timestamp
            ))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_parameter_history(user_id, parameter_name, limit=10):
    """Get historical values for a specific parameter."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT value, unit, status, severity, recorded_at, reference_range
            FROM historical_parameters
            WHERE user_id = %s AND parameter_name = %s
            ORDER BY recorded_at DESC
            LIMIT %s
        ''', (user_id, parameter_name, limit))
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "value": row[0],
                "unit": row[1],
                "status": row[2],
                "severity": row[3],
                "date": str(row[4]),
                "range": row[5]
            })
        return history
    finally:
        cursor.close()
        conn.close()

def get_all_parameters_with_history():
    """Get all unique parameters that have historical data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT DISTINCT parameter_name
            FROM historical_parameters
            ORDER BY parameter_name
        ''')
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        cursor.close()
        conn.close()

def get_report_parameters(report_id):
    """Get all parameters for a specific report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT parameter_name, value, unit, reference_range, status, severity, confidence_score, recorded_at
            FROM historical_parameters
            WHERE report_id = %s
            ORDER BY parameter_name
        ''', (report_id,))
        rows = cursor.fetchall()
        
        parameters = []
        for row in rows:
            parameters.append({
                "name": row[0],
                "value": str(row[1]),
                "unit": row[2],
                "range": row[3],
                "status": row[4],
                "severity": row[5],
                "confidence_score": row[6],
                "date": str(row[7])
            })
        return parameters
    finally:
        cursor.close()
        conn.close()

def get_history(user_id, limit=50, search=None, favorite_only=False, status_filter=None, sort_order="newest"):
    """Retrieves the last N reports for a user with optional search/filter/sort."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = '''
            SELECT id, filename, timestamp, summary_status, report_type, lab_name, lab_date, is_favorite, notes
            FROM reports 
            WHERE user_id = %s AND (is_archived IS NULL OR is_archived = FALSE)
        '''
        params = [user_id]
        
        if search:
            query += " AND filename ILIKE %s"
            params.append(f"%{search}%")
        
        if favorite_only:
            query += " AND is_favorite = TRUE"
        
        if status_filter:
            if status_filter == "attention":
                query += " AND summary_status ILIKE %s"
                params.append("%issue%")
            elif status_filter == "normal":
                query += " AND (summary_status = '0 issues' OR summary_status = 'Normal')"
        
        if sort_order == "oldest":
            query += " ORDER BY id ASC"
        else:
            query += " ORDER BY id DESC"
        
        query += " LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "filename": row[1],
                "timestamp": str(row[2]),
                "status": row[3],
                "report_type": row[4],
                "lab_name": row[5],
                "lab_date": str(row[6]) if row[6] else None,
                "is_favorite": row[7],
                "notes": row[8]
            })
        return history
    finally:
        cursor.close()
        conn.close()


def delete_report(user_id, report_id):
    """Delete a report and its linked parameters. Verifies user ownership."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify ownership
        cursor.execute('SELECT id FROM reports WHERE id = %s AND user_id = %s', (report_id, user_id))
        if not cursor.fetchone():
            return False
        
        # Delete linked parameters first
        cursor.execute('DELETE FROM historical_parameters WHERE report_id = %s AND user_id = %s', (report_id, user_id))
        
        # Delete from optional related tables (may not exist)
        for table in ['parameter_flags', 'shareable_links']:
            try:
                cursor.execute(f'DELETE FROM {table} WHERE report_id = %s AND user_id = %s', (report_id, user_id))
            except Exception:
                pass  # Table might not exist
        
        # Delete the report
        cursor.execute('DELETE FROM reports WHERE id = %s AND user_id = %s', (report_id, user_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting report: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def toggle_favorite(user_id, report_id):
    """Toggle the is_favorite status of a report. Returns the new value."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE reports SET is_favorite = NOT COALESCE(is_favorite, FALSE)
            WHERE id = %s AND user_id = %s
            RETURNING is_favorite
        ''', (report_id, user_id))
        result = cursor.fetchone()
        conn.commit()
        if result:
            return result[0]
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error toggling favorite: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_report_notes(user_id, report_id, notes):
    """Update the notes field on a report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE reports SET notes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s AND user_id = %s
        ''', (notes, report_id, user_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error updating notes: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_history_stats(user_id):
    """Get summary statistics for a user's report history."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_favorite = TRUE) as favorites,
                COUNT(*) FILTER (WHERE summary_status ILIKE '%%issue%%' AND summary_status != '0 issues') as flagged
            FROM reports
            WHERE user_id = %s AND (is_archived IS NULL OR is_archived = FALSE)
        ''', (user_id,))
        row = cursor.fetchone()
        return {
            "total": row[0] if row else 0,
            "favorites": row[1] if row else 0,
            "flagged": row[2] if row else 0
        }
    finally:
        cursor.close()
        conn.close()

def get_report_parameters(report_id):
    """Get all parameters for a specific report."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT parameter_name, value, unit, reference_range, status, severity, confidence_score
            FROM historical_parameters
            WHERE report_id = %s
        ''', (report_id,))
        rows = cursor.fetchall()
        
        parameters = {}
        for row in rows:
            parameters[row[0]] = {
                "value": row[1],
                "unit": row[2],
                "range": row[3],
                "status": row[4],
                "severity": row[5],
                "confidence_score": row[6]
            }
        return parameters
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# Parameter Verification Functions
# ============================================================================

def create_parameter_flag(user_id, report_id, parameter_name, original_value, corrected_value, issue_type, notes=None):
    """
    Create a flag for a parameter that was incorrectly extracted.
    
    Args:
        user_id: ID of the user reporting the issue
        report_id: ID of the report containing the parameter
        parameter_name: Name of the parameter
        original_value: Original extracted value
        corrected_value: User-corrected value
        issue_type: Type of issue (misread/missing/incorrect_unit)
        notes: Optional additional notes
    
    Returns:
        ID of the created flag
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()
    
    try:
        cursor.execute('''
            INSERT INTO parameter_flags 
            (user_id, report_id, parameter_name, original_value, corrected_value, issue_type, notes, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, report_id, parameter_name, original_value, corrected_value, issue_type, notes, timestamp))
        flag_id = cursor.fetchone()[0]
        conn.commit()
        return flag_id
    finally:
        cursor.close()
        conn.close()

def get_parameter_flags(user_id=None, limit=50):
    """
    Get parameter flags for analysis.
    
    Args:
        user_id: Optional user ID to filter by
        limit: Max number of flags to return
    
    Returns:
        List of parameter flags
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if user_id:
            cursor.execute('''
                SELECT id, user_id, report_id, parameter_name, original_value, corrected_value, 
                       issue_type, notes, created_at, resolved
                FROM parameter_flags
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT id, user_id, report_id, parameter_name, original_value, corrected_value, 
                       issue_type, notes, created_at, resolved
                FROM parameter_flags
                ORDER BY created_at DESC
                LIMIT %s
            ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def update_parameter_value(user_id, report_id, parameter_name, new_value, new_unit=None):
    """
    Update a parameter's value in the database.
    
    Args:
        user_id: ID of the user making the update
        report_id: ID of the report
        parameter_name: Name of the parameter to update
        new_value: New value for the parameter
        new_unit: Optional new unit
    
    Returns:
        Boolean indicating success
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if new_unit:
            cursor.execute('''
                UPDATE historical_parameters
                SET value = %s, unit = %s
                WHERE user_id = %s AND report_id = %s AND parameter_name = %s
            ''', (float(new_value), new_unit, user_id, report_id, parameter_name))
        else:
            cursor.execute('''
                UPDATE historical_parameters
                SET value = %s
                WHERE user_id = %s AND report_id = %s AND parameter_name = %s
            ''', (float(new_value), user_id, report_id, parameter_name))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error updating parameter: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_report_id_from_session(user_id):
    """
    Get the most recent report ID for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Most recent report ID or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id FROM reports
            WHERE user_id = %s
            ORDER BY id DESC
            LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# Authentication Functions
# ============================================================================

def create_user(email, username, password_hash, full_name=None, date_of_birth=None, gender=None, age=None, ethnicity=None):
    """Create a new user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (email, username, password_hash, full_name, date_of_birth, gender, age, ethnicity)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (email, username, password_hash, full_name, date_of_birth, gender, age, ethnicity))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if 'email' in str(e) or 'users_email_key' in str(e):
            raise ValueError("Email already exists")
        elif 'username' in str(e) or 'users_username_key' in str(e):
            raise ValueError("Username already exists")
        else:
            raise ValueError(f"User creation failed: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise ValueError(f"User creation failed: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def get_user_by_username(username):
    """Get user by username using RealDictCursor for cleaner mapping."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, email, username, password_hash, full_name, date_of_birth, gender, 
                   age, ethnicity, is_active, created_at, last_login
            FROM users
            WHERE username = %s
        ''', (username,))
        user = cursor.fetchone()
        if user:
            user = dict(user)
            # Convert date/datetime objects to ISO strings for JSON serialization
            if user.get('date_of_birth') is not None:
                user['date_of_birth'] = str(user['date_of_birth'])
            if user.get('created_at') is not None:
                user['created_at'] = str(user['created_at'])
            if user.get('last_login') is not None:
                user['last_login'] = str(user['last_login'])
            return user
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    """Get user by email."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, email, username, password_hash, full_name, date_of_birth, gender, 
                   age, ethnicity, is_active, created_at, last_login
            FROM users
            WHERE email = %s
        ''', (email,))
        user = cursor.fetchone()
        if user:
            user = dict(user)
            # Convert date/datetime objects to ISO strings for JSON serialization
            if user.get('date_of_birth') is not None:
                user['date_of_birth'] = str(user['date_of_birth'])
            if user.get('created_at') is not None:
                user['created_at'] = str(user['created_at'])
            if user.get('last_login') is not None:
                user['last_login'] = str(user['last_login'])
            return user
        return None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, email, username, full_name, date_of_birth, gender, 
                   age, ethnicity, is_active, created_at, last_login
            FROM users
            WHERE id = %s
        ''', (user_id,))
        user = cursor.fetchone()
        if user:
            user = dict(user)
            # Convert date/datetime objects to ISO strings for JSON serialization
            if user.get('date_of_birth') is not None:
                user['date_of_birth'] = str(user['date_of_birth'])
            if user.get('created_at') is not None:
                user['created_at'] = str(user['created_at'])
            if user.get('last_login') is not None:
                user['last_login'] = str(user['last_login'])
            return user
        return None
    finally:
        conn.close()

def update_last_login(user_id):
    """Update user's last login timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()
    try:
        cursor.execute('''
            UPDATE users SET last_login = %s WHERE id = %s
        ''', (timestamp, user_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# Session Management Functions
# ============================================================================

def create_session(user_id, session_token, ip_address=None, user_agent=None, expires_in_hours=24):
    """Create a new session for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()
    expires_at = timestamp + datetime.timedelta(hours=expires_in_hours)
    
    try:
        cursor.execute('''
            INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        ''', (user_id, session_token, ip_address, user_agent, expires_at))
        session_id = cursor.fetchone()[0]
        conn.commit()
        return session_id
    finally:
        cursor.close()
        conn.close()

def get_session(session_token):
    """Get session by token."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, user_id, session_token, created_at, expires_at, is_active
            FROM user_sessions
            WHERE session_token = %s
        ''', (session_token,))
        session = cursor.fetchone()
        if session:
            return dict(session)
        return None
    finally:
        conn.close()

def validate_session(session_token):
    """Validate session and return user_id if valid, None otherwise."""
    session = get_session(session_token)
    if not session:
        return None
    
    if not session['is_active']:
        return None
    
    # Check if session is expired
    # Postgres returns datetime object, so we can compare directly
    expires_at = session['expires_at']
    if expires_at and datetime.datetime.now(datetime.timezone.utc) > expires_at.replace(tzinfo=datetime.timezone.utc):
        invalidate_session(session_token)
        return None
        
    # Handle naive datetime from older records if any
    if isinstance(expires_at, datetime.datetime) and expires_at.tzinfo is None:
         if datetime.datetime.now() > expires_at:
             invalidate_session(session_token)
             return None

    return session['user_id']

def invalidate_session(session_token):
    """Invalidate a session (logout)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE user_sessions SET is_active = FALSE WHERE session_token = %s
        ''', (session_token,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def cleanup_expired_sessions():
    """Remove expired sessions from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    current_time = datetime.datetime.now()
    try:
        cursor.execute('''
            DELETE FROM user_sessions WHERE expires_at < %s
        ''', (current_time,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# ============================================================================
# Activity Logging Functions
# ============================================================================

def log_activity(user_id, action, resource_type=None, resource_id=None, ip_address=None):
    """Log user activity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, resource_type, resource_id, ip_address)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, action, resource_type, resource_id, ip_address))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_user_activity(user_id, limit=50):
    """Get activity log for a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT action, resource_type, resource_id, ip_address, timestamp
            FROM activity_log
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
        ''', (user_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ============================================================================
# Shareable Links Functions
# ============================================================================

def create_shareable_link(user_id, report_id, share_token, expires_in_days=30):
    """
    Create a shareable link for a report.
    
    Args:
        user_id: ID of user sharing the report
        report_id: ID of report to share
        share_token: Unique token for the link
        expires_in_days: Number of days until link expires
        
    Returns:
        ID of created share link
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()
    expires_at = timestamp + datetime.timedelta(days=expires_in_days)
    
    try:
        cursor.execute('''
            INSERT INTO shareable_links 
            (user_id, report_id, share_token, expires_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (user_id, report_id, share_token, expires_at))
        link_id = cursor.fetchone()[0]
        conn.commit()
        return link_id
    finally:
        cursor.close()
        conn.close()


def get_shareable_link(share_token):
    """Get shareable link by token."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT id, user_id, report_id, share_token, created_at, expires_at, access_count, is_active
            FROM shareable_links
            WHERE share_token = %s AND is_active = TRUE
        ''', (share_token,))
        link = cursor.fetchone()
        if link:
            return dict(link)
        return None
    finally:
        conn.close()


def validate_shareable_link(share_token):
    """Validate shareable link and return report_id if valid."""
    link = get_shareable_link(share_token)
    if not link:
        return None
    
    # Check if link is expired
    expires_at = link['expires_at']
    if expires_at:
        now = datetime.datetime.now()
        if isinstance(expires_at, datetime.datetime):
            if expires_at.tzinfo:
                now = now.replace(tzinfo=datetime.timezone.utc)
                if now > expires_at:
                    return None
            else:
                if now > expires_at:
                    return None
    
    # Increment access count
    increment_share_access_count(link['id'])
    
    return link['report_id']


def increment_share_access_count(link_id):
    """Increment access count for a shareable link."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE shareable_links 
            SET access_count = access_count + 1, last_accessed_at = %s
            WHERE id = %s
        ''', (datetime.datetime.now(), link_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def revoke_shareable_link(share_token, user_id):
    """Revoke a shareable link (owner only)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE shareable_links 
            SET is_active = FALSE
            WHERE share_token = %s AND user_id = %s
        ''', (share_token, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def get_user_shareable_links(user_id, limit=50):
    """Get all shareable links created by a user."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT sl.id, sl.report_id, sl.share_token, sl.created_at, sl.expires_at, 
                   sl.access_count, sl.is_active, r.filename
            FROM shareable_links sl
            JOIN reports r ON sl.report_id = r.id
            WHERE sl.user_id = %s
            ORDER BY sl.created_at DESC
            LIMIT %s
        ''', (user_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

