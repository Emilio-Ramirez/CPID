# README.md - Sistema de Procesamiento de Datos

## Descripción

Sistema completo de ETL para datos de ventas con validación automatizada y API REST.

## Estructura del Proyecto

```
proyecto/
├── data/                    # Archivos CSV originales
├── scripts/                 # Scripts de procesamiento
│   ├── procesamiento.py    # Tarea 1: ETL y carga BD
│   ├── validacion.py       # Tarea 2: Validaciones
│   └── api.py              # Tarea 3: API REST
├── database/               # Base de datos generada
│   └── empresa.db          # SQLite
├── logs/                   # Logs del sistema
│   ├── procesamiento.log   # Logs ETL
│   └── alertas.log         # Logs validaciones
└── requirements.txt        # Dependencias
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

### Tarea 1: Procesamiento y Carga

```bash
python scripts/procesamiento.py
```

**Funciones:**

- Limpia y homologa formatos de fecha (YYYY-MM-DD)
- Normaliza IDs a enteros (prod001 → 1)
- Enriquece ventas con ciudades de clientes
- Crea esquema normalizado SQLite
- Carga 10 productos, 20 clientes, 5,407 ventas

### Tarea 2: Validaciones

```bash
python scripts/validacion.py
```

**Validaciones implementadas:**

- Sin venta_id duplicados ✓
- Cantidades ≥ 0 (permite 0 como devoluciones)
- producto_id válidos en FK
- Precios no negativos ✓
- cliente_id válidos en FK
- **Adicional:** Fechas futuras (1,479 detectadas)
- **Adicional:** Stock negativo ✓
- **Adicional:** Estructura BD ✓

### Tarea 3: API REST

```bash
python scripts/api.py
```

## API Endpoint

### GET /ventas/resumen_por_categoria

**URL:** `http://localhost:5000/ventas/resumen_por_categoria`  
**Parámetros:** Ninguno

**Respuesta exitosa (200):**

```json
{
  "Electronicos": 2957,
  "Ropa": 3042,
  "Accesorios": 2942,
  "Almacenamiento": 988
}
```

**Errores:**

- `500`: Error de base de datos

## Supuestos y Decisiones

### Esquema de Datos

- **SQLite:** Elegido por simplicidad y portabilidad
- **IDs numéricos:** Más eficientes que strings
- **LEFT JOIN:** Preserva ventas aunque falten datos de cliente

### Manejo de Datos Faltantes

- **Cantidad = 0:** Válida (devoluciones), genera WARNING
- **Clientes inexistentes:** Ciudad "ciudad_desconocida"
- **Fechas futuras:** Genera WARNING (posibles datos de prueba)

### Calidad de Datos

- **Productos válidos:** 10/10 ✓
- **Clientes válidos:** 20/20 ✓
- **Ventas procesadas:** 5,407/5,500 (98.3%)
- **Inventario procesado:** 4,900/5,000 (98%)

**Estado del sistema:** REQUIERE ATENCIÓN ⚠️ (fechas futuras y producto_id=11 faltante)

