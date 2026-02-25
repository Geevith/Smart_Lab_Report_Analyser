/**
 * Authentication Utilities
 * Client-side authentication helper functions
 */

// API_BASE_URL is defined in config.js (loaded before this script)

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

    // Attach event delegation for logout (handled at document level or container level)
    // We'll use a document-level listener for simplicity and reliability with dynamic elements
    if (!window.logoutListenerAttached) {
        document.addEventListener('click', async (e) => {
            const logoutBtn = e.target.closest('#logoutBtn');
            if (logoutBtn) {
                e.preventDefault();
                e.stopPropagation();

                // Find the dropdown and close it (optional, but good UX)
                const dropdown = logoutBtn.closest('.absolute');
                if (dropdown) {
                    dropdown.classList.add('opacity-0', 'scale-95', 'pointer-events-none');
                }

                if (confirm('Are you sure you want to logout?')) {
                    await handleLogout();
                }
            }
        });
        window.logoutListenerAttached = true;
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
