# config/settings.py
# Configuración central del sistema

DB_NAME = "database.sqlite"
BIDONES_POR_LOTE = 92
LOTES_ALERT_THRESHOLD = 10

RAW_MATERIALS = [
    "Bicarbonato de Sodio",
    "Cloruro de Sodio",
    "Ácido Acético",
    "Cloruro de Calcio",
    "Cloruro de Magnesio",
    "Cloruro de Potasio",
]

DEFAULT_RECIPES = [
    ("SOLUCION BASICA", "Bicarbonato de Sodio", 75.6),
    ("SOLUCION ÁCIDA", "Cloruro de Sodio", 193.30),
    ("SOLUCION ÁCIDA", "Ácido Acético", 7.56),
    ("SOLUCION ÁCIDA", "Cloruro de Calcio", 6.93),
    ("SOLUCION ÁCIDA", "Cloruro de Magnesio", 3.15),
    ("SOLUCION ÁCIDA", "Cloruro de Potasio", 4.68),
]
