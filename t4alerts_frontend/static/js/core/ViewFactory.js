/**
 * ViewFactory
 * Handles navigation/redirection logic.
 * (Simplified for multi-page app, but prepared for SPA)
 */
class ViewFactory {
    static navigateTo(viewName) {
        window.T4Logger.info(`Navigating to ${viewName}`);

        switch (viewName) {
            case 'menu':
                window.location.href = '/menu';
                break;
            case 'certificates':
                window.location.href = '/certificates';
                break;
            case 'error-history':
                // SPA navigation pattern
                window.history.pushState({ page: 'history' }, '', '/errors/history');

                document.querySelectorAll('main > div').forEach(div => div.style.display = 'none');
                document.querySelector('main > header').style.display = 'flex';
                document.getElementById('view-error-history').style.display = 'block';
                document.getElementById('page-title').innerText = 'Global Error History';

                // Call global loader
                if (window.loadErrorHistory) {
                    window.loadErrorHistory();
                }
                break;
            case 'custom-scan':
                // SPA navigation pattern
                window.history.pushState({ page: 'custom-scan' }, '', '/errors/custom-scan');

                document.querySelectorAll('main > div').forEach(div => div.style.display = 'none');
                document.querySelector('main > header').style.display = 'flex';
                document.getElementById('custom-scan-view').style.display = 'block';
                document.getElementById('page-title').innerText = 'Custom App Scan';

                // Set default date to today
                const today = new Date().toISOString().split('T')[0];
                document.getElementById('scan-date').value = today;
                break;
            case 'errors':
                window.location.href = '/errors';
                break;
            case 'login':
                window.location.href = '/login';
                break;
            default:
                window.T4Logger.error(`Unknown view: ${viewName}`);
        }
    }
}

window.ViewFactory = ViewFactory;
