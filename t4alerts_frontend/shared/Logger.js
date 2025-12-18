class T4Logger {
    static info(message) {
        console.log(`%c[INFO][${new Date().toLocaleTimeString()}]: ${message}`, "color: #2ecc71");
    }
    static error(message, err) {
        console.error(`%c[ERROR][${new Date().toLocaleTimeString()}]: ${message}`, "color: #e74c3c", err);
    }
}
