from t4alerts_backend.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
