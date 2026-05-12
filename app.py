# app.py — Orquestador de Navegación
# Responsabilidad: Inicialización global y configuración del menú nativo.

import time
import streamlit as st
from database.connection import db_exists, init_db
from services.inventory_service import get_app_state

# Configuración de página (debe ser lo primero)
st.set_page_config(page_title="Control de MP y PT", layout="wide", page_icon="📊")

# ── 1. Verificación de Base de Datos (Primer arranque) ──────────────────────
if not db_exists():
    st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h1 style="color: #2e7bcf;">✨ ¡Bienvenido/a! ✨</h1>
            <p style="font-size: 1.2em; color: #555;">
                Sistema inteligente de control de producción y gestión de inventarios.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("""
        ### 🚀 Configuración Inicial Requerida
        - ✅ Creación de Base de Datos.
        - ✅ Estructura de Inventarios.
        - ✅ Recetas de Producción.
        """)
        if st.button("🎉 ¡Comenzar ahora!", width='stretch'):
            with st.spinner("Configurando el sistema..."):
                init_db()
                st.balloons()
                time.sleep(2)
                st.rerun()
    st.stop()

# ── 2. Inicialización de Estado Global ──────────────────────────────────────
# Esto asegura que los datos estén listos para cualquier página
get_app_state()

# Mensaje de éxito global (si existe)
if 'success_msg' in st.session_state:
    st.toast(st.session_state.success_msg, icon="✅")
    del st.session_state.success_msg

# ── 3. Configuración del Menú de Navegación (Native Multipage) ──────────────
# Aquí definimos el orden, los iconos y los nombres sin que aparezca "app.py"

pg = st.navigation({
    "Menú": [
        st.Page("pages/01_dashboard.py", title="Dashboard", icon="📈", default=True),
        st.Page("pages/04_compras.py", title="Compras MP", icon="📦"),
        st.Page("pages/05_produccion.py", title="Producción", icon="⚗️"),
        st.Page("pages/07_facturas.py", title="Facturas / Ventas", icon="📑"),
    ],
    "Administración": [
        st.Page("pages/06_clientes.py", title="Clientes", icon="👥"),
        st.Page("pages/03_proveedores.py", title="Proveedores", icon="🤝"),
    ],
    "Configuración": [
        st.Page("pages/02_configuracion.py", title="Ajustes de Sistema", icon="⚙️"),
    ]
})

# Ejecutar la página seleccionada
pg.run()
