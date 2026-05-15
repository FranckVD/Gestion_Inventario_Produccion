# Sistema de Gestión de Inventarios y Producción

Esta es una aplicación integral desarrollada en **Python** con **Streamlit**, diseñada para la gestión eficiente de inventarios en el rubro de **LABORATORIOS DE SOLUCIONES QUIMICAS** de Materia Prima (MP), control de producción de Productos Terminados (PT) y seguimiento de ventas/facturación.

## 🚀 Características Principales

*   **📈 Dashboard Gerencial**: Visualización en tiempo real de métricas clave, utilidades brutas, tendencias de ventas y niveles de stock crítico.
*   **📦 Gestión de Materia Prima**: Registro de compras, historial de proveedores y control de ingresos.
*   **⚗️ Control de Producción**: Registro de lotes de producción con descuento automático de insumos basado en recetas predefinidas.
*   **📑 Facturación y Ventas**: Gestión de salidas de productos, registro de clientes y seguimiento de notas de entrega.
*   **📋 Kardex Valorado**: Historial detallado por material utilizando el método de **Costo Promedio Ponderado**.
*   **⚙️ Configuración**: Ajustes de saldos iniciales y mantenimiento de la base de datos.

## 🛠️ Tecnologías Utilizadas

*   **Lenguaje**: Python 3.12+
*   **Interfaz de Usuario**: [Streamlit](https://streamlit.io/)
*   **Procesamiento de Datos**: Pandas
*   **Base de Datos**: SQLite
*   **Visualización**: Altair (Gráficos interactivos)
*   **Gestor de Paquetes**: uv

## 📂 Estructura del Proyecto

```text
ProjectStreamlit/
├── app.py                # Punto de entrada y orquestador de navegación
├── config/               # Configuraciones globales y constantes
├── database/             # Conexión y repositorios SQL (Acceso a datos)
├── pages/                # Módulos individuales de la aplicación (UI)
├── services/             # Lógica de negocio y servicios de inventario
├── database.sqlite       # Base de datos local
└── pyproject.toml        # Dependencias del proyecto
```

## ⚙️ Instalación y Ejecución

1.  **Clonar el repositorio** (o descargar los archivos).
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    # O si usas uv:
    uv sync
    ```
3.  **Ejecutar la aplicación**:
    ```bash
    uv run streamlit run app.py
    ```

## 💡 Notas de Uso

*   Al iniciar por primera vez, el sistema solicitará crear la base de datos inicial.
*   La navegación se realiza a través del menú lateral izquierdo, organizado por secciones (Operaciones, Administración y Configuración).
*   Todos los cálculos de costos en el Kardex se basan en el valor neto (87%) tras la compra de materia prima.

---
Sistema personal de gestión optimizada de recursos y producción desarrollado por `FranckVD`, para visualizar la app vé a [gestiónInventario]([https://streamlit.io/](https://gestioninventarioapp.streamlit.app/)).
