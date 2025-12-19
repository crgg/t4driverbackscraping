class _T4Logger {
    constructor() {
        if (_T4Logger.instance) return _T4Logger.instance;
        _T4Logger.instance = this;
    }

    log(message, type = "info") {
        const timestamp = new Date().toISOString();
        const style = type === "error" ? "color: red; font-weight: bold;" : "color: #2ecc71;";
        console.log(`%c[${timestamp}] [${type.toUpperCase()}]: ${message}`, style);
    }

    info(message) {
        this.log(message, "info");
    }

    error(message, error) {
        this.log(message, "error");
        if (error) console.error(error);
    }

    warn(message) {
        this.log(message, "warn");
    }
}
const logger = new _T4Logger();
Object.freeze(logger);

// Attach to window object for global access (required for non-module scripts)
window.T4Logger = logger;

// Conditional export for compatibility with ES modules if used elsewhere
// Conditional exports removed to avoid syntax errors with reserved keywords in non-module scripts.
// The primary access method for this legacy setup is window.T4Logger.

// For module systems (Node/Bundlers), we use module.exports or exports
if (typeof module !== 'undefined' && module.exports) {
    module.exports = logger;
}
