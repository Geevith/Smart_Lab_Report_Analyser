// ==========================================
// SHARED UTILITY FUNCTIONS
// v2 — Added CSRF support, apiFetch, improved notifications
// ==========================================

// ── ApiError ────────────────────────────────────────────────────────────────

class ApiError extends Error {
    constructor(status, code, message) {
        super(message);
        this.status = status;
        this.code = code;
        this.name = 'ApiError';
    }
}

// ── CSRF Token ───────────────────────────────────────────────────────────────

/**
 * Read the csrf_token cookie (set by the server, httponly=false so JS can read it).
 * Returns empty string if not found (graceful fallback).
 * @returns {string}
 */
function getCSRFToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
}

// ── apiFetch — enhanced fetch wrapper ─────────────────────────────────────────

/**
 * Wrapper around fetch() that:
 *  - Always sends credentials (cookies)
 *  - Auto-attaches X-CSRF-Token header for state-mutating requests
 *  - Parses JSON and throws ApiError on non-2xx responses
 *  - Redirects to /login.html on 401
 *
 * @param {string} url
 * @param {RequestInit} options
 * @returns {Promise<any>}
 */
async function apiFetch(url, options = {}) {
    const method = (options.method || 'GET').toUpperCase();
    const needsCsrf = !['GET', 'HEAD', 'OPTIONS'].includes(method);

    const headers = {
        'Content-Type': 'application/json',
        ...(needsCsrf ? { 'X-CSRF-Token': getCSRFToken() } : {}),
        ...(options.headers || {}),
    };

    // Don't set Content-Type for FormData — browser sets it with boundary
    if (options.body instanceof FormData) {
        delete headers['Content-Type'];
    }

    let response;
    try {
        response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include',
        });
    } catch (networkErr) {
        throw new ApiError(0, 'network_error', 'Network error — check your internet connection.');
    }

    // Auth redirect
    if (response.status === 401) {
        sessionStorage.setItem('redirect_after_login', location.href);
        location.href = '/login.html';
        throw new ApiError(401, 'unauthorized', 'Session expired. Please log in again.');
    }

    if (response.status === 204) return null;

    let body;
    try { body = await response.json(); } catch { body = null; }

    if (!response.ok) {
        const message = body?.detail ?? body?.message ?? `Server error ${response.status}`;
        const code = body?.error ?? 'unknown_error';
        throw new ApiError(response.status, code, message);
    }

    return body;
}

// ── Notifications ─────────────────────────────────────────────────────────────

const _NOTIFICATION_ICONS = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
};

/**
 * Show a toast notification.
 * Uses the #notification-container from skeleton_and_alerts.css if present,
 * or falls back to creating a minimal container (backwards compatible).
 *
 * @param {string} message
 * @param {'info'|'success'|'error'|'warning'} type
 * @param {number} [duration=4000] ms before auto-dismiss (0 = sticky)
 */
function showNotification(message, type = 'info', duration = 4000) {
    // Ensure container exists
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        // Fallback styles when skeleton_and_alerts.css not loaded
        container.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9500;display:flex;flex-direction:column;gap:0.5rem;pointer-events:none;max-width:380px;';
        document.body.appendChild(container);
    }

    // Announce to screen readers
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'false');

    const toast = document.createElement('div');
    toast.className = `notification notification--${type}`;
    toast.setAttribute('role', 'status');
    toast.innerHTML = `
        <span class="notification__icon" aria-hidden="true">${_NOTIFICATION_ICONS[type] || 'ℹ'}</span>
        <span class="notification__message">${escapeHtml(message)}</span>
        <button class="notification__close" aria-label="Dismiss notification" title="Dismiss">×</button>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.add('notification--visible');
    });

    function dismiss() {
        toast.classList.add('notification--dismissing');
        toast.classList.remove('notification--visible');
        setTimeout(() => toast.remove(), 220);
    }

    toast.querySelector('.notification__close').addEventListener('click', dismiss);

    if (duration > 0) {
        setTimeout(dismiss, duration);
    }
}

// ── Date Formatting ───────────────────────────────────────────────────────────

/**
 * Format an ISO date string into a human-friendly string.
 * @param {string} isoString
 * @returns {string}
 */
function formatDate(isoString) {
    if (!isoString) return 'N/A';
    try {
        return new Date(isoString).toLocaleDateString('en-GB', {
            day: 'numeric', month: 'short', year: 'numeric'
        });
    } catch {
        return isoString;
    }
}

// ── File Size ─────────────────────────────────────────────────────────────────

/**
 * Format bytes into a human-readable string (KB, MB, etc.).
 * @param {number} bytes
 * @returns {string}
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

// ── HTML Escaping ─────────────────────────────────────────────────────────────

/**
 * Escape HTML entities to prevent XSS.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = String(text ?? '');
    return div.innerHTML;
}

// ── Debounce ──────────────────────────────────────────────────────────────────

function debounce(fn, ms = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

// ── Auth Helpers ──────────────────────────────────────────────────────────────

/**
 * Redirect to login page, saving current URL for post-login redirect.
 */
function requireAuth() {
    sessionStorage.setItem('redirect_after_login', location.href);
    location.href = '/login.html';
}

/**
 * Consume the post-login redirect URL (call once after successful login).
 * @returns {string|null}
 */
function consumeRedirectAfterLogin() {
    const url = sessionStorage.getItem('redirect_after_login');
    sessionStorage.removeItem('redirect_after_login');
    return url;
}
