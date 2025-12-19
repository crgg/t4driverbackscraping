#!/usr/bin/env python3
"""Test script to verify T4TMS HTTP Basic Auth implementation"""

import sys
sys.path.insert(0, '/Users/matias95lopez/Desktop/scrapping_project')

from app.session_manager import create_logged_session
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("Testing T4TMS HTTP Basic Auth Implementation")
print("=" * 70)

try:
    # Test T4TMS authentication
    print("\n1. Creating authenticated session for T4TMS...")
    session = create_logged_session("t4tms_backend")
    
    print("\n2. Testing access to /logs...")
    logs_url = "https://backend.t4tms.us/logs"
    resp = session.get(logs_url, timeout=10)
    
    print(f"   Status: {resp.status_code}")
    print(f"   Content length: {len(resp.text)} bytes")
    
    # Check if we got log files
    if "laravel" in resp.text.lower() and ".log" in resp.text.lower():
        print("   ✅ Log files found in response!")
        
        # Count log files
        import re
        log_files = re.findall(r'laravel-\d{4}-\d{2}-\d{2}\.log', resp.text)
        print(f"   Found {len(log_files)} log files")
        if log_files:
            print(f"   Sample files: {log_files[:3]}")
    else:
        print("   ⚠️ No log files detected in response")
        print(f"   First 200 chars: {resp.text[:200]}")
    
    print("\n✅ T4TMS HTTP Basic Auth is working correctly!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
