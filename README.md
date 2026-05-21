# 🏭 Simulador Logístico: Fábrica de Impresoras 3D (DGSI-Lab5)

## 📖 ¿Qué es este proyecto?

Este proyecto es un simulador web de tipo "juego de gestión" basado en turnos diarios, donde tú tomas el control de una fábrica que ensambla y vende **impresoras 3D** (*P3D-Classic* y *P3D-Pro*). 

Se trata de un sistema transaccional donde convergen varios flujos vitales de gestión empresarial:
- **Flujo de Demanda:** Diariamente recibes aleatoriamente nuevos pedidos ("Manufacturing Orders") por parte de clientes según una curva normal parametrizada. 
- **Cadena de Suministro (Supply Chain):** Tú no fabricas las piezas de las impresoras (PCB, motores, extrusores), se las tienes que comprar a proveedores externos. Debes jugar contando con sus tiempos logísticos de entrega (*Lead Times*).
- **Control de Inventario y MRP:** Un motor logístico lee la lista de componentes (BOM - *Bill of Materials*), reserva las partes y frena tus pedidos a estado `waiting_for_materials` (esperando materiales) cuando sufres de escasez (Stockout).
- **Capacidad de Fábrica:** Tienes la limitación realista de poder ensamblar, como máximo, 10 impresoras por día.

El sistema completo usa una arquitectura **FastAPI** robusta para manejar la capa de servicios y **Streamlit** para que disfrutes de una interfaz moderna conectada mediante una API REST. Todo el backend funciona gracias a modelos transaccionales de **SQLAlchemy** respaldados por una base de datos local SQLite persistente.

---

## 🛠️ Requisitos Previos

- **Python 3.10 o superior** (Desarrollado y probado en entorno Python 3.12).
- Tener instalado `pip` e idealmente un creador de entornos virtuales tipo `venv`.

---

## 🚀 Instalación y Preparación

Abre tu terminal en la carpeta principal del proyecto (donde estás leyendo este README) y ejecuta los siguientes comandos para encapsular todo e instalar las librerías:

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar el entorno virtual
# En Linux/macOS:
source venv/bin/activate
# En Windows (Powershell):
# venv\Scripts\Activate.ps1

# 3. Instalar librerías
pip install -r requirements.txt
```

*(Nota: Al arrancarse el sistema por la primera vez, el backend auto-generará su base de datos `data/database.sqlite` y leerá `data/default_config.json` para pre-poblar los productos y proveedores).*

---

## 🕹️ Cómo Ejecutar el Simulador

El software ahora está diseñado como una arquitectura de microservicios distribuidos. Necesitas ejecutar cada componente de la cadena de suministro por separado para que puedan comunicarse a través de la red.

### 1️⃣ Levantar los Microservicios

Abre tres terminales independientes. En cada una, asegúrate de activar tu entorno virtual (`source venv/bin/activate`) e inicia el servicio correspondiente en su puerto asignado:

**Terminal 1 (Provider / Proveedor de Piezas):**
```bash
./provider-cli serve --port 8001
```

**Terminal 2 (Manufacturer / Fábrica de Impresoras):**
```bash
./manufacturer-cli serve --port 8002
```

**Terminal 3 (Retailer / Tienda Minorista):**
```bash
./retailer-cli serve --port 8003
```

*(Opcional: Si lo deseas, puedes seguir usando la interfaz gráfica de la fábrica en otra terminal ejecutando `streamlit run factory-app/src/ui/app.py` en el puerto 8501).*

---

## 🎮 El Turn Engine (Motor de Turnos)

Una vez que los tres microservicios (Proveedor, Fabricante y Minorista) están funcionando en segundo plano, la simulación de la cadena de suministro se avanza de forma sincronizada mediante el **Turn Engine**.

El Turn Engine es un script que inyecta la demanda de clientes en la tienda minorista y luego orquesta que cada microservicio tome sus decisiones diarias antes de avanzar todos al siguiente día.

Para ejecutar una simulación de varios días (por ejemplo, 5 días), abre una cuarta terminal, activa tu entorno y ejecuta:

```bash
python turn_engine.py config/sim.json scenarios/smoke-test.json 5
```

En la salida de la consola verás cómo el Turn Engine avanza día a día: generará pedidos de usuarios finales, ejecutará el turno de cada agente involucrado, y hará avanzar las manecillas del tiempo en las bases de datos de todos los microservicios simultáneamente a través de sus APIs REST `v1`.
