# Notas importantes para ejecutar el sistema web: 

0. Siguiendo las instrucciones del readme_instructivo_execution.md, para ejecutar el sistema web, luego de eso viene la parte del UX, que es la que vamos a explicar a continuacion:

1. Lo primero es crear un usuario tipo admin, para ello debemos ejecutar el archivo create_admin_user.py, el cual se encuentra en la carpeta principal del proyecto. Este archivo recibe dos argumentos: el correo electronico y la contraseña. Por ejemplo:

python create_admin_user.py tu@correo.com EligeTuPassword123

2. Lo segundo es crear las cuentas de usuario tipo user para los trabajadoresa de t4, esto se logra en la ruta /register, estas cuentas no cuentan con ningun permiso inicial, por lo que al principio veran un mensaje avisando que necesitan que el admin les otorgue permisos, ya sea para ver los errores registrados en los logs de las apps internas de t4, o para ver los certificados ssl y los dias que quedan para que expiren -de nuestras apps internas-. 

3. Una vez los usuarios tipo user sean creados y el admin les otorgue los permisos, ellos podran acceder a la ruta de errores /errors, naturalmente, no se vera nada al inicio, para analizar los errores entonces se debe ir primero a la ruta custom-scan, donde se debe rellenar el formulario para analizar los errores de una app interna de t4, una vez rellenado el formulario, se puede presionar el boton "Scrap" para iniciar el scraping, una vez que se inicie el scraping, se podra ver la informacion de la app interna de t4, y luego se podra ver la informacion de los errores de la app interna de t4 para cualquier fecha presionando en Logs / Stats, todos los errores se guardaran en la subruta de /errors llamada /history. 

4. Ademas de ver los errores registrados, se puede ver la informacion de los certificados ssl de nuestras apps internas de t4, para ello se debe ir a la ruta /certificates, donde se podra ver la informacion de los certificados ssl de nuestras apps internas de t4, y luego se podra ver la informacion de los certificados ssl de nuestras apps internas de t4 para cualquier fecha presionando en Logs / Stats, todos los certificados ssl se guardaran en la subruta de /certificates llamada /history.