class AuthService {
    constructor() {
        // No need to construct API URL anymore - ApiClient handles it
        this.apiBasePath = '/auth';
    }

    async register(email, password) {
        try {
            ApiLogger.logInfo(`Registering user: ${email}`);

            const data = await ApiClient.post(`${this.apiBasePath}/register`, {
                email,
                password,
                role: "user"
            });

            ApiLogger.logInfo("Registration successful");
            return data;

        } catch (error) {
            ApiLogger.logError("Registration error", this.apiBasePath, error);

            // Extract user-friendly error message
            const errorMessage = error.response?.data?.msg || "Registration failed";
            throw new Error(errorMessage);
        }
    }

    async login(email, password) {
        try {
            ApiLogger.logInfo(`Attempting login for: ${email}`);

            const data = await ApiClient.post(`${this.apiBasePath}/login`, {
                email,
                password
            });

            // Save token
            if (data.access_token) {
                localStorage.setItem("t4_access_token", data.access_token);
                ApiLogger.logInfo("JWT token saved to localStorage");
            }

            ApiLogger.logInfo("Login successful");
            return data;

        } catch (error) {
            ApiLogger.logError("Login error", this.apiBasePath, error);

            // Detailed debug logging
            if (error.response) {
                console.error('❌ Login Failed - Server Response:', error.response.status, error.response.data);
            } else {
                console.error('❌ Login Failed - Network/Client Error:', error.message);
            }

            // Extract user-friendly error message
            const errorMessage = error.response?.data?.msg || "Login failed";
            throw new Error(errorMessage);
        }
    }
}
