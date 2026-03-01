from fastapi import FastAPI, UploadFile, File, Response, HTTPException, Depends, Request, status, Cookie, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import shutil
import os
import io
import uuid
import logging
import secrets
import concurrent.futures
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path
from datetime import datetime

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
load_dotenv()

from .extractor import extract_text, extract_text_enhanced
from .parser import parse_blood_test, merge_multi_page_results
from .interpretation import generate_insights
from .report_generator import generate_pdf
from .database import init_db, save_report, get_history, save_parameters, get_parameter_history, log_activity
from .systems_impact import compute_systems_impact
from .auth import register_user, login_user, logout_user, validate_session
from .models import UserRegister, UserLogin, UserResponse, MessageResponse, ErrorResponse, ReportRequest
from .quality_assessment import assess_image
from .dependencies import verify_csrf, generate_csrf_token
from .report_classifier import classify_report
from .ai_analyzer import analyze_with_ai

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# ── In-memory job store for async analysis ────────────────────────────────────
# Jobs are stored as: {job_id: {"status": str, "result": dict|None, "error": str|None, "created_at": datetime}}
_analysis_jobs: dict = {}

# Thread pool for CPU-bound OCR work
_ocr_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

app = FastAPI(title="Smart Lab Report Analyser - Multi-User Edition")
# Force reload trigger - Auth fix applied + security headers + async analyze

# ── Middleware setup ──────────────────────────────────────────────────────────
# IMPORTANT: Starlette applies middleware in reverse order, so FIRST added = OUTERMOST

SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "change-this-to-a-random-secret-key")
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))  # 24 hours

# 1. Rate limiter (needs to be registered before other middleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Session middleware (must be added FIRST so it wraps everything)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE,
    same_site="lax",
    https_only=False  # Set to True in production with HTTPS
)

# 3. Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers to every response."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# 4. Request ID middleware (attach unique ID to each request for tracing)
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach X-Request-ID to every request and response."""
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

app.add_middleware(RequestIDMiddleware)

# 5. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token", "X-Request-ID"],
)

# Initialize DB on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    log.info("✅ Database initialized with authentication tables")

# Add global exception handler to ensure JSON responses for errors
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and return JSON (excluding HTTPExceptions)"""
    # HTTPExceptions should be handled by http_exception_handler below
    from fastapi import HTTPException as FastAPIHTTPException
    if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
        return await http_exception_handler(request, exc)
    import traceback
    log.error("Unhandled exception for %s %s: %s\n%s",
              request.method, request.url.path, str(exc), traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}: {str(exc)}",
            "success": False
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure HTTP exceptions return JSON"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "success": False
        }
    )




# ============================================================================
# Authentication Dependency
# ============================================================================

