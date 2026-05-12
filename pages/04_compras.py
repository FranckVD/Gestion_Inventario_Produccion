# pages/compras.py

import pandas as pd
import streamlit as st
from config.settings import RAW_MATERIALS
from database import repositories as repo
from services.inventory_service import StockService, reload_app_state


def render(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.header("📦 Compras de Materia Prima")
    sups = repo.get_suppliers()
    t_reg, t_gest = st.tabs(["📝 Registrar Compra", "🛠️ Gestionar Compras"])

    with t_reg:
        _tab_registrar(sups)

    with t_gest:
        df_compras = df_master[df_master['tipo'] == 'INGRESO_COMPRA'].copy()
        _tab_gestionar(df_compras, sups)

    st.divider()
    _render_kardex_mp(df_master, stock_service)


def _tab_registrar(sups: pd.DataFrame) -> None:
    with st.form("f_compra", clear_on_submit=True):
        from datetime import datetime
        f = st.date_input("Fecha", datetime.now(), format="DD/MM/YYYY")
        item = st.selectbox("Material", RAW_MATERIALS)
        c1, c2 = st.columns(2)
        cant = c1.number_input("Cantidad (Kg)", min_value=0.0)
        p_unit = c2.number_input("Precio Unitario (Bs/Kg)", min_value=0.0)
        c3, c4 = st.columns(2)
        opciones_prov = ["Seleccione..."] + sups['nombre'].tolist()
        prov_sel = c3.selectbox("Proveedor", opciones_prov)
        nro_fac = c4.text_input("N° Factura")

        if st.form_submit_button("🚀 Registrar"):
            if cant <= 0:
                st.error("La cantidad debe ser mayor a 0.")
            elif prov_sel == "Seleccione...":
                st.error("Por favor seleccione un proveedor.")
            else:
                sid = int(sups[sups['nombre'] == prov_sel]['id'].values[0])
                p_neto = p_unit * 0.87
                repo.save_movement(
                    "INGRESO_COMPRA", item, cant, "MP", "kg",
                    fecha=f, proveedor_id=sid, nro_factura=nro_fac,
                    precio_u=p_neto, total=cant * p_neto
                )
                st.session_state.success_msg = "Compra registrada."
                reload_app_state()
                st.rerun()


def _tab_gestionar(df_compras: pd.DataFrame, sups: pd.DataFrame) -> None:
    st.subheader("🛠️ Gestión y Historial de Compras")

    search = st.text_input("🔍 Buscar compra (Material, Proveedor, Factura):")
    if not df_compras.empty and search:
        mask = (
            df_compras['item'].str.contains(search, case=False, na=False) |
            df_compras['proveedor_nom'].str.contains(search, case=False, na=False) |
            df_compras['nro_factura'].str.contains(search, case=False, na=False)
        )
        df_filtered = df_compras[mask]
    else:
        df_filtered = df_compras

    if df_filtered.empty:
        st.info("No hay compras registradas.")
        return

    st.dataframe(
        df_filtered[['Fecha', 'item', 'cantidad', 'proveedor_nom', 'nro_factura', 'total_bs']]
        .sort_index(ascending=False)
        .style.format({"cantidad": "{:,.2f}", "total_bs": "{:,.2f}"}),
        width='stretch'
    )

    st.divider()
    st.info("Seleccione una compra para editar o eliminar.")
    df_filtered['display'] = df_filtered.apply(
        lambda x: f"{x['Fecha']} - {x['item']} - {x['cantidad']:,.2f} kg - "
                  f"Prov: {x['proveedor_nom']} - Fac: {x['nro_factura']}", axis=1
    )
    sel_id = st.selectbox(
        "Seleccione registro:",
        df_filtered['id'].tolist(),
        format_func=lambda x: df_filtered[df_filtered['id'] == x]['display'].values[0]
    )
    if sel_id:
        _form_editar_compra(sel_id, df_filtered, sups)


def _form_editar_compra(sel_id, df_filtered: pd.DataFrame, sups: pd.DataFrame) -> None:
    row = df_filtered[df_filtered['id'] == sel_id].iloc[0]
    with st.form("f_edit_compra"):
        f_edit = st.date_input("Fecha", row['fecha_dt'], format="DD/MM/YYYY")
        item_edit = st.selectbox(
            "Material", RAW_MATERIALS,
            index=RAW_MATERIALS.index(row['item']) if row['item'] in RAW_MATERIALS else 0
        )
        c1e, c2e = st.columns(2)
        cant_edit = c1e.number_input("Cantidad (Kg)", min_value=0.01, value=float(row['cantidad']))
        p_unit_orig = float(row['precio_unitario']) / 0.87 if row['precio_unitario'] else 0.0
        p_unit_edit = c2e.number_input("Precio Unitario (Bs/Kg)", min_value=0.0, value=p_unit_orig)
        c3e, c4e = st.columns(2)
        opciones = ["Seleccione..."] + sups['nombre'].tolist()
        prov_idx = opciones.index(row['proveedor_nom']) if row['proveedor_nom'] in sups['nombre'].tolist() else 0
        prov_edit = c3e.selectbox("Proveedor", opciones, index=prov_idx)
        nro_fac_edit = c4e.text_input("N° Factura", value=row['nro_factura'] if row['nro_factura'] else "")

        c_del, c_upd = st.columns(2)
        if c_del.form_submit_button("🗑️ Eliminar", type="primary"):
            repo.delete_movement(sel_id)
            st.session_state.success_msg = "Registro eliminado."
            reload_app_state()
            st.rerun()
        if c_upd.form_submit_button("💾 Actualizar"):
            sid_new = int(sups[sups['nombre'] == prov_edit]['id'].values[0]) if prov_edit != "Seleccione..." else None
            p_neto_new = p_unit_edit * 0.87
            repo.update_movement(sel_id, f_edit.strftime("%Y-%m-%d"), item_edit,
                                 cant_edit, p_neto_new, cant_edit * p_neto_new,
                                 proveedor_id=sid_new, nro_factura=nro_fac_edit)
            st.session_state.success_msg = "Registro actualizado."
            reload_app_state()
            st.rerun()


def _render_kardex_mp(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.subheader("📋 Kardex Físico - Materia Prima")
    if df_master.empty:
        return

    for material in stock_service.raw_materials:
        curr_stock = stock_service.stock_actual.get(material, 0)
        thresh = stock_service.threshold_10_lots.get(material, 0)
        df_kardex = stock_service.build_kardex(material)

        if df_kardex.empty:
            continue

        icon = "⚠️" if curr_stock <= thresh else "✅"
        with st.expander(f"{icon} Kardex: {material} (Stock: {curr_stock:,.2f} kg)"):
            if curr_stock <= thresh:
                st.warning(f"⚠️ Stock bajo. Mínimo sugerido para 10 lotes: {thresh:,.2f} kg")

            if 'fecha_f' in df_kardex.columns:
                df_kardex = df_kardex.rename(columns={'fecha_f': 'Fecha'})

            cols = ['Fecha', 'tipo', 'cantidad', 'Precio Unit', 'Saldo Kg',
                    'Precio 87%', 'Ingreso Bs', 'Egreso Bs', 'Saldo Bs']
            
            df_display = df_kardex.sort_index(ascending=False)
            fmt = {c: "{:,.2f}" for c in ['cantidad', 'Precio Unit', 'Saldo Kg',
                                           'Precio 87%', 'Ingreso Bs', 'Egreso Bs', 'Saldo Bs']}
            st.dataframe(
                df_display[cols].style
                .format(fmt)
                .map(lambda x: 'color: red; font-weight: bold;' if x <= thresh else None,
                     subset=['Saldo Kg']),
                width='stretch'
            )

if __name__ == "__main__":
    from services.inventory_service import get_app_state
    df_m, ss = get_app_state()
    render(df_m, ss)
