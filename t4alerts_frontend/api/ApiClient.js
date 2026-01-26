/**
 * API Client
 * Centralized HTTP client using axios with automatic token injection,
 * error handling, and logging
 * 
 * @requires axios (loaded via CDN)
 * @requires ApiLogger
 * @requires ApiConfig
 */
class ApiClientService {
    constructor() {
        if (ApiClientService.instance) {
            return ApiClientService.instance;
        }
        ApiClientService.instance = this;

        // Check if axios is available
        if (typeof axios === 'undefined') {
            throw new Error('Axios is not loaded. Please include axios CDN in your HTML.');
        }

        // Create axios instance
        this.client = axios.create({
            baseURL: ApiConfig.BACKEND_URL,
            timeout: ApiConfig.TIMEOUT,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Setup interceptors
        this._setupRequestInterceptor();
        this._setupResponseInterceptor();

        ApiLogger.logInfo('ApiClient initialized', {
            baseURL: ApiConfig.BACKEND_URL,
            timeout: ApiConfig.TIMEOUT
        });
    }

    /**
     * Setup request interceptor to inject JWT token
     */
    _setupRequestInterceptor() {
        this.client.interceptors.request.use(
            (config) => {
                // Store request start time for duration calculation
                config.metadata = { startTime: Date.now() };

                // Inject JWT token if available
                const token = localStorage.getItem('t4_access_token');
                if (token) {
                    config.headers['Authorization'] = `Bearer ${token}`;
                }

                // Log the request
                ApiLogger.logRequest(config.method.toUpperCase(), config.url, {
                    headers: config.headers,
                    data: config.data,
                    params: config.params
                });

                return config;
            },
            (error) => {
                ApiLogger.logError('REQUEST_INTERCEPTOR', 'Error in request interceptor', error);
                return Promise.reject(error);
            }
        );
    }

    /**
     * Setup response interceptor to handle errors
     */
    _setupResponseInterceptor() {
        this.client.interceptors.response.use(
            (response) => {
                // Calculate request duration
                const duration = Date.now() - response.config.metadata.startTime;

                // Log the response
                ApiLogger.logResponse(
                    response.config.method.toUpperCase(),
                    response.config.url,
                    response,
                    duration
                );

                return response;
            },
            (error) => {
                // Calculate request duration if possible
                const duration = error.config?.metadata?.startTime
                    ? Date.now() - error.config.metadata.startTime
                    : 0;

                // Log the error
                ApiLogger.logError(
                    error.config?.method?.toUpperCase() || 'UNKNOWN',
                    error.config?.url || 'UNKNOWN',
                    error,
                    duration
                );

                // Handle specific error cases
                if (error.response) {
                    const status = error.response.status;

                    // 401 Unauthorized or 422 Unprocessable Entity (invalid token)
                    if (status === 401 || status === 422) {
                        ApiLogger.logWarning('Session expired or invalid token. Redirecting to login...');

                        // Clear token
                        localStorage.removeItem('t4_access_token');

                        // Redirect to login (avoid infinite loop)
                        if (!window.location.pathname.includes('/login')) {
                            window.location.href = '/login';
                        }
                    }
                }

                return Promise.reject(error);
            }
        );
    }

    /**
     * GET request
     * @param {string} url - Endpoint URL
     * @param {object} config - Axios config
     * @returns {Promise} Response data
     */
    async get(url, config = {}) {
        try {
            const response = await this.client.get(url, config);
            return response.data;
        } catch (error) {
            this._handleError('GET', url, error);
            throw error;
        }
    }

    /**
     * POST request
     * @param {string} url - Endpoint URL
     * @param {object} data - Request body
     * @param {object} config - Axios config
     * @returns {Promise} Response data
     */
    async post(url, data = {}, config = {}) {
        try {
            const response = await this.client.post(url, data, config);
            return response.data;
        } catch (error) {
            this._handleError('POST', url, error);
            throw error;
        }
    }

    /**
     * PUT request
     * @param {string} url - Endpoint URL
     * @param {object} data - Request body
     * @param {object} config - Axios config
     * @returns {Promise} Response data
     */
    async put(url, data = {}, config = {}) {
        try {
            const response = await this.client.put(url, data, config);
            return response.data;
        } catch (error) {
            this._handleError('PUT', url, error);
            throw error;
        }
    }

    /**
     * DELETE request
     * @param {string} url - Endpoint URL
     * @param {object} config - Axios config
     * @returns {Promise} Response data
     */
    async delete(url, config = {}) {
        try {
            const response = await this.client.delete(url, config);
            return response.data;
        } catch (error) {
            this._handleError('DELETE', url, error);
            throw error;
        }
    }

    /**
     * PATCH request
     * @param {string} url - Endpoint URL
     * @param {object} data - Request body
     * @param {object} config - Axios config
     * @returns {Promise} Response data
     */
    async patch(url, data = {}, config = {}) {
        try {
            const response = await this.client.patch(url, data, config);
            return response.data;
        } catch (error) {
            this._handleError('PATCH', url, error);
            throw error;
        }
    }

    /**
     * Handle API errors
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Error} error - Error object
     */
    _handleError(method, url, error) {
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;
            ApiLogger.logWarning(
                `${method} ${url} failed with status ${status}`,
                data
            );
        } else if (error.request) {
            // Request was made but no response
            ApiLogger.logWarning(
                `${method} ${url} - No response from server`,
                { request: error.request }
            );
        } else {
            // Something else happened
            ApiLogger.logWarning(
                `${method} ${url} - Request setup error`,
                { message: error.message }
            );
        }
    }
}

// Export singleton - defer initialization to avoid race condition
(function () {
    // Wait for dependencies to be ready
    if (typeof ApiLogger === 'undefined') {
        console.error('⚠️ ApiLogger not loaded yet! Make sure ApiLogger.js is loaded before ApiClient.js');
        return;
    }

    if (typeof ApiConfig === 'undefined') {
        console.error('⚠️ ApiConfig not loaded yet! Make sure ApiConfig.js is loaded before ApiClient.js');
        return;
    }

    if (typeof axios === 'undefined') {
        console.error('⚠️ Axios not loaded yet! Make sure axios CDN is loaded before ApiClient.js');
        return;
    }

    const apiClient = new ApiClientService();
    window.ApiClient = apiClient;
})();
