# Guía: Ejecución de Scheduler en Background con Launchd (macOS)

Esta guía documenta el proceso para configurar `scheduler/scheduler_main.py` como un servicio nativo de macOS usando `launchd`. Esto asegura que el script se ejecute automáticamente al iniciar sesión, se reinicie si falla, y no dependa de tener una terminal abierta.

## 1. Prerrequisitos

Identificar la ruta absoluta del intérprete de Python que se usará (especialmente si se usa un entorno virtual).

source venv/bin/activate
which python
# Salida ejemplo: /Users/administrator/Desktop/scrapping_project/venv/bin/python

## 2. Configuración del Archivo `.plist`

Se crea un archivo de configuración XML en `scheduler/com.scrapping_project.scheduler.plist`.

**Puntos Clave del Archivo:**
*   `Label`: Identificador único (ej. `com.scrapping_project.scheduler`).
*   `ProgramArguments`: Ruta al Python y ruta al script `.py`.
*   `WorkingDirectory`: Carpeta donde se ejecutará el script (importante para imports y rutas relativas).
*   `KeepAlive`: `true` (reinicia el script si crashea).
*   `RunAtLoad`: `true` (inicia al arrancar el sistema/sesión).
*   `StandardOutPath` / `StandardErrorPath`: Rutas para los logs.

**Corrección de Errores Comunes:**
Si usas un bloque `<dict>` para variables de entorno u otros, asegúrate de que tenga su `<key>` correspondiente antes.
*   ❌ Incorrecto: `<dict>...</dict>` suelto.
*   ✅ Correcto: `<key>EnvironmentVariables</key> <dict>...</dict>`.

## 3. Instalación y Ejecución

Los servicios de usuario ("Agents") viven en `~/Library/LaunchAgents/`.

### Paso 1: Copiar el archivo al directorio del sistema
cp scheduler/com.scrapping_project.scheduler.plist ~/Library/LaunchAgents/


### Paso 2: Cargar el servicio
El comando `launchctl load` registra y arranca el servicio. El flag `-w` asegura que se marque como habilitado permanentemente.

launchctl load -w ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist

### Paso 3: Troubleshooting (Error "Input/output error")
Si obtienes `Load failed: 5: Input/output error`, suele ser por:
1.  **Sintaxis XML inválida:** El archivo `.plist` está mal formado.
2.  **Permisos:** El archivo no pertenece a tu usuario.

**Diagnóstico:**
Usa `plutil` para validar la sintaxis:
plutil -lint ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist
# Si hay error, te dirá la línea exacta (ej. "Found non-key inside <dict>").

**Solución:**
1.  Corrige el archivo `.plist`.
2.  Vuelve a copiarlo (`cp ...`).
3.  Recarga:
    # Intentar descargar primero (puede dar error si no estaba cargado, es normal ignorarlo)
    launchctl unload ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist
    
    # Cargar de nuevo
    launchctl load -w ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist

## 4. Verificación y Monitoreo

### Verificar si está corriendo
launchctl list | grep scrapping

*   **Salida esperada:** `29254   0   com.scrapping_project.scheduler`
    *   `29254`: PID (Process ID). Significa que está vivo.
    *   `0`: Status (0 = OK).
    *   Si ves un guion `-` en vez del PID, no está corriendo.

### Ver los Logs en tiempo real
Como el servicio corre en background, no ves el output en la terminal. Para verlo:
tail -f scheduler/scheduler.log

Esto mostrará lo que el script está imprimiendo (stdout) en tiempo real.

## 5. Comandos Útiles

| Acción | Comando |
| :--- | :--- |
| **Detener** | `launchctl unload ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist` |
| **Iniciar** | `launchctl load -w ~/Library/LaunchAgents/com.scrapping_project.scheduler.plist` |
| **Ver Logs** | `tail -f scheduler/scheduler.log` |
| **Ver Errores** | `tail -f scheduler/scheduler.err` |

## 6. Verificar que el script se está ejecutando correctamente
    tail -f /Users/administrator/Desktop/scrapping_project/scheduler/scheduler.log
    