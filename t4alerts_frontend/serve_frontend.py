#!/usr/bin/env python3
"""
Servidor simple para el frontend con rutas personalizadas.
Mapea /registration -> frontend_registration/
Mapea /login -> frontend_login/
Proxy /api/* requests to backend server
"""
from flask import Flask, send_from_directory, redirect, request, Response
import os
import requests

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable cache for development

# Directorio base del frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    """Redirige a la página de login por defecto"""
    return redirect('/login')

@app.route('/registration')
@app.route('/registration/')
def registration_redirect():
    """Registration is disabled - redirect to login"""
    return redirect('/login')

@app.route('/registration/<path:filename>')
def registration_files(filename):
    """Registration is disabled - redirect to login"""
    return redirect('/login')

@app.route('/login')
@app.route('/login/')
def login_redirect():
    """Redirige a la página de login"""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend_login'), 'index.html')

@app.route('/login/<path:filename>')
def login_files(filename):
    """Sirve archivos estáticos de login"""
    return send_from_directory(os.path.join(BASE_DIR, 'frontend_login'), filename)

# --- Nuevas Rutas v2.0 ---

@app.route('/menu')
def menu_redirect():
    return redirect('/menu/')

@app.route('/menu/')
def menu_index():
    return send_from_directory(os.path.join(BASE_DIR, 'menu'), 'index.html')

@app.route('/menu/<path:filename>')
def menu_files(filename):
    # Ensure we serve files from the menu directory
    return send_from_directory(os.path.join(BASE_DIR, 'menu'), filename)

@app.route('/certificates')
def certificates_redirect():
    return redirect('/certificates/')

@app.route('/certificates/')
def certificates_index():
    return send_from_directory(os.path.join(BASE_DIR, 'certificates'), 'index.html')

@app.route('/certificates/<path:filename>')
def certificates_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'certificates'), filename)

@app.route('/errors')
def errors_redirect():
    return redirect('/errors/')

@app.route('/errors/')
def errors_index():
    return send_from_directory(os.path.join(BASE_DIR, 'dashboard'), 'index.html')

@app.route('/errors/<path:filename>')
def errors_routing(filename):
    """
    Handle dashboard routing.
    If filename has an extension (contains dot), try to serve as static file.
    Otherwise, serve index.html to allow SPA routing (e.g., /errors/driverapp_goto).
    """
    if '.' in filename:
        return send_from_directory(os.path.join(BASE_DIR, 'dashboard'), filename)
    
    # It's an SPA route, serve index.html
    return send_from_directory(os.path.join(BASE_DIR, 'dashboard'), 'index.html')

@app.route('/admin')
def admin_redirect():
    return redirect('/admin/')

@app.route('/admin/')
def admin_index():
    """Sirve la página de administración"""
    return send_from_directory(os.path.join(BASE_DIR, 'admin'), 'index.html')

@app.route('/admin/<path:filename>')
def admin_files(filename):
    """Sirve archivos estáticos de admin"""
    return send_from_directory(os.path.join(BASE_DIR, 'admin'), filename)

# @app.route('/apps')
# def apps_redirect():
#     return redirect('/apps/')
#
# @app.route('/apps/')
# def apps_index():
#     """Sirve la página de gestión de apps"""
#     return send_from_directory(os.path.join(BASE_DIR, 'apps'), 'index.html')
#
# @app.route('/apps/<path:filename>')
# def apps_files(filename):
#     """Sirve archivos estáticos de apps"""
#     return send_from_directory(os.path.join(BASE_DIR, 'apps'), filename)

# Sirve archivos estáticos globales (static/js/core, etc)
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)

# Sirve archivos compartidos (shared)
@app.route('/shared/<path:filename>')
def shared_files(filename):
    """Sirve archivos compartidos"""
    return send_from_directory(os.path.join(BASE_DIR, 'shared'), filename)

# Sirve assets
@app.route('/assets/<path:filename>')
def assets_files(filename):
    """Sirve archivos de assets"""
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)

# API Proxy to Backend
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy_api(path):
    """
    Proxy all /api/* requests to the backend server on port 5001
    This mimics nginx behavior in production
    """
    backend_url = f'http://127.0.0.1:5001/api/{path}'
    
    # Forward the request to backend
    try:
        resp = requests.request(
            method=request.method,
            url=backend_url,
            headers={key: value for key, value in request.headers if key.lower() != 'host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False
        )
        
        # Create response with backend's content
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        
        response = Response(resp.content, resp.status_code, headers)
        return response
        
    except Exception as e:
        print(f"❌ Error proxying to backend: {e}")
        return {"msg": "Backend connection error"}, 502


if __name__ == '__main__':
    print("🚀 Frontend Server iniciado en http://localhost:8000")
    print("🔐 Login: http://localhost:8000/login")
    app.run(host='0.0.0.0', port=8000, debug=True)
