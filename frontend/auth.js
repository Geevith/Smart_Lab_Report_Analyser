/**
 * Authentication Utilities
 * Client-side authentication helper functions
 */

// API_BASE_URL is defined in config.js (loaded before this script)

/**
 * Apply the user's theme preference to the document
 * @param {string} theme - 'light', 'dark', or 'system'
 */
function applyTheme(theme) {
    if (!theme) return;

    // Check if there is already a local override (e.g. from a toggle button)
    const localTheme = localStorage.getItem('theme');

    // We prioritize local theme if it exists, otherwise use the DB value
    const activeTheme = localTheme || theme;

    const isSystemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (activeTheme === 'dark' || (activeTheme === 'system' && isSystemDark) || theme === 'dark') {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
}

/**
 * Initialize auto-logout after 15 minutes of inactivity
 */
function initAutoLogout() {
    // Only run if not already running to avoid duplicate listeners
    if (window._autoLogoutInitialized) return;
    window._autoLogoutInitialized = true;

    const INACTIVITY_LIMIT_MS = 15 * 60 * 1000; // 15 mins
    const WARNING_TIME_MS = 14 * 60 * 1000; // 14 mins

    let inactivityTimer;
    let warningTimer;
    let warningModalOpen = false;

    function resetTimers() {
        if (warningModalOpen) return; // Don't reset if showing warning

        clearTimeout(inactivityTimer);
        clearTimeout(warningTimer);

        warningTimer = setTimeout(showWarning, WARNING_TIME_MS);
        inactivityTimer = setTimeout(triggerLogout, INACTIVITY_LIMIT_MS);
    }

    function showWarning() {
        warningModalOpen = true;
        const modal = document.createElement('div');
        modal.id = 'inactivityWarningModal';
        modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm transition-opacity duration-300';
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl max-w-sm w-full p-6 text-center transform transition-all scale-100">
                <div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span class="material-icons-round text-3xl text-red-600 dark:text-red-400">timer</span>
                </div>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white mb-2">Session Expiring Soon</h3>
                <p class="text-slate-600 dark:text-slate-300 mb-6 text-sm">For your security, you will be logged out automatically in 1 minute due to inactivity.</p>
                <button id="stayLoggedInBtn" class="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-md hover:shadow-lg focus:ring-4 focus:ring-teal-500/30">
                    Stay Logged In
                </button>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('stayLoggedInBtn').addEventListener('click', () => {
            document.body.removeChild(modal);
            warningModalOpen = false;
            resetTimers();
        });
    }

    async function triggerLogout() {
        // Clear session and redirect independently of API response
        await handleLogout();
    }

    // Attach listeners
    ['mousemove', 'keydown', 'scroll', 'click'].forEach(evt => {
        window.addEventListener(evt, resetTimers, { passive: true });
    });

    // Start timer
    resetTimers();
}

/**
 * Check if user is authenticated
 * @returns {Promise<Object|null>} User object if authenticated, null otherwise
 */
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            method: 'GET',
            credentials: 'include', // Include cookies
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const user = await response.json();
            return user;
        } else {
            return null;
        }
    } catch (error) {
        console.error('Auth check error:', error);
        return null;
    }
}

/**
 * Redirect to login page if not authenticated
 * Call this on protected pages
 */
async function requireAuth() {
    const user = await checkAuth();

    if (!user) {
        // Save current page to redirect back after login
        const currentPage = window.location.pathname.split('/').pop() || 'upload_ui.html';
        window.location.href = `login.html?redirect=${encodeURIComponent(currentPage)}`;
        return null;
    }

    return user;
}

/**
 * Handle user registration
 * @param {Object} formData - Registration form data
 * @returns {Promise<Object>} Response with success/error
 */
async function handleRegister(formData) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            return {
                success: true,
                message: data.message,
                auto_login: data.auto_login,
                user: data.user
            };
        } else {
            return {
                success: false,
                error: data.detail || 'Registration failed'
            };
        }
    } catch (error) {
        console.error('Registration error:', error);
        return {
            success: false,
            error: 'Network error. Please check your connection and try again.'
        };
    }
}

/**
 * Handle user login
 * @param {Object} credentials - Login credentials
 * @returns {Promise<Object>} Response with success/error and user data
 */
async function handleLogin(credentials) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            credentials: 'include', // Include cookies
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(credentials)
        });

        const data = await response.json();

        if (response.ok) {
            return {
                success: true,
                user: data.user,
                message: data.message
            };
        } else {
            return {
                success: false,
                error: data.detail || 'Login failed'
            };
        }
    } catch (error) {
        console.error('Login error:', error);
        return {
            success: false,
            error: 'Network error. Please check your connection and try again.'
        };
    }
}

/**
 * Handle user logout
 * @returns {Promise<Object>} Response with success/error
 */
async function handleLogout() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include', // Include cookies
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Redirect to landing page
            window.location.href = 'index.html';
            return {
                success: true,
                message: data.message
            };
        } else {
            return {
                success: false,
                error: data.detail || 'Logout failed'
            };
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Even if network error, redirect to landing page
        window.location.href = 'index.html';
        return {
            success: false,
            error: 'Network error during logout'
        };
    }
}

/**
 * Display current user info in UI
 * @param {HTMLElement} element - Element to display user info
 */
