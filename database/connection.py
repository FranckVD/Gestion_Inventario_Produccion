# database/connection.py
# Manejo de conexión y esquema de la base de datos

import sqlite3
import os
from config.settings import DB_NAME, DEFAULT_RECIPES


def get_connection() -> sqlite3.Connection:
    """Retorna una conexión a la base de datos."""
    return sqlite3.connect(DB_NAME)


def db_exists() -> bool:
    """Verifica si el archivo de base de datos existe."""
    return os.path.exists(DB_NAME)


def init_db() -> None:
    """Crea todas las tablas necesarias y aplica migraciones suaves."""
    conn = get_connection()
    cursor = conn.cursor()

    _create_tables(cursor)
    _run_migrations(cursor)
    _seed_default_recipes(cursor)

    conn.commit()
    conn.close()


def _create_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT,
            item TEXT,
            cantidad REAL,
            categoria TEXT,
            unidad TEXT,
            lotes_equiv REAL DEFAULT 0,
            nro_nota TEXT,
            concepto TEXT,
            cliente_id INTEGER,
            proveedor_id INTEGER,
            nro_factura TEXT,
            precio_unitario REAL DEFAULT 0,
            total_bs REAL DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            producto TEXT,
            insumo TEXT,
            cantidad_kg REAL,
            PRIMARY KEY (producto, insumo)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            nit_ci TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            nit_ci TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS delivery_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            cantidad REAL,
            entrega_nombre TEXT,
            recibe_nombre TEXT,
            nro_nota TEXT,
            movement_id INTEGER,
            FOREIGN KEY (movement_id) REFERENCES movements (id)
        )
    ''')


def _run_migrations(cursor: sqlite3.Cursor) -> None:
    """Agrega columnas faltantes a tablas existentes (migraciones suaves)."""
    cursor.execute("PRAGMA table_info(movements)")
    columns = [col[1] for col in cursor.fetchall()]

    real_cols = ['precio_unitario', 'total_bs', 'lotes_equiv']
    for col in real_cols:
        if col not in columns:
            cursor.execute(f'ALTER TABLE movements ADD COLUMN {col} REAL DEFAULT 0')

    text_cols = ['nro_nota', 'concepto', 'nro_factura']
    for col in text_cols:
        if col not in columns:
            cursor.execute(f'ALTER TABLE movements ADD COLUMN {col} TEXT')

    for fk_col in ['cliente_id', 'proveedor_id']:
        if fk_col not in columns:
            cursor.execute(f'ALTER TABLE movements ADD COLUMN {fk_col} INTEGER')

    cursor.execute("PRAGMA table_info(clients)")
    columns_c = [col[1] for col in cursor.fetchall()]
    if 'nit_ci' not in columns_c:
        cursor.execute('ALTER TABLE clients ADD COLUMN nit_ci TEXT')


def _seed_default_recipes(cursor: sqlite3.Cursor) -> None:
    """Inserta las recetas por defecto si la tabla está vacía."""
    cursor.execute("SELECT COUNT(*) FROM recipes")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO recipes VALUES (?, ?, ?)", DEFAULT_RECIPES)
