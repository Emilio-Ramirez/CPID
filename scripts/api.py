# scripts/api.py
from flask import Flask, jsonify
import sqlite3
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DB_PATH = "database/empresa.db"


@app.route("/ventas/resumen_por_categoria", methods=["GET"])
def resumen_por_categoria():
    """Retorna total de unidades vendidas por categoría"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT p.categoria, SUM(v.cantidad) as total_unidades
                FROM ventas v
                JOIN productos p ON v.producto_id = p.producto_id
                GROUP BY p.categoria
                ORDER BY total_unidades DESC
            """)
            resultados = cursor.fetchall()

            if not resultados:
                return jsonify({"mensaje": "No hay datos disponibles"}), 200

            resumen = {categoria: int(total) for categoria, total in resultados}
            return jsonify(resumen)

    except sqlite3.Error as e:
        return jsonify({"error": "Error de base de datos"}), 500
    except Exception as e:
        return jsonify({"error": "Error interno del servidor"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
