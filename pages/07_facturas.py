# pages/facturas.py

import pandas as pd
import streamlit as st
from datetime import datetime
from database import repositories as repo
from services.inventory_service import StockService, reload_app_state


def render(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.header("📑 Gestión de Facturas")
    clis = repo.get_clients()
    df_v = df_master[df_master['tipo'] == 'VENTA_SALIDA'].copy()
    if not df_v.empty:
        df_v['Cantidad'] = df_v['cantidad'].abs()

    t_reg, t_gest = st.tabs(["📦 Registrar y Gestionar Entregas", "🛠️ Modificar / Eliminar"])

    with t_reg:
        _tab_registrar(clis, stock_service, df_v)

    with t_gest:
        _tab_gestionar(df_v)


def _tab_registrar(clis: pd.DataFrame, stock_service: StockService, df_v: pd.DataFrame) -> None:
    st.write("#### 📝 Registrar Nueva Factura")
    with st.form("f_venta", clear_on_submit=True):
        f = st.date_input("Fecha", datetime.now(), format="DD/MM/YYYY")
        c1, c2 = st.columns(2)
        producto = c1.selectbox("Producto", stock_service.finished_products)
        cantidad = c2.number_input("Cantidad (Bidones)", min_value=1)
        cli_sel = st.selectbox("Cliente", ["Seleccione..."] + clis['nombre'].tolist())
        c3, c4 = st.columns(2)
        p_u = c3.number_input("Precio de Venta (Bs/Bidón)", min_value=0.0)
        nro_fac = c4.text_input("N° Factura")
        obs = st.text_area("Observaciones")

        if st.form_submit_button("📦 Guardar Factura"):
            if cli_sel == "Seleccione...":
                st.error("Seleccione un cliente.")
            elif stock_service.stock_actual.get(producto, 0) < cantidad:
                st.error("❌ Stock insuficiente para esta venta.")
            else:
                cid = int(clis[clis['nombre'] == cli_sel]['id'].values[0])
                repo.save_movement(
                    "VENTA_SALIDA", producto, -cantidad, "PT", "bidon",
                    fecha=f, nro_factura=nro_fac, concepto=obs,
                    cliente_id=cid, precio_u=p_u, total=cantidad * p_u
                )
                st.session_state.success_msg = "Factura guardada."
                reload_app_state()
                st.rerun()

    if not df_v.empty:
        st.divider()
        _historial_y_entregas(df_v)


def _historial_y_entregas(df_v: pd.DataFrame) -> None:
    st.subheader("📋 Historial de Facturas")
    st.dataframe(
        df_v[['Fecha', 'item', 'Cantidad', 'precio_unitario', 'total_bs',
              'cliente_nom', 'nro_factura', 'concepto']]
        .rename(columns={'concepto': 'Observaciones'})
        .sort_index(ascending=False)
        .style.format({"Cantidad": "{:.0f}", "precio_unitario": "{:,.2f}", "total_bs": "{:,.2f}"}),
        width='stretch'
    )

    st.divider()
    st.subheader("📦 Gestión de Notas de Entrega")
    df_v['display'] = df_v.apply(
        lambda x: f"{x['Fecha']} - {x['cliente_nom']} - {x['item']} "
                  f"({x['Cantidad']:.0f}) - Fac: {x['nro_factura']}", axis=1
    )
    sel_id = st.selectbox(
        "Seleccione Factura para Entregas:",
        df_v['id'].tolist(),
        format_func=lambda x: df_v[df_v['id'] == x]['display'].values[0]
    )
    if sel_id:
        _panel_entregas(df_v, sel_id)


def _panel_entregas(df_v: pd.DataFrame, sel_id: int) -> None:
    row_n = df_v[df_v['id'] == sel_id].iloc[0]
    dns = repo.get_delivery_notes(sel_id)
    total_despachado = dns['cantidad'].sum() if not dns.empty else 0
    por_despachar = float(row_n['Cantidad']) - total_despachado

    c1m, c2m = st.columns(2)
    c1m.metric("Total Facturado", f"{row_n['Cantidad']:.0f} bidones")
    c2m.metric("Pendiente por Despachar", f"{por_despachar:.0f} bidones")

    with st.expander("➕ Registrar Nota de Entrega", expanded=True):
        with st.form(f"f_delivery_{sel_id}", clear_on_submit=True):
            c1n, c2n = st.columns(2)
            f_n = c1n.date_input("Fecha Entrega", datetime.now(), format="DD/MM/YYYY")
            q_n = c2n.number_input(
                "Cantidad Bidones Despachados",
                min_value=1.0,
                value=float(por_despachar) if por_despachar > 0 else 1.0
            )
            c3n, c4n = st.columns(2)
            ent_n = c3n.text_input("Nombre quien Entrega")
            rec_n = c4n.text_input("Nombre quien Recibe")
            nro_n = st.text_input("N° Nota de Entrega")

            if st.form_submit_button("✅ Guardar Nota de Entrega"):
                if q_n > por_despachar:
                    st.error(f"❌ La cantidad ({q_n:.0f}) excede lo pendiente ({por_despachar:.0f}).")
                else:
                    repo.save_delivery_note(f_n, q_n, ent_n, rec_n, nro_n, sel_id)
                    st.session_state.success_msg = "Nota de Entrega registrada."
                    reload_app_state()
                    st.rerun()

    if not dns.empty:
        st.write("#### Entregas Realizadas")
        st.dataframe(
            dns[['Fecha', 'cantidad', 'entrega_nombre', 'recibe_nombre', 'nro_nota']]
            .rename(columns={
                'Fecha': 'Fecha', 'cantidad': 'Cant. Bidones',
                'entrega_nombre': 'Entregado por', 'recibe_nombre': 'Recibido por',
                'nro_nota': 'N° Nota'
            }),
            width='stretch'
        )


def _tab_gestionar(df_v: pd.DataFrame) -> None:
    if df_v.empty:
        st.info("No hay facturas para gestionar.")
        return

    st.subheader("🛠️ Modificar o Eliminar Factura")
    df_v['display_edit'] = df_v.apply(
        lambda x: f"{x['Fecha']} - {x['cliente_nom']} - {x['item']} "
                  f"({x['Cantidad']:.0f}) - Fac: {x['nro_factura']}", axis=1
    )
    sel_id = st.selectbox(
        "Seleccione Factura para modificar:",
        df_v['id'].tolist(),
        format_func=lambda x: df_v[df_v['id'] == x]['display_edit'].values[0]
    )
    if not sel_id:
        return

    row_e = df_v[df_v['id'] == sel_id].iloc[0]
    with st.form("f_edit_venta"):
        f_edit = st.date_input("Fecha", value=row_e['fecha_dt'], format="DD/MM/YYYY")
        c1e, c2e = st.columns(2)
        q_edit = c1e.number_input("Cantidad", value=int(row_e['Cantidad']), min_value=1)
        p_u_edit = c2e.number_input("Precio Unit.", value=float(row_e['precio_unitario']), min_value=0.0)
        nro_fac_edit = st.text_input("N° Factura", value=row_e['nro_factura'] if row_e['nro_factura'] else "")
        obs_edit = st.text_area("Observaciones", value=row_e['concepto'] if row_e['concepto'] else "")

        col_d, col_u = st.columns(2)
        if col_d.form_submit_button("🗑️ Eliminar Factura", type="primary"):
            repo.delete_movement(sel_id)
            st.session_state.success_msg = "Factura eliminada."
            reload_app_state()
            st.rerun()
        if col_u.form_submit_button("💾 Actualizar Factura"):
            repo.update_venta(sel_id, f_edit.strftime("%Y-%m-%d"), q_edit,
                              p_u_edit, q_edit * p_u_edit, nro_fac_edit, obs_edit)
            st.session_state.success_msg = "Factura actualizada."
            reload_app_state()
            st.rerun()

if __name__ == "__main__":
    from services.inventory_service import get_app_state
    df_m, ss = get_app_state()
    render(df_m, ss)
