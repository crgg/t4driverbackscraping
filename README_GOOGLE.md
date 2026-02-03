# Google Chat API Project

Proyecto de interfaz CLI para interactuar con Google Chat API, permitiendo gestión de mensajes directos (DM), espacios de trabajo y gestión de incidentes.

## 📋 Índice

- [Descripción General](#descripción-general)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Flujo de Ejecución desde main.py](#flujo-de-ejecución-desde-mainpy)
- [Librerías Involucradas](#librerías-involucradas-en-orden-de-ejecución)
- [Comandos Disponibles](#comandos-disponibles)
- [Estructura de Base de Datos](#estructura-de-base-de-datos)

---

## 🎯 Descripción General

Este proyecto proporciona una interfaz de línea de comandos (CLI) para:
- **Mensajes Directos (DM)**: Envío y recepción de mensajes 1:1 con otros usuarios
- **Gestión de Incidentes**: Crear espacios de incidentes con hilos organizados (timeline y actions)
- **Chat Interactivo (REPL)**: Consola interactiva para conversaciones en tiempo real
- **Persistencia**: Almacenamiento de mensajes y espacios en base de datos SQLite/PostgreSQL

---

## 📦 Requisitos

### Librerías Python (requirements.txt)

```
Flask
google-apps-chat
google-auth
google-auth-oauthlib
google-auth-httplib2
SQLAlchemy
psycopg2-binary
python-dotenv
```

### Archivos de Autenticación

- `credentials.json`: Credenciales OAuth2 de Google Cloud Console
- `token.json`: Token de acceso generado automáticamente (modo usuario)
- `GOOGLE_APPLICATION_CREDENTIALS`: Variable de entorno para Service Account (modo app)

---

## 🚀 Instalación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales de Google Cloud
# 1. Descargar credentials.json desde Google Cloud Console
# 2. Colocar en el directorio raíz del proyecto

# Ejemplo de uso
python main.py dm --mode user --user-ref users/usuario@dominio.com --db-url sqlite:///chat.db --repl
```

---

## 🏗️ Arquitectura del Proyecto

```
google_chat_api_project/
├── main.py                    # Punto de entrada CLI
├── app/
│   ├── core/
│   │   ├── auth.py           # Autenticación OAuth2 y Service Account
│   │   └── logging.py        # Configuración de logging
│   ├── gchat/
│   │   └── client.py         # Cliente de Google Chat API
│   ├── db/
│   │   ├── models.py         # Modelos SQLAlchemy (ChatSpace, ChatMessage)
│   │   └── repository.py    # Repositorio de mensajes
│   ├── repo/
│   │   ├── base.py          # Configuración base SQLAlchemy
│   │   └── incident_repo.py # Repositorio de incidentes
│   ├── services/
│   │   ├── chat_service.py      # Lógica de negocio para chat
│   │   └── incident_services.py # Lógica de negocio para incidentes
│   └── errors/
│       └── gchat_errors.py   # Manejo de errores personalizado
├── credentials.json           # Credenciales OAuth2
├── token.json                # Token de acceso (generado)
└── chat.db                   # Base de datos SQLite
```

---

## 🔄 Flujo de Ejecución desde main.py

### 1️⃣ **Inicialización (main.py)**

#### Librerías importadas:
- `argparse` - Parseo de argumentos CLI
- `os` - Operaciones del sistema operativo
- `app.core.logging.setup_logger` - Configuración de logging

```python
# Orden de carga de módulos:
1. argparse (stdlib)
2. os (stdlib)
3. app.core.auth.ChatAuthConfig
4. app.gchat.client.GoogleChatClient
5. app.db.repository.MessageRepository
6. app.services.chat_service.ChatService
7. app.repo.incident_repo.IncidentRepository
8. app.services.incident_services.IncidentService
9. app.errors.GChatErrorHandler
```

**Proceso:**
1. Parsea argumentos con `argparse.ArgumentParser()`
2. Carga el logger con `setup_logger()`
3. Inicializa `GChatErrorHandler` para manejo de errores

---

### 2️⃣ **Autenticación (app/core/auth.py)**

#### Librerías clave:
- `google_auth_oauthlib.flow.InstalledAppFlow` - Flujo OAuth2
- `google.auth.transport.requests.Request` - Refresh de tokens
- `google.oauth2.credentials.Credentials` - Credenciales de usuario
- `google.oauth2.service_account.Credentials` - Service Account

**Proceso de autenticación:**

```
ChatAuthConfig(mode="user") → build_credentials()
├── Lee token.json (si existe)
├── Valida credenciales con creds.valid
├── Si hay error → Ejecuta OAuth2 flow (abre navegador)
│   └── InstalledAppFlow.from_client_secrets_file()
│       └── flow.run_local_server(port=0)
└── Guarda token.json actualizado
```

**Scopes utilizados:**
- Usuario: `chat.spaces`, `chat.spaces.create`, `chat.messages.create`, `chat.messages.readonly`
- App: `chat.bot`

---

### 3️⃣ **Cliente Google Chat (app/gchat/client.py)**

#### Librerías clave:
- `google.apps.chat_v1.ChatServiceClient` - Cliente principal de Chat API
- `google.apps.chat_v1.types` - Tipos de datos (Message, Space, etc.)

**Flujo de inicialización:**

```
GoogleChatClient(cfg) → __init__()
├── build_credentials(cfg) → (creds, client_options)
└── ChatServiceClient(credentials=creds, client_options=client_options)
```

**Métodos principales:**
- `list_spaces()` - Lista espacios disponibles
- `find_or_create_dm_with()` - Crea/obtiene DM
- `send_text()` - Envía mensaje
- `list_messages()` - Lista mensajes de un espacio
- `set_up_space()` - Crea espacio de trabajo con miembros
- `add_member()` - Agrega miembro a espacio

**Decorador:** `@gchat_error_boundary` - Captura errores de API y los convierte en `ChatAPIError`

---

### 4️⃣ **Repositorios de Base de Datos**

#### app/db/repository.py (Mensajes)

**Librerías:**
- `sqlalchemy` - ORM para base de datos
- `sqlalchemy.orm.sessionmaker` - Gestión de sesiones

**Flujo:**
```
MessageRepository(dsn) → __init__()
├── create_engine(dsn) → SQLAlchemy engine
├── Base.metadata.create_all() → Crea tablas
└── sessionmaker(bind=engine) → Factory de sesiones
```

**Métodos:**
- `upsert_space()` - Inserta/actualiza espacio
- `record_message()` - Registra mensaje en BD

#### app/repo/incident_repo.py (Incidentes)

**Modelos:**
- `Incident` - Tabla de incidentes con campos: space_name, title, sev, system, status, timeline_thread_key, actions_thread_key

**Métodos:**
- `create_incident()` - Crea registro de incidente
- `update_incident_status()` - Actualiza estado (Open → Resolved)

---

### 5️⃣ **Servicios de Lógica de Negocio**

#### app/services/chat_service.py

**Librerías adicionales:**
- `threading` - Manejo de hilos para REPL
- `datetime` - Gestión de timestamps
- `google.api_core.datetime_helpers.to_rfc3339` - Conversión RFC3339

**Flujo de servicio DM:**
```
ChatService(chat_client, repo) → ensure_dm_and_send()
├── _maybe_extract_email_from_user_ref() → Extrae email
├── handler.validate_email_or_raise() → Valida formato
├── chat.find_or_create_dm_with() → API: Crea/obtiene DM
├── chat.send_text() → API: Envía mensaje
└── repo.record_message() → BD: Persiste mensaje
```

**REPL (Read-Eval-Print Loop):**
```
chat_loop()
├── Thread 1 (receiver): follow_dm() polling
│   └── chat.list_messages() cada poll_interval
└── Thread 2 (main): stdin loop
    └── Envía mensajes escritos por usuario
```

#### app/services/incident_services.py

**Flujo de creación de incidente:**
```
IncidentService.create_incident_space()
├── 1. Genera display_name: "INC-{timestamp} {sev} {system}"
├── 2. _validate_member_emails() → Valida correos
├── 3. chat.set_up_space() → API: Crea espacio
├── 4. _safe_send_text() → API: Envía header
├── 5. _safe_send_text(thread_key="timeline") → Crea hilo timeline
├── 6. _safe_send_text(thread_key="actions") → Crea hilo actions
└── 7. repo.create_incident() → BD: Persiste incidente
```

---

### 6️⃣ **Manejo de Errores (app/errors/gchat_errors.py)**

**Jerarquía de excepciones:**
- `ChatAPIError` - Base para errores de API
- `InvalidEmailError` - Email inválido
- `NotFoundError` - Recurso no encontrado
- `PermissionDeniedError` - Permisos insuficientes
- `RateLimitError` - Límite de tasa excedido

**Funciones:**
- `gchat_error_boundary` - Decorador que captura excepciones de Google API
- `GChatErrorHandler.alert_message()` - Formatea mensajes de error amigables
- `GChatErrorHandler.validate_email_or_raise()` - Valida formato de email

---

## 📚 Librerías Involucradas en Orden de Ejecución

### 1. **Parseo de argumentos** (Inicio)
- `argparse` - Parsea comandos CLI (dm, incident:new, etc.)

### 2. **Logging básico**
- `logging` - Configuración del sistema de logs

### 3. **Autenticación OAuth2**
- `google.oauth2.credentials` - Manejo de credenciales de usuario
- `google_auth_oauthlib.flow` - Flujo OAuth2 interactivo
- `google.auth.transport.requests` - Refresh de tokens

### 4. **Cliente API de Google Chat**
- `google.apps.chat_v1` - SDK de Google Chat API
- `google.apps.chat_v1.types` - Tipos de datos (Message, Space, User, etc.)

### 5. **Base de Datos (Persistencia)**
- `sqlalchemy` - ORM para operaciones CRUD
- `sqlalchemy.orm` - Sesiones y modelos
- `psycopg2-binary` - Driver PostgreSQL (opcional, también soporta SQLite)

### 6. **Utilidades de tiempo**
- `datetime` - Manejo de timestamps
- `google.api_core.datetime_helpers` - Conversión a formato RFC3339

### 7. **Concurrencia (REPL)**
- `threading` - Hilos para polling + stdin simultáneos
- `sys` - Lectura de stdin
- `time` - sleep() para polling intervals

---

## 💻 Comandos Disponibles

### 1. **Mensaje Directo (DM)**

```bash
# Enviar mensaje único
python main.py dm \
  --mode user \
  --user-ref users/destinatario@dominio.com \
  --db-url sqlite:///chat.db \
  --message "Hola, este es un mensaje de prueba"

# REPL interactivo (chat en tiempo real)
python main.py dm \
  --mode user \
  --user-ref users/destinatario@dominio.com \
  --db-url sqlite:///chat.db \
  --repl \
  --poll-interval 2.0
```

**Flujo interno:**
```
main() → dm command
├── GoogleChatClient(mode="user") → Autentica con OAuth2
├── MessageRepository(db_url) → Conecta BD
├── ChatService(chat, repo)
└── Si --repl:
    └── chat_loop() → REPL con polling
    Si --message:
    └── ensure_dm_and_send() → Envío único
```

### 2. **Crear Incidente**

```bash
python main.py incident:new \
  --mode user \
  --db-url sqlite:///chat.db \
  --title "Error en producción" \
  --sev P1 \
  --system "Backend API" \
  --members ana@dominio.com matias@dominio.com
```

**Flujo interno:**
```
main() → incident:new command
├── GoogleChatClient(mode="user")
├── IncidentRepository(db_url)
├── IncidentService(chat, irepo, log)
└── create_incident_space()
    ├── Crea space con display_name calculado
    ├── Publica mensaje header
    ├── Abre hilo "timeline"
    ├── Abre hilo "actions"
    └── Persiste en BD tabla incidents
```

### 3. **Publicar en Timeline**

```bash
python main.py incident:timeline \
  --mode user \
  --db-url sqlite:///chat.db \
  --space spaces/AAAA... \
  --text "Update: Se identificó fallo en servidor DB-01"
```

### 4. **Cerrar Incidente**

```bash
python main.py incident:close \
  --mode user \
  --db-url sqlite:///chat.db \
  --space spaces/AAAA...
```

**Flujo interno:**
```
close_incident()
├── send_text(space, "✅ Resolved", thread_key="timeline")
└── repo.update_incident_status(space, "Resolved")
```

### 5. **REPL en Espacio de Trabajo**

```bash
python main.py space:repl \
  --mode user \
  --db-url sqlite:///chat.db \
  --space spaces/AAAA... \
  --thread-key mi-hilo \
  --poll-interval 1.0
```

---

## 🗄️ Estructura de Base de Datos

### Tabla: `chat_spaces`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `space_name` | String (PK) | Identificador del espacio (ej: spaces/AAAA...) |
| `type` | String | Tipo: DIRECT_MESSAGE, GROUP_CHAT, SPACE |

### Tabla: `chat_messages`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID autoincrementable |
| `space_name` | String (FK) | Referencia a chat_spaces |
| `chat_message_name` | String | Nombre del mensaje (messages/...) |
| `body` | Text | Contenido del mensaje |
| `sent_by` | String | Usuario que envió (users/...) |
| `thread_key` | String | Clave de hilo (opcional) |
| `private_viewer` | String | Viewer privado (opcional) |
| `created_at` | DateTime | Timestamp de creación |

### Tabla: `incidents`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | ID autoincrementable |
| `space_name` | String (UNIQUE) | Espacio del incidente |
| `title` | Text | Título del incidente |
| `sev` | String | Severidad (P1, P2, P3) |
| `system` | String | Sistema afectado |
| `status` | String | Estado (Open, Resolved) |
| `timeline_thread_key` | String | Clave hilo timeline ("timeline") |
| `actions_thread_key` | String | Clave hilo actions ("actions") |
| `created_at` | DateTime | Timestamp de creación |

---

## 🔧 Manejo de Errores

El proyecto implementa manejo robusto de errores:

1. **Validación de Emails**: `InvalidEmailError` si formato incorrecto
2. **Permisos**: `PermissionDeniedError` si falta acceso
3. **Rate Limiting**: `RateLimitError` si excede cuota API
4. **Degradación Graceful**: Si falla envío con thread_key, reintenta sin hilo

**Ejemplo de error capturado:**
```python
try:
    inc.create_incident_space(...)
except ChatAPIError as e:
    print(handler.alert_message(e))
    # Salida: "⚠️ Error API: INVALID_ARGUMENT - Invalid email format"
```

---

## 📝 Notas Importantes

1. **Modo de autenticación:**
   - `--mode user`: Requiere OAuth2 interactivo (abre navegador)
   - `--mode app`: Requiere Service Account (`GOOGLE_APPLICATION_CREDENTIALS`)

2. **Base de datos:**
   - SQLite: `sqlite:///chat.db`
   - PostgreSQL: `postgresql://user:pass@host/db`

3. **Thread Keys:**
   - Los hilos se identifican con `thread_key` (ej: "timeline", "actions")
   - Permiten organizar conversaciones dentro de un espacio

4. **Polling Interval:**
   - Controla frecuencia de lectura de nuevos mensajes (en segundos)
   - Valores típicos: 1.0 - 5.0 segundos

---

## 🎬 Diagrama de Flujo Completo

```
Usuario ejecuta: python main.py dm --mode user --user-ref users/ana@dominio.com --db-url sqlite:///chat.db --repl
                                    ↓
                        1. argparse parsea argumentos
                                    ↓
                        2. setup_logger() configura logging
                                    ↓
                    3. ChatAuthConfig(mode="user") crea config
                                    ↓
        4. build_credentials() → Lee/genera token.json con OAuth2
                                    ↓
        5. GoogleChatClient(cfg) → Inicializa ChatServiceClient
                                    ↓
            6. MessageRepository(dsn) → Conecta SQLite/PostgreSQL
                                    ↓
                7. ChatService(client, repo) → Inicializa servicio
                                    ↓
                    8. chat_loop(user_ref) → REPL en modo DM
                                    ↓
                        ┌─────────────────────┬─────────────────────┐
                        ↓                     ↓                     ↓
              Thread receiver()       Main thread stdin      Cada mensaje:
              ├─ follow_dm()          ├─ input()            ├─ find_or_create_dm_with()
              ├─ list_messages()      └─ send_text()        ├─ send_text()
              └─ Imprime nuevos                             └─ record_message() en BD
```

---

## ✨ Características Destacadas

- ✅ **Persistencia completa** de mensajes y espacios
- ✅ **Validación robusta** de emails y permisos
- ✅ **REPL interactivo** con polling en tiempo real
- ✅ **Gestión de incidentes** con hilos organizados
- ✅ **Degradación graceful** ante errores de API
- ✅ **Soporte dual** para autenticación (user/app)
- ✅ **Logging estructurado** con timestamps

---

## 📄 Licencia

Este proyecto es de uso interno educativo/empresarial.
