/**
 * Settings UI Logic
 */

let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Require authentication
    currentUser = await initAuth({
        requireAuthentication: true,
        displayUser: true,
        userInfoElementId: 'userInfo',
        navElementId: 'navActions'
    });

    if (!currentUser) return; // Will be redirected by auth.js

    setupThemeSelector();
    setupExportData();
    setupDeleteAccount();

    // BUG-16 FIX: Wire the header dark mode toggle button
    const darkToggle = document.getElementById('settingsHeaderDarkToggle');
    if (darkToggle) {
        // Set correct icon on load
        const updateIcon = () => {
            const icon = darkToggle.querySelector('span');
            if (icon) icon.textContent = document.documentElement.classList.contains('dark') ? 'light_mode' : 'dark_mode';
        };
        updateIcon();
        darkToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            updateIcon();
        });
    }
});

// ==========================================
// Theme Selector Logic
// ==========================================
function setupThemeSelector() {
    const buttons = document.querySelectorAll('.theme-btn');

    // Determine active theme
    const activeTheme = localStorage.getItem('theme') || currentUser.theme || 'system';

    function setActiveButton(theme) {
        buttons.forEach(btn => {
            const check = btn.querySelector('.check-icon');
            if (btn.dataset.theme === theme) {
                btn.classList.add('ring-4', 'ring-indigo-500/50');
                if (check) check.classList.remove('hidden');
            } else {
                btn.classList.remove('ring-4', 'ring-indigo-500/50');
                if (check) check.classList.add('hidden');
            }
        });
    }

    setActiveButton(activeTheme);

    buttons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const selectedTheme = btn.dataset.theme;

            // Optimistic update
            setActiveButton(selectedTheme);
            localStorage.setItem('theme', selectedTheme);
            applyTheme(selectedTheme);

            // Sync with backend
            try {
                await fetch(`${API_BASE_URL}/api/user/theme`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ theme: selectedTheme })
                });
            } catch (err) {
                console.error("Failed to sync theme to backend", err);
            }
        });
    });
}

// ==========================================
// Export Data Logic (HIPAA/GDPR)
// ==========================================
function setupExportData() {
    const exportBtn = document.getElementById('exportDataBtn');

    exportBtn.addEventListener('click', async () => {
        try {
            exportBtn.disabled = true;
            exportBtn.innerHTML = '<span class="material-icons-round text-teal-600 animate-spin">sync</span> Exporting...';

            const response = await fetch(`${API_BASE_URL}/api/user/export`, {
                method: 'GET',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error("Failed to export data");
            }

            const data = await response.json();

            // Create downloadable JSON file
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            const dateStr = new Date().toISOString().split('T')[0];
            downloadAnchorNode.setAttribute("download", `medlab_export_${currentUser.username}_${dateStr}.json`);
            document.body.appendChild(downloadAnchorNode); // required for firefox
            downloadAnchorNode.click();
            downloadAnchorNode.remove();

            // Reset button
            exportBtn.innerHTML = '<span class="material-icons-round text-teal-600">check</span> Export Complete';
            setTimeout(() => {
                exportBtn.innerHTML = '<span class="material-icons-round text-teal-600 dark:text-teal-400">cloud_download</span> Export JSON';
                exportBtn.disabled = false;
            }, 3000);

        } catch (error) {
            console.error(error);
            alert("Error exporting data. Please try again later.");
            exportBtn.innerHTML = '<span class="material-icons-round text-teal-600 dark:text-teal-400">cloud_download</span> Export JSON';
            exportBtn.disabled = false;
        }
    });
}

// ==========================================
// Delete Account Logic
// ==========================================
function setupDeleteAccount() {
    const triggerBtn = document.getElementById('deleteAccountTargetBtn');
    const modal = document.getElementById('deleteModal');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const input = document.getElementById('deleteConfirmInput');

    // Show modal
    triggerBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        // Small delay to allow CSS transition
        setTimeout(() => {
            modal.querySelector('#deleteModalContent').classList.remove('scale-95', 'opacity-0');
            modal.querySelector('#deleteModalContent').classList.add('scale-100', 'opacity-100');
        }, 10);
    });

    // Hide modal
    function hideModal() {
        modal.querySelector('#deleteModalContent').classList.add('scale-95', 'opacity-0');
        modal.querySelector('#deleteModalContent').classList.remove('scale-100', 'opacity-100');
        setTimeout(() => {
            modal.classList.add('hidden');
            input.value = '';
            confirmBtn.disabled = true;
        }, 300);
    }

    cancelBtn.addEventListener('click', hideModal);

    // Validate input
    input.addEventListener('input', (e) => {
        if (e.target.value === 'DELETE') {
            confirmBtn.disabled = false;
        } else {
            confirmBtn.disabled = true;
        }
    });

    // Handle Deletion
    confirmBtn.addEventListener('click', async () => {
        try {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<span class="material-icons-round animate-spin">sync</span> Deleting...';

            const response = await fetch(`${API_BASE_URL}/api/user`, {
                method: 'DELETE',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error("Failed to delete account");
            }

            // Success! Clear local state and redirect to landing
            localStorage.removeItem('theme');
            window.location.href = 'index.html';

        } catch (error) {
            console.error(error);
            alert("Error deleting account. Please contact support.");
            hideModal();
            confirmBtn.innerHTML = 'Permanently Delete';
            confirmBtn.disabled = false;
        }
    });
}
