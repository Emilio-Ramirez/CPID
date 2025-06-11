# scripts/procesamiento.py
import pandas as pd
import sqlite3
import logging
import os
from datetime import datetime
import re

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/procesamiento.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self):
        self.db_path = "database/empresa.db"
        os.makedirs("database", exist_ok=True)

    def clean_productos(self, df):
        """Limpia y normaliza datos de productos"""
        logger.info("Limpiando productos...")

        # Extraer solo números del producto_id
        df["producto_id"] = df["producto_id"].str.extract(r"(\d+)")[0].astype(int)

        # Normalizar nombres y categorías
        df["nombre_producto"] = df["nombre_producto"].str.strip()
        df["categoria"] = df["categoria"].str.strip()

        # Validar precios
        df = df[df["precio_unitario"] >= 0]

        # Eliminar duplicados
        df = df.drop_duplicates(subset=["producto_id"])

        return df

    def clean_clientes(self, df):
        """Limpia y normaliza datos de clientes"""
        logger.info("Limpiando clientes...")

        # Extraer solo números del cliente_id
        df["cliente_id"] = df["cliente_id"].str.extract(r"(\d+)")[0].astype(int)

        # Limpiar nombres y ciudades
        df["nombre"] = df["nombre"].str.strip()
        df["ciudad"] = df["ciudad"].str.strip()

        # Eliminar duplicados y nulos
        df = df.dropna(subset=["cliente_id"]).drop_duplicates(subset=["cliente_id"])

        return df

    def clean_ventas(self, df):
        """Limpia y normaliza datos de ventas"""
        logger.info("Limpiando ventas...")

        # Extraer números de los IDs
        df["venta_id"] = df["venta_id"].str.extract(r"(\d+)")[0].astype(int)
        df["producto_id"] = df["producto_id"].str.extract(r"(\d+)")[0].astype(int)
        df["cliente_id"] = df["cliente_id"].str.extract(r"(\d+)")[0].astype(int)

        # Limpiar fechas
        df["fecha_venta"] = df["fecha_venta"].apply(self.parse_date)

        # Validar cantidades
        df = df[df["cantidad"] >= 0]

        # Eliminar registros con datos faltantes
        df = df.dropna(subset=["venta_id", "producto_id", "cliente_id", "fecha_venta"])

        return df

    def clean_inventario(self, df):
        """Limpia y normaliza datos de inventario"""
        logger.info("Limpiando inventario...")

        # Extraer números del producto_id
        df["producto_id"] = df["producto_id"].str.extract(r"(\d+)")[0].astype(int)

        # Limpiar fechas
        df["fecha_snapshot"] = df["fecha_snapshot"].apply(self.parse_date)

        # Validar stock
        df = df[df["stock_actual"] >= 0]
        df = df.dropna(subset=["producto_id", "fecha_snapshot"])

        return df

    def parse_date(self, date_str):
        """Parsea múltiples formatos de fecha"""
        if pd.isna(date_str):
            return None

        date_str = str(date_str).strip()

        # Formato: YYYY-MM-DD
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return date_str

        # Formato: YYYYMMDD
        if re.match(r"^\d{8}$", date_str):
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

        # Formato: DD - Month - YYYY
        if " - " in date_str:
            try:
                return datetime.strptime(date_str, "%d - %B - %Y").strftime("%Y-%m-%d")
            except:
                pass

        logger.warning(f"Formato de fecha no reconocido: {date_str}")
        return None

    def enrich_ventas(self, ventas_df, clientes_df):
        """Enriquece ventas con datos de ciudad"""
        logger.info("Enriqueciendo ventas con ciudades...")

        # LEFT JOIN para preservar todas las ventas
        result = ventas_df.merge(
            clientes_df[["cliente_id", "ciudad"]], on="cliente_id", how="left"
        )

        # Rellenar ciudades faltantes
        result["ciudad"] = result["ciudad"].fillna("ciudad_desconocida")

        missing_cities = result["ciudad"].eq("ciudad_desconocida").sum()
        if missing_cities > 0:
            logger.warning(f"{missing_cities} ventas sin datos de ciudad del cliente")

        return result

    def create_schema(self):
        """Crea el esquema de la base de datos"""
        logger.info("Creando esquema de base de datos...")

        schema_sql = """
        -- Eliminar tablas si existen
        DROP TABLE IF EXISTS ventas;
        DROP TABLE IF EXISTS inventario;
        DROP TABLE IF EXISTS productos;
        DROP TABLE IF EXISTS clientes;
        
        CREATE TABLE productos (
            producto_id INTEGER PRIMARY KEY NOT NULL,
            nombre_producto TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio_unitario REAL NOT NULL CHECK (precio_unitario >= 0)
        );

        CREATE TABLE clientes (
            cliente_id INTEGER PRIMARY KEY NOT NULL,
            nombre TEXT NOT NULL,
            edad INTEGER,
            ciudad TEXT NOT NULL
        );

        CREATE TABLE ventas (
            venta_id INTEGER PRIMARY KEY NOT NULL,
            producto_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            fecha_venta DATE NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
            ciudad TEXT NOT NULL,
            FOREIGN KEY (producto_id) REFERENCES productos(producto_id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
        );
        
        -- Tabla de inventario
        CREATE TABLE inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id TEXT NOT NULL,
            fecha_snapshot DATE NOT NULL,
            stock_actual INTEGER NOT NULL CHECK (stock_actual >= 0),
            FOREIGN KEY (producto_id) REFERENCES productos(producto_id)
        );
        
        -- Índices para rendimiento
        CREATE INDEX idx_ventas_producto ON ventas(producto_id);
        CREATE INDEX idx_ventas_cliente ON ventas(cliente_id);
        CREATE INDEX idx_ventas_fecha ON ventas(fecha_venta);
        CREATE INDEX idx_inventario_producto ON inventario(producto_id);
        CREATE INDEX idx_inventario_fecha ON inventario(fecha_snapshot);
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)

        logger.info("Esquema creado exitosamente")

    def load_to_database(self, productos_df, clientes_df, ventas_df, inventario_df):
        """Carga datos a la base de datos"""
        logger.info("Cargando datos a la base de datos...")

        with sqlite3.connect(self.db_path) as conn:
            # Cargar en orden (por foreign keys)
            productos_df.to_sql("productos", conn, if_exists="append", index=False)
            clientes_df.to_sql("clientes", conn, if_exists="append", index=False)
            ventas_df.to_sql("ventas", conn, if_exists="append", index=False)
            inventario_df.to_sql("inventario", conn, if_exists="append", index=False)

        logger.info("Datos cargados exitosamente")

    def process_all(self):
        """Ejecuta el procesamiento completo"""
        logger.info("=== INICIANDO PROCESAMIENTO DE DATOS ===")

        try:
            # 1. Leer datos
            productos_df = pd.read_csv("productos.csv")
            clientes_df = pd.read_csv("datos.csv")
            ventas_df = pd.read_csv("ventas.csv")
            inventario_df = pd.read_csv("inventario.csv")

            logger.info(
                f"Datos originales - Productos: {len(productos_df)}, Clientes: {len(clientes_df)}, Ventas: {len(ventas_df)}, Inventario: {len(inventario_df)}"
            )

            # 2. Limpiar datos
            productos_clean = self.clean_productos(productos_df)
            clientes_clean = self.clean_clientes(clientes_df)
            ventas_clean = self.clean_ventas(ventas_df)
            inventario_clean = self.clean_inventario(inventario_df)

            # 3. Enriquecer ventas
            ventas_enriched = self.enrich_ventas(ventas_clean, clientes_clean)

            logger.info(
                f"Datos procesados - Productos: {len(productos_clean)}, Clientes: {len(clientes_clean)}, Ventas: {len(ventas_enriched)}, Inventario: {len(inventario_clean)}"
            )

            # 4. Crear esquema y cargar datos
            self.create_schema()
            self.load_to_database(
                productos_clean, clientes_clean, ventas_enriched, inventario_clean
            )

            logger.info("=== PROCESAMIENTO COMPLETADO EXITOSAMENTE ===")

        except Exception as e:
            logger.error(f"Error en procesamiento: {str(e)}")
            raise


if __name__ == "__main__":
    processor = DataProcessor()
    processor.process_all()
