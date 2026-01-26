/**
 * API Configuration
 * Centralized configuration for API endpoints and settings
 */
class ApiConfigService {
    constructor() {
        if (ApiConfigService.instance) {
            return ApiConfigService.instance;
        }
        ApiConfigService.instance = this;

        // Determine backend URL
        // Priority:
        // 1. Use hardcoded backend URL for localhost development
        // 2. In production, use dynamic URL based on window.location
        this.BACKEND_URL = this._determineBackendUrl();
        this.TIMEOUT = 30000; // 30 seconds

        // API endpoints
        this.endpoints = {
            // Auth
            login: '/auth/login',
            register: '/auth/register',

            // Menu
            menu: '/menu',

            // Certificates
            certificates: '/certificates',

            // Dashboard/Errors
            errors: '/dashboard/errors',
            error_history: '/error-history/',
            error_history_scan: '/error-history/scan',

            // Stats
            stats_apps: '/stats/apps',
            stats_apps_debug: '/stats/debug/apps',
            stats_view: '/stats/view',
            stats_send_email: '/stats/send-email',

            // Admin
            admin_users: '/admin/users',
            admin_user_permissions: (userId) => `/admin/users/${userId}/permissions`,
            admin_user_details: (userId) => `/admin/users/${userId}`,
            admin_available_permissions: '/admin/permissions/available',

            // Apps
            apps: '/apps'
        };

        ApiLogger.logInfo('ApiConfig initialized', {
            backendUrl: this.BACKEND_URL,
            timeout: this.TIMEOUT
        });
    }

    /**
     * Determine the correct backend URL
     * @returns {string} Backend base URL
     */
    _determineBackendUrl() {
        const protocol = window.location.protocol;
        const hostname = window.location.hostname;
        const port = window.location.port;

        // Local development detection
        const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

        if (isLocalhost) {
            // For localhost, we need to check which port we're on
            // Port 8000 = frontend server with proxy → use relative /api
            // Port 80 or no port = direct access → use absolute backend URL

            if (port === '8000') {
                // Frontend server with proxy - use relative URL
                return '/api';
            } else {
                // Direct access or non-standard port - use hardcoded backend
                return 'http://127.0.0.1:5001/api';
            }
        }

        // Production: use dynamic URL based on current location
        const baseUrl = port
            ? `${protocol}//${hostname}:${port}`
            : `${protocol}//${hostname}`;

        return `${baseUrl}/api`;
    }

    /**
     * Get full URL for an endpoint
     * @param {string} endpointKey - Key from endpoints object
     * @param {object} params - Optional URL parameters
     * @returns {string} Full URL
     */
    getUrl(endpointKey, params = {}) {
        let endpoint = this.endpoints[endpointKey];

        // Handle function endpoints (like admin_user_permissions)
        if (typeof endpoint === 'function') {
            endpoint = endpoint(params);
        }

        if (!endpoint) {
            ApiLogger.logWarning(`Unknown endpoint: ${endpointKey}`);
            return this.BACKEND_URL;
        }

        return `${this.BACKEND_URL}${endpoint}`;
    }
}

// Export singleton - defer initialization to avoid race condition
(function () {
    // Wait for ApiLogger to be ready
    if (typeof ApiLogger === 'undefined') {
        console.error('⚠️ ApiLogger not loaded yet! Make sure ApiLogger.js is loaded before ApiConfig.js');
        return;
    }

    const apiConfig = new ApiConfigService();
    window.ApiConfig = apiConfig;
})();
