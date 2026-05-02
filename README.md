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

El software está dividido en dos grandes "cerebros". Tienes que tener tanto la parte lógica encendida (FastAPI) como la parte gráfica encendida (Streamlit). Para ello, **necesitas abrir dos terminales separadas.**

### 1️⃣ Levantar el Servidor Backend (API)
Abre la primera terminal, asegúrate de activar tu entorno virtual (`source venv/bin/activate`) e inicia el motor con:
```bash
uvicorn src.main:app --port 8000
```
Tambien se puede usar la cli para ejecutar el servidor:
```
./manufacturer-cli serve --port 8000
```
Y en otra terminal: 
```
./provider-cli serve --port 8001
```
> El backend quedará ejecutándose en segundo plano exponiendo todos sus servicios en el puerto 8000. Además, puedes interactuar directamente con toda su documentación Swagger en `http://localhost:8000/docs`. No la cierres.

### 2️⃣ Levantar el Panel Visual (Dashboard Frontend)
Abre una **segunda terminal**, vuelve a activar el entorno y manda arrancar el renderizado web visual:
```bash
streamlit run factory-app/src/ui/app.py
```
> Tu navegador abrirá automáticamente el panel visual en `http://localhost:8501`.

---

## 🎮 Guía Rápida para Probar el Sistema (Mini-Tutorial)

Una vez en el dashboard del navegador `http://localhost:8501`:

1. Acabas de entrar en el **Día 0**. Notarás que aunque le des al botón `Advance Day`, se generan pedidos y caen a la cola (**Pending Manufacturing Orders**), pero automáticamente pasan de estado `pending` a `waiting_for_materials`. Esto ocurre porque tu **Inventario (tabla derecha)** está seco.
2. Vete al menú lateral de **Purchasing** (Compras). Selecciona uno de tus proveedores (por ejemplo, *Componentes ABC*) y selecciona algún producto para comprarle (Ej: *kit_piezas*). Fíjate en los Lead Times (algunos tardan 3 o incluso 7 días en llegar desde Europa/Asia). Dale a `Issue PO` para gastar el dinero.
3. Observa tu pequeña tabla de **Open Purchase Orders**. Se quedará ahí estática la "promesa de entrega" hasta que hayan pasado los días acordados.
4. Pulsa varias veces de nuevo **Advance Day**. En el instante en el que virtualmente cruces la fecha acordada (ej. `expected_delivery` = Día 4), un camión de mercancía descargará tu pedido y verás tu Stock inflarse por fin en la tabla de Inventario.
5. Inmediatamente, el cerebro de la fábrica de impresoras comprobará qué pedidos atascados (los *waiting_for_materials*) cumplen con las piezas recién llegadas, y deducirá individualmente placa por placa, cable por cable los sub-módulos hasta vaciarte las estanterías (pasando esos pedidos a `in_progress` o `completed`).
6. Observa la gráfica animada **📈 Charts** al fondo del todo: muestra numéricamente tu evolución y desempeño logístico conforma más entregas despachas en el tiempo.
