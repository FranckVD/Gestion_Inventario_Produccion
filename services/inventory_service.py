# services/inventory_service.py
# Capa de servicios: lógica de negocio desacoplada de la UI y la DB

import uuid
import pandas as pd
from config.settings import BIDONES_POR_LOTE, LOTES_ALERT_THRESHOLD
from database import repositories as repo


class StockService:
    """Calcula y consulta el estado actual del stock."""

    def __init__(self, df_master: pd.DataFrame, recipes: dict, raw_materials: list):
        self.df_master = df_master
        self.recipes = recipes
        self.raw_materials = raw_materials
        self.finished_products = list(recipes.keys())
        self.stock_actual = self._calculate_stock()
        self.threshold_10_lots = self._calculate_thresholds()

    def _calculate_stock(self) -> dict:
        stock = (
            self.df_master.groupby('item')['cantidad'].sum().to_dict()
            if not self.df_master.empty else {}
        )
        for item in self.raw_materials + self.finished_products:
            stock.setdefault(item, 0.0)
        return stock

    def _calculate_thresholds(self) -> dict:
        thresholds = {}
        for prod, ingr_dict in self.recipes.items():
            for ingr, qty in ingr_dict.items():
                req_10 = qty * LOTES_ALERT_THRESHOLD
                if ingr not in thresholds or req_10 > thresholds[ingr]:
                    thresholds[ingr] = req_10
        return thresholds

    def check_production_feasibility(self, product: str, bidones: int) -> list[str]:
        """Retorna lista de materiales faltantes. Vacía = producción posible."""
        lotes = bidones / BIDONES_POR_LOTE
        rec = self.recipes.get(product, {})
        faltantes = []
        for insumo, qty_per_lot in rec.items():
            required = qty_per_lot * lotes
            available = self.stock_actual.get(insumo, 0)
            if available < required:
                faltantes.append(f"{insumo} (Faltan {required - available:,.2f} kg)")
        return faltantes

    def get_average_cost(self, item: str) -> float:
        """Calcula el costo promedio ponderado de un ítem."""
        h = self.df_master[self.df_master['item'] == item]
        s = h['cantidad'].sum()
        v = h['total_bs'].sum()
        return v / s if s > 0 else 0.0

    def build_kardex(self, material: str) -> pd.DataFrame:
        """Construye el Kardex valorado (costo promedio ponderado) para un material."""
        df_m = self.df_master[
            (self.df_master['item'] == material) &
            (self.df_master['categoria'] == 'MP')
        ].copy().sort_values(['fecha_dt', 'id'])

        saldos_kg, saldos_bs, precios_avg, ingresos_bs, egresos_bs = [], [], [], [], []
        curr_kg, curr_bs, curr_avg = 0.0, 0.0, 0.0

        for _, row in df_m.iterrows():
            cant = float(row['cantidad'])
            tipo = row['tipo']

            if tipo == 'SALDO_INICIAL':
                ingreso = float(row['total_bs'])
                egreso = 0.0
                curr_kg += cant
                curr_bs += ingreso
                if curr_kg > 0:
                    curr_avg = curr_bs / curr_kg
                display_avg = 0.0

            elif tipo == 'INGRESO_COMPRA':
                ingreso = float(row['total_bs'])
                egreso = 0.0
                curr_kg += cant
                curr_bs += ingreso
                if curr_kg > 0:
                    curr_avg = curr_bs / curr_kg
                display_avg = row['precio_unitario']

            elif tipo == 'CONSUMO_PRODUCCION':
                ingreso = 0.0
                display_avg = round(curr_avg, 2)
                egreso = round(abs(cant * display_avg), 2)
                curr_kg += cant
                curr_bs = round(curr_bs - egreso, 2)

            else:
                ingreso = float(row['total_bs']) if row['total_bs'] > 0 else 0.0
                egreso = abs(float(row['total_bs'])) if row['total_bs'] < 0 else 0.0
                curr_kg += cant
                curr_bs += ingreso - egreso
                if curr_kg > 0:
                    curr_avg = curr_bs / curr_kg
                display_avg = curr_avg

            saldos_kg.append(curr_kg)
            saldos_bs.append(curr_bs)
            precios_avg.append(display_avg)
            ingresos_bs.append(ingreso)
            egresos_bs.append(egreso)

        df_m['Saldo Kg'] = saldos_kg
        df_m['Saldo Bs'] = saldos_bs
        df_m['Precio 87%'] = precios_avg
        df_m['Ingreso Bs'] = ingresos_bs
        df_m['Egreso Bs'] = egresos_bs
        df_m['Precio Unit'] = df_m.apply(
            lambda x: 0.0 if x['tipo'] == 'CONSUMO_PRODUCCION'
            else (x['precio_unitario'] / 0.87 if x['precio_unitario'] > 0 else 0.0),
            axis=1
        )
        df_m['tipo'] = df_m['tipo'].replace('SALDO_INICIAL', 'SALDO INICIAL')
        return df_m


