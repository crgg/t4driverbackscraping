import requests
import sys
import json

BASE_URL = "http://localhost:8000/api"
EMAIL = "matiasdamianlopezg@gmail.com"
PASSWORD = "matias"

def run_test():
    print(f"🚀 Testing Authentication Flow on {BASE_URL}")
    
    # 1. Login
    print(f"\n1️⃣  Attempting Login with {EMAIL}...")
    try:
        login_payload = {"email": EMAIL, "password": PASSWORD}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ Login Failed: {response.text}")
            return False
            
        data = response.json()
        token = data.get('access_token')
        
        if not token:
            print("❌ No access_token received!")
            return False
            
        print("✅ Login Successful! Token received.")
        # Print first few chars of token for verification
        print(f"   Token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Exception during login: {e}")
        return False

    # 2. Access Admin Route
    print(f"\n2️⃣  Attempting to access Admin Users list...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json().get('users', [])
            print(f"✅ Success! Retrieved {len(users)} users.")
            for user in users:
                print(f"   - {user.get('email')} ({user.get('role')})")
            return True
        elif response.status_code == 422:
            print("❌ 422 Unprocessable Entity - Token might be malformed or header missing/wrong.")
            print(f"   Response: {response.text}")
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Token expired or invalid.")
            print(f"   Response: {response.text}")
        else:
            print(f"❌ Unexpected Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during admin access: {e}")
        return False

if __name__ == "__main__":
    if run_test():
        print("\n✨ Test PASSED: Full flow is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Test FAILED.")
        sys.exit(1)
