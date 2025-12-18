class RegistrationManager {
    constructor() {
        this.authService = new AuthService();
        this.form = document.getElementById('register-form');
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleRegister(e));
    }

    async handleRegister(e) {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;

        if (password !== confirmPassword) {
            this.showStatus("Passwords do not match!", "error");
            return;
        }

        try {
            await this.authService.register(email, password);
            this.showStatus("User Created! Redirecting...", "success");

            // Redirect after 2 seconds
            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, "error");
        }
    }

    showStatus(message, type) {
        const display = document.getElementById("status-message");
        display.innerText = message;
        display.className = type === "success" ? "bg-green-success" : "bg-red-error";
        display.style.display = "block";
    }
}

// Initialize
new RegistrationManager();
