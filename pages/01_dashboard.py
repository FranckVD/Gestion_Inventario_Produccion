# pages/dashboard.py

import pandas as pd
import altair as alt
import streamlit as st
from services.inventory_service import StockService


def render(df_master: pd.DataFrame, stock_service: StockService) -> None:
    st.header("📈 Dashboard Gerencial")

    if df_master.empty:
        st.info("No hay datos registrados aún.")
        return

    _render_metrics(df_master)
    st.divider()
    _render_ventas_e_inversion(df_master)
    st.divider()
    _render_tendencias_y_clientes(df_master)
    st.divider()
    _render_stock_vs_minimo(stock_service)
    st.divider()
    _render_produccion_mensual(df_master)


def _render_metrics(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    v_bs = df[df['tipo'] == 'VENTA_SALIDA']['total_bs'].sum()
    c_bs = df[
        (df['tipo'] == 'INGRESO_COMPRA') |
        ((df['tipo'] == 'SALDO_INICIAL') & (df['categoria'] == 'MP'))
    ]['total_bs'].sum()
    p_und = df[
        (df['tipo'] == 'PRODUCCION_ENTRADA') |
        ((df['tipo'] == 'SALDO_INICIAL') & (df['categoria'] == 'PT'))
    ]['cantidad'].sum()

    c1.metric("Ingresos Facturas", f"{v_bs:,.2f} Bs", delta="Total Histórico")
    c2.metric("Inversión MP (Neto)", f"{c_bs:,.2f} Bs", delta="Costo MP + Saldo Ini", delta_color="inverse")
    c3.metric("Stock Prod. Total", f"{p_und:,.0f} und", delta="Bidones (Prod + SI)")
    c4.metric("Utilidad Bruta", f"{(v_bs - c_bs):,.2f} Bs", delta="Aprox.", delta_color="normal")


def _render_ventas_e_inversion(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💰 Ventas por Producto")
        v_data = df[df['tipo'] == 'VENTA_SALIDA'].groupby('item')['total_bs'].sum().abs().reset_index()
        if not v_data.empty:
            chart = alt.Chart(v_data).mark_bar().encode(
                x=alt.X('item', sort='-y', title='Producto'),
                y=alt.Y('total_bs', title='Total Ventas (Bs)'),
                color=alt.Color('item', legend=None, scale=alt.Scale(scheme='viridis')),
                tooltip=['item', 'total_bs']
            ).interactive()
            st.altair_chart(chart, width='stretch')
        else:
            st.info("No hay datos de ventas.")

    with col2:
        st.subheader("📉 Inversión y Saldos por Material")
        i_data = df[
            (df['tipo'] == 'INGRESO_COMPRA') |
            ((df['tipo'] == 'SALDO_INICIAL') & (df['categoria'] == 'MP'))
        ].groupby(['item', 'tipo'])['total_bs'].sum().reset_index()

        if not i_data.empty:
            i_data['tipo'] = i_data['tipo'].replace({
                'SALDO_INICIAL': 'Saldo Inicial',
                'INGRESO_COMPRA': 'Compra'
            })
            chart = alt.Chart(i_data).mark_bar().encode(
                x=alt.X('item', sort='-y', title='Materia Prima'),
                y=alt.Y('total_bs', title='Inversión (Bs)'),
                color=alt.Color('tipo', title='Tipo', scale=alt.Scale(scheme='magma')),
                tooltip=['item', 'tipo', 'total_bs']
            ).interactive()
            st.altair_chart(chart, width='stretch')
        else:
            st.info("No hay datos de compras o saldos iniciales.")


def _render_tendencias_y_clientes(df: pd.DataFrame) -> None:
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("📈 Tendencia de Ventas (Mensual)")
        df_trend = df[df['tipo'] == 'VENTA_SALIDA'].copy()
        if not df_trend.empty:
            df_trend['Mes'] = df_trend['fecha_dt'].dt.strftime('%Y-%m')
            trend_data = df_trend.groupby('Mes')['total_bs'].sum().reset_index()
            chart = alt.Chart(trend_data).mark_line(point=True).encode(
                x=alt.X('Mes', title='Mes'),
                y=alt.Y('total_bs', title='Ventas (Bs)'),
                color=alt.value('#FF4B4B'),
                tooltip=['Mes', 'total_bs']
            ).interactive()
            st.altair_chart(chart, width='stretch')
        else:
            st.info("Sin datos históricos suficientes.")

    with c4:
        st.subheader("🏆 Top Clientes")
        df_cli = df[df['tipo'] == 'VENTA_SALIDA'].copy()
        if not df_cli.empty:
            top_cli = (
                df_cli.groupby('cliente_nom')['total_bs'].sum()
                .reset_index().sort_values('total_bs', ascending=False).head(5)
            )
            chart = alt.Chart(top_cli).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("total_bs", stack=True),
                color=alt.Color("cliente_nom", legend=alt.Legend(title="Cliente"),
                                scale=alt.Scale(scheme='category20b')),
                tooltip=["cliente_nom", "total_bs"]
            ).interactive()
            st.altair_chart(chart, width='stretch')
        else:
            st.info("Sin datos de clientes.")


def _render_stock_vs_minimo(stock_service: StockService) -> None:
    st.subheader("📦 Niveles de Stock de Materia Prima vs. Mínimo (10 Lotes)")
    stock_list = [
        {
            "Material": m,
            "Stock Actual": stock_service.stock_actual.get(m, 0),
            "Mínimo Requerido": stock_service.threshold_10_lots.get(m, 0)
        }
        for m in stock_service.raw_materials
    ]
    df_melted = pd.DataFrame(stock_list).melt('Material', var_name='Tipo', value_name='Cantidad (Kg)')
    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('Tipo:N', title=None, axis=alt.Axis(labels=False)),
        y=alt.Y('Cantidad (Kg):Q'),
        color='Tipo:N',
        column=alt.Column('Material:N', title=None, header=alt.Header(labelOrient='bottom'))
    ).properties(width=100).interactive()
    st.altair_chart(chart)


def _render_produccion_mensual(df: pd.DataFrame) -> None:
    st.subheader("⚗️ Volumen de Producción Mensual")
    df_prod = df[df['tipo'] == 'PRODUCCION_ENTRADA'].copy()
    if not df_prod.empty:
        df_prod['Mes'] = df_prod['fecha_dt'].dt.strftime('%Y-%m')
        prod_data = df_prod.groupby(['Mes', 'item'])['cantidad'].sum().reset_index()
        chart = alt.Chart(prod_data).mark_area(opacity=0.6).encode(
            x=alt.X('Mes', title='Mes'),
            y=alt.Y('cantidad', title='Bidones Producidos'),
            color=alt.Color('item', title='Producto'),
            tooltip=['Mes', 'item', 'cantidad']
        ).interactive()
        st.altair_chart(chart, width='stretch')
    else:
        st.info("No hay datos de producción para mostrar tendencias.")

if __name__ == "__main__":
    from services.inventory_service import get_app_state
    df_m, ss = get_app_state()
    render(df_m, ss)
