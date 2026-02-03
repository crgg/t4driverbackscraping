#!/usr/bin/env python3
# test/test_gchat_notifier.py
"""
Test script for Google Chat notifier functions
Tests error notification formatting and sending
"""

import sys
import os
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_chat.notifier import enviar_gchat_errores_no_controlados, enviar_aviso_gchat


def test_error_notification():
    """Test error notification with mock data"""
    print("=" * 70)
    print("TEST: Error Notification")
    print("=" * 70)
    
    # Mock resultado structure (same as procesar_aplicacion output)
    resultado_mock = {
        "dia": date.today().isoformat(),
        "app_name": "DriverApp GoTo [TEST]",
        "app_key": "driverapp_goto",
        "errores_sql": [
            {
                "err_hash": "abc123def456",
                "error": "SQLSTATE[HY000]: General error: 1366 Incorrect integer value: '' for column 'id'",
                "archivo": "app/Http/Controllers/TestController.php",
                "linea": 45,
                "conteo": 3,
                "es_nuevo": True,
                "controlado": False,
                "sql_query": "INSERT INTO test VALUES (?, ?, ?)"
            },
            {
                "err_hash": "xyz789abc123",
                "error": "SQLSTATE[23000]: Integrity constraint violation: 1062 Duplicate entry 'test' for key 'PRIMARY'",
                "archivo": "app/Models/User.php",
                "linea": 128,
                "conteo": 2,
                "es_nuevo": False,
                "controlado": False,
                "sql_query": "INSERT INTO users (name, email) VALUES (?, ?)"
            }
        ],
        "errores_generales": [
            {
                "err_hash": "http404xyz",
                "error": "GuzzleHttp\\Exception\\ClientException: Client error: `GET https://api.example.com/data` resulted in a `404 Not Found` response",
                "archivo": "app/Services/ApiService.php",
                "linea": 67,
                "conteo": 1,
                "es_nuevo": True,
                "controlado": False
            }
        ]
    }
    
    print(f"Sending test error notification...")
    print(f"App: {resultado_mock['app_name']}")
    print(f"Date: {resultado_mock['dia']}")
    print(f"SQL Errors: {len(resultado_mock['errores_sql'])}")
    print(f"General Errors: {len(resultado_mock['errores_generales'])}")
    
    try:
        enviado = enviar_gchat_errores_no_controlados(resultado_mock)
        
        if enviado:
            print(f"\n✓ Error notification sent successfully!")
            print(f"  Check Google Chat Space -> Thread 'app-driverapp_goto'")
            return True
        else:
            print(f"\n⚠️ Notification not sent (Google Chat may be disabled or no errors)")
            return False
            
    except Exception as e:
        print(f"\n✗ Error sending notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_warning_notification():
    """Test general warning notification"""
    print("\n" + "=" * 70)
    print("TEST: Warning Notification")
    print("=" * 70)
    
    mensaje = (
        "⚠️ **TEST WARNING** - Future Date Query\n"
        "📅 Date: `2026-02-10`\n"
        "ℹ️ The content for this date has not been created yet, please check back later."
    )
    
    print(f"Sending test warning...")
    
    try:
        enviado = enviar_aviso_gchat(mensaje)
        
        if enviado:
            print(f"\n✓ Warning notification sent successfully!")
            print(f"  Check Google Chat Space -> Thread 'avisos'")
            return True
        else:
            print(f"\n⚠️ Notification not sent (Google Chat may be disabled)")
            return False
            
    except Exception as e:
        print(f"\n✗ Error sending notification: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_errors():
    """Test notification when there are no errors (should not send)"""
    print("\n" + "=" * 70)
    print("TEST: No Errors (Should Not Send)")
    print("=" * 70)
    
    resultado_sin_errores = {
        "dia": date.today().isoformat(),
        "app_name": "Test App [NO ERRORS]",
        "app_key": "test_app",
        "errores_sql": [],
        "errores_generales": []
    }
    
    try:
        enviado = enviar_gchat_errores_no_controlados(resultado_sin_errores)
        
        if not enviado:
            print(f"✓ Correctly skipped sending (no errors)")
            return True
        else:
            print(f"✗ Unexpected: notification was sent despite no errors")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all notifier tests"""
    print("\n🧪 Google Chat Notifier Test Suite")
    print("=" * 70)
    
    results = []
    
    # Test 1: Error notification
    results.append(("Error Notification", test_error_notification()))
    
    # Test 2: Warning notification
    results.append(("Warning Notification", test_warning_notification()))
    
    # Test 3: No errors
    results.append(("No Errors", test_no_errors()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nGoogle Chat integration is working correctly!")
        print("\nNext step: Run main.py to test full integration:")
        print("  python main.py")
    else:
        print("⚠️ SOME TESTS HAD ISSUES")
        print("=" * 70)
        print("\nCheck the output above for details.")


if __name__ == "__main__":
    main()
