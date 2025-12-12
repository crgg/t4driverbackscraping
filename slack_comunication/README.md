# Guía de Configuración de Slack

Esta guía te ayudará a configurar las notificaciones de Slack para el proyecto de scraping.

## 📋 Requisitos Previos

1. Tener acceso de administrador a un workspace de Slack
2. Python 3.7 o superior
3. Tener instaladas las dependencias del proyecto

## 🔧 Paso 1: Crear una Slack App

1. Ve a https://api.slack.com/apps
2. Haz clic en **"Create New App"**
3. Selecciona **"From scratch"**
4. Ingresa:
   - **App Name**: "Monitor de Errores" (o el nombre que prefieras)
   - **Workspace**: Selecciona tu workspace
5. Haz clic en **"Create App"**

## 🔑 Paso 2: Configurar Permisos (OAuth Scopes)

1. En el menú lateral, ve a **"OAuth & Permissions"**
2. Baja hasta la sección **"Scopes"** → **"Bot Token Scopes"**
3. Agrega los siguientes permisos:
   - `chat:write` - Enviar mensajes como el bot
   - `chat:write.public` - Enviar mensajes a canales públicos sin unirse
   - `channels:read` - Ver información de canales públicos

## 🚀 Paso 3: Instalar la App en tu Workspace

1. Sube en la misma página de **"OAuth & Permissions"**
2. Haz clic en **"Install to Workspace"**
3. Revisa los permisos y haz clic en **"Allow"**
4. Copia el **"Bot User OAuth Token"** que empieza con `xoxb-`

## 📝 Paso 4: Configurar Variables de Entorno

Agrega las siguientes variables a tu archivo `.env`:

```bash
# ========== SLACK CONFIGURATION ==========
# Bot Token (empieza con xoxb-)
SLACK_BOT_TOKEN=xoxb-tu-token-aqui

# Canal donde se enviarán las notificaciones
SLACK_CHANNEL=#errores-criticos

# Habilitar notificaciones de Slack (1 = activado, 0 = desactivado)
SLACK_ENABLED=1
```

### Valores requeridos:

- **SLACK_BOT_TOKEN**: El token que copiaste en el paso anterior
- **SLACK_CHANNEL**: El nombre del canal (puede ser `#nombre-canal` o solo `nombre-canal`)
- **SLACK_ENABLED**: `1` para activar, `0` para desactivar

## 🔄 Paso 5: Instalar Dependencias

```bash
# Instalar todas las dependencias (incluye slack-sdk)
pip install -r requirements.txt

# O solo instalar slack-sdk
pip install slack-sdk>=3.0.0
```

## 🧪 Paso 6: Probar la Integración

Ejecuta el script de prueba:

```bash
python test_slack_integration.py
```

Este script:
1. ✓ Verifica que las variables de entorno estén configuradas
2. ✓ Prueba la conexión con Slack
3. ✓ Envía un mensaje de prueba
4. ✓ Simula una notificación de error

## 🎯 Paso 7: Ejecutar el Proyecto

Ahora puedes ejecutar el proyecto normalmente:

```bash
python main.py
```

Cuando se detecten errores NO controlados, recibirás:
- 📧 Email con el resumen completo
- 📱 SMS con alertas críticas
- 💬 **Notificación de Slack con formato enriquecido**

---

## 🔀 Método Alternativo: Webhooks (Opcional)

Si prefieres usar Webhooks en lugar del Bot Token:

### 1. Crear Incoming Webhook

1. Ve a https://api.slack.com/apps
2. Selecciona tu app
3. En el menú lateral, **"Incoming Webhooks"**
4. Activa **"Activate Incoming Webhooks"**
5. Haz clic en **"Add New Webhook to Workspace"**
6. Selecciona el canal y autoriza
7. Copia la **Webhook URL**

### 2. Configurar en .env

```bash
# Usar webhook en lugar de bot token
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
SLACK_ENABLED=1
```

**Nota**: El webhook es más simple pero menos flexible. El Bot Token permite más funcionalidades.

---

## 🎨 Formato de Mensajes

Los mensajes de Slack incluyen:

```
🚨 Errores NO Controlados Detectados
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aplicación:     [Nombre de la App]
Fecha:          2025-12-12
Total Errores:  5
App Key:        app_key

📊 Categorización:
• Errores SQL: 2
• Otros errores: 3

🔍 Muestra de errores:
1. ERROR: SQL Error - Connection timeout...
2. ERROR: NullPointerException in...
3. ERROR: Failed to load resource...

⚠️ Acción requerida: Revisar logs urgentemente
```

---

## 🐛 Solución de Problemas

### Error: "No se configuró SLACK_BOT_TOKEN"
- Verifica que el token esté en el archivo `.env`
- Asegúrate de que el token empiece con `xoxb-`

### Error: "channel_not_found"
- El bot debe tener acceso al canal
- Invita al bot al canal con `/invite @NombreDelBot`
- O usa el permiso `chat:write.public` para escribir sin unirse

### Error: "not_authed" o "invalid_auth"
- El token es inválido o expiró
- Reinstala la app en el workspace
- Genera un nuevo token

### Error: "Import error: No module named 'slack_sdk'"
- Ejecuta: `pip install slack-sdk>=3.0.0`

---

## ✅ Checklist de Configuración

- [ ] Crear Slack App
- [ ] Agregar permisos (chat:write, chat:write.public, channels:read)
- [ ] Instalar app en workspace
- [ ] Copiar Bot Token
- [ ] Configurar variables en .env
- [ ] Instalar dependencia slack-sdk
- [ ] Ejecutar test_slack_integration.py
- [ ] Verificar mensajes en canal de Slack
- [ ] Ejecutar main.py y verificar notificaciones

---

## 📚 Recursos Adicionales

- [Documentación oficial de Slack API](https://api.slack.com/)
- [Block Kit Builder](https://app.slack.com/block-kit-builder/) - Para personalizar mensajes
- [slack-sdk Python Docs](https://slack.dev/python-slack-sdk/)
