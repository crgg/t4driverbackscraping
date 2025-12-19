class LoginManager {
    constructor() {
        this.authService = new AuthService();
        this.form = document.getElementById('login-form');
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => this.handleLogin(e));
    }

    async handleLogin(e) {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        try {
            await this.authService.login(email, password);
            this.showStatus("SUCCESSFUL AUTHENTICATION", "success");

            // Redirect to the new menu
            window.location.href = "/menu";
        } catch (error) {
            this.showStatus("❌ FAILED AUTHENTICATION ❌", "error");
        }
    }

    showStatus(message, type) {
        const display = document.getElementById("status-message");
        display.innerText = message;

        // Remove existing classes
        display.classList.remove("bg-green-success", "bg-red-error");

        // Add new class
        if (type === "success") {
            display.classList.add("bg-green-success");
        } else {
            display.classList.add("bg-red-error");
        }

        display.style.display = "block";
    }
}

// Initialize
new LoginManager();
