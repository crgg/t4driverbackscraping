# Scrapping de logs con cron

Este proyecto hace scrapping de la sección de logs de varias aplicaciones y envía correos si se detectan muchos errores **no controlados** durante el día (errores con estados SQL o mensajes muy técnicos).

Este README explica **cómo dejar todo funcionando con `cron` desde cero**.

---

## 0. Estructura relevante del proyecto

```text
scrapping_project/
  main.py
  docker-compose.yml
  temporizador/
    run_scraping.sh
    cron_run.log        # se crea al ejecutar el script
````

* `main.py`: ejecuta el scrapping y envía los correos.
* `temporizador/run_scraping.sh`: script que usa `cron` para lanzar `main.py` y guardar logs.
* `temporizador/cron_run.log`: log de ejecuciones hechas por el script (incluyendo las de cron).

---

## 1. Probar `main.py` a mano

Antes de meter `cron`, hay que verificar que el scrapping funciona solo.

En la terminal:

```bash
conda activate backend
/opt/anaconda3/envs/backend/bin/python /Users/administrator/Desktop/scrapping_project/main.py
```

Salida esperada (ejemplo resumido):

```text
📅 Fecha de reporte: 2025-12-03
📧 Procesando 4 aplicaciones...

======================================================================
Procesando: DriverApp GoTo Logistics
======================================================================
🔐 Autenticando en DriverApp GoTo Logistics (https://driverapp.goto-logistics.com)...
✅ Autenticación exitosa en DriverApp GoTo Logistics
...
✓ Correo enviado para DriverApp GoTo Logistics

... (más aplicaciones) ...

======================================================================
✅ Scrapping completado para todas las aplicaciones
======================================================================
```

Si aquí:

* Autentica bien,
* Guarda HTML/logs,
* Y envía correos,

entonces **la lógica principal está OK**.

---

## 2. Probar el script `run_scraping.sh`

`cron` no llama directo a `main.py`, sino al script `run_scraping.sh`.
Primero hay que comprobar que este script funciona.

### 2.1. Ir a la carpeta y dar permisos de ejecución

```bash
conda activate backend
cd /Users/administrator/Desktop/scrapping_project/temporizador

# IMPORTANTE: sin comentarios en la misma línea
chmod +x run_scraping.sh   # <- esto se escribe SIN el comentario en la terminal
```

En la terminal se escribe solo:

```bash
chmod +x run_scraping.sh
```

> Si se escribe `chmod +x run_scraping.sh   # solo la primera vez`
> la parte `# solo la primera vez` se interpreta como argumentos extra y salen errores tipo:
>
> chmod: #: No such file or directory
> chmod: solo: No such file or directory
> ...
> ```

### 2.2. Ejecutar el script

./run_scraping.sh

Es normal ver advertencias de Docker, por ejemplo:

```text
WARN[0000] The "APP_NAME" variable is not set. Defaulting to a blank string.
WARN[0000] /Users/administrator/Desktop/scrapping_project/docker-compose.yml: the attribute `version` is obsolete...
[+] Running 1/1
 ✔ Container scrapping_pg  Running
```

Luego, el script:

* Levanta el contenedor de Postgres.
* Ejecuta `main.py`.
* Escribe todo en `temporizador/cron_run.log`.

### 2.3. Verificar el log del script

Desde la carpeta raíz del proyecto:

```bash
cd /Users/administrator/Desktop/scrapping_project
cat temporizador/cron_run.log
```

Ejemplo de contenido:

```text
=== EJECUCIÓN Wed Dec  3 15:47:03 CST 2025 ===
📅 Fecha de reporte: 2025-12-03
📧 Procesando 4 aplicaciones...

... (salida detallada por aplicación) ...

======================================================================
✅ Scrapping completado para todas las aplicaciones
======================================================================
```

Si esto se ve bien, significa que **`run_scraping.sh` está funcionando correctamente**.

---

## 3. Configurar `cron` para ejecutar el script

Ahora sí: automatizar con `cron`.

### 3.1. Abrir el crontab

En la terminal (no importa en qué carpeta estés):

```bash
crontab -e
```

La primera vez puede mostrar:

```text
crontab: no crontab for administrator - using an empty one
crontab: installing new crontab
```

Eso es normal: está creando tu primer crontab.

Se abrirá un editor (normalmente `vi` / `vim`).

### 3.2. Escribir la tarea de cron

Dentro del editor:

1. Pulsa `i` para entrar en modo insertar (si estás en `vi`/`vim`).

2. Escribe esta línea:

   ```text
   * * * * * /bin/bash /Users/administrator/Desktop/scrapping_project/temporizador/run_scraping.sh
   ```

   Esto significa: **ejecutar el script cada minuto** (sirve para probar).

3. Pulsa `Esc`.

4. Escribe:

   ```text
   :wq
   ```

   y pulsa Enter para guardar y salir.

> **IMPORTANTE:**
> No hay que escribir la línea `* * * * * ...` directamente en la terminal normal.
> Si lo haces, el `*` se expande a nombres de archivos (por ejemplo `cron_run.log`) y sale algo como:
>
> ```text
> zsh: command not found: cron_run.log
> ```
>
> Eso es el shell intentando ejecutar el archivo `cron_run.log` como comando.
> La línea de `cron` **solo va dentro del editor** de `crontab -e`.

### 3.3. Confirmar que cron guardó la tarea

En la terminal:

```bash
crontab -l
```

Debería mostrar:

```text
* * * * * /bin/bash /Users/administrator/Desktop/scrapping_project/temporizador/run_scraping.sh
```

Si aparece esa línea, **cron ya quedó configurado**.

---

## 4. Comprobar que cron está ejecutando el scrapping

Cron ejecutará `run_scraping.sh` cada minuto y el script irá agregando entradas al log `cron_run.log`.

Para ver las últimas líneas:

```bash
cd /Users/administrator/Desktop/scrapping_project
tail -n 40 temporizador/cron_run.log
```

Cuando cron ya lo haya ejecutado varias veces, deberías ver varias secciones:

```text
=== EJECUCIÓN Wed Dec  3 15:47:03 CST 2025 ===
...

=== EJECUCIÓN Wed Dec  3 15:48:03 CST 2025 ===
...

=== EJECUCIÓN Wed Dec  3 15:49:03 CST 2025 ===
...
```

Si hay **varias ejecuciones con minutos distintos**, eso confirma que:

* `cron` está corriendo bien.
* El script se ejecuta automáticamente.
* Los correos se envían cuando corresponde.

---

## 5. Cambiar la frecuencia de ejecución (producción)

Una vez comprobado que funciona, probablemente no quieras ejecutar el scrapping cada minuto.

Para editar la tarea:

```bash
crontab -e
```

Ejemplos de configuraciones:

* Ejecutar todos los días a las 08:00:

  ```text
  0 8 * * * /bin/bash /Users/administrator/Desktop/scrapping_project/temporizador/run_scraping.sh
  ```

* Ejecutar cada 30 minutos:

  ```text
  */30 * * * * /bin/bash /Users/administrator/Desktop/scrapping_project/temporizador/run_scraping.sh
  ```

Recordatorio rápido del formato de cron:

```text
* * * * *  comando
│ │ │ │ └─ día de la semana (0–7, 0 y 7 = domingo)
│ │ │ └─── mes (1–12)
│ │ └───── día del mes (1–31)
│ └─────── hora (0–23)
└───────── minuto (0–59)
```

---

## 6. Errores típicos y su explicación

### `chmod: #: No such file or directory`

Ocurre si se ejecuta en la terminal:

```bash
chmod +x run_scraping.sh   # solo la primera vez
```

El comentario `# solo la primera vez` **no es un comentario para el shell** en ese contexto; se interpreta como más argumentos para `chmod`.
Solución: ejecutar solo:

```bash
chmod +x run_scraping.sh
```

### `zsh: command not found: cron_run.log`

Aparece cuando se escribe algo así en la terminal:

```bash
* * * * * /bin/bash /Users/administrator/Desktop/scrapping_project/temporizador/run_scraping.sh
```

Estando en la carpeta `temporizador`, el `*` se expande a archivos como `cron_run.log`, y el shell intenta ejecutarlos como comandos.

Solución:

* No escribir la línea de cron en la terminal normal.
* Siempre editarla dentro de `crontab -e`.

---

## 7. Pregunta: ¿se puede combinar cron y AWS?

Sí. Algunas formas de hacerlo:

* Ejecutar este mismo proyecto en una instancia **EC2** o en un contenedor en AWS (por ejemplo en ECS o en una máquina propia) y usar `cron` ahí dentro, igual que en tu Mac.
* O usar servicios de AWS que hacen de “cron en la nube”, como:

  * **EventBridge / CloudWatch Events** para lanzar tareas según un horario.
  * **AWS Lambda** disparada con una regla de EventBridge con expresión tipo cron.
  * Tareas programadas en **ECS/Fargate**.

En resumen:
✅ **Sí, se puede combinar cron con AWS**, ya sea usando `cron` clásico dentro de una máquina/contendor de AWS, o usando los servicios programados de AWS que cumplen el mismo rol.