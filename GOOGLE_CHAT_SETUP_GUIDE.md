# Configuración de Google Chat App para Service Account

## 🚨 Problema con DMs y Service Account

**IMPORTANTE:** Con Service Account, NO puedes enviar DMs a usuarios directamente sin configurar primero un Chat App.

### Por qué falló:

Google Chat requiere que:
1. Configures tu Service Account como un **Chat App**
2. Los usuarios **agreguen el app** primero
3. Solo entonces el app puede enviarles mensajes

---

## ✅ SOLUCIÓN RECOMENDADA: Usar Spaces en lugar de DMs

En lugar de DMs 1-a-1, es **mucho más simple** crear un **Space dedicado** para alertas.

###Ventajas de Spaces vs DMs:
- ✅ No require que usuarios agreguen el app primero
- ✅ Todos los miembros ven las alertas
- ✅ Histórico centralizado
- ✅ Más fácil de configurar

---

## 🎯 Opción 1: Crear Space Manualmente (FÁCIL)

### Paso 1: Crear el Space en Google Chat

1. Ve a https://chat.google.com/
2. Click en ➕ (junto a "Spaces")
3. **Create space**
4. **Space name:** `T4 Alerts`
5. Agrega miembros:
   - matias@t4app.com (tú)
   - ramon@t4app.com
   - t4alerts-bot@big-cabinet-486219-e0.iam.gserviceaccount.com ← **IMPORTANTE: Agrega el bot!**

### Paso 2: Obtener el Space ID

1. En chat.google.com, abre el space "T4 Alerts"
2. Click en el nombre del space arriba
3. Click en "⚙️ Settings" o "Configuración"
4. Busca el **Space ID** - aparece como: `spaces/AAAAxxxxxxx`
5. **Cópialo**

### Paso 3: Configurar .env

```bash
# Cambiar de DM a Space mode
GCHAT_ENABLED=1
GCHAT_MODE=space                                    # ← CAMBIO AQUÍ
GOOGLE_APPLICATION_CREDENTIALS=/Users/administrator/Desktop/scrapping_project/service-account-key.json
GCHAT_SPACE_NAME=spaces/AAAAxxxxxxx                # ← PEGA EL SPACE ID
GCHAT_THREAD_KEY=t4-alerts                         # Opcional: organiza por thread
```

### Paso 4: Probar

```bash
python test_gchat_send.py
```

**Resultado esperado:**
- ✅ Mensaje enviado al space
- 👥 TODOS los miembros lo ven (matias, ramon, etc.)
- 🤖 Mensaje viene del bot

---

## 🔧 Opción 2: Configurar Chat App (AVANZADO)

Si realmente quieres DMs, necesitas configurar el Chat App:

### Paso A: Configurar Chat API

** URL:** https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat

1. **App name:** `T4 Alerts Bot`
2. **Avatar URL:** (opcional)
3. **Description:** `Bot de alertas para errores T4`
4. **Functionality:**
   - ✅ **Receive 1:1 messages  
   - ✅ **Join spaces and group conversations**
5. **Connection settings:**
   - **App URL:** (necesitas servidor web, complejo)
6. **OAuth scopes:** (las que ya tienes)
7. **Visibility:**
   - ⚪ **Make this Google Chat app available to**
   - Selecciona tu dominio t4app.com
8. **Save**

### Paso B: Publicar App

1. En la misma página, **Publish**
2. Los usuarios ahora pueden agregar el bot

### Paso C: Ramon debe agregar el bot

Ramon debe:
1. Abrir Google Chat
2. Buscar: `T4 Alerts Bot`
3. Click en "Message"
4. Ahora puede recibir DMs

---

## 📊 Comparación

| Método | Setup | Complejidad | Miembros | Recomendado |
|--------|-------|-------------|----------|-------------|
| **Space** | 5 min | Fácil | Múltiples ✅ | ✅ SÍ |
| **DM** | 30+ min | Difícil | Solo uno | ❌ NO |

---

## 🚀 MI RECOMENDACIÓN

**USA SPACE**, es mucho más simple y mejor para alertas:

```bash
# .env
GCHAT_MODE=space
GCHAT_SPACE_NAME=spaces/AAAAxxxxxxx   # Del space que crees
```

Beneficios adicionales:
- 📊 Histórico compartido de todas las alertas
- 👥 Fácil agregar más personas al equipo
- 🔍 Búsqueda centralizada
- 🧵 Threads para organizar por app

---

## ¿Qué prefieres?

1. **Space** (recomendado): Crea el space ahora en chat.google.com, obtén el ID, actualiza .env
2. **DM**: Configurar el Chat App completo (más complejo)