class ProductionService:
    """Orquesta el registro de lotes de producción."""

    def __init__(self, stock_service: StockService):
        self.stock = stock_service

    def register_production(self, product: str, bidones: int, fecha) -> str:
        """Registra entrada de producción + consumos de MP. Retorna el batch_id."""
        lotes = bidones / BIDONES_POR_LOTE
        batch_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"

        repo.save_movement(
            "PRODUCCION_ENTRADA", product, bidones, "PT", "bidon",
            lotes_equiv=lotes, fecha=fecha, nro_nota=batch_id
        )

        rec = self.stock.recipes.get(product, {})
        for insumo, qty_per_lot in rec.items():
            qty_consumed = qty_per_lot * lotes
            avg_cost = self.stock.get_average_cost(insumo)
            repo.save_movement(
                "CONSUMO_PRODUCCION", insumo, -qty_consumed, "MP", "kg",
                fecha=fecha, precio_u=avg_cost, total=-(qty_consumed * avg_cost),
                nro_nota=batch_id
            )
        return batch_id

    def edit_production(self, old_batch_id: str, product: str,
                        new_bidones: int, new_fecha) -> bool:
        """
        Elimina el lote anterior y crea uno nuevo.
        Retorna False si no hay stock suficiente.
        """
        df_master = self.stock.df_master
        cons_batch = df_master[
            (df_master['nro_nota'] == old_batch_id) &
            (df_master['tipo'] == 'CONSUMO_PRODUCCION')
        ]
        # Stock liberado virtualmente del lote anterior
        cons_map = cons_batch.set_index('item')['cantidad'].abs().to_dict()

        lotes = new_bidones / BIDONES_POR_LOTE
        rec = self.stock.recipes.get(product, {})
        for insumo, qty_per_lot in rec.items():
            required = qty_per_lot * lotes
            available = self.stock.stock_actual.get(insumo, 0) + cons_map.get(insumo, 0)
            if available < required:
                return False

        repo.delete_production_batch(old_batch_id)
        new_batch_id = f"PROD-{uuid.uuid4().hex[:8].upper()}"
        repo.save_movement(
            "PRODUCCION_ENTRADA", product, new_bidones, "PT", "bidon",
            lotes_equiv=lotes, fecha=new_fecha, nro_nota=new_batch_id
        )
        for insumo, qty_per_lot in rec.items():
            qty_consumed = qty_per_lot * lotes
            avg_cost = self.stock.get_average_cost(insumo)
            repo.save_movement(
                "CONSUMO_PRODUCCION", insumo, -qty_consumed, "MP", "kg",
                fecha=new_fecha, precio_u=avg_cost,
                total=-(qty_consumed * avg_cost), nro_nota=new_batch_id
            )
        return True


def get_app_state():
    """Inicializa y retorna (df_master, stock_service) asegurando persistencia en reloads."""
    import streamlit as st
    from database.connection import init_db
    from database.repositories import load_all_movements, load_recipes
    from config.settings import RAW_MATERIALS

    init_db()
    if 'df_master' not in st.session_state or st.session_state.get('_reload_data', False):
        recipes = load_recipes()
        df_master = load_all_movements()
        st.session_state.df_master = df_master
        st.session_state.stock_service = StockService(df_master, recipes, RAW_MATERIALS)
        st.session_state._reload_data = False
    
    return st.session_state.df_master, st.session_state.stock_service


def reload_app_state():
    """Fuerza la recarga de los datos en el próximo ciclo."""
    import streamlit as st
    st.session_state._reload_data = True
