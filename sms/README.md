# 📱 Sistema de Notificaciones SMS con Twilio

## Descripción General

Este módulo implementa un sistema automatizado de notificaciones SMS que alerta sobre errores SQL críticos detectados en los logs de las aplicaciones monitoreadas. Cuando se ejecuta `main.py`, el sistema analiza los logs, identifica errores nuevos y envía alertas SMS a través de Twilio.

## 🔄 Flujo de Ejecución

### 1. Inicio desde `main.py`

Cuando ejecutas el script principal:

```bash
python main.py [FECHA-OPCIONAL]
```

El sistema inicia el siguiente flujo:

1. **Inicialización** (`main.py`)
   - Carga la configuración de aplicaciones
   - Inicializa la base de datos de alertas
   - Resuelve la fecha a procesar (hoy o fecha específica)

2. **Procesamiento de Logs** (`main.py` → `app/scrapper.py`)
   - Itera sobre cada aplicación configurada
   - Descarga y analiza los archivos de log
   - Clasifica errores en:
     - **Controlados**: Errores conocidos y esperados
     - **No Controlados**: Errores nuevos o inesperados

3. **Notificación** (`main.py` → `app/notifier.py`)
   - Envía resumen por correo electrónico
   - **Envía SMS si hay errores SQL no controlados**
   - Envía notificación a Slack

### 2. Detección de Errores SQL

El módulo `sms/sms_notifier.py` implementa la función `_contar_errores_sql()` que identifica errores SQL buscando palabras clave:

```python
keywords = ['sql', 'sqlstate', 'database', 'pdo']
```

**Solo se envían SMS cuando se detectan errores SQL**, no para todos los errores no controlados.

### 3. Generación del Mensaje SMS

El formato del mensaje es conciso y directo:

```
🚨 [Nombre App]: X SQL error(s)
Check logs immediately
```

Ejemplo:
```
🚨 DriveApp: 3 SQL errors
Check logs immediately
```

### 4. Envío a través de Twilio

**Archivo**: `sms/twilio_client.py`

El cliente Twilio maneja:
- Autenticación con credenciales del archivo `.env`
- Validación de configuración
- Reintentos automáticos (hasta 3 intentos)
- Manejo de rate limits (delay de 3 segundos entre mensajes)
- Logging detallado de errores

## 📋 Requisitos de Configuración

### Variables de Entorno (`.env`)

```bash
# Credenciales de Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+1XXXXXXXXXX  # Número Twilio (origen)
TWILIO_TO_NUMBER=+56XXXXXXXXX    # Número destino (tu teléfono)

# Control de activación
TWILIO_ENABLED=1  # 1 = activado, 0 = desactivado
```

### Obtener Credenciales de Twilio

