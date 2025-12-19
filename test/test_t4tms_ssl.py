import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
from dotenv import load_dotenv

load_dotenv()

# Test T4TMS connection with different configurations
base_url = "https://backend.t4tms.us"
login_url = f"{base_url}/login"

print("=" * 70)
print("Test 1: Basic requests.get (without adapters)")
print("=" * 70)
try:
    r = requests.get(login_url, timeout=10)
    print(f"✓ Status: {r.status_code}")
    print(f"✓ Content length: {len(r.text)} bytes")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("Test 2: With session (no adapters)")
print("=" * 70)
try:
    session = requests.Session()
    r = session.get(login_url, timeout=10)
    print(f"✓ Status: {r.status_code}")
    print(f"✓ Content length: {len(r.text)} bytes")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("Test 3: With HTTPAdapter and Retry (current configuration)")
print("=" * 70)
try:
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    r = session.get(login_url, timeout=10)
    print(f"✓ Status: {r.status_code}")
    print(f"✓ Content length: {len(r.text)} bytes")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("Test 4: Test full login flow")
print("=" * 70)
try:
    username = os.getenv("T4TMS_BACKEND_USER")
    password = os.getenv("T4TMS_BACKEND_PASSWORD")
    
    if not username or not password:
        print("⚠️ Missing credentials in .env file")
    else:
        session = requests.Session()
        
        # Get login page
        resp = session.get(login_url, timeout=10)
        print(f"✓ GET login Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, "html.parser")
        token_input = soup.find("input", {"name": "_token"})
        csrf_token = token_input["value"] if token_input else ""
        print(f"✓ CSRF token extracted: {csrf_token[:20]}...")
        
        # Detect field name
        field_name = "identity"  # default
        if soup.find("input", {"name": "email"}):
            field_name = "email"
        elif soup.find("input", {"name": "identity"}):
            field_name = "identity"
        elif soup.find("input", {"name": "username"}):
            field_name = "username"
        
        print(f"✓ Login field detected: {field_name}")
        
        # Login
        payload = {
            field_name: username,
            "password": password,
        }
        if csrf_token:
            payload["_token"] = csrf_token
        
        headers = {
            "Referer": login_url,
            "User-Agent": "Mozilla/5.0"
        }
        
        resp = session.post(login_url, data=payload, headers=headers, allow_redirects=True, timeout=10)
        print(f"✓ POST login Status: {resp.status_code}")
        print(f"✓ Final URL: {resp.url}")
        print(f"✓ Login successful!" if "password" not in resp.text.lower() else "⚠️ Login may have failed")
        
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
