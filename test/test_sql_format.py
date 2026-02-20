#!/usr/bin/env python3
# test_sql_format.py
"""
Script de prueba para verificar el formato de mensajes SQL
"""

import sys
sys.path.insert(0, '/Users/administrator/Desktop/scrapping_project')

from mailer.builder import _formatear_mensaje_sql

# Casos de prueba con ejemplos reales del usuario
test_cases = [
    # Caso 1: SQL0911N - deadlock
    'SQLSTATE[40001]: Serialization failure: -911 [IBM][CLI Driver][DB2/NT64] SQL0911N The current transaction has been rolled back because of a deadlock or timeout. Reason code "68". SQLSTATE=40001',
    
    # Caso 2: SQL30081N - communication error
    'SQLSTATE[08001] SQLConnect: -30081 [IBM][CLI Driver] SQL30081N A communication error has been detected. Communication protocol being used: "TCP/IP". SQLSTATE=08001',
    
    # Caso 3: SQL0803N - unique violation
    'SQLSTATE[23505]: Unique violation: -803 [IBM][CLI Driver][DB2/NT64] SQL0803N One or more values in the INSERT statement, UPDATE statement, or foreign key update caused by a DELETE statement are not valid because the primary key, unique constraint or unique index identified by "1" constrains table. SQLSTATE=23505',
    
    # Caso 4: Mensaje sin SQL (no debe cambiar)
    'Allowed memory size of 134217728 bytes exhausted (tried to allocate 12288 bytes)',
]

print("=" * 80)
print("PRUEBA DE FORMATO SQL")
print("=" * 80)

for i, test in enumerate(test_cases, 1):
    print(f"\n📝 Caso {i}:")
    print(f"Original ({len(test)} chars):")
    print(test[:100] + "..." if len(test) > 100 else test)
    print()
    
    resultado = _formatear_mensaje_sql(test)
    print(f"Formateado ({len(resultado)} chars):")
    print(resultado)
    
    # Verificar si se aplicó formato
    tiene_formato = '<strong style="color: red;">' in resultado
    print(f"\n✅ Formato aplicado: {tiene_formato}")
    print("-" * 80)

print("\n🎉 Prueba completada!")
print("\nNota: Los mensajes SQL deberían mostrar <strong style=\"color: red;\">MENSAJE</strong>")
print("      entre el código SQL####N y SQLSTATE")
