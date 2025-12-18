class AuthService {
    constructor() {
        // Points to local backend
        this.apiEndpoint = "http://127.0.0.1:5001/api/auth";
    }

    async register(email, password) {
        try {
            T4Logger.info(`Registering user: ${email}`);
            const response = await fetch(`${this.apiEndpoint}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password, role: "user" })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.msg || "Registration failed");
            }

            T4Logger.info("Registration successful");
            return data;
        } catch (error) {
            T4Logger.error("Registration error", error);
            throw error;
        }
    }

    async login(email, password) {
        try {
            T4Logger.info(`Attempting login for: ${email}`);
            const response = await fetch(`${this.apiEndpoint}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.msg || "Login failed");
            }

            // Save token
            if (data.access_token) {
                localStorage.setItem("t4_access_token", data.access_token);
            }

            T4Logger.info("Login successful");
            return data;
        } catch (error) {
            T4Logger.error("Login error", error);
            throw error;
        }
    }
}
