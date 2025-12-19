/**
 * T4Alerts Logger Singleton
 * Centralizes logging with levels and optional silent mode for production.
 */
class T4Logger {
    constructor() {
        if (T4Logger.instance) {
            return T4Logger.instance;
        }
        T4Logger.instance = this;
        this.debugMode = true; // Set to false in production
    }

    log(message, ...args) {
        if (this.debugMode) console.log(`[LOG] ${message}`, ...args);
    }

    info(message, ...args) {
        if (this.debugMode) console.info(`%c[INFO] ${message}`, 'color: blue', ...args);
    }

    warn(message, ...args) {
        console.warn(`[WARN] ${message}`, ...args);
    }

    error(message, ...args) {
        console.error(`[ERROR] ${message}`, ...args);
    }
}

// Export singleton instance
const logger = new T4Logger();
window.T4Logger = logger; // Global access
