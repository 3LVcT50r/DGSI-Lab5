# 🏭 Simulador Logístico: Fábrica de Impresoras 3D (DGSI-Lab5)

## 📖 ¿Qué es este proyecto?

Este proyecto es un simulador web de tipo "juego de gestión" basado en turnos diarios, donde tú tomas el control de una fábrica que ensambla y vende **impresoras 3D** (*P3D-Classic* y *P3D-Pro*). 

Se trata de un sistema transaccional donde convergen varios flujos vitales de gestión empresarial:
- **Flujo de Demanda:** Diariamente recibes aleatoriamente nuevos pedidos ("Manufacturing Orders") por parte de clientes según una curva normal parametrizada. 
- **Cadena de Suministro (Supply Chain):** Tú no fabricas las piezas de las impresoras (PCB, motores, extrusores), se las tienes que comprar a proveedores externos. Debes jugar contando con sus tiempos logísticos de entrega (*Lead Times*).
- **Control de Inventario y MRP:** Un motor logístico lee la lista de componentes (BOM - *Bill of Materials*), reserva las partes y frena tus pedidos a estado `waiting_for_materials` (esperando materiales) cuando sufres de escasez (Stockout).
- **Capacidad de Fábrica:** Tienes la limitación realista de poder ensamblar, como máximo, 10 impresoras por día.

El sistema completo evolucionó hacia una **Arquitectura Distribuida de Microservicios**. La fábrica y el proveedor corren en procesos separados y se comunican vía REST APIs. La capa de servicios usa **FastAPI** y el dashboard interactivo usa **Streamlit**. Todo el backend funciona gracias a modelos transaccionales de **SQLAlchemy** respaldados por bases de datos SQLite persistentes e independientes para cada servicio.

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

## 🕹️ Cómo Ejecutar el Simulador Distribuido

El software está dividido ahora en tres procesos independientes (Microservicios). Necesitas tener la terminal del Proveedor, la de la Fábrica y la del Panel Gráfico funcionando en paralelo. Para ello, **necesitas abrir TRES terminales separadas.** Asegúrate de activar el entorno virtual (`source venv/bin/activate`) en todas ellas.

### 1️⃣ Inicializar y Levantar el Proveedor (Terminal 1)
Primero, cargamos la base de datos del proveedor con el catálogo de piezas:
```bash
python -m provider.cli import provider/seed-provider.json
```
Luego, levantamos su servidor REST:
```bash
python -m provider.cli serve
```
> Quedará ejecutándose en el puerto **8001**. (Documentación en `http://localhost:8001/docs`)

### 2️⃣ Levantar la Fábrica / Manufacturer (Terminal 2)
Arrancamos el servidor REST de la fábrica, que ya viene programado para conectarse al proveedor:
```bash
python -m src.cli serve
```
> Quedará ejecutándose en el puerto **8002**.

### 3️⃣ Levantar el Panel Visual / Dashboard (Terminal 3)
Mandamos arrancar el renderizado web visual:
```bash
streamlit run src/ui/app.py
```
> Tu navegador abrirá automáticamente el panel en `http://localhost:8501`.

---

## 🛠️ Comandos CLI (Modo Hacker)
Además del entorno gráfico, ambos servicios poseen potentes interfaces de línea de comandos (CLI) con `typer`:

- **Proveedor:** `python -m provider.cli --help` (ver catálogo, stock, avanzar el día del proveedor).
- **Fábrica:** `python -m src.cli --help` (comprar mercancía, avanzar el día de la fábrica, ver proveedores en red).

## 🎮 Guía Rápida para Probar el Sistema (Mini-Tutorial)

Una vez en el dashboard del navegador `http://localhost:8501`:

1. Acabas de entrar en el **Día 0**. Notarás que aunque le des al botón `Advance Day`, se generan pedidos y caen a la cola (**Pending Manufacturing Orders**), pero automáticamente pasan de estado `pending` a `waiting_for_materials`. Esto ocurre porque tu **Inventario (tabla derecha)** está seco.
2. Vete al menú lateral de **Purchasing** (Compras). Selecciona tu proveedor de red (por ejemplo, *ChipSupply Co*). Dale a `Issue PO` para encargar componentes. Esto mandará una petición HTTP en la vida real desde el microservicio de la Fábrica al del Proveedor.
3. Observa tu pequeña tabla de **Open Purchase Orders**. Se quedará ahí estática la "promesa de entrega" hasta que hayan pasado los días acordados según los tiempos del proveedor.
4. Para que el proveedor procese el envío y pasen los días logísticos, puedes avanzar el día en el propio proveedor vía terminal (`python -m provider.cli day advance`). O alternativamente, pulsa varias veces el botón **Advance Day** en tu panel web. En el instante en el que virtualmente cruces la fecha acordada (ej. `expected_delivery` = Día 4), un camión de mercancía descargará tu pedido vía REST API y verás tu Stock inflarse por fin en la tabla de Inventario.
5. Inmediatamente, el cerebro de la fábrica de impresoras comprobará qué pedidos atascados (los *waiting_for_materials*) cumplen con las piezas recién llegadas, y deducirá individualmente placa por placa, cable por cable los sub-módulos hasta vaciarte las estanterías (pasando esos pedidos a `in_progress` o `completed`).
6. Observa la gráfica animada **📈 Charts** al fondo del todo: muestra numéricamente tu evolución y desempeño logístico conforma más entregas despachas en el tiempo.
