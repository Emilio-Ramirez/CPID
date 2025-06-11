# scripts/validar_y_enviar.py
import os
import logging
import time
import fcntl  # Para Linux/Mac
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validar_y_enviar():
    """Script con bloqueo atómico"""
    lock_file = "proceso.lock"

    try:
        # Bloqueo atómico
        lock_fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(lock_fd, "w") as f:
            f.write(f"PID: {os.getpid()}\n{datetime.now()}")
        logger.info("🔒 Lock adquirido")

        # Validaciones
        report_file = "reporte_mensual.csv"
        if not os.path.exists(report_file):
            logger.error(f"❌ {report_file} no encontrado")
            return False

        mod_date = date.fromtimestamp(os.path.getmtime(report_file))
        if mod_date != date.today():
            logger.error(f"❌ Archivo no es de hoy: {mod_date}")
            return False

        logger.info("✅ Validaciones OK")

        # Procesamiento simulado
        logger.info("🔄 Procesando...")
        time.sleep(3)
        logger.info("✅ Completado")

    except FileExistsError:
        logger.error("❌ Proceso ya en ejecución")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)
            logger.info("🔓 Lock liberado")


if __name__ == "__main__":
    validar_y_enviar()
