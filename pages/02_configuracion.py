# pages/configuracion.py

import os
import pandas as pd
import streamlit as st
from datetime import datetime
from config.settings import DB_NAME, RAW_MATERIALS
from database import repositories as repo
from services.inventory_service import StockService, reload_app_state


def render(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.header("⚙️ Configuración")
    st.subheader("🛠️ Parámetros del Sistema (Saldos Iniciales)")

    col1, col2 = st.columns(2)
    with col1:
        _saldo_inicial_mp(df_master)
    with col2:
        _saldo_inicial_pt(df_master, stock_service)

    st.divider()
    _reset_db()


def _saldo_inicial_mp(df_master: pd.DataFrame) -> None:
    st.write("**Materia Prima**")
    has_purchases = not df_master[df_master['tipo'] == 'INGRESO_COMPRA'].empty
    if has_purchases:
        st.info("El sistema ya contiene movimientos de compra. El ajuste de saldo inicial manual está deshabilitado.")
        return

    with st.form("f_si_mp"):
        f_si = st.date_input("Fecha Saldo Inicial", datetime.now(), format="DD/MM/YYYY")
        item_si = st.selectbox("Material", RAW_MATERIALS)
        c1, c2 = st.columns(2)
        cant_si = c1.number_input("Cantidad (Kg)", min_value=0.0)
        bs_si = c2.number_input("Valor (Bs)", min_value=0.0)
        if st.form_submit_button("💾 Guardar Saldo MP"):
            if cant_si > 0:
                repo.save_movement("SALDO_INICIAL", item_si, cant_si, "MP", "kg",
                                   fecha=f_si, total=bs_si)
                st.session_state.success_msg = f"Saldo inicial de {item_si} registrado."
                reload_app_state()
                st.rerun()


def _saldo_inicial_pt(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.write("**Productos Terminados**")
    has_prod = not df_master[df_master['tipo'] == 'PRODUCCION_ENTRADA'].empty
    if has_prod:
        st.info("El sistema ya contiene registros de producción. El ajuste de saldo inicial manual está deshabilitado.")
        return

    with st.form("f_si_pt"):
        f_si_pt = st.date_input("Fecha Saldo Inicial", datetime.now(), format="DD/MM/YYYY")
        item_si_pt = st.selectbox("Producto", stock_service.finished_products)
        cant_si_pt = st.number_input("Bidones", min_value=0.0)
        if st.form_submit_button("💾 Guardar Saldo PT"):
            if cant_si_pt > 0:
                repo.save_movement("SALDO_INICIAL", item_si_pt, cant_si_pt, "PT", "bidon",
                                   fecha=f_si_pt, total=0)
                st.session_state.success_msg = f"Saldo inicial de {item_si_pt} registrado."
                reload_app_state()
                st.rerun()


def _reset_db() -> None:
    if st.checkbox("Confirmar Reset"):
        if st.button("🚨 Borrar Base de Datos"):
            os.remove(DB_NAME)
            st.rerun()

if __name__ == "__main__":
    from services.inventory_service import get_app_state
    df_m, ss = get_app_state()
    render(df_m, ss)
