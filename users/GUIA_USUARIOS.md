# Guía de Gestión de Usuarios

Has creado un set de herramientas para gestionar usuarios de manera fácil desde la terminal. Los scripts ahora se encuentran en la carpeta `users/`.

Puedes ejecutarlos de dos formas:

**Opción A (Desde la raíz del proyecto):**
Ejecuta el comando indicando la carpeta: `python users/script.py`

**Opción B (Entrando a la carpeta):**
Primero entra a la carpeta: `cd users`
Luego ejecuta normal: `python script.py`

## 1. Ver qué usuarios existen

Usa `list_users.py` para ver una tabla con todos los usuarios registrados.

Opción A:
python users/list_users.py
python users/list_users.py --admins-only
python users/list_users.py --users-only

Opción B:
cd users
python list_users.py

**Salida ejemplo:**
📋 ALL USERS IN DATABASE
================================================================================
1. 👑 admin@t4app.com
   ID: 1
   Role: admin
   Created: 2024-01-22 14:00:00

2. 👤 usuario@bad.com
   ID: 2
   Role: user
   Created: 2024-01-22 14:05:00
================================================================================
Total users: 2 (👑 1 admins, 👤 1 regular users)


## 2. Borrar un usuario con error

Si detectas un usuario mal creado (ej. `usuario@bad.com`), usa `delete_user.py`.

# Te pedirá confirmación por seguridad
python users/delete_user.py usuario@bad.com

**Si estás seguro y no quieres confirmar:**
python users/delete_user.py usuario@bad.com --force


## 3. Borrar TODOS los usuarios

Si necesitas limpiar la base de datos (por ejemplo, en entorno de pruebas), usa `delete_all_users.py`.

# Borra TODO (requiere escribir "DELETE ALL")
python users/delete_all_users.py

# Borra solo los usuarios normales (deja a los admins vivos)
python users/delete_all_users.py --exclude-admins


## 4. Crear usuarios nuevos

Una vez limpiado, puedes crear usuarios correctamente:

# Crear admin
python users/create_admin_user.py mi_admin@t4app.com password123

# Crear usuario normal
python users/create_user.py empleado@t4app.com password123


## Resumen de Comandos (Desde raíz)

| Acción | Comando |
|--------|---------|
| **Listar** | `python users/list_users.py` |
| **Borrar Uno** | `python users/delete_user.py <email>` |
| **Borrar Todos** | `python users/delete_all_users.py` |
| **Crear User** | `python users/create_user.py <email> <pass>` |
| **Crear Admin** | `python users/create_admin_user.py <email> <pass>` |
