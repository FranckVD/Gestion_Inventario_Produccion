# pages/proveedores.py

import streamlit as st
from database import repositories as repo
from services.inventory_service import reload_app_state


def render() -> None:
    st.header("🤝 Gestión de Proveedores")
    t_reg, t_gest = st.tabs(["👤 Registrar Proveedor", "🛠️ Gestionar Proveedores"])

    with t_reg:
        _tab_registrar()

    with t_gest:
        _tab_gestionar()


def _tab_registrar() -> None:
    with st.form("f_add_sup", clear_on_submit=True):
        nombre = st.text_input("Nombre/Razón Social")
        nit = st.text_input("NIT/CI")
        telefono = st.text_input("Teléfono/WhatsApp")
        direccion = st.text_input("Dirección")
        if st.form_submit_button("Guardar"):
            repo.create_supplier(nombre, nit, telefono, direccion)
            st.session_state.success_msg = "Proveedor guardado"
            reload_app_state()
            st.rerun()


def _tab_gestionar() -> None:
    sups = repo.get_suppliers()
    st.dataframe(sups, width='stretch')
    st.write("---")
    st.write("#### ✏️ Editar / Eliminar Proveedor")

    if sups.empty:
        st.info("No hay proveedores registrados.")
        return

    # Función auxiliar para mostrar el nombre en el selectbox
    def get_supplier_name(sid):
        row = sups[sups['id'] == sid]
        return row['nombre'].values[0] if not row.empty else str(sid)

    # UN SOLO selectbox con la lógica correcta
    sel_id = st.selectbox(
        "Seleccione Proveedor para editar:",
        options=sups['id'].tolist(),
        format_func=get_supplier_name,
        key="selectbox_gestionar_proveedores"
    )

    if not sel_id:
        return

    row = sups[sups['id'] == sel_id].iloc[0]
    with st.form("f_edit_sup"):
        n_e = st.text_input("Nombre", value=row['nombre'])
        nit_e = st.text_input("NIT/CI", value=row['nit_ci'] if row['nit_ci'] else "")
        t_e = st.text_input("Teléfono", value=row['telefono'] if row['telefono'] else "")
        d_e = st.text_input("Dirección", value=row['direccion'] if row['direccion'] else "")

        c_del, c_upd = st.columns(2)
        if c_del.form_submit_button("🗑️ Eliminar", type="primary"):
            repo.delete_supplier(sel_id)
            st.session_state.success_msg = "Proveedor eliminado."
            reload_app_state()
            st.rerun()
        if c_upd.form_submit_button("💾 Actualizar"):
            repo.update_supplier(sel_id, n_e, t_e, d_e, nit_e)
            st.session_state.success_msg = "Proveedor actualizado."
            reload_app_state()
            st.rerun()

if __name__ == "__main__":
    render()