async function displayUserInfo(element) {
    const user = await checkAuth();

    if (user && element) {
        element.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 14px;
                ">
                    ${(user.username || user.email).charAt(0).toUpperCase()}
                </div>
                <div>
                    <div style="font-weight: 600; font-size: 14px; color: #1F2937;">
                        ${user.full_name || user.username}
                    </div>
                    <div style="font-size: 12px; color: #6B7280;">
                        ${user.email}
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Add logout button to navigation
 * @param {HTMLElement} navElement - Navigation element
 */
/**
 * Create profile dropdown with logout or login
 * @param {HTMLElement} navElement - Navigation element to attach to
 * @param {Object|null} user - User object or null if guest
 */
function createProfileDropdown(navElement, user) {
    if (!navElement) return;

    // clear existing
    navElement.innerHTML = '';

    const container = document.createElement('div');
    container.className = 'relative inline-block text-left';

    const isGuest = !user;
    const initial = isGuest ? '?' : (user.username || user.email).charAt(0).toUpperCase();
    const name = isGuest ? 'Guest User' : (user.full_name || user.username);
    const email = isGuest ? 'Not logged in' : user.email;
    const bgColor = isGuest ? 'from-gray-400 to-gray-600' : 'from-teal-500 to-teal-700';

    // Avatar Button
    const btn = document.createElement('button');
    btn.className = `flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br ${bgColor} text-white font-bold text-sm shadow-md hover:shadow-lg transition-all focus:outline-none ring-2 ring-offset-2 ring-transparent focus:ring-teal-500`;

    if (isGuest) {
        btn.innerHTML = '<span class="material-icons-round text-lg">person</span>';
    } else {
        btn.innerHTML = initial;
    }
    btn.title = name;

    // Dropdown Menu
    const dropdown = document.createElement('div');
    dropdown.className = 'absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-gray-100 dark:border-slate-700/50 transform transition-all duration-200 opacity-0 scale-95 pointer-events-none z-50 origin-top-right';

    let menuContent = '';

    if (isGuest) {
        menuContent = `
            <div class="px-4 py-3 border-b border-gray-100 dark:border-slate-700/50">
                <p class="text-sm font-bold text-gray-900 dark:text-white">${name}</p>
                <p class="text-xs text-text-gray-500 dark:text-gray-400">Please log in to save reports</p>
            </div>
            <div class="p-1">
                <a href="login.html" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-teal-600 hover:bg-teal-50 dark:hover:bg-teal-900/20 rounded-lg transition-colors text-left font-medium">
                    <span class="material-icons-round text-lg">login</span>
                    Log In / Register
                </a>
            </div>
        `;
    } else {
        menuContent = `
            <div class="px-4 py-3 border-b border-gray-100 dark:border-slate-700/50">
                <p class="text-sm font-bold text-gray-900 dark:text-white truncate">${name}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 truncate">${email}</p>
            </div>
            <div class="p-1 border-b border-gray-100 dark:border-slate-700/50">
                <a href="settings.html" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-left">
                    <span class="material-icons-round text-lg">settings</span>
                    Settings & Privacy
                </a>
            </div>
            <div class="p-1">
                <button id="logoutBtn" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors text-left">
                    <span class="material-icons-round text-lg">logout</span>
                    Logout
                </button>
            </div>
        `;
    }

    dropdown.innerHTML = menuContent;

    // Toggle logic
    let isOpen = false;

    function toggleDropdown(show) {
        isOpen = show;
        if (isOpen) {
            dropdown.classList.remove('opacity-0', 'scale-95', 'pointer-events-none');
        } else {
            dropdown.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
        }
    }

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleDropdown(!isOpen);
    });

    // Close on click outside
    document.addEventListener('click', () => {
        if (isOpen) toggleDropdown(false);
    });

    dropdown.addEventListener('click', (e) => e.stopPropagation());

    container.appendChild(btn);
    container.appendChild(dropdown);
    navElement.appendChild(container);

    // Attach event listener directly to logout button if it exists
    const logoutBtn = dropdown.querySelector('#logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();

            // Close the dropdown
            toggleDropdown(false);

            if (confirm('Are you sure you want to logout?')) {
                await handleLogout();
            }
        });
    }
}

/**
 * Initialize auth on page load
 * Call this in DOMContentLoaded on protected pages
 */
async function initAuth(options = {}) {
    const {
        requireAuthentication = true,
        displayUser = true,
        userInfoElementId = 'userInfo',
        navElementId = 'navActions'
    } = options;

    // Check authentication
    let user = null;
    if (requireAuthentication) {
        user = await requireAuth();
        if (!user) return null; // User was redirected
    } else {
        user = await checkAuth();
    }

    // Display user profile (Guest or User)
    if (displayUser) {
        const navElement = document.getElementById(navElementId);
        if (navElement) {
            // If we have a user OR we want to show guest dropdown
            createProfileDropdown(navElement, user);
        }
    }

    // Initialize Global User Settings if logged in
    if (user) {
        if (user.theme) {
            applyTheme(user.theme);
        }
        initAutoLogout();
    }

    return user;
}

// Export for module usage (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkAuth,
        requireAuth,
        handleRegister,
        handleLogin,
        handleLogout,
        displayUserInfo,
        createProfileDropdown,
        initAuth
    };
}
