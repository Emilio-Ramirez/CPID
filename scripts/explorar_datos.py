# scripts/explorar_datos.py
import pandas as pd
import os


def explorar_csv():
    """Explora la estructura de todos los archivos CSV"""

    archivos = ["productos.csv", "ventas.csv", "inventario.csv", "datos.csv"]

    for archivo in archivos:
        ruta = f"data/{archivo}" if os.path.exists(f"data/{archivo}") else archivo

        if os.path.exists(ruta):
            print(f"\n=== {archivo.upper()} ===")
            df = pd.read_csv(ruta)
            print(f"Filas: {len(df)}")
            print(f"Columnas: {list(df.columns)}")
            print("Primeras 3 filas:")
            print(df.head(3))
            print("Tipos de datos:")
            print(df.dtypes)
            print("Valores nulos:")
            print(df.isnull().sum())
            print("-" * 50)
        else:
            print(f"No encontrado: {archivo}")


if __name__ == "__main__":
    explorar_csv()
