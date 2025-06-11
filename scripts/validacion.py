# scripts/validacion.py
import sqlite3
import logging
import os
from datetime import datetime

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/alertas.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DataValidator:
    def __init__(self):
        self.db_path = "database/empresa.db"
        self.alertas = []

    def log_alerta(self, nivel, mensaje, detalle=""):
        """Registra una alerta"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alerta = f"[ALERTA] [{timestamp}] [{nivel}] {mensaje}"
        if detalle:
            alerta += f"\nDetalles: {detalle}"

        self.alertas.append((nivel, mensaje, detalle))

        if nivel == "ERROR":
            logger.error(mensaje + (" - " + detalle if detalle else ""))
        elif nivel == "WARNING":
            logger.warning(mensaje + (" - " + detalle if detalle else ""))
        else:
            logger.info(mensaje + (" - " + detalle if detalle else ""))

    def validar_duplicados_ventas(self):
        """Valida venta_id duplicados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
               SELECT venta_id, COUNT(*) as duplicados 
               FROM ventas 
               GROUP BY venta_id 
               HAVING COUNT(*) > 1
           """)
            duplicados = cursor.fetchall()

            if duplicados:
                self.log_alerta(
                    "ERROR",
                    f"Encontrados {len(duplicados)} venta_id duplicados",
                    f"IDs afectados: {[d[0] for d in duplicados]}",
                )
            else:
                self.log_alerta("INFO", "✓ Sin venta_id duplicados")

    def validar_cantidades(self):
        """Valida cantidades >= 0"""
        with sqlite3.connect(self.db_path) as conn:
            # Cantidades negativas
            cursor = conn.execute("SELECT COUNT(*) FROM ventas WHERE cantidad < 0")
            negativos = cursor.fetchone()[0]

            if negativos > 0:
                self.log_alerta("ERROR", f"{negativos} ventas con cantidad negativa")

            # Cantidades = 0 (warning)
            cursor = conn.execute("SELECT COUNT(*) FROM ventas WHERE cantidad = 0")
            ceros = cursor.fetchone()[0]

            if ceros > 0:
                self.log_alerta(
                    "WARNING",
                    f"{ceros} ventas con cantidad = 0 (posibles devoluciones)",
                )

            if negativos == 0 and ceros == 0:
                self.log_alerta("INFO", "✓ Todas las cantidades son válidas")

    def validar_productos_validos(self):
        """Valida que producto_id existan"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
               SELECT COUNT(*) 
               FROM ventas v 
               LEFT JOIN productos p ON v.producto_id = p.producto_id 
               WHERE p.producto_id IS NULL
           """)
            invalidos = cursor.fetchone()[0]

            if invalidos > 0:
                cursor = conn.execute("""
                   SELECT DISTINCT v.producto_id 
                   FROM ventas v 
                   LEFT JOIN productos p ON v.producto_id = p.producto_id 
                   WHERE p.producto_id IS NULL
               """)
                ids_invalidos = [row[0] for row in cursor.fetchall()]

                self.log_alerta(
                    "ERROR",
                    f"{invalidos} ventas con producto_id inválido",
                    f"IDs no encontrados: {ids_invalidos}",
                )
            else:
                self.log_alerta("INFO", "✓ Todos los producto_id son válidos")

    def validar_precios_productos(self):
        """Valida precios no negativos"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM productos WHERE precio_unitario < 0"
            )
            negativos = cursor.fetchone()[0]

            if negativos > 0:
                self.log_alerta("ERROR", f"{negativos} productos con precio negativo")
            else:
                self.log_alerta("INFO", "✓ Todos los precios son válidos")

    def validar_clientes_validos(self):
        """Valida que cliente_id existan"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
               SELECT COUNT(*) 
               FROM ventas v 
               LEFT JOIN clientes c ON v.cliente_id = c.cliente_id 
               WHERE c.cliente_id IS NULL
           """)
            invalidos = cursor.fetchone()[0]

            if invalidos > 0:
                cursor = conn.execute("""
                   SELECT DISTINCT v.cliente_id 
                   FROM ventas v 
                   LEFT JOIN clientes c ON v.cliente_id = c.cliente_id 
                   WHERE c.cliente_id IS NULL 
                   LIMIT 10
               """)
                ids_invalidos = [row[0] for row in cursor.fetchall()]

                self.log_alerta(
                    "ERROR",
                    f"{invalidos} ventas con cliente_id inválido",
                    f"Ejemplos: {ids_invalidos}",
                )
            else:
                self.log_alerta("INFO", "✓ Todos los cliente_id son válidos")

    def validar_fechas_futuras(self):
        """Valida fechas no futuras (validación adicional)"""
        hoy = datetime.now().strftime("%Y-%m-%d")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM ventas 
                WHERE fecha_venta > ?
            """,
                (hoy,),
            )
            futuras = cursor.fetchone()[0]

            if futuras > 0:
                self.log_alerta(
                    "WARNING",
                    f"{futuras} ventas con fechas futuras (hoy: {hoy})",
                    "Revisar si son válidas",
                )
            else:
                self.log_alerta("INFO", f"✓ Sin ventas con fechas futuras (hoy: {hoy})")

    def validar_stock_negativo(self):
        """Valida stock no negativo (validación adicional)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM inventario WHERE stock_actual < 0"
            )
            negativos = cursor.fetchone()[0]

            if negativos > 0:
                self.log_alerta("ERROR", f"{negativos} registros con stock negativo")
            else:
                self.log_alerta("INFO", "✓ Sin stock negativo")

    def validar_estructura_bd(self):
        """Valida existencia de tablas (validación adicional)"""
        tablas_requeridas = ["productos", "clientes", "ventas", "inventario"]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
               SELECT name FROM sqlite_master 
               WHERE type='table' AND name NOT LIKE 'sqlite_%'
           """)
            tablas_existentes = [row[0] for row in cursor.fetchall()]

            faltantes = set(tablas_requeridas) - set(tablas_existentes)

            if faltantes:
                self.log_alerta("CRITICAL", f"Tablas faltantes: {list(faltantes)}")
            else:
                self.log_alerta("INFO", "✓ Estructura de BD completa")

    def generar_resumen(self):
        """Genera resumen de validaciones"""
        conteo = {"INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}

        for nivel, _, _ in self.alertas:
            conteo[nivel] += 1

        logger.info("=== RESUMEN DE VALIDACIONES ===")
        logger.info(f"Total alertas: {len(self.alertas)}")
        for nivel, cantidad in conteo.items():
            if cantidad > 0:
                logger.info(f"{nivel}: {cantidad}")

        if conteo["ERROR"] == 0 and conteo["CRITICAL"] == 0:
            logger.info("ESTADO: APROBADO ✓")
        else:
            logger.info("ESTADO: REQUIERE ATENCIÓN ⚠️")

    def ejecutar_validaciones(self):
        """Ejecuta todas las validaciones"""
        logger.info("=== INICIANDO VALIDACIONES ===")

        self.validar_estructura_bd()
        self.validar_duplicados_ventas()
        self.validar_cantidades()
        self.validar_productos_validos()
        self.validar_precios_productos()
        self.validar_clientes_validos()
        self.validar_fechas_futuras()
        self.validar_stock_negativo()

        self.generar_resumen()
        logger.info("=== VALIDACIONES COMPLETADAS ===")


if __name__ == "__main__":
    validator = DataValidator()
    validator.ejecutar_validaciones()
