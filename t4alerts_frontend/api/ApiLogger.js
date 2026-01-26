/**
 * API Logger
 * Provides detailed logging for API requests and responses
 */
class ApiLoggerService {
    constructor(isDebugMode = true) {
        this.isDebugMode = isDebugMode;
        this.colors = {
            request: '#2196F3',  // Blue
            response: '#4CAF50', // Green
            error: '#F44336',    // Red
            warning: '#FF9800'   // Orange
        };
    }

    /**
     * Get current timestamp in readable format
     */
    getTimestamp() {
        const now = new Date();
        return now.toISOString().split('T')[1].split('.')[0]; // HH:MM:SS
    }

    /**
     * Log an API request
     */
    logRequest(method, url, config = {}) {
        if (!this.isDebugMode) return;

        const timestamp = this.getTimestamp();
        console.group(`%c[API] → ${method} ${url}`, `color: ${this.colors.request}; font-weight: bold`);
        console.log(`⏰ Time: ${timestamp}`);

        if (config.headers) {
            console.log('📋 Headers:', config.headers);
        }

        if (config.data) {
            console.log('📦 Body:', config.data);
        }

        if (config.params) {
            console.log('🔍 Query Params:', config.params);
        }

        console.groupEnd();
    }

    /**
     * Log an API response
     */
    logResponse(method, url, response, duration = 0) {
        if (!this.isDebugMode) return;

        const timestamp = this.getTimestamp();
        console.group(`%c[API] ← ${response.status} ${method} ${url}`, `color: ${this.colors.response}; font-weight: bold`);
        console.log(`⏰ Time: ${timestamp}`);
        console.log(`⚡ Duration: ${duration}ms`);
        console.log('📦 Data:', response.data);
        console.groupEnd();
    }

    /**
     * Log an API error
     */
    logError(method, url, error, duration = 0) {
        if (!this.isDebugMode) return;

        const timestamp = this.getTimestamp();
        const status = error.response ? error.response.status : 'Network Error';

        console.group(`%c[API] ✖ ${status} ${method} ${url}`, `color: ${this.colors.error}; font-weight: bold`);
        console.log(`⏰ Time: ${timestamp}`);
        console.log(`⚡ Duration: ${duration}ms`);

        if (error.response) {
            console.log('📋 Status:', error.response.status);
            console.log('📦 Response:', error.response.data);
        } else if (error.request) {
            console.log('📡 No response received');
            console.log('Request:', error.request);
        } else {
            console.log('⚠️ Error:', error.message);
        }

        console.groupEnd();
    }

    /**
     * Log a warning
     */
    logWarning(message, data = null) {
        if (!this.isDebugMode) return;

        const timestamp = this.getTimestamp();
        console.warn(`%c[API] ⚠️ ${message}`, `color: ${this.colors.warning}; font-weight: bold`);
        console.log(`⏰ Time: ${timestamp}`);

        if (data) {
            console.log('Data:', data);
        }
    }

    /**
     * Log an info message
     */
    logInfo(message, data = null) {
        if (!this.isDebugMode) return;

        const timestamp = this.getTimestamp();
        console.log(`%c[API] ℹ️ ${message}`, `color: ${this.colors.request}`);
        console.log(`⏰ Time: ${timestamp}`);

        if (data) {
            console.log('Data:', data);
        }
    }
}

// Export singleton instance immediately
(function () {
    const apiLogger = new ApiLoggerService(true);
    window.ApiLogger = apiLogger;
})();
