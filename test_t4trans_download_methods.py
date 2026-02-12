#!/usr/bin/env python3
"""
Test different download methods for T4TRANS logs
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.session_manager import create_logged_session
import re

session = create_logged_session("t4trans")
print("✅ Autenticado\n")

# URLs to test
urls_to_test = [
    # Original URL (with HTML viewer)
    ("HTML Viewer", "https://core.t4trans.com/t4notification/logs/laravel-2026-02-11.log"),
    
    # Try with download parameter
    ("With ?download=1", "https://core.t4trans.com/t4notification/logs/laravel-2026-02-11.log?download=1"),
    
    # Try with download parameter alternative
    ("With ?dl=1", "https://core.t4trans.com/t4notification/logs/laravel-2026-02-11.log?dl=1"),
    
    # Try /download/ path
    ("With /download/", "https://core.t4trans.com/t4notification/logs/download/laravel-2026-02-11.log"),
]

for name, url in urls_to_test:
    try:
        resp = session.get(url, timeout=60, allow_redirects=True)
        content_type = resp.headers.get('Content-Type', '')
        content_disposition = resp.headers.get('Content-Disposition', '')
        
        print(f"{'='*60}")
        print(f"Test: {name}")
        print(f"URL: {url}")
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {content_type}")
        print(f"Content-Disposition: {content_disposition}")
        print(f"Size: {len(resp.content):,} bytes ({len(resp.content)/1024:.2f} KB)")
        
        # Check if it's HTML or raw text
        is_html = '<html' in resp.text[:1000].lower() or 'DOCTYPE' in resp.text[:1000]
        print(f"Format: {'HTML' if is_html else 'Plain text/Raw'}")
        
        # Check for truncation message
        if 'Showing last' in resp.text:
            print(f"⚠️ TRUNCATED (contains 'Showing last' message)")
        else:
            # Count timestamps
            timestamps = re.findall(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', resp.text)
            if timestamps:
                from datetime import datetime
                first_dt = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
                last_dt = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
                print(f"✅ {len(timestamps)} log entries")
                print(f"   Time range: {first_dt.strftime('%H:%M')} - {last_dt.strftime('%H:%M')}")
                    
    except Exception as e:
        print(f"Test: {name}")
        print(f"❌ Error: {e}")
    
    print()
