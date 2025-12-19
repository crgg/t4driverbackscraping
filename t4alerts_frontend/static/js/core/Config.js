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

        this.API_BASE_URL = "http://localhost:5001/api";
        this.endpoints = {
            login: `${this.API_BASE_URL}/auth/login`,
            menu: `${this.API_BASE_URL}/menu`,
            certificates: `${this.API_BASE_URL}/certificates/status`,
            errors: `${this.API_BASE_URL}/dashboard/errors`,
            stats_apps: `${this.API_BASE_URL}/stats/apps`,
            stats_apps_debug: `${this.API_BASE_URL}/stats/debug/apps`,
            stats_view: `${this.API_BASE_URL}/stats/view`
        };
    }

    getEndpoint(name) {
        return this.endpoints[name];
    }
}

const config = new Config();
window.T4Config = config;
