document.addEventListener('DOMContentLoaded', async () => {
    T4Logger.info("Menu loaded");

    // Check if user is authenticated (simplified check, ideally verify token)
    const token = localStorage.getItem('t4_access_token');
    if (!token) {
        T4Logger.warn("No token found, redirecting to login");
        window.location.href = '/login';
        return;
    }

    // Animate cards on entry
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100 * (index + 1));
    });
});
