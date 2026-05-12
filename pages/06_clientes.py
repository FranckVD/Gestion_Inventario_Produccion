# pages/clientes.py

import streamlit as st
from database import repositories as repo
from services.inventory_service import reload_app_state


def render() -> None:
    st.header("👥 Gestión de Clientes")
    t_reg, t_gest = st.tabs(["👤 Registrar Cliente", "🛠️ Gestionar Clientes"])

    with t_reg:
        _tab_registrar()

    with t_gest:
        _tab_gestionar()


def _tab_registrar() -> None:
    with st.form("f_add_cli", clear_on_submit=True):
        nombre = st.text_input("Nombre/Razón Social")
        nit = st.text_input("NIT/CI")
        telefono = st.text_input("Teléfono/WhatsApp")
        direccion = st.text_input("Dirección")
        if st.form_submit_button("Guardar"):
            repo.create_client(nombre, nit, telefono, direccion)
            st.session_state.success_msg = "Registro guardado"
            reload_app_state()
            st.rerun()


def _tab_gestionar() -> None:
    clis = repo.get_clients()
    st.dataframe(clis, width='stretch')
    st.write("---")
    st.write("#### ✏️ Editar / Eliminar Cliente")

    if clis.empty:
        return

    sel_id = st.selectbox(
        "Seleccione Cliente:",
        clis['id'].tolist(),
        format_func=lambda x: clis[clis['id'] == x]['nombre'].values[0]
    )
    if not sel_id:
        return

    row = clis[clis['id'] == sel_id].iloc[0]
    with st.form("f_edit_cli"):
        n_e = st.text_input("Nombre", value=row['nombre'])
        nit_e = st.text_input("NIT/CI", value=row['nit_ci'] if row['nit_ci'] else "")
        t_e = st.text_input("Teléfono", value=row['telefono'] if row['telefono'] else "")
        d_e = st.text_input("Dirección", value=row['direccion'] if row['direccion'] else "")

        c_del, c_upd = st.columns(2)
        if c_del.form_submit_button("🗑️ Eliminar", type="primary"):
            repo.delete_client(sel_id)
            st.session_state.success_msg = "Cliente eliminado."
            reload_app_state()
            st.rerun()
        if c_upd.form_submit_button("💾 Actualizar"):
            repo.update_client(sel_id, n_e, t_e, d_e, nit_e)
            st.session_state.success_msg = "Cliente actualizado."
            reload_app_state()
            st.rerun()

if __name__ == "__main__":
    render()
