# google_chat/README.md
# Google Chat Integration Module

Este módulo permite enviar notificaciones de errores a Google Chat Spaces con soporte para hilos (threads).

## Características

- ✅ Envío de notificaciones de errores SQL y generales
- ✅ Organización por hilos para facilitar seguimiento
- ✅ Soporte para OAuth user mode y Service Account
- ✅ Manejo robusto de errores
- ✅ Integración transparente con el sistema existente (email, SMS, Slack)

## Configuración

### Variables de Entorno

Agregar al archivo `.env`:

```bash
# Habilitar/deshabilitar Google Chat
GCHAT_ENABLED=1

# Modo de autenticación: 'user' (OAuth) o 'app' (Service Account)
GCHAT_MODE=user

# Space ID donde se envían las alertas (obtener de chat.google.com)
GCHAT_SPACE_NAME=spaces/AAAAxxxxxxx

# Estrategia de organización por threads
# Opciones: per_app, per_error_type, per_date, none
GCHAT_THREAD_STRATEGY=per_app
```

### Autenticación - User Mode (Recomendado)

1. **Credenciales OAuth**: Asegurar que existe `credentials.json` en el directorio raíz
   - Descargado de Google Cloud Console
   - Proyecto: `woven-edge-477319-f6`
   - Cliente OAuth configurado para Desktop App

2. **Primera Ejecución**: Al ejecutar por primera vez:
   ```bash
   python test/test_gchat_integration.py
   ```
   - Se abrirá el navegador para autorizar con la cuenta de Google
   - Autorizar con **matias@t4app.com**
   - Se creará automáticamente `token.json` con las credenciales

3. **Ejecuciones Posteriores**: El módulo usa `token.json` y refresca automáticamente

### Crear un Space de Google Chat

1. Ir a [chat.google.com](https://chat.google.com/)
2. Click en ➕ junto a "Spaces"
3. **Create space**
4. **Space name**: `T4 Alerts` (o nombre deseado)
5. Agregar miembros:
   - `matias@t4app.com`
   - `ramon@t4app.com`
   - `geremy@t4app.com`
   - Otros miembros del equipo

6. **Obtener Space ID**:
   - Abrir el Space creado
   - Click en el nombre del Space (arriba)
   - Click en "⚙️ Settings"
   - Copiar el **Space ID** (formato: `spaces/AAAAxxxxxxx`)
   - Pegar en `.env` como `GCHAT_SPACE_NAME`

## Uso

### Desde app/notifier.py

El módulo se integra automáticamente. No requiere cambios en el código existente:

```python
from google_chat import enviar_gchat_errores_no_controlados, enviar_aviso_gchat

# Enviar errores no controlados (automático)
enviar_gchat_errores_no_controlados(resultado)

# Enviar avisos generales
enviar_aviso_gchat("⚠️ Mensaje de aviso")
```

### Estrategias de Threading

#### `per_app` (Recomendado)
- Un hilo por aplicación: `driverapp_goto`, `klc`, `broker_goto`, etc.
- Facilita seguimiento de errores por sistema
- Thread key: `app-{app_key}`

#### `per_error_type`
- Un hilo por tipo de error: SQL, timeout, 404, etc.
- Útil para análisis de patrones

#### `per_date`
- Un hilo por fecha de ejecución
- Histórico organizado cronológicamente

#### `none`
- Sin hilos, todos los mensajes en el Space principal
- Más simple pero menos organizado

## Estructura del Módulo

```
google_chat/
├── __init__.py           # Exporta funciones principales
├── auth.py              # Autenticación OAuth y Service Account
├── client.py            # Cliente de Google Chat API
├── config.py            # Gestión de configuración
├── errors.py            # Manejo de errores y excepciones
├── notifier.py          # Funciones de notificación
└── README.md            # Esta documentación
```

## Formato de Mensajes

### Errores No Controlados

```
🚨 **DriverApp GoTo** - Errores Detectados
📅 Fecha: `2026-02-03`
⚠️ Errores no controlados: **5**

**Errores SQL:**
• `SQLSTATE[HY000]: General error` (3x)
• `Duplicate entry for key 'PRIMARY'` (2x)

**Errores Generales:**
• `Timeout connecting to API` (1x)
```

### Avisos Generales

```
⚠️ **DriverApp GoTo** - Future date query `2026-02-05`
ℹ️ The content for date 2026-02-05 has not been created yet, please check back later.
```

## Troubleshooting

### Error: "Missing credentials.json"
- Descargar `credentials.json` de Google Cloud Console
- Colocar en el directorio raíz del proyecto

### Error: "PERMISSION_DENIED"
- Verificar que la cuenta autorizada tiene acceso al Space
- Agregar la cuenta como miembro del Space

### Error: "Invalid GCHAT_SPACE_NAME"
- Verificar formato: debe ser `spaces/AAAAxxxxxxx`
- Obtener ID correcto desde configuración del Space

### Mensajes no aparecen en threads
- Verificar `GCHAT_THREAD_STRATEGY` en `.env`
- Los threads se crean automáticamente al primer envío

## API Reference

### `enviar_gchat_errores_no_controlados(resultado: Dict) -> bool`

Envía notificación de errores no controlados al Space.

**Args:**
- `resultado`: Dict del resultado de `procesar_aplicacion()` con:
  - `app_name`: Nombre de la aplicación
  - `app_key`: Clave de la aplicación
  - `dia`: Fecha del reporte
  - `errores_sql`: Lista de errores SQL
  - `errores_generales`: Lista de errores generales

**Returns:**
- `True` si se envió la notificación
- `False` si no había errores o si Google Chat está deshabilitado

### `enviar_aviso_gchat(mensaje: str) -> bool`

Envía un mensaje de aviso general al Space.

**Args:**
- `mensaje`: Texto del mensaje (soporta markdown)

**Returns:**
- `True` si se envió el mensaje
- `False` si Google Chat está deshabilitado o hubo error

## Dependencias

Las siguientes dependencias ya están en `requirements.txt`:

```
google-apps-chat>=0.1.9
google-auth>=2.28.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
```

## Seguridad

- ⚠️ **NO** commitear `token.json` - ya está en `.gitignore`
- ⚠️ **NO** commitear `credentials.json` si contiene secretos
- Para producción, considerar usar Service Account mode (`GCHAT_MODE=app`)
