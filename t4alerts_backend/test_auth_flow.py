import requests
import time

BASE_URL = "http://127.0.0.1:5001/api/auth"

def test_registration():
    print("Testing Registration...")
    payload = {
        "email": f"checkuser_{int(time.time())}@t4app.com",
        "password": "securepassword123",
        "role": "admin"
    }
    try:
        response = requests.post(f"{BASE_URL}/register", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return payload
    except Exception as e:
        print(f"Registration Failed: {e}")
        return None

def test_login(credentials):
    print("\nTesting Login...")
    if not credentials:
        print("Skipping login due to missing credentials.")
        return

    payload = {
        "email": credentials['email'],
        "password": credentials['password']
    }
    try:
        response = requests.post(f"{BASE_URL}/login", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200 and 'access_token' in response.json():
            print("✅ LOGIN SUCCESS: Token received.")
        else:
            print("❌ LOGIN FAILED.")
    except Exception as e:
        print(f"Login Failed: {e}")

if __name__ == "__main__":
    print("Ensure server is running on port 5001!")
    # We assume the server is running. If not, this script will fail connection.
    # In a real CI, we'd start the server in a subprocess.
    user_creds = test_registration()
    test_login(user_creds)
