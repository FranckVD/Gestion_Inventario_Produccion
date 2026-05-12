# pages/produccion.py

import pandas as pd
import streamlit as st
from datetime import datetime
from config.settings import BIDONES_POR_LOTE
from database import repositories as repo
from services.inventory_service import StockService, ProductionService, reload_app_state


def render(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.header("⚗️ Registro de Producción")
    prod_service = ProductionService(stock_service)
    t_reg, t_gest = st.tabs(["⚗️ Registrar Producción", "🛠️ Gestionar Producción"])

    with t_reg:
        _tab_registrar(stock_service, prod_service)

    with t_gest:
        _tab_gestionar(df_master, stock_service, prod_service)

    st.divider()
    _render_kardex_pt(df_master, stock_service)


def _tab_registrar(stock_service: StockService, prod_service: ProductionService) -> None:
    f = st.date_input("Fecha", datetime.now(), format="DD/MM/YYYY")
    producto = st.selectbox("Producto", stock_service.finished_products)
    bidones = st.number_input("Bidones", min_value=0, step=BIDONES_POR_LOTE)
    lotes = bidones / BIDONES_POR_LOTE
    st.info(f"Producción para **{lotes:,.2f} lotes**")

    if bidones <= 0:
        return

    faltantes = stock_service.check_production_feasibility(producto, bidones)
    if faltantes:
        st.error("⚠️ NO SE PUEDE REGISTRAR. Faltan materias primas:\n" +
                 "\n".join([f"- {m}" for m in faltantes]))
    else:
        st.success("✅ Stock suficiente. Listo para registrar.")
        if st.button("🚀 Registrar Producción"):
            prod_service.register_production(producto, bidones, f)
            st.session_state.success_msg = "Producción completada."
            reload_app_state()
            st.rerun()


def _tab_gestionar(df_master: pd.DataFrame, stock_service: StockService,
                   prod_service: ProductionService) -> None:
    st.info("Gestión de Producciones Anteriores")
    df_prods = df_master[df_master['tipo'] == 'PRODUCCION_ENTRADA'].copy()

    if df_prods.empty:
        st.info("No hay producciones registradas.")
        return

    df_prods['display'] = df_prods.apply(
        lambda x: f"{x['Fecha']} - {x['item']} - {x['cantidad']:.0f} und - ID: {x['nro_nota']}",
        axis=1
    )
    sel_batch = st.selectbox(
        "Seleccione Producción:",
        df_prods['nro_nota'].unique(),
        format_func=lambda x: (
            df_prods[df_prods['nro_nota'] == x]['display'].values[0]
            if not df_prods[df_prods['nro_nota'] == x].empty else x
        )
    )

    if not sel_batch:
        return

    row_p = df_prods[df_prods['nro_nota'] == sel_batch].iloc[0]

    with st.expander("🛠️ Acciones", expanded=True):
        if st.button("🗑️ Eliminar Producción", type="primary"):
            repo.delete_production_batch(sel_batch)
            st.session_state.success_msg = "Producción eliminada y stock revertido."
            reload_app_state()
            st.rerun()

        st.write("---")
        st.write("**Editar Producción** (Modifique valores y guarde)")
        with st.form("f_edit_prod"):
            f_e = st.date_input("Nueva Fecha", row_p['fecha_dt'], format="DD/MM/YYYY")
            q_e = st.number_input("Nuevos Bidones", min_value=0, step=BIDONES_POR_LOTE,
                                  value=int(row_p['cantidad']))
            if st.form_submit_button("💾 Guardar Cambios"):
                ok = prod_service.edit_production(sel_batch, row_p['item'], q_e, f_e)
                if ok:
                    st.session_state.success_msg = "Producción editada correctamente."
                    reload_app_state()
                    st.rerun()
                else:
                    falt = [i for i, q in stock_service.recipes.get(row_p['item'], {}).items()
                            if stock_service.stock_actual.get(i, 0) < q * q_e / BIDONES_POR_LOTE]
                    st.error(f"No se puede editar a esa cantidad. Falta stock: {', '.join(falt)}")


def _render_kardex_pt(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.subheader("📋 Kardex Físico - Productos Terminados")
    if df_master.empty:
        return

    df_pt = df_master[df_master['categoria'] == 'PT'].copy()
    if not df_pt.empty:
        df_display = df_pt.rename(columns={'Fecha': 'Fecha', 'item': 'Producto'}).sort_index(ascending=False)
        st.dataframe(
            df_display[['Fecha', 'tipo', 'Producto', 'cantidad']].style.format({"cantidad": "{:.0f}"}),
            width='stretch'
        )

    st.subheader("💰 Stock Actual")
    stock_data = [
        {"Ítem": k, "Stock": v}
        for k, v in stock_service.stock_actual.items()
        if k in stock_service.finished_products
    ]
    st.table(pd.DataFrame(stock_data).style.format({"Stock": "{:,.0f}"}))

if __name__ == "__main__":
    from services.inventory_service import get_app_state
    df_m, ss = get_app_state()
    render(df_m, ss)
