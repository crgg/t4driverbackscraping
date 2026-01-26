/**
 * T4Alerts Config Singleton
 * Manages configuration constants.
 */
class Config {
    constructor() {
        if (Config.instance) {
            return Config.instance;
        }
        Config.instance = this;

        // Dynamically construct API URL based on current window location
        // This ensures the frontend works regardless of the server's port/domain
        const protocol = window.location.protocol; // http: or https:
        const hostname = window.location.hostname; // e.g., t4alerts.local or 127.0.0.1
        const port = window.location.port;         // e.g., 8085 or empty string

        // Build base URL with port if it exists
        const baseUrl = port
            ? `${protocol}//${hostname}:${port}`
            : `${protocol}//${hostname}`;

        this.API_BASE_URL = `${baseUrl}/api`;
        this.endpoints = {
            login: `${this.API_BASE_URL}/auth/login`,
            menu: `${this.API_BASE_URL}/menu`,
            certificates: `${this.API_BASE_URL}/certificates`,
            errors: `${this.API_BASE_URL}/dashboard/errors`,
            stats_apps: `${this.API_BASE_URL}/stats/apps`,
            stats_apps_debug: `${this.API_BASE_URL}/stats/debug/apps`,
            stats_view: `${this.API_BASE_URL}/stats/view`,
            stats_send_email: `${this.API_BASE_URL}/stats/send-email`,
            error_history: `${this.API_BASE_URL}/error-history/`,
            error_history_scan: `${this.API_BASE_URL}/error-history/scan`,
            error_history: `${this.API_BASE_URL}/error-history/`,
            error_history_scan: `${this.API_BASE_URL}/error-history/scan`,
            apps: `${this.API_BASE_URL}/apps`,
            notifications_settings: `${this.API_BASE_URL}/notifications/settings`,
            notifications_send: `${this.API_BASE_URL}/notifications/send`
        };
    }

    getEndpoint(name) {
        return this.endpoints[name];
    }
}

const config = new Config();
window.T4Config = config;
