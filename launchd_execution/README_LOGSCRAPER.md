Comandos oficiales 

Los siguientes comandos son para mantener activa una terminal en forma de background, 
Y con ello mantener viva la ejecución de scheduler_main.py de la carpeta scheduler, 
Un programa que ejecuta a main.py cada 7 horas -se define en config.py de la misma carpeta-

- INICIAR UN PROCESO 

# Paso 1: Asegurarse de que el .plist está actualizado
cp launchd_execution/com.user.logscraper.plist ~/Library/LaunchAgents/

# Paso 2: Cargar el servicio
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.logscraper.plist

# Paso 3: Verificar que está corriendo
launchctl list | grep com.user.logscraper
# Debería mostrar: PID   0   com.user.logscraper

- VER LOGS DEL PROCESO EN VIVO

tail -f launchd_execution/logs/stdout.log

- MATAR UN PROCESO 

# Paso 1: Detener y descargar el servicio
launchctl bootout gui/$(id -u)/com.user.logscraper

# Paso 2 (Opcional): Verificar que se detuvo
launchctl list | grep com.user.logscraper
# No debería mostrar nada

Una vez matado el proceso, volver a iniciar siguiendo lo de arriba.

- REINICIAR UN PROCESO

# Paso 1: Detener
launchctl bootout gui/$(id -u)/com.user.logscraper

# Paso 2: Actualizar .plist (si hubo cambios)
cp launchd_execution/com.user.logscraper.plist ~/Library/LaunchAgents/

# Paso 3: Iniciar
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.logscraper.plist

- OTRA FORMA DE VERIFICACION

# Ver si está corriendo (busca el PID)
launchctl list | grep com.user.logscraper

tail -f launchd_execution/logs/stdout.log
tail -f launchd_execution/logs/stderr.log

---

## 🔐 SERVICIO SSL CHECKER (Verificación Diaria de Certificados)

Este servicio automático verifica DIARIAMENTE (9:00 AM) los certificados SSL de todas las apps 
configuradas en app/config.py y envía correos de alerta si quedan menos de 30 días para expirar.

- INICIAR SERVICIO SSL CHECKER

# Paso 1: Copiar configuración
cp launchd_execution/com.user.sslchecker.plist ~/Library/LaunchAgents/

# Paso 2: Cargar el servicio
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.user.sslchecker.plist

# Paso 3: Verificar que está cargado
launchctl list | grep com.user.sslchecker
# Puede mostrar: -   0   com.user.sslchecker (el "-" es normal para tareas programadas)

- EJECUTAR MANUALMENTE (sin esperar a las 9:00 AM)

launchctl start com.user.sslchecker

- VER LOGS DEL SSL CHECKER

tail -f launchd_execution/logs/ssl_checker_stdout.log
tail -f launchd_execution/logs/ssl_checker_stderr.log

- DETENER SERVICIO SSL CHECKER

launchctl bootout gui/$(id -u)/com.user.sslchecker

- CAMBIAR HORA DE EJECUCIÓN

Editar launchd_execution/com.user.sslchecker.plist y modificar:
<key>Hour</key>
<integer>9</integer>  <!-- Cambiar a la hora deseada (0-23) -->

Luego reiniciar el servicio (bootout + bootstrap)