async def get_current_user(request: Request) -> dict:
    """
    Dependency to get current user from session
    Raises HTTP 401 if not authenticated
    """
    session_token = request.cookies.get("session_token")
    print(f"DEBUG: get_current_user called for {request.url.path}", flush=True)
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (DEBUG). Please login."
        )
    
    user = validate_session(session_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please login again."
        )
    
    return user


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Dependency to get current user from session (optional)
    Returns None if not authenticated
    """
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    
    return validate_session(session_token)


# ============================================================================
# Helper function to get client IP
# ============================================================================

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


# ============================================================================
# Public Endpoints (No Authentication Required)
# ============================================================================

@app.get("/api/status")
def read_root():
    return {
        "message": "Smart Lab Report Analyser - Multi-User Edition",
        "version": "2.0.0",
        "status": "online",
        "features": ["multi-user", "authentication", "personalization"]
    }

@app.get("/")
async def serve_landing_page():
    return FileResponse(os.path.join("frontend", "index.html"))


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/health/db")
def health_check_db():
    """Database connectivity check — shows which env vars are set and if DB connects."""
    db_host = os.getenv("DB_HOST", "")
    db_name = os.getenv("DB_NAME", "postgres")
    db_user = os.getenv("DB_USER", "")
    db_pass = "SET" if os.getenv("DB_PASS") else "MISSING"
    db_port = os.getenv("DB_PORT", "5432")
    gemini_key = "SET" if os.getenv("GEMINI_API_KEY") else "MISSING"

    env_status = {
        "DB_HOST": db_host if db_host else "MISSING",
        "DB_NAME": db_name,
        "DB_USER": db_user if db_user else "MISSING",
        "DB_PASS": db_pass,
        "DB_PORT": db_port,
        "GEMINI_API_KEY": gemini_key,
    }

    # Try a real DB connection
    try:
        from .database import get_db_connection
        conn = get_db_connection()
        conn.close()
        db_ok = True
        db_error = None
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return {
        "db_connected": db_ok,
        "db_error": db_error,
        "env": env_status,
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/register", response_model=MessageResponse)
@limiter.limit("3/minute")
async def register(user_data: UserRegister, request: Request):
    """
    Register a new user
    
    Returns success message (does not auto-login)
    """
    # Check if user already exists
    # NOTE: email and username are stored in lowercase — must normalize before lookup
    from .database import get_user_by_email, get_user_by_username
    
    existing_user = get_user_by_email(user_data.email.lower())
    if not existing_user:
        existing_user = get_user_by_username(user_data.username.lower())
        
    if existing_user:
        # If user exists, try to verify password for auto-login
        from .auth import verify_password
        
        if verify_password(user_data.password, existing_user['password_hash']):
            # Password matches! Auto-login
            ip_address = get_client_ip(request)
            user_agent = request.headers.get("User-Agent", "unknown")
            
            user, session_token = login_user(
                username_or_email=existing_user['email'],
                password=user_data.password,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Set session cookie
            max_age = SESSION_MAX_AGE # Default max age
            response = JSONResponse(content={
                "message": "Account already exists with this password. Logging you in...",
                "success": True,
                "auto_login": True,
                "user": user
            })
            
            response.set_cookie(
                key="session_token",
                value=session_token,
                max_age=max_age,
                httponly=True,
                samesite="lax",
                secure=False 
            )
            return response
            
        else:
            # User exists but password mismatch
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account with this email or username already exists."
            )

    try:
        user = register_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            date_of_birth=str(user_data.date_of_birth) if user_data.date_of_birth else None,
            gender=user_data.gender
        )
        
        # Log registration activity
        ip_address = get_client_ip(request)
        log_activity(user['id'], "register", ip_address=ip_address)
        
        return JSONResponse(content={
            "message": f"Registration successful! Welcome, {user_data.username}. Please login to continue.",
            "success": True,
            "auto_login": False
        })
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(login_data: UserLogin, request: Request, response: Response):
    """
    Login and create session
    
    Returns user info and sets session cookie.
    Also sets a csrf_token cookie (httponly=False) for CSRF protection.
    Rate-limited to 5 requests/minute per IP.
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")
        
        user, session_token = login_user(
            username_or_email=login_data.username_or_email,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Set session cookie (HTTPOnly for security)
        max_age = SESSION_MAX_AGE if not login_data.remember_me else SESSION_MAX_AGE * 30  # 30 days for remember me
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=max_age,
            httponly=True,  # Prevent JavaScript access
            samesite="lax",  # CSRF protection
            secure=False  # Set to True in production with HTTPS
        )

        # Set CSRF token cookie (NOT httponly — JS needs to read and send it as header)
        csrf_token = generate_csrf_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=max_age,
            httponly=False,   # JavaScript must be able to read this
            samesite="lax",
            secure=False,
        )
        
        return {
            "message": "Login successful",
            "user": user,
            "success": True
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        log.error("Login endpoint crashed: %s\n%s", str(e), traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {type(e).__name__}: {str(e)}"
        )


@app.post("/auth/logout")
async def logout(request: Request, response: Response, current_user: dict = Depends(get_current_user)):
    """
    Logout user by invalidating session
    """
    session_token = request.cookies.get("session_token")
    
    if session_token:
        logout_user(session_token, current_user['id'])
    
    # Clear session cookie
    response.delete_cookie(key="session_token")
    
    return MessageResponse(
        message="Logout successful",
        success=True
    )


@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user's information
    """
    return UserResponse(**current_user)

# ============================================================================
# User Preferences, Data Export, and Tracking
# ============================================================================

@app.put("/api/user/theme")
async def update_theme(request: Request, current_user: dict = Depends(get_current_user)):
    """Update user's theme preference."""
    try:
        data = await request.json()
        theme = data.get("theme", "light")
        if theme not in ["light", "dark", "system"]:
            raise ValueError("Invalid theme value")
            
        from .database import update_user_theme
        update_user_theme(current_user['id'], theme)
        return MessageResponse(message="Theme updated successfully", success=True)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.get("/api/user/export")
async def export_user_data(current_user: dict = Depends(get_current_user)):
    """Export all user data as JSON (HIPAA/GDPR compliance)."""
    from .database import get_user_export_data
    try:
        data = get_user_export_data(current_user['id'])
        if not data:
            raise HTTPException(status_code=404, detail="User data not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to export data: {str(e)}")

@app.delete("/api/user")
async def delete_account(request: Request, response: Response, current_user: dict = Depends(get_current_user)):
    """Permanently delete user account and all cascaded data."""
    from .database import delete_user_account
    try:
        success = delete_user_account(current_user['id'])
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account completely")
            
        # Log them out by clearing session
        session_token = request.cookies.get("session_token")
        if session_token:
            from .auth import logout_user
            logout_user(session_token, current_user['id'])
        response.delete_cookie(key="session_token")
        
        return MessageResponse(message="Account permanently deleted", success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tracking/parameter/{param_name}")
async def get_parameter_tracking(param_name: str, limit: int = 50, current_user: dict = Depends(get_current_user)):
    """Get longitudinal data for a specific lab parameter."""
    from .database import get_parameter_history
    try:
        history = get_parameter_history(current_user['id'], param_name, limit)
        return {"parameter": param_name, "history": history, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/compare")
async def compare_reports(id1: int, id2: int, current_user: dict = Depends(get_current_user)):
    """Get parameters and insights for two specific reports for side-by-side comparison."""
    from .database import get_report_parameters, get_history
    try:
        # Verify ownership efficiently
        user_reports = get_history(current_user['id'], limit=1000)
        report_ids = [r['id'] for r in user_reports]
        if id1 not in report_ids or id2 not in report_ids:
            raise HTTPException(status_code=403, detail="Unauthorized access to these reports")
            
        r1_params = get_report_parameters(id1)
        r2_params = get_report_parameters(id2)
        
        report1_details = next((r for r in user_reports if r['id'] == id1), None)
        report2_details = next((r for r in user_reports if r['id'] == id2), None)
        
        return {
            "report1": {"details": report1_details, "parameters": r1_params},
            "report2": {"details": report2_details, "parameters": r2_params},
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Protected Endpoints (Authentication Required)
# ============================================================================

@app.post("/preview")
async def preview_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    rotation: int = 0
):
    """
    Preview uploaded file with text extraction and quality assessment.
    Does NOT perform parameter analysis - just extraction and quality check.
    
    Args:
        file: Uploaded file (PDF or image)
        rotation: Optional rotation in degrees (0, 90, 180, 270) for images
        
    Returns:
        - text: Extracted text
        - quality: Quality assessment scores
        - pages: Number of pages
        - suggestions: Improvement suggestions
    """
    os.makedirs("temp", exist_ok=True)
    file_location = f"temp/{file.filename}"
    
    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        # Perform quality assessment for images
        quality = {}
        if file.content_type and file.content_type.startswith('image/'):
            quality = assess_image(file_location)
        else:
            # Default quality for PDFs (can be enhanced later)
            quality = {
                "resolution_score": 0.8,
                "contrast_score": 0.8,
                "sharpness_score": 0.8,
                "overall_score": 0.8,
                "ocr_confidence": 0.8,
                "suggestions": []
            }
        
        # Extract text with enhanced function
        extraction = extract_text_enhanced(file_location, rotation)
        
        # Add suggestions based on extraction results
        if extraction['success_rate'] < 50:
            quality['suggestions'].append(f"Only {extraction['success_rate']:.0f}% of pages extracted successfully. Consider re-uploading a higher quality document.")
        
        if len(extraction['text'].strip()) < 100:
            quality['suggestions'].append("Very little text extracted. Ensure document is not encrypted or image-based without OCR.")
        
        return {
            "text": extraction['text'],
            "quality": quality,
            "pages": extraction['page_count'],
            "success_rate": extraction['success_rate'],
            "extraction_errors": extraction.get('errors', []),
            "suggestions": quality.get('suggestions', [])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )
    finally:
        # Cleanup temp file
        if os.path.exists(file_location):
            os.remove(file_location)


@app.post("/analyze/async")
async def analyze_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    rotation: int = 0
):
    """
    Async analysis endpoint: returns a job_id immediately (HTTP 202).
    The client polls /analyze/status/{job_id} for progress.
    """
    os.makedirs("temp", exist_ok=True)
    job_id = str(uuid.uuid4())
    file_content = await file.read()
    file_location = f"temp/{job_id}_{file.filename}"

    with open(file_location, "wb") as f:
        f.write(file_content)

    # Register job immediately
    _analysis_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
    }

    # Start background task
    def run_analysis():
        try:
            _analysis_jobs[job_id]["status"] = "extracting"
            # Quality assessment (for images)
            quality_data = {}
            if file.content_type and file.content_type.startswith('image/'):
                quality_data = assess_image(file_location)

            _analysis_jobs[job_id]["status"] = "parsing"
            extraction = extract_text_enhanced(file_location, rotation)
            text = extraction['text']
            pages_processed = extraction['page_count']
            extraction_warnings = extraction.get('errors', [])

            # ── Classify report type ──────────────────────────────────────────
            report_classification = classify_report(text)
            report_type = report_classification["type"]
            report_type_label = report_classification["label"]
            report_type_icon = report_classification["icon"]
            ai_metadata = {}

            if report_classification["requires_ai"]:
                # ── Narrative report (CT, MRI, pathology, cardiology, etc.) ──
                _analysis_jobs[job_id]["status"] = "parsing"
                ai_result = analyze_with_ai(text, report_type_label)
                analysis_result = ai_result.get("analysis_result", {})
                ai_metadata = ai_result.get("ai_metadata", {})
                duplicates_count = 0
            elif pages_processed > 1 and extraction.get('pages'):
                # ── Multi-page blood/lab test ──
                page_results = []
                for page_info in extraction['pages']:
                    if page_info.get('success') and page_info.get('text'):
                        page_params = parse_blood_test(page_info['text'])
                        page_results.append(page_params)
                if page_results:
                    analysis_result, duplicates_count = merge_multi_page_results(page_results)
                else:
                    analysis_result, duplicates_count = {}, 0
            else:
                # ── Single-page blood/lab test ──
                analysis_result = parse_blood_test(text)
                duplicates_count = 0

            _analysis_jobs[job_id]["status"] = "analysing"
            insights = generate_insights(analysis_result)

            user_id = current_user['id']
            parameters_list = []
            total_count = optimal_count = attention_count = 0
            critical_parameters = []

            for name, data in analysis_result.items():
                total_count += 1
                param_status = data.get("status", "Normal")
                if param_status in ["High", "Low", "Critical"]:
                    attention_count += 1
                elif param_status == "Normal":
                    optimal_count += 1

                try:
                    from backend.abnormality_detector import Severity, get_severity_label
                    severity_enum = data.get("severity", Severity.MEDIUM)
                    severity_label = get_severity_label(severity_enum) if isinstance(severity_enum, Severity) else "Moderate Deviation"
                    severity_code = severity_enum.value if isinstance(severity_enum, Severity) else "MEDIUM"
                except Exception:
                    severity_label, severity_code = "Moderate Deviation", "MEDIUM"

                param_entry = {
                    "name": name,
                    "description": f"{name} ({data.get('category', 'Lab Test')})",
                    "value": str(data.get("value")),
                    "unit": data.get("unit"),
                    "range": data.get("range"),
                    "status": param_status,
                    "confidence": data.get("confidence", "Medium").lower(),
                    "notes": data.get("notes", []),
                    "severity": severity_code,
                    "severity_label": severity_label,
                    "source_page": data.get("source_page", 1),
                    "source_pages": data.get("source_pages", [data.get("source_page", 1)])
                }
                parameters_list.append(param_entry)

                # Track critical parameters for alert modal
                if param_status == "Critical" or str(severity_code).upper() == "CRITICAL":
                    critical_parameters.append({
                        "name": name,
                        "value": str(data.get("value")),
                        "unit": data.get("unit", ""),
                    })

            summary_stats = {
                "total_extracted": total_count,
                "optimal_count": optimal_count,
                "attention_count": attention_count,
                "analysis_depth": f"{min(98.4, total_count * 2.5):.1f}%"
            }
            systems_impact = compute_systems_impact(parameters_list)

            try:
                report_id = save_report(
                    user_id=user_id,
                    filename=file.filename,
                    summary_status=f"{attention_count} issues",
                    original_filename=file.filename
                )
                save_parameters(user_id, report_id, analysis_result)
                log_activity(user_id, "upload_report", "report", report_id)
            except Exception as db_err:
                log.warning("DB save error: %s", db_err)
                report_id = None

            _analysis_jobs[job_id]["status"] = "completed"
            _analysis_jobs[job_id]["result"] = {
                "filename": file.filename,
                "text": text,
                "analysis": analysis_result,
                "parameters": parameters_list,
                "insights": insights,
                "summary": summary_stats,
                "systems_impact": systems_impact,
                "pages_processed": pages_processed,
                "duplicates_removed": duplicates_count,
                "extraction_warnings": extraction_warnings,
                "quality_assessment": quality_data if quality_data else None,
                "has_critical": len(critical_parameters) > 0,
                "critical_parameters": critical_parameters,
                "report_id": report_id,
                # Report type classification
                "report_type": report_type,
                "report_type_label": report_type_label,
                "report_type_icon": report_type_icon,
                "ai_metadata": ai_metadata,
            }
        except Exception as exc:
            log.exception("Analysis job %s failed", job_id)
            _analysis_jobs[job_id]["status"] = "failed"
            _analysis_jobs[job_id]["error"] = str(exc)
        finally:
            if os.path.exists(file_location):
                os.remove(file_location)

    background_tasks.add_task(lambda: _ocr_executor.submit(run_analysis))

    return JSONResponse(
        status_code=202,
        content={"job_id": job_id, "status": "queued"}
    )


@app.get("/analyze/status/{job_id}")
async def analyze_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """
    Poll the status of an async analysis job.

    Possible statuses: queued | extracting | parsing | analysing | completed | failed
    When status is 'completed', the 'result' field contains the full analysis data.
    """
    job = _analysis_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    response_data = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed" and job["result"]:
        response_data["result"] = job["result"]
        # Clean up job after delivery
        del _analysis_jobs[job_id]
    elif job["status"] == "failed":
        response_data["error"] = job.get("error", "Unknown error")
        del _analysis_jobs[job_id]

    return response_data


@app.post("/analyze")
async def analyze_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    request: Request = None,
    rotation: int = 0
):
    """
    Synchronous analysis endpoint (kept for backward compatibility).
    Prefer /analyze/async for the non-blocking version.
    """
    os.makedirs("temp", exist_ok=True)
    file_location = f"temp/{file.filename}"
    
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    
    try:
        # Quality assessment (for images)
        quality_data = {}
        if file.content_type and file.content_type.startswith('image/'):
            quality_data = assess_image(file_location)
        
        # Enhanced extraction
        extraction = extract_text_enhanced(file_location, rotation)
        text = extraction['text']
        pages_processed = extraction['page_count']
        extraction_warnings = extraction.get('errors', [])
        
        # Classify report type and route accordingly
        report_classification = classify_report(text)
        report_type = report_classification["type"]
        report_type_label = report_classification["label"]
        report_type_icon = report_classification["icon"]
        ai_metadata = {}

        # Multi-page parsing and deduplication
        if report_classification["requires_ai"]:
            # Narrative report: CT, MRI, pathology, cardiology, etc.
            ai_result = analyze_with_ai(text, report_type_label)
            analysis_result = ai_result.get("analysis_result", {})
            ai_metadata = ai_result.get("ai_metadata", {})
            duplicates_count = 0
        elif pages_processed > 1 and extraction.get('pages'):
            page_results = []
            for page_info in extraction['pages']:
                if page_info.get('success') and page_info.get('text'):
                    page_params = parse_blood_test(page_info['text'])
                    page_results.append(page_params)
            if page_results:
                analysis_result, duplicates_count = merge_multi_page_results(page_results)
            else:
                analysis_result = {}
                duplicates_count = 0
        else:
            analysis_result = parse_blood_test(text)
            duplicates_count = 0
        
        # Generate insights
        insights = generate_insights(analysis_result)

        # Determine summary status for history
        summary_status = "Normal"
        for param, details in analysis_result.items():
            if isinstance(details, dict) and details.get("status") in ["High", "Low", "Critical"]:
                summary_status = "Attention Needed"
                break
                
        # Get user ID
        user_id = current_user['id']
        
        # Transform for frontend
        parameters_list = []
        total_count = 0
        optimal_count = 0
        attention_count = 0
        
        for name, data in analysis_result.items():
            total_count += 1
            conf = data.get("confidence", "Medium").lower()
            if data.get("status") in ["High", "Low", "Critical"]:
                attention_count += 1
            elif data.get("status") == "Normal":
                optimal_count += 1
            
            # Import severity label function
            try:
                from backend.abnormality_detector import Severity, get_severity_label
                severity_enum = data.get("severity", Severity.MEDIUM)
                severity_label = get_severity_label(severity_enum) if isinstance(severity_enum, Severity) else "Moderate Deviation"
                severity_code = severity_enum.value if isinstance(severity_enum, Severity) else "MEDIUM"
            except:
                severity_label = "Moderate Deviation"
                severity_code = "MEDIUM"
                
            parameters_list.append({
                "name": name,
                "description": f"{name} ({data.get('category', 'Lab Test')})",
                "value": str(data.get("value")),
                "unit": data.get("unit"),
                "range": data.get("range"),
                "status": data.get("status"),
                "confidence": conf,
                "notes": data.get("notes", []),
                "severity": severity_code,
                "severity_label": severity_label,
                "source_page": data.get("source_page", 1),
                "source_pages": data.get("source_pages", [data.get("source_page", 1)])
            })

        # Frontend Summary Stats
        summary_stats = {
            "total_extracted": total_count,
            "optimal_count": optimal_count,
            "attention_count": attention_count,
            "analysis_depth": f"{min(98.4, total_count * 2.5):.1f}%"
        }
        
        # Compute systems impact
        systems_impact = compute_systems_impact(parameters_list)
        
        # Save to database
        report_id = None
        try:
            report_id = save_report(
                user_id=user_id,
                filename=file.filename,
                summary_status=f"{attention_count} issues",
                original_filename=file.filename
            )
            save_parameters(user_id, report_id, analysis_result)
            
            # Log upload activity
            ip_address = get_client_ip(request) if request else None
            log_activity(user_id, "upload_report", "report", report_id, ip_address)
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
        
        return {
            "filename": file.filename,
            "text": text,
            "analysis": analysis_result,
            "parameters": parameters_list,
            "insights": insights,
            "summary": summary_stats,
            "systems_impact": systems_impact,
            # Enhanced fields
            "pages_processed": pages_processed,
            "duplicates_removed": duplicates_count,
            "extraction_warnings": extraction_warnings,
            "quality_assessment": quality_data if quality_data else None,
            # Report type classification
            "report_type": report_type,
            "report_type_label": report_type_label,
            "report_type_icon": report_type_icon,
            "ai_metadata": ai_metadata,
            "report_id": report_id,
        }
        
    finally:
        # Cleanup
        if os.path.exists(file_location):
            os.remove(file_location)

