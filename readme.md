# 🧹 Monitor de Errores de Aplicaciones (Scrapping de Logs)

Script que:

1. Se loguea en varias aplicaciones (DriverApp GoTo, GoExperior, KLC, AccurateCargo).
2. Hace *scrapping* de la vista de logs de cada app.
3. Clasifica los errores en:
   - **Controlados**
   - **No controlados**
   - Y, dentro del día, distingue entre **nuevos** y **ya avisados** (suponiendo que el codigo se ejecutara mañana tarde y noche, en ese caso, los errores de la tarde no marcarian como nuevos a los de la mañana, y los de la noche no marcarian
   como nuevos ni los de la tarde ni los de la mañana, solo se marcaran como nuevos los que aparezcan en la mañana).
4. Guarda los errores nuevos en archivos `.log`.
5. Envía un **correo por cada aplicación** con el resumen de errores nuevos vistos al momento de ejecutar main.py

---

## ✅ 1. Requisitos

### 🐍 Python

- Python 3.10+ (se uso el 3.12.4 aqui)
- Instalar dependencias:
pip install -r requirements.txt
