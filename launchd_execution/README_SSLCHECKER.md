# SSL CHECKER - Verificación Automática de Certificados

Servicio que verifica certificados SSL diariamente y envía correos si quedan menos de X días para expirar.

---

## INICIAR SERVICIO

```bash
# Paso 1: Copiar configuración
cp launchd_execution/com.user.sslchecker.plist ~/Library/LaunchAgents/

# Paso 2: Cargar el servicio
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.sslchecker.plist

# Paso 3: Verificar (el "-" es normal para tareas programadas)
launchctl list | grep com.user.sslchecker
```

---

## EJECUTAR MANUALMENTE (sin esperar al horario)

```bash
launchctl start com.user.sslchecker
```

---

## VER LOGS

```bash
tail -f launchd_execution/logs/ssl_checker_stdout.log
tail -f launchd_execution/logs/ssl_checker_stderr.log
```

---

## DETENER SERVICIO

```bash
launchctl bootout gui/$(id -u)/com.user.sslchecker
```

---

## CONFIGURACIÓN

### Cambiar hora de ejecución

**Archivo:** `launchd_execution/com.user.sslchecker.plist`

```xml
<key>Hour</key>
<integer>9</integer>      <!-- Cambiar hora (0-23) -->
<key>Minute</key>
<integer>0</integer>      <!-- Cambiar minuto (0-59) -->
```

Luego reiniciar servicio (bootout + bootstrap)

---

### Cambiar umbral de días para alertas

**Archivo:** `.env` (raíz del proyecto)

```bash
DAYS_UMBRAL=30    # Cambiar al número de días deseado
```

**Archivo:** `ssl_checker/checker.py` (línea 360)

```python
elif 8 <= days_left <= 30:    # Cambiar 30 al umbral deseado
```

**Archivo:** `ssl_checker/checker.py` (línea 400)

```python
if result["days_left"] <= 30:  # Solo enviar si <= 30 días
```

---

### Cambiar destinatarios de correo

**Archivo:** `.env`

```bash
ALERT_EMAIL_TO=correo1@example.com, correo2@example.com
```

Los destinatarios son los mismos que reciben correos de `main.py`

---

### Agregar/quitar apps a monitorear

**Archivo:** `app/config.py`

Editar el diccionario `APPS_CONFIG_LEGACY` (líneas 20-86)

El servicio lee automáticamente las URLs de ahí.

---

## NOTAS

- Ejecuta diariamente según horario configurado
- Envía correo CADA DÍA si hay certificados por expirar
- Monitorea las 8 apps configuradas en `app/config.py`
- Niveles: < 8 días (CRITICAL), 8-30 días (WARNING), > 30 días (OK)
