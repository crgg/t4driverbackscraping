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
