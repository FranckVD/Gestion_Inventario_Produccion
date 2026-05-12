# database/repositories.py
# Repositorios: toda la lógica de acceso a datos (queries SQL)

import pandas as pd
from datetime import datetime
from database.connection import get_connection


# ---------------------------------------------------------------------------
# Movimientos
# ---------------------------------------------------------------------------

def save_movement(
    tipo, item, cantidad, categoria, unidad,
    lotes_equiv=0, fecha=None, nro_nota="", concepto="",
    cliente_id=None, proveedor_id=None, nro_factura="",
    precio_u=0, total=0
) -> int:
    """Inserta un movimiento y retorna el id generado."""
    conn = get_connection()
    cursor = conn.cursor()
    if not fecha:
        fecha = datetime.now().strftime("%d-%m-%Y")
    elif not isinstance(fecha, str):
        fecha = fecha.strftime("%Y-%m-%d")

    cursor.execute('''
        INSERT INTO movements
            (fecha, tipo, item, cantidad, categoria, unidad, lotes_equiv,
             nro_nota, concepto, cliente_id, proveedor_id, nro_factura,
             precio_unitario, total_bs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        fecha, tipo, item, float(cantidad), categoria, unidad,
        float(lotes_equiv), nro_nota, concepto, cliente_id, proveedor_id,
        nro_factura, float(precio_u), float(total)
    ))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return last_id


def update_movement(id_mov, fecha, item, cantidad, precio_u, total,
                    proveedor_id=None, nro_factura="") -> None:
    conn = get_connection()
    conn.execute('''
        UPDATE movements
        SET fecha=?, item=?, cantidad=?, precio_unitario=?, total_bs=?,
            proveedor_id=?, nro_factura=?
        WHERE id=?
    ''', (fecha, item, cantidad, precio_u, total, proveedor_id, nro_factura, id_mov))
    conn.commit()
    conn.close()


def update_venta(id_mov, fecha, cantidad, precio_u, total, nro_factura, concepto) -> None:
    conn = get_connection()
    conn.execute('''
        UPDATE movements
        SET fecha=?, cantidad=?, precio_unitario=?, total_bs=?,
            nro_factura=?, concepto=?
        WHERE id=?
    ''', (fecha, -cantidad, precio_u, total, nro_factura, concepto, id_mov))
    conn.commit()
    conn.close()


def delete_movement(id_mov) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM movements WHERE id=?", (id_mov,))
    conn.commit()
    conn.close()


def delete_production_batch(batch_id) -> None:
    """Elimina todos los movimientos de un lote de producción por nro_nota."""
    conn = get_connection()
    conn.execute("DELETE FROM movements WHERE nro_nota=?", (batch_id,))
    conn.commit()
    conn.close()


def load_all_movements() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT m.*, c.nombre AS cliente_nom, s.nombre AS proveedor_nom
        FROM movements m
        LEFT JOIN clients c ON m.cliente_id = c.id
        LEFT JOIN suppliers s ON m.proveedor_id = s.id
    ''', conn)
    conn.close()

    if not df.empty:
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0.0)
        df['total_bs'] = pd.to_numeric(df['total_bs'], errors='coerce').fillna(0.0)
        df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors='coerce').fillna(0.0)
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['Fecha'] = df['fecha_dt'].dt.strftime('%d/%m/%Y').fillna("S/F")
    return df


# ---------------------------------------------------------------------------
# Clientes
# ---------------------------------------------------------------------------

def get_clients() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    conn.close()
    return df


def create_client(nombre, nit_ci, telefono, direccion) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO clients (nombre, nit_ci, telefono, direccion) VALUES (?,?,?,?)",
        (nombre, nit_ci, telefono, direccion)
    )
    conn.commit()
    conn.close()


def update_client(id_cli, nombre, telefono, direccion, nit_ci) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE clients SET nombre=?, telefono=?, direccion=?, nit_ci=? WHERE id=?",
        (nombre, telefono, direccion, nit_ci, id_cli)
    )
    conn.commit()
    conn.close()


def delete_client(id_cli) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM clients WHERE id=?", (id_cli,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Proveedores
# ---------------------------------------------------------------------------

def get_suppliers() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM suppliers", conn)
    conn.close()
    return df


def create_supplier(nombre, nit_ci, telefono, direccion) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO suppliers (nombre, nit_ci, telefono, direccion) VALUES (?,?,?,?)",
        (nombre, nit_ci, telefono, direccion)
    )
    conn.commit()
    conn.close()


def update_supplier(id_sup, nombre, telefono, direccion, nit_ci) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE suppliers SET nombre=?, telefono=?, direccion=?, nit_ci=? WHERE id=?",
        (nombre, telefono, direccion, nit_ci, id_sup)
    )
    conn.commit()
    conn.close()


def delete_supplier(id_sup) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM suppliers WHERE id=?", (id_sup,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Notas de entrega
# ---------------------------------------------------------------------------

def save_delivery_note(fecha, cantidad, entrega, recibe, nro, mov_id) -> None:
    conn = get_connection()
    if not isinstance(fecha, str):
        fecha = fecha.strftime("%Y-%m-%d")
    conn.execute('''
        INSERT INTO delivery_notes
            (fecha, cantidad, entrega_nombre, recibe_nombre, nro_nota, movement_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (fecha, float(cantidad), entrega, recibe, nro, mov_id))
    conn.commit()
    conn.close()


def get_delivery_notes(mov_id) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM delivery_notes WHERE movement_id = ?", conn, params=(mov_id,)
    )
    conn.close()
    if not df.empty:
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['Fecha'] = df['fecha_dt'].dt.strftime('%d/%m/%Y').fillna("S/F")
    return df


# ---------------------------------------------------------------------------
# Recetas
# ---------------------------------------------------------------------------

def load_recipes() -> dict:
    """Retorna un dict {producto: {insumo: cantidad_kg}}."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM recipes", conn)
    conn.close()
    return {
        p: df[df['producto'] == p].set_index('insumo')['cantidad_kg'].to_dict()
        for p in df['producto'].unique()
    }