@app.get("/history")
async def get_history_endpoint(
    current_user: dict = Depends(get_current_user),
    limit: int = 50,
    search: str = None,
    favorite: bool = False,
    status: str = None,
    sort: str = "newest"
):
    """Returns the list of analyzed reports for the current user with optional filters."""
    return get_history(
        current_user['id'], limit,
        search=search,
        favorite_only=favorite,
        status_filter=status,
        sort_order=sort
    )

@app.get("/history/stats")
async def get_history_stats_endpoint(current_user: dict = Depends(get_current_user)):
    """Returns summary statistics for the user's report history."""
    from .database import get_history_stats
    return get_history_stats(current_user['id'])

@app.delete("/report/{report_id}")
async def delete_report_endpoint(
    report_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a report and all its linked data."""
    from .database import delete_report
    success = delete_report(current_user['id'], report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found or unauthorized")
    log_activity(current_user['id'], "delete_report", "report", report_id)
    return {"success": True, "message": "Report deleted successfully"}

@app.put("/report/{report_id}/favorite")
async def toggle_favorite_endpoint(
    report_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Toggle the favorite status of a report."""
    from .database import toggle_favorite
    new_status = toggle_favorite(current_user['id'], report_id)
    if new_status is None:
        raise HTTPException(status_code=404, detail="Report not found or unauthorized")
    return {"success": True, "is_favorite": new_status}

@app.put("/report/{report_id}/notes")
async def update_notes_endpoint(
    report_id: int,
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Add or update notes on a report."""
    from .database import update_report_notes
    notes = data.get("notes", "")
    success = update_report_notes(current_user['id'], report_id, notes)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found or unauthorized")
    return {"success": True, "message": "Notes updated"}

@app.post("/report/{report_id}/save-insights")
async def save_report_insights_endpoint(
    report_id: int,
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Save detailed insights JSON for a report."""
    from .database import save_report_insights
    success = save_report_insights(current_user['id'], report_id, data)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found or unauthorized")
    return {"success": True, "message": "Report saved successfully"}

@app.get("/report/{report_id}")
async def get_report_details(
    report_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the detailed parameters, insights, and summary for a specific report.
    """
    try:
        from .database import get_report_parameters
        
        # 1. Get raw parameters (Dict)
        parameters_dict = get_report_parameters(report_id)
        if not parameters_dict:
             raise HTTPException(status_code=404, detail="Report details not found")
        
        # 2. Re-construct analysis result
        analysis_result = parameters_dict
        
        # 3. Generate Insights
        insights = generate_insights(analysis_result)
        
        # 4. Transform to List & Calculate Stats
        parameters_list = []
        total_count = 0
        optimal_count = 0
        attention_count = 0
        
        for name, data in analysis_result.items():
            total_count += 1
            conf = data.get("confidence_score", "Medium")
            status_val = data.get("status", "Normal")
            
            # Normalize status for counting
            status_upper = status_val.upper() if status_val else "NORMAL"
            if status_upper in ["HIGH", "LOW", "CRITICAL", "ABNORMAL"]:
                attention_count += 1
            else:
                optimal_count += 1
                
            # Severity handling
            severity_code = data.get("severity", "MEDIUM")
            if isinstance(severity_code, int): # Handle enum if returned as int
                severity_code = "MEDIUM" 
            
            severity_label = "Moderate Deviation"
            if str(severity_code).upper() == "LOW": severity_label = "Mild Deviation"
            elif str(severity_code).upper() == "HIGH": severity_label = "Significant Deviation"
            elif str(severity_code).upper() == "CRITICAL": severity_label = "Critical Deviation"

            parameters_list.append({
                "name": name,
                "description": f"{name} (Lab Test)",
                "value": str(data.get("value")),
                "unit": data.get("unit"),
                "range": data.get("range"),
                "status": status_val,
                "confidence": str(conf),
                "severity": severity_code,
                "severity_label": severity_label,
                "source_page": 1
            })

        # 5. Summary Stats
        summary_stats = {
            "total_extracted": total_count,
            "optimal_count": optimal_count,
            "attention_count": attention_count,
            "analysis_depth": f"{min(98.4, total_count * 2.5):.1f}%"
        }
        
        # 6. Systems Impact
        systems_impact = compute_systems_impact(parameters_list)
        
        return {
            "parameters": parameters_list,
            "analysis": analysis_result,
            "insights": insights,
            "summary": summary_stats,
            "systems_impact": systems_impact
        }

    except Exception as e:
        print(f"Error getting report details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/parameter_history/{parameter_name}")
async def get_parameter_history_endpoint(
    parameter_name: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    Returns historical values for a specific parameter for the current user
    
    Args:
        parameter_name: Name of the parameter (e.g., "Hemoglobin")
        limit: Maximum number of historical records to return
    
    Returns:
        List of historical values with dates, values, and status
    """
    try:
        history = get_parameter_history(current_user['id'], parameter_name, limit)
        return {
            "parameter": parameter_name,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        return {
            "parameter": parameter_name,
            "history": [],
            "count": 0,
            "error": str(e)
        }




@app.post("/api/export/{format_type}")
async def export_report_endpoint(
    format_type: str,
    data: dict,
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Export report in multiple formats: excel, csv, hl7, pdf
    
    Args:
        format_type: 'excel', 'csv', 'hl7', or 'pdf'
        data: Report data including analysis, insights, systems_impact
    """
    from .export_handlers import (
        export_to_excel, export_to_csv, export_to_hl7_fhir, 
        get_export_filename
    )
    
    analysis = data.get("analysis", {})
    insights = data.get("insights", {})
    systems_impact = data.get("systems_impact", {})
    source_filename = data.get("filename", "report")
    
    user_info = None
    if current_user:
        user_info = {
            'full_name': current_user.get('full_name', 'Patient'),
            'date_of_birth': current_user.get('date_of_birth', 'N/A'),
            'gender': current_user.get('gender', 'N/A'),
            'email': current_user.get('email', 'N/A')
        }
    
    try:
        if format_type == 'excel':
            buffer = export_to_excel(analysis, insights, systems_impact, user_info, source_filename)
            filename = get_export_filename('excel', 'lab_report')
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            content = buffer.getvalue()
            
        elif format_type == 'csv':
            buffer = export_to_csv(analysis, user_info)
            filename = get_export_filename('csv', 'lab_report')
            media_type = "text/csv"
            content = buffer.getvalue().encode('utf-8')
            
        elif format_type == 'hl7':
            fhir_data = export_to_hl7_fhir(analysis, user_info, source_filename)
            filename = get_export_filename('hl7', 'lab_report')
            media_type = "application/fhir+json"
            import json
            content = json.dumps(fhir_data, indent=2).encode('utf-8')
            
        elif format_type == 'pdf':
            from .report_generator import generate_pdf
            buffer = generate_pdf(analysis, insights, systems_impact, source_filename, user_info)
            filename = get_export_filename('pdf', 'lab_report')
            media_type = "application/pdf"
            content = buffer.getvalue()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format_type}"
            )
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        # Log export activity
        if current_user:
            log_activity(current_user['id'], f"export_{format_type}", "report", None, get_client_ip(request) if request else None)
        
        return Response(content=content, media_type=media_type, headers=headers)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@app.post("/api/share/create")
async def create_share_link_endpoint(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a shareable link for a report
    
    Request body:
        - report_id: ID of report to share
        - expires_in_days: Optional expiration (default 30 days)
    """
    import secrets
    from .database import create_shareable_link, get_report_parameters
    
    report_id = data.get('report_id')
    expires_in_days = data.get('expires_in_days', 30)
    
    if not report_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing report_id"
        )
    
    # Generate unique token
    share_token = secrets.token_urlsafe(32)
    
    try:
        link_id = create_shareable_link(
            user_id=current_user['id'],
            report_id=report_id,
            share_token=share_token,
            expires_in_days=expires_in_days
        )
        
        # Generate shareable URL
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        shareable_url = f"{base_url}/share/{share_token}"
        
        # Log activity
        log_activity(current_user['id'], "create_share_link", "shareable_link", link_id)
        
        return {
            "success": True,
            "share_url": shareable_url,
            "share_token": share_token,
            "expires_in_days": expires_in_days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create shareable link: {str(e)}"
        )


@app.get("/api/share/{share_token}")
async def access_shared_report(share_token: str):
    """
    Access a shared report via shareable link (no authentication required)
    """
    from .database import validate_shareable_link, get_report_parameters
    
    report_id = validate_shareable_link(share_token)
    
    if not report_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shareable link not found or expired"
        )
    
    try:
        parameters = get_report_parameters(report_id)
        
        return {
            "success": True,
            "report_id": report_id,
            "parameters": parameters,
            "shared": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access report: {str(e)}"
        )


@app.get("/api/qrcode/{share_token}")
async def get_qr_code(share_token: str):
    """Generate QR code for a shareable link"""
    from .export_handlers import generate_qr_code
    
    # Generate URL for the share link
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    shareable_url = f"{base_url}/share/{share_token}"
    
    try:
        qr_buffer = generate_qr_code(shareable_url)
        return Response(content=qr_buffer.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QR code generation failed: {str(e)}"
        )


@app.get("/api/trajectory/{parameter_name}")
async def get_trajectory_analysis(
    parameter_name: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    Get trajectory analysis for a specific parameter
    
    Returns velocity, trend direction, risk level, and projections
    """
    from .trajectory_analyzer import analyze_trajectory
    from .parser import parse_reference_range
    
    try:
        # Get historical data
        history = get_parameter_history(current_user['id'], parameter_name, limit)
        
        if not history or len(history) < 2:
            return {
                "success": False,
                "message": "Insufficient historical data for trajectory analysis"
            }
        
        # Get reference range from most recent entry
        ref_range_str = history[0].get('range')
        ref_range = None
        if ref_range_str:
            try:
                from .report_generator import parse_reference_range
                min_val, max_val = parse_reference_range(ref_range_str)
                if min_val is not None and max_val is not None:
                    ref_range = {'min': min_val, 'max': max_val}
            except:
                pass
        
        # Analyze trajectory
        trajectory = analyze_trajectory(parameter_name, history, ref_range)
        
        return {
            "success": True,
            "parameter": parameter_name,
            "trend_direction": trajectory.trend_direction.value,
            "velocity": trajectory.velocity,
            "risk_level": trajectory.risk_level.value,
            "projected_value": trajectory.projected_value,
            "projected_date": trajectory.projected_date,
            "confidence": trajectory.confidence,
            "analysis": trajectory.analysis,
            "concerning_pathway": trajectory.concerning_pathway
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trajectory analysis failed: {str(e)}"
        )



# ============================================================================
# Verification Endpoints (New Features)
# ============================================================================

@app.post("/api/verify/update_parameter")
async def update_parameter_endpoint(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a parameter value inline during verification.
    
    Request body:
        - parameter_name: Name of the parameter
        - new_value: New value for the parameter
        - new_unit: Optional new unit
        - report_id: Optional report ID (uses most recent if not provided)
    
    Returns:
        Updated parameter object
    """
    from .database import update_parameter_value, get_report_id_from_session
    
    parameter_name = data.get("parameter_name")
    new_value = data.get("new_value")
    new_unit = data.get("new_unit")
    report_id = data.get("report_id")
    
    if not parameter_name or new_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: parameter_name and new_value"
        )
    
    # Get report_id if not provided
    if not report_id:
        report_id = get_report_id_from_session(current_user['id'])
        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reports found for this user"
            )
    
    # Attempt to update
    try:
        success = update_parameter_value(
            user_id=current_user['id'],
            report_id=report_id,
            parameter_name=parameter_name,
            new_value=new_value,
            new_unit=new_unit
        )
        
        if success:
            return {
                "success": True,
                "message": f"Parameter '{parameter_name}' updated successfully",
                "parameter": {
                    "name": parameter_name,
                    "value": new_value,
                    "unit": new_unit
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parameter '{parameter_name}' not found in report"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.post("/api/verify/flag_parameter")
async def flag_parameter_endpoint(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Flag a parameter as incorrectly extracted.
    
    Request body:
        - parameter_name: Name of the parameter
        - report_id: Optional report ID
        - issue_type: Type of issue (misread/missing/incorrect_unit)
        - notes: Optional additional notes
        - corrected_value: Optional user-corrected value
    
    Returns:
        Flag ID and success message
    """
    from .database import create_parameter_flag, get_report_id_from_session
    
    parameter_name = data.get("parameter_name")
    issue_type = data.get("issue_type", "misread")
    notes = data.get("notes", "")
    corrected_value = data.get("corrected_value", "")
    original_value = data.get("original_value", "")
    report_id = data.get("report_id")
    
    if not parameter_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: parameter_name"
        )
    
    # Get report_id if not provided
    if not report_id:
        report_id = get_report_id_from_session(current_user['id'])
        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No reports found for this user"
            )
    
    try:
        flag_id = create_parameter_flag(
            user_id=current_user['id'],
            report_id=report_id,
            parameter_name=parameter_name,
            original_value=original_value,
            corrected_value=corrected_value,
            issue_type=issue_type,
            notes=notes
        )
        
        # Log activity
        from .database import log_activity
        log_activity(current_user['id'], "flag_parameter", "parameter_flag", flag_id)
        
        return {
            "success": True,
            "message": "Parameter flagged successfully. Thank you for helping improve our system!",
            "flag_id": flag_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create flag: {str(e)}"
        )


@app.post("/api/verify/suggest_missing_tests")
async def suggest_missing_tests_endpoint(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Suggest missing follow-up tests based on detected abnormalities.
    
    Request body:
        - parameters: List of parameter objects with name, value, status, etc.
    
    Returns:
        Array of suggested tests with rationale and priority
    """
    from .missing_tests_suggester import suggest_missing_tests, get_demographic_specific_suggestions
    
    parameters = data.get("parameters", [])
    
    if not parameters:
        return {
            "suggestions": [],
            "count": 0
        }
    
    try:
        # Get abnormality-based suggestions
        suggestions = suggest_missing_tests(parameters)
        
        # Get demographic-specific suggestions
        user_data = {
            "age": current_user.get("age"),
            "gender": current_user.get("gender"),
        }
        demographic_suggestions = get_demographic_specific_suggestions(parameters, user_data)
        
        # Combine and deduplicate
        all_suggestions = suggestions + demographic_suggestions
        unique_suggestions = []
        seen_tests = set()
        
        for suggestion in all_suggestions:
            if suggestion["test_name"] not in seen_tests:
                seen_tests.add(suggestion["test_name"])
                unique_suggestions.append(suggestion)
        
        return {
            "suggestions": unique_suggestions,
            "count": len(unique_suggestions)
        }
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error generating test suggestions: {e}")
        return {
            "suggestions": [],
            "count": 0,
            "error": "Failed to generate suggestions"
        }


@app.get("/api/verify/flags")
async def get_flags_endpoint(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    Get parameter flags for the current user.
    
    Returns:
        List of flagged parameters
    """
    from .database import get_parameter_flags
    
    try:
        flags = get_parameter_flags(user_id=current_user['id'], limit=limit)
        return {
            "flags": flags,
            "count": len(flags)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve flags: {str(e)}"
        )


# ============================================================================
# Shareable Links Endpoints
# ============================================================================

@app.post("/api/share/create")
async def create_share_link(
    report_id: int,
    expires_in_days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a shareable link for a lab report.
    """
    import secrets
    from .database import create_shareable_link, get_report_parameters
    
    try:
        report_params = get_report_parameters(report_id)
        if not report_params:
            raise HTTPException(status_code=404, detail="Report not found")
        
        share_token = secrets.token_urlsafe(32)
        
        link_id = create_shareable_link(
            user_id=current_user['id'],
            report_id=report_id,
            share_token=share_token,
            expires_in_days=expires_in_days
        )
        
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        share_url = f"{base_url}/shared/{share_token}"
        
        return {
            "success": True,
            "share_token": share_token,
            "share_url": share_url,
            "expires_in_days": expires_in_days,
            "link_id": link_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/share/{share_token}")
async def get_shared_report(share_token: str):
    """Get report data via shareable link (public access, no auth required)."""
    from .database import validate_shareable_link, get_report_parameters
    
    try:
        report_id = validate_shareable_link(share_token)
        
        if not report_id:
            raise HTTPException(
                status_code=404, 
                detail="Share link not found, expired, or revoked"
            )
        
        parameters = get_report_parameters(report_id)
        
        if not parameters:
            raise HTTPException(status_code=404, detail="Report data not found")
        
        return {
            "success": True,
            "report_id": report_id,
            "parameters": parameters,
            "shared": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/share/{share_token}")
async def revoke_share_link(
    share_token: str,
    current_user: dict = Depends(get_current_user)
):
    """Revoke a shareable link (owner only)."""
    from .database import revoke_shareable_link
    
    try:
        success = revoke_shareable_link(share_token, current_user['id'])
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Share link not found or you don't have permission to revoke it"
            )
        
        return {
            "success": True,
            "message": "Share link revoked successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/share/my-links")
async def get_my_share_links(
    current_user: dict = Depends(get_current_user)
):
    """Get all shareable links created by the current user."""
    from .database import get_user_shareable_links
    
    try:
        links = get_user_shareable_links(current_user['id'])
        
        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
        for link in links:
            link['share_url'] = f"{base_url}/shared/{link['share_token']}"
        
        return {
            "success": True,
            "links": links,
            "count": len(links)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# Report Generation Endpoint
# ============================================================================

@app.post("/generate_report")
async def generate_report_endpoint(
    request: ReportRequest,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Generate a PDF report based on the provided analysis data.
    """
    try:
        user_info = None
        if current_user:
            user_info = {
                'full_name': current_user.get('full_name', 'Patient'),
                'date_of_birth': current_user.get('date_of_birth', 'N/A'),
                'gender': current_user.get('gender', 'N/A'),
                'email': current_user.get('email', 'N/A')
            }

        # Generate the PDF
        pdf_buffer = generate_pdf(
            analysis_data=request.analysis,
            insights_data=request.insights,
            systems_impact=request.systems_impact,
            source_filename=request.filename,
            user_info=user_info
        )
        
        # Return as a streaming response
        return StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={request.filename}_report.pdf"
            }
        )
    except Exception as e:
        # print(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# Mount static files for frontend (must be last to avoid overriding API routes)

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

