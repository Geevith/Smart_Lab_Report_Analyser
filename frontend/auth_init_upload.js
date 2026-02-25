// Authentication initialization for upload_ui.html
// Add this script before upload_ui.js in the HTML file

document.addEventListener('DOMContentLoaded', async () => {
    // Require authentication for this page
    const user = await initAuth({
        requireAuthentication: false, // Allow guest access (landing page)
        displayUser: true, // Enable automatic profile dropdown (shows Guest or User)
        userInfoElementId: 'userInfo',
        navElementId: 'navActions'
    });

    // Manual DOM updates are no longer needed as initAuth handles the dropdown
});
