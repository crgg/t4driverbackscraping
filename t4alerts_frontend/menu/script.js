document.addEventListener('DOMContentLoaded', async () => {
    T4Logger.info("Menu loaded");

    // Check if user is authenticated (simplified check, ideally verify token)
    const token = localStorage.getItem('t4_access_token');
    if (!token) {
        T4Logger.warn("No token found, redirecting to login");
        window.location.href = '/login';
        return;
    }

    // Check if token is expired
    if (PermissionManager.isTokenExpired()) {
        T4Logger.warn("Token expired, redirecting to login");
        localStorage.removeItem('t4_access_token');
        window.location.href = '/login';
        return;
    }

    // Log permissions for debugging
    PermissionManager.logPermissions();

    // Show/hide cards based on permissions
    setupMenuCards();

    // Animate cards on entry
    animateCards();
});

/**
 * Setup menu cards based on user permissions
 */
function setupMenuCards() {
    const adminCard = document.getElementById('adminCard');
    const certificatesCard = document.getElementById('certificatesCard');
    const errorsCard = document.getElementById('errorsCard');

    // Admin card - only for admins
    if (PermissionManager.isAdmin()) {
        adminCard.style.display = 'block';
        adminCard.onclick = () => {
            T4Logger.info("Navigating to admin panel");
            window.location.href = '/admin';
        };
    }

    // Certificates card - requires view_certificates permission
    if (PermissionManager.hasPermission('view_certificates')) {
        certificatesCard.style.display = 'block';
        certificatesCard.onclick = () => {
            T4Logger.info("Navigating to certificates");
            ViewFactory.navigateTo('certificates');
        };
    }

    // Errors card - requires view_errors permission
    if (PermissionManager.hasPermission('view_errors')) {
        errorsCard.style.display = 'block';
        errorsCard.onclick = () => {
            T4Logger.info("Navigating to errors dashboard");
            ViewFactory.navigateTo('errors');
        };
    }

    // Check if user has no permissions at all (not even admin)
    if (!PermissionManager.isAdmin() &&
        !PermissionManager.hasPermission('view_certificates') &&
        !PermissionManager.hasPermission('view_errors')) {

        T4Logger.warn("User has no permissions");

        // Show a message
        const optionsWrapper = document.querySelector('.options-wrapper');
        optionsWrapper.innerHTML = `
            <div class="no-permissions-message">
                <h2>⚠️ No Permissions ⚠️</h2>
                <p>You don't have access to any sections yet.</p>
                <p>Please contact an administrator to grant you permissions.</p>
                <button onclick="logout()" class="logout-btn">Logout</button>
            </div>
        `;
    }
}

/**
 * Animate visible cards
 */
function animateCards() {
    const cards = document.querySelectorAll('.menu-card[style*="display: block"], .menu-card:not([style*="display: none"])');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * (index + 1));
    });
}

/**
 * Logout function
 */
function logout() {
    localStorage.removeItem('t4_access_token');
    window.location.href = '/login';
}

