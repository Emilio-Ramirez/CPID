# README.md - Sistema de Procesamiento de Datos

## Descripción

Sistema completo de ETL para datos de ventas con validación automatizada y API REST.

### Estructura del Proyecto

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

### 1: Procesamiento y Carga

```bash
python scripts/procesamiento.py
```

**Funciones:**

- Limpia y homologa formatos de fecha (YYYY-MM-DD)
- Normaliza IDs a enteros (prod001 → 1)
- Enriquece ventas con ciudades de clientes
- Crea esquema normalizado SQLite
- Carga 10 productos, 20 clientes, 5,407 ventas

---

### Tarea 2: Validaciones

---

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

### Evolución del Sistema de Alertas en Producción

---

### **Estado Actual**

- Logs estructurados en `alertas.log`
- Alertas en consola con severidad

### **Evolución Productiva**

#### **1. Notificaciones Automáticas**

- **Slack/Teams**: Alertas WARNING y ERROR
- **Email**: Solo CRITICAL al equipo DevOps
- **PagerDuty**: Incidentes automáticos para fallos críticos

#### **2. Monitoreo Visual**

- **Grafana**: Dashboards con métricas de validación
- **ELK Stack**: Búsqueda y análisis de logs históricos

#### **3. Respuesta Automática**

- **Auto-remediation**: Corrección automática de errores comunes
- **Circuit breaker**: Pausa procesos tras fallos repetidos
- **Escalamiento**: Notifica manager si >3 CRITICAL en 1 hora

#### **4. Contexto Enriquecido**

- **Impacto**: Cuantifica registros afectados y pérdida estimada
- **Correlación**: Relaciona múltiples alertas del mismo origen
- **Runbooks**: Enlaces automáticos a guías de solución

---

### Tarea 3: API REST

---

```bash
python scripts/api.py
```

#### GET /ventas/resumen_por_categoria

**URL:** <http://localhost:5000/ventas/resumen_por_categoria>  
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

### Supuestos y Decisiones

---

#### Esquema de Datos

- **SQLite:** Elegido por simplicidad y portabilidad
- **IDs numéricos:** Más eficientes que strings
- **LEFT JOIN:** Preserva ventas aunque falten datos de cliente

#### Manejo de Datos Faltantes

- **Cantidad = 0:** Válida (devoluciones), genera WARNING
- **Clientes inexistentes:** Ciudad "ciudad_desconocida"
- **Fechas futuras:** Genera WARNING (posibles datos de prueba)

#### Calidad de Datos

- **Productos válidos:** 10/10 ✓
- **Clientes válidos:** 20/20 ✓
- **Ventas procesadas:** 5,407/5,500 (98.3%)
- **Inventario procesado:** 4,900/5,000 (98%)

**Estado del sistema:** REQUIERE ATENCIÓN ⚠️ (fechas futuras y producto_id=11 faltante)

---

### Tarea 4: Carga AWS S3 (OPCIONAL)

---

```bash
python scripts/aws_upload.py
```

**Configuración:**

- Variables de entorno en `.env`
- Usuario IAM: `CSV_Uploader` con permisos de escritura

### **Consideraciones de Producción:**

---

### 1. Seguridad de Credenciales

**IAM Roles vs Access Keys:**

- **Producción:** IAM Roles (temporales, rotación automática)
- **Desarrollo:** Access Keys en variables de entorno
- **Gestión:** AWS Secrets Manager + rotación automática
- **Principio:** Menor privilegio (solo permisos necesarios)

### 2. Automatización Diaria

**Opción A - Serverless:**

- Lambda función + EventBridge (cron schedule)
- Sin gestión de infraestructura
- Escalable y costo-efectivo

**Opción B - Contenedores:**

- ECS/Fargate + EventBridge
- Mayor control del entorno
- Para procesos complejos

### 3. Manejo Robusto de Errores

- **Reintentos:** Exponential backoff
- **Monitoreo:** CloudWatch + SNS alertas
- **Logs:** Structured logging con contexto
- **Dead Letter Queue:** Para fallos persistentes

### 4. Archivos Grandes (>5GB)

- **Multipart upload:** Paralelo, recuperable
- **Streaming:** Procesar sin cargar en memoria
- **Compresión:** Parquet/gzip para eficiencia
- **Transfer Acceleration:** ones:\*\* ACID compliance
- **Orquestadores:** Airflow, Prefect con manejo nativo de concurrencia
- **Servicios de cola:** SQS/RabbitMQ para serialización

---

### Tarea 5: Monitoreo y Bloqueo

---

```bash
python scripts/validar_y_enviar.py
```

**Funcionalidades:**

- ✅ Bloqueo atómico con `os.O_EXCL`
- ✅ Verificación de existencia de archivo
- ✅ Validación de frescura (modificado hoy)
- ✅ Limpieza garantizada con `finally`

**Limitaciones del bloqueo actual:**

- **Proceso zombie:** Lock persiste si el proceso muere abruptamente
- **Sin timeout:** No hay expiración automática del lock
- **Monousuario:** Solo funciona en una máquina

**Alternativas para producción:**

- **Redis locks:** Distribuidos con TTL automático
- **DB transacciones:** ACID compliance
- **Orquestadores:** Airflow, Prefect con manejo nativo de concurrencia
- **Servicios de cola:** SQS/RabbitMQ para serialización
