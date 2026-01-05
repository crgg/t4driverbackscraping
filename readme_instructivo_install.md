# 📋 Instructivo de Instalación y Ejecución - T4 Alerts System

## 📦 Instalación de Dependencias

Todas las librerías necesarias están listadas en el archivo `requirements.txt` ubicado en la raíz del proyecto. Para instalar todas las dependencias de una sola vez, ejecuta:

pip install -r requirements.txt

---

## 🔧 Librerías Necesarias por Componente

### 1️⃣ **Backend (`t4alerts_backend`)**

El backend de T4 Alerts es una API REST construida con Flask que gestiona la autenticación, almacenamiento de errores y proporciona endpoints para el frontend.

**Librerías principales:**
- `Flask` - Framework web para crear la API
- `Flask-JWT-Extended` - Autenticación mediante JSON Web Tokens
- `Flask-SQLAlchemy` - ORM para interactuar con PostgreSQL
- `Flask-CORS` - Manejo de CORS para permitir peticiones del frontend
- `bcrypt` - Encriptación de contraseñas
- `psycopg2-binary` - Adaptador de PostgreSQL para Python
- `python-dotenv` - Carga de variables de entorno desde `.env`

### 2️⃣ **Frontend (`t4alerts_frontend`)**

El frontend es una aplicación web basada en **HTML, CSS y JavaScript vanilla** servida mediante Nginx dentro de un contenedor Docker.

**Dependencias de desarrollo/servicio:**
- Nginx (incluido en el contenedor Docker)
- Python 3.11+ (para `serve_frontend.py` en desarrollo local)

### 3️⃣ **Scheduler (`scheduler/scheduler_main.py`)**

El scheduler es un proceso que ejecuta automáticamente el script `main.py` de la raíz del proyecto en intervalos definidos para scraping y notificaciones automatizadas.

**Librerías principales:**
- `apscheduler` - Programador de tareas para ejecutar `main.py` periódicamente
- `python-dotenv` - Carga de configuración desde `.env`
- `pytz` - Manejo de zonas horarias

**Relación con `main.py`:**
El scheduler importa y ejecuta las funciones principales de `main.py`, que a su vez depende de:
- `requests` - Peticiones HTTP para scraping
- `beautifulsoup4` - Parsing de HTML
- `psycopg2-binary` - Conexión a PostgreSQL
- `python-dotenv` - Variables de entorno

### 4️⃣ **Script Principal (`main.py`)**

El script principal realiza el scraping de logs de aplicaciones, clasifica errores y envía notificaciones.

**Librerías principales:**
- `requests` - Para hacer peticiones a las aplicaciones a monitorear
- `beautifulsoup4` - Para parsear respuestas HTML
- `psycopg2-binary` - Para guardar errores en PostgreSQL
- `twilio>=8.0.0` - Para enviar notificaciones SMS
- `slack-sdk>=3.0.0` - Para enviar notificaciones a Slack
- `python-dotenv` - Para configuración

### 5️⃣ **Otras Dependencias**

**Módulos de SSL (`ssl_checker`):**
- `pyopenssl` - Verificación de certificados SSL
- `cryptography` - Operaciones criptográficas
- `idna` - Manejo de nombres de dominio internacionalizados

---

## 📂 Estructura del Proyecto

```
scrapping_project/
├── requirements.txt              # ← Todas las dependencias aquí
├── main.py                       # Script principal de scraping
├── docker-compose.yml            # Definición de servicios Docker
├── create_admin_user.py          # Script para crear usuarios admin
├── scheduler/
│   ├── scheduler_main.py         # Ejecutor automático de main.py
│   ├── config.py                 # Configuración de intervalos
│   └── utils.py                  # Utilidades del scheduler
├── t4alerts_backend/
│   ├── app.py                    # API Flask principal
│   ├── admin/                    # ← Módulo de administración (NUEVO)
│   │   ├── models.py             # Modelo de permisos
│   │   ├── services.py           # Lógica de negocio
│   │   └── routes.py             # Endpoints admin
│   ├── common/
│   │   ├── models.py             # Modelos (User actualizado)
│   │   └── decorators.py         # Decoradores de permisos (NUEVO)
│   ├── Dockerfile                # Imagen Docker del backend
│   └── ...                       # Módulos de backend
├── t4alerts_frontend/
│   ├── admin/                    # ← Panel de administración (NUEVO)
│   │   ├── index.html            # Interfaz admin
│   │   ├── style.css             # Estilos admin
│   │   └── script.js             # Lógica admin
│   ├── shared/
│   │   └── PermissionManager.js  # Utilidad de permisos (NUEVO)
│   ├── menu/                     # Menú actualizado con permisos
│   ├── dashboard/                # Dashboard principal
│   ├── nginx.conf                # Configuración de Nginx
│   ├── Dockerfile                # Imagen Docker del frontend
│   └── ...                       # Archivos HTML/CSS/JS
└── db/
    ├── init.sql                  # Inicialización de DB
    └── permissions_init.sql      # Tabla de permisos (NUEVO)
```

---

## 📝 Notas Importantes

1. **Variables de entorno:** Asegúrate de tener configurado el archivo `.env` en la raíz del proyecto con las credenciales necesarias (Twilio, Slack, PostgreSQL, etc.)

2. **PostgreSQL:** El contenedor de PostgreSQL debe estar corriendo antes de ejecutar `main.py` o `scheduler_main.py`

3. **Primera vez:** Si es tu primera ejecución, el script `db/init.sql` creará automáticamente las tablas necesarias en PostgreSQL

4. **Sistema de permisos:** Los usuarios nuevos NO tienen permisos por defecto. Un administrador debe otorgarles acceso explícitamente a través del panel de administración

5. **JWT Tokens:** Los tokens incluyen los permisos del usuario y son validados tanto en frontend como en backend

---

## 🆘 Soporte

Si encuentras errores durante la ejecución, verifica:
- ✅ Que Docker esté corriendo
- ✅ Que todas las dependencias estén instaladas
- ✅ Que el archivo `.env` esté correctamente configurado
- ✅ Que los puertos 80 y 5435 no estén siendo usados por otros servicios
- ✅ Que hayas creado al menos un usuario administrador