1. Crea una cuenta en [Twilio](https://www.twilio.com/)
2. Ve a [Console Dashboard](https://console.twilio.com/)
3. Copia tu **Account SID** y **Auth Token**
4. Obtén un número de teléfono en [Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
5. **Importante para cuentas Trial**: Verifica el número destino en [Verified Caller IDs](https://console.twilio.com/us1/develop/phone-numbers/manage/verified)

## 🏗️ Arquitectura del Módulo

```
sms/
├── __init__.py                  # Exporta funciones principales
├── twilio_client.py            # Cliente Twilio (autenticación, envío)
├── sms_notifier.py             # Lógica de notificación y formateo
├── diagnosticar_twilio.py      # Script de diagnóstico
├── comparar_metodos_twilio.py  # Testing de métodos alternativos
└── README.md                   # Este archivo
```

### Componentes Principales

#### 1. `TwilioSMSClient` (`twilio_client.py`)

Clase que encapsula toda la interacción con la API de Twilio:

```python
cliente = TwilioSMSClient()
exito = cliente.enviar_sms("Tu mensaje aquí")
```

**Características**:
- Validación de credenciales al iniciar
- Lazy loading del cliente (solo se crea cuando se necesita)
- Reintentos con backoff exponencial (2s, 4s, 8s)
- Detección y reporte de errores específicos:
  - Número no verificado
  - Saldo insuficiente
  - Número inválido
  - Errores HTTP 404

#### 2. `enviar_sms_errores_no_controlados()` (`sms_notifier.py`)

Función principal llamada desde `app/notifier.py`:

```python
def enviar_sms_errores_no_controlados(resultado: Dict[str, Any]) -> bool:
    """
    1. Cuenta errores SQL en los errores no controlados
    2. Si hay errores SQL > 0:
       - Genera mensaje conciso
       - Envía SMS
       - Aplica delay de 3 segundos (rate limit)
    3. Retorna True si se envió exitosamente
    """
```

#### 3. `enviar_aviso_sms()` (`sms_notifier.py`)

Función genérica para enviar mensajes SMS personalizados:

```python
def enviar_aviso_sms(mensaje: str) -> bool:
    """Envía un SMS genérico sin validación de errores SQL"""
```

Usada para:
- Alertas de fecha futura
- Logs desactualizados (stale logs)
- Mensajes administrativos

## 🔍 Ejemplo de Flujo Completo

### Escenario: Error SQL Detectado en T4App

```
1. Ejecutas: python main.py 2026-02-01

2. main.py procesa T4App:
   ├─ Descarga logs del 2026-02-01
   ├─ Encuentra 5 errores nuevos:
   │  ├─ 3 errores SQL (SQLSTATE, PDOException, etc.)
   │  └─ 2 errores PHP normales
   └─ Llama a notificar_app(resultado)

3. app/notifier.py:
   ├─ Envía correo con resumen completo
   ├─ Llama a enviar_sms_errores_no_controlados()
   └─ Envía notificación a Slack

4. sms/sms_notifier.py:
   ├─ Cuenta: 3 errores SQL encontrados
   ├─ Genera mensaje: "🚨 T4App: 3 SQL errors\nCheck logs immediately"
   └─ Llama a twilio_client.enviar_sms()

5. sms/twilio_client.py:
   ├─ Valida credenciales ✓
   ├─ Inicializa cliente Twilio ✓
   ├─ Envía POST a API de Twilio
   ├─ Recibe confirmación (SID: SMxxxxxxxx)
   ├─ Log: "✅ SMS enviado exitosamente"
   └─ Espera 3 segundos (rate limit)

6. Resultado en consola:
   ✓ Correo enviado para T4App
   ✓ SMS enviado para T4App
   ✓ Notificación de Slack enviada para T4App
   📱 SMS enviados al número: +56XXXXXXXXX
```

## 🛠️ Diagnóstico y Testing

### Script de Diagnóstico

Para verificar que la configuración de Twilio es correcta:

```bash
python sms/diagnosticar_twilio.py
```

Este script:
1. Carga y verifica variables de entorno
2. Prueba la autenticación con Twilio
3. Intenta enviar un SMS de prueba
4. Reporta cualquier error encontrado

### Testing Manual

```python
from sms import enviar_aviso_sms

# Enviar un mensaje de prueba
exito = enviar_aviso_sms("🧪 Test de SMS desde Python")
print(f"Resultado: {'Éxito' if exito else 'Fallo'}")
```

## ⚡ Optimizaciones Implementadas

### 1. Cliente Singleton

Para evitar errores HTTP 404 causados por crear múltiples clientes rápidamente:

```python
_twilio_cliente_singleton = None

def _obtener_cliente_twilio():
    global _twilio_cliente_singleton
    if _twilio_cliente_singleton is None:
        _twilio_cliente_singleton = TwilioSMSClient()
    return _twilio_cliente_singleton
```

### 2. Fetch de Cuenta Obligatorio

Bug/quirk de la librería Twilio solucionado:

```python
# Antes de enviar mensaje, hacer fetch de cuenta
account = client.api.accounts(self.account_sid).fetch()
time.sleep(0.5)
# Ahora sí enviar mensaje
message = client.messages.create(...)
```

### 3. Rate Limiting

Respeto a límites de Twilio Trial (1 SMS/segundo):

```python
if exito:
    time.sleep(3)  # 3 segundos para mayor seguridad
```

### 4. Reintentos Inteligentes

Backoff exponencial para errores transitorios:

```python
for intento in range(1, 4):  # 3 intentos máximo
    try:
        # Intento de envío
    except Exception as e:
        delay = 2 ** intento  # 2s, 4s, 8s
        time.sleep(delay)
        self._client = None  # Reiniciar cliente
```

## 🚨 Manejo de Errores

### Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "Unable to create record" | Número no verificado en cuenta Trial | Verificar número en [Verified Caller IDs](https://console.twilio.com/us1/develop/phone-numbers/manage/verified) |
| "Insufficient balance" | Saldo agotado en cuenta Twilio | Recargar saldo o upgrade a plan de pago |
| "Not a valid phone number" | Formato de número incorrecto | Usar formato internacional: `+56XXXXXXXXX` |
| HTTP 404 | Cliente no inicializado correctamente | El sistema hace auto-retry (ya implementado) |
| "Credenciales faltantes" | Variables `.env` no configuradas | Revisar que todas las variables `TWILIO_*` estén definidas |

### Logging Detallado

El sistema registra cada paso:

```
✓ Cliente de Twilio inicializado correctamente
✓ Cliente Twilio inicializado: My Twilio Account
📤 Enviando SMS a +56XXXXXXXXX... (intento 1/3)
✅ SMS enviado exitosamente. SID: SMxxxxxxxx, Status: queued
✅ SMS enviado para T4App: 3 errores SQL detectados
```

## 📊 Filtrado de Errores SQL

### ¿Por qué solo errores SQL?

Los errores SQL suelen indicar problemas críticos:
- Fallos en migraciones de base de datos
- Consultas mal formadas (inyección SQL potencial)
- Conexiones perdidas con la BD
- Corrupción de datos

### Palabras Clave Detectadas

```python
SQL_KEYWORDS = ['sql', 'sqlstate', 'database', 'pdo']
```

Ejemplos de errores que disparan SMS:
- `SQLSTATE[HY000]: General error`
- `PDOException: Connection failed`
- `Database connection timeout`
- `SQL syntax error near 'SELECT'`

Ejemplos que NO disparan SMS:
- `Warning: Undefined array key`
- `Fatal error: Call to undefined function`
- `Exception: File not found`

## 🔐 Seguridad

### Mejores Prácticas

1. **Nunca commitear credenciales**: El archivo `.env` está en `.gitignore`
2. **Rotar tokens periódicamente**: Cambiar `TWILIO_AUTH_TOKEN` cada 6 meses
3. **Usar números verificados**: En producción, verifica todos los números destino
4. **Monitorear uso**: Revisar dashboard de Twilio para detectar uso anómalo
5. **Limitar rate**: Los 3 segundos de delay previenen spam accidental

## 📞 Soporte y Contacto

### Para Problemas con Twilio
- [Twilio Support](https://support.twilio.com/)
- [Twilio Console](https://console.twilio.com/)
- [Twilio Status](https://status.twilio.com/)

### Para Problemas con el Código
- Revisar logs en `logs/` del proyecto
- Ejecutar `diagnosticar_twilio.py`
- Verificar que todas las dependencias estén instaladas: `pip install -r requirements.txt`

## 📝 Notas Técnicas

### Limitaciones de Cuenta Trial

Las cuentas Trial de Twilio tienen restricciones:
- Solo pueden enviar SMS a números verificados
- Mensajes incluyen prefijo "Sent from your Twilio trial account"
- Límite de crédito: ~$15 USD
- Rate limit: 1 mensaje por segundo

Para producción, considera **upgrade a cuenta de pago**.

### Personalización de Mensajes

Para cambiar el formato del mensaje SMS, edita `sms/sms_notifier.py`:

```python
def _generar_mensaje_sms(resultado: Dict[str, Any]) -> str:
    # Tu formato personalizado aquí
    mensaje = f"Tu mensaje: {sql_count} errores"
    return mensaje
```

## 🔄 Integración con Otros Sistemas

El módulo SMS se integra con:

1. **Sistema de Email** (`app/email_notifier.py`)
   - Envío paralelo de correos con detalles completos
   - SMS complementa el email con alerta inmediata

2. **Slack** (`slack_comunication/`)
   - Notificaciones en canales de equipo
   - Formato Markdown enriquecido

3. **Base de Datos** (`db/`)
   - Registro de errores ya alertados
   - Prevención de alertas duplicadas

## 📚 Recursos Adicionales

- [Documentación oficial de Twilio Python](https://www.twilio.com/docs/libraries/python)
- [Twilio SMS Quickstart](https://www.twilio.com/docs/sms/quickstart/python)
- [Twilio Error Codes](https://www.twilio.com/docs/api/errors)
