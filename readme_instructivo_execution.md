# Notas importantes para ejecutar el sistema web: 

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Levantar Docker (Terminal 1)
docker-compose up -d --build

# 3. Ejecutar script principal del backend (Terminal 2)
Nos cambiamos a la carpeta t4alerts_backend, y dentro ejecutamos: 
python app.py 

# 4. Ejecutar script principal del frontend (Terminal 3)
Nos cambiamos a la carpeta t4alerts_frontend, y dentro ejecutamos: 
python serve_frontend.py

# 5. Crear usuario admin (Terminal 4 - PRIMERA VEZ)
En la carpeta principal, ejecutamos -en otra terminal-: 
python create_admin_user.py tu@correo.com EligeTuPassword123 

-> Esto crea al usuario tipo admin, cuyo correo de entrada en la web sera tu@correo.com y su contraseña sera EligeTuPassword123 

Luego, ingresar a la url indicada en la terminal del frontend para ir a nuestro sistema web:

Login: http://localhost:8000/login

*OJO: el usuario tipo admin no se registra en la web, solo se crea ejecutando create_admin_user.py, los unicos que se registran en la web son los usuarios tipo user o normales. Ademas, como el frontend se sirve en nginx, al levantar docker, entonces deberia bastar con:

http://localhost/login 

----------- MONITOREO EN PARALELO -----------

# 6. Iniciar scheduler (Terminal 5)
En otra terminal, primero nos cambiamos a la carpeta scheduler, y dentro ejecutamos: 
python scheduler_main.py

Esto lo que hara es ejecutar main.py periodicamente, para recibir los avisos de los errores que se generen en las apps internas de T4.

# 7. Ejecutar scraping manual (Terminal 6 - opcional)
python main.py

Esto lo que hara es ejecutar main.py manualmente, para recibir los avisos de los errores que se generen en las apps internas en la fecha actual. Si se quiere revisar los errores de otras fechas, como por ejemplo el 31 de diciembre de 2025, se debe ejecutar:

python main.py 2025-12-31
