# 3D Printer Factory Simulator

Sistema de simulación discreta de producción de una fábrica de impresoras 3D. Permite gestionar inventario, capacidad de producción, pedidos de compra y demanda estocástica.

## 🚀 Inicio Rápido

### Opción 1: Setup Automático (Recomendado)

**Windows:**
```bash
# Ejecuta el script de configuración
setup.bat
```

**Linux/Mac:**
```bash
# Haz el script ejecutable y ejecútalo
chmod +x setup.sh
./setup.sh
```

### Opción 2: Setup Manual

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Ejecutar la Aplicación

### Método 1: Ejecución Completa (Backend + Frontend)

**Paso 1: Iniciar el Backend (API)**
```bash
# En una terminal/consola separada
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

**Paso 2: Iniciar el Frontend (UI)**
```bash
# En otra terminal/consola separada
streamlit run src/ui/app.py
```

### Método 2: Ejecución Simplificada con Scripts

**Windows:**
```bash
# Ejecutar backend
start_backend.bat

# En otra terminal, ejecutar frontend
start_frontend.bat
```

**Linux/Mac:**
```bash
# Ejecutar backend
./start_backend.sh

# En otra terminal, ejecutar frontend
./start_frontend.sh
```

## 📋 URLs de Acceso

Una vez ejecutándose ambos servicios:

- **API Backend:** http://127.0.0.1:8000
- **Documentación API (Swagger):** http://127.0.0.1:8000/docs
- **Interfaz Web (Streamlit):** http://localhost:8501
- **Health Check:** http://127.0.0.1:8000/health

## 🛠️ Comandos Manuales de Consola

### Backend (FastAPI)

```bash
# Ejecutar servidor de desarrollo con recarga automática
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Ejecutar servidor de producción
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

# Ejecutar con configuración específica
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --log-level info
```

### Frontend (Streamlit)

```bash
# Ejecutar aplicación Streamlit
streamlit run src/ui/app.py

# Ejecutar en modo headless (sin navegador)
streamlit run src/ui/app.py --server.headless true

# Ejecutar en puerto específico
streamlit run src/ui/app.py --server.port 8502
```

### Testing

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=src --cov-report=html

# Ejecutar tests específicos
pytest tests/test_simulation.py

# Ejecutar tests en modo verbose
pytest -v
```

### Desarrollo

```bash
# Formatear código
black src/
isort src/

# Verificar estilo de código
flake8 src/

# Verificar tipos (si tienes mypy configurado)
mypy src/
```

## 📁 Estructura del Proyecto

```
DGSI-Lab5/
├── src/
│   ├── main.py              # Punto de entrada FastAPI
│   ├── config.py            # Configuración de la aplicación
│   ├── database.py          # Configuración de base de datos
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Esquemas Pydantic
│   ├── api/
│   │   └── routes.py        # Endpoints REST API
│   ├── services/
│   │   ├── simulation.py    # Lógica de simulación
│   │   ├── inventory.py     # Gestión de inventario
│   │   ├── metrics.py       # Métricas históricas
│   │   └── initialization.py # Carga de datos iniciales
│   └── ui/
│       ├── app.py           # Aplicación Streamlit
│       └── charts.py        # Funciones de gráficos
├── tests/
│   └── test_*.py            # Tests unitarios
├── data/
│   ├── database.sqlite      # Base de datos SQLite
│   └── default_config.json  # Configuración inicial
├── requirements.txt          # Dependencias Python
└── README.md                # Este archivo
```

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
# Asegúrate de tener activado el entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstala dependencias
pip install -r requirements.txt
```

### Error: "Port already in use"
```bash
# Mata procesos usando el puerto
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Error: "Database not found"
```bash
# La base de datos se crea automáticamente al iniciar
# Si hay problemas, elimina el archivo de BD
rm data/database.sqlite
```

## 📊 Características

- ✅ Simulación discreta de eventos
- ✅ Gestión de inventario en tiempo real
- ✅ Sistema de órdenes de fabricación
- ✅ Pedidos de compra con lead times
- ✅ Dashboard interactivo con gráficos
- ✅ API REST completa
- ✅ Métricas históricas
- ✅ Persistencia en SQLite

## 🤝 Contribuir

1. Crea un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request
```
- **URL:** http://localhost:8501

### 3. Ejecutar Tests
```bash
python -m pytest tests/ -v
```

## 📁 Estructura del Proyecto

```
DGSI-Lab5/
├── src/
│   ├── main.py              # FastAPI app principal
│   ├── config.py            # Configuración (Pydantic Settings)
│   ├── database.py          # Conexión SQLAlchemy
│   ├── models.py            # Modelos de base de datos
│   ├── schemas.py           # Esquemas Pydantic
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # Endpoints REST API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── simulation.py    # Lógica de simulación
│   │   └── inventory.py     # Gestión de inventario
│   └── ui/
│       └── app.py           # Interfaz Streamlit
├── tests/
│   └── test_skeleton.py     # Tests básicos
├── data/
│   └── default_config.json  # Configuración inicial
├── requirements.txt          # Dependencias Python
├── setup.bat               # Script setup Windows
├── setup.sh                # Script setup Linux/Mac
└── README.md
```

## 🛠️ Tecnologías Utilizadas

- **Backend:** FastAPI + SQLAlchemy + Pydantic
- **Frontend:** Streamlit
- **Base de Datos:** SQLite
- **Testing:** pytest
- **Configuración:** python-dotenv

## 📋 API Endpoints

### Simulación
- `GET /api/v1/simulate/status` - Estado actual
- `POST /api/v1/simulate/advance` - Avanzar día
- `POST /api/v1/simulate/reset` - Reiniciar simulación

### Órdenes
- `POST /api/v1/orders/{id}/release` - Liberar orden
- `POST /api/v1/purchase-orders` - Crear orden de compra

### Estado
- `GET /api/v1/state/export` - Exportar estado JSON
- `POST /api/v1/state/import` - Importar estado JSON

## 🧪 Testing

```bash
# Ejecutar todos los tests
python -m pytest tests/

# Con cobertura
python -m pytest tests/ --cov=src

# Tests específicos
python -m pytest tests/test_skeleton.py -v
```

## 🔧 Configuración

El sistema usa variables de entorno. Crea un archivo `.env` en la raíz:

```env
APP_NAME=3D Printer Factory Simulator
DATABASE_URL=sqlite:///./data/database.sqlite
WAREHOUSE_CAPACITY=500
PRODUCTION_CAPACITY_PER_DAY=10
DEMAND_SEED=1234
```

## 📊 Modelo de Datos

- **Product:** Materiales y productos terminados
- **BOM:** Lista de materiales por producto
- **Supplier:** Proveedores con precios y tiempos de entrega
- **Inventory:** Niveles de stock actuales
- **ManufacturingOrder:** Órdenes de producción
- **PurchaseOrder:** Órdenes de compra
- **Event:** Log de eventos de simulación

## 🚀 Despliegue

### Desarrollo
```bash
# Backend + Frontend simultáneamente
# Terminal 1:
python -m uvicorn src.main:app --reload

# Terminal 2:
streamlit run src/ui/app.py
```

### Producción
```bash
# Solo backend (API)
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Con Gunicorn (recomendado para producción)
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🤝 Contribución

1. Crea una rama para tu feature
2. Ejecuta tests antes de commit
3. Sigue PEP 8 para estilo de código
4. Actualiza documentación según cambios

## 📝 Notas

- El sistema está en desarrollo activo
- Los servicios principales son placeholders que necesitan implementación
- La base de datos se crea automáticamente al iniciar la aplicación
