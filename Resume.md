# 📘 GUÍA MAESTRA: Simulación de Cadena de Suministro Multi-Agente (Labs 5 → 8)
> **Nota para la IA ejecutora:** Este documento es el plan maestro secuencial. Sigue el orden estricto. Cada fase depende de la anterior. Mantén `CLAUDE.md` y `docs/PRD.md` actualizados después de cada commit estable. Usa el flujo **PRD-First** y `claude --print` según se especifica.

---

## 🌍 CONFIGURACIÓN GLOBAL Y CONVENCIONES
| Aspecto | Especificación |
|---------|----------------|
| **Stack** | Python 3.11+, FastAPI + Pydantic, SQLite, Streamlit, `httpx`, `typer`/`click`, `matplotlib` |
| **CLI Pattern** | `<app>-cli <recurso> <acción> [args]` (Ej: `manufacturer-cli stock`) |
| **Puertos** | Provider: `8001` \| Manufacturer: `8002` \| Retailer: `8003` |
| **Gestión de Tiempo** | Cada app mantiene su propio `sim_day` en SQLite. Se avanza vía `POST /api/day/advance` o CLI. |
| **Regla de Oro** | **Nunca** llames a `day advance` desde un agente. El Turn Engine lo controla. |
| **Seguridad** | `.env` con `ANTHROPIC_API_KEY` y `ANTHROPIC_BASE_URL`. Nunca commitear `.env` o `*.db`. |
| **Logs** | Guardar output de agentes en `logs/day-XXX-role.log`. Añadir `logs/` a `.gitignore`. |

---

## 🛠️ FASE 1: LAB 5 — El Simulador Base (Vibe Coding)
### 🎯 Objetivo
Construir un simulador de producción de impresoras 3D en una sola app con UI (Streamlit), API REST (FastAPI) y lógica de simulación por turnos.

### 📐 Arquitectura & Modelo
- **Entidades:** `Product`, `BOMEntry`, `Supplier`, `Inventory`, `ManufacturingOrder`, `PurchaseOrder`, `Event`, `SimState`
- **Flujo Diario:** `Advance Day` → Genera demanda → Procesa producción (consume partes, respeta capacidad) → Recibe pedidos → Registra eventos.
- **UI (Streamlit):** Día actual + botón "Advance", tablas de pedidos/inventario/stock, panel de compras, gráficos (`matplotlib`).

### ✅ Pasos de Implementación
1. Inicializar repo: `mkdir printer-sim && cd printer-sim && git init`
2. Instalar deps: `pip install fastapi uvicorn pydantic sqlite3 streamlit matplotlib httpx typer`
3. Crear `CLAUDE.md` y `docs/PRD.md` usando el prompt PRD-First especificado en el lab.
4. Implementar modelos Pydantic y esquema SQLite.
5. Crear capa de servicios (`services/`) separada de API y UI.
6. Desarrollar endpoints REST (`/api/...`) y comandos CLI básicos.
7. Integrar Streamlit para visualizar y controlar la simulación.
8. Añadir `GET/POST` para JSON import/export de estado completo.

### 📦 Entregables Lab 5
- Repo con estructura base, `CLAUDE.md`, `docs/PRD.md`, `README.md`
- App funcionando: UI + REST + CLI + simulación diaria
- Reporte (3-5 págs) + Presentación (max 10 slides)

---

## 🔗 FASE 2: LAB 6 — El Proveedor y Comunicación REST
### 🎯 Objetivo
Crear la app `provider` (vendedora de partes) y modificar `manufacturer` para comprarle vía REST. Probar comunicación entre dos procesos independientes.

### 📐 Arquitectura
- **Provider (`:8001`)**: Catálogo, precios por tramos (`pricing_tiers`), lead times, stock, órdenes, eventos.
- **Manufacturer (`:8002`)**: Extiende Lab 5. Añade configuración de proveedor, cliente HTTP, seguimiento de órdenes de compra, polling en `day advance`.
- **Contrato REST**: Documentado automáticamente en `/docs`. No hay acceso directo a BDs cruzadas.

### 📡 Endpoints Clave
| App | Método | Ruta | Payload/Función |
|-----|--------|------|-----------------|
| Provider | `GET` | `/api/catalog` | Lista productos + tramos de precio |
| Provider | `GET` | `/api/stock` | Inventario actual |
| Provider | `POST`| `/api/orders` | `{"buyer": "...", "product_id": x, "quantity": y}` |
| Manufacturer | `GET` | `/api/purchases` | Lista órdenes salientes |
| Ambos | `POST`| `/api/day/advance` | Avanza simulación 1 día |

### 🔄 Lógica Crítica
- **Precios por volumen**: Ej: 1-9 unidades: 50€, 10-99: 35€, 100+: 25€.
- **Lead Time mínimo**: 1 día. `expected_delivery = current_day + lead_time_days`.
- **Avance de día (Provider)**: Mueve órdenes `pending` → `shipped` → `delivered` según `sim_day`. Registra en `events`.
- **Avance de día (Manufacturer)**: Hace polling al provider. Si `delivered`, suma a inventario local y marca orden como entregada.

### 📦 Entregables Lab 6
- Apps `provider/` y `manufacturer/` funcionando en puertos separados
- Escenario manual de 5 días ejecutado y verificado (inventario y logs coherentes)
- Reporte (2-3 págs) con diagrama de arquitectura, contrato REST y notas de vibe-coding

---

## ⚙️ FASE 3: LAB 7 — Minorista, Motor de Turnos y Primer Agente
### 🎯 Objetivo
Agregar la app `retailer`, construir el `turn_engine.py`, crear el primer skill file (`manufacturer-manager.md`) y ejecutar 1 día autónomo.

### 📐 Arquitectura de Cadena
```
Retailer (:8003) --[compra]--> Manufacturer (:8002) --[compra]--> Provider (:8001)
      ^                                      |
      |----[vende a clientes]----------------|
```

### 🏪 Retailer Specs
- **Modelo**: `Catalog`, `CustomerOrders`, `PurchaseOrders`, `Stock`, `SalesHistory`, `Events`
- **Reglas**: Cumple pedidos desde stock o backordea. Compra al manufacturer. Precio venta ≥ precio mayorista + 15%. Auto-cumple backorders cuando llega stock.
- **CLI/REST**: `retailer-cli serve --config retailer.json --port 8003`, endpoints `/api/catalog`, `/api/orders`, `/api/purchases`, `/api/day/advance`.

### ⚙️ Turn Engine (`turn_engine.py`)
Orden estricto por turno:
1. Leer señales del día (archivo de escenario)
2. Generar demanda determinista → `POST /api/orders` al retailer
3. Ejecutar decisiones del Retailer (stub o agente)
4. Ejecutar decisiones del Manufacturer (agente)
5. Ejecutar decisiones del Provider (stub o agente)
6. `POST /api/day/advance` a TODAS las apps
7. Guardar logs por rol/día

### 🧠 Primer Skill File: `skills/manufacturer-manager.md`
```markdown
# Skill: Manufacturer Manager
## Tu Rol
Gestiona la producción. Revisa órdenes entrantes, stock, libera producción, compra partes, ajusta precios.
## Comandos Disponibles
`./manufacturer-cli day current`, `stock`, `sales orders`, `production status`, `capacity`, `suppliers list`, `purchase create --supplier <name> --product <id> --qty <n>`, `production release <order_id>`, `price list/set <model> <price>`
## DO NOT
- NO llames a `day advance`. El motor lo hace.
- NO liberes órdenes que excedan la capacidad diaria.
- NO compres partes que lleguen tarde para los pedidos urgentes.
## Marco de Decisión
1. Assess: Ejecuta `stock`, `sales orders`, `capacity`. Resume en 2 líneas.
2. Fulfill: Libera órdenes pendientes si hay materiales.
3. Order: Compra partes si stock < 2 días de consumo esperado.
4. Adjust: Sube precio si órdenes > capacidad x1.5 por 2+ días.
5. Log: Imprime razón antes de cada mutación.
## Señales de Mercado
`demand_modifier > 1.5`: Alta demanda. Construye inventario. `supply_modifier < 0.7`: Escasez. Compra antes.
## Final
Resume 3-5 bullets. SAL.
```
**Ejecución con Claude Code**:
```python
import subprocess
result = subprocess.run(
    ["claude", "--print", "--prompt", prompt_text],
    capture_output=True, text=True, cwd=manufacturer_dir, timeout=180
)
```

### 📦 Entregables Lab 7
- 3 apps corriendo + `turn_engine.py` determinista → luego con 1 agente
- `skills/manufacturer-manager.md` funcional
- `config/sim.json` y `scenarios/smoke-test.json`
- Reporte (3-4 págs) con diseño del motor, skill file, logs del agente y reflexiones

---

## 🤖 FASE 4: LAB 8 — Autonomía Total, Escenarios y Análisis
### 🎯 Objetivo
Activar los 3 agentes, ejecutar simulaciones de 15-25 días con escenarios complejos, capturar métricas, generar gráficos y analizar comportamiento emergente.

### 📜 Skill Files Faltantes
Crear `skills/provider-manager.md` y `skills/retail-manager.md` siguiendo el mismo patrón del Lab 7. Incluir reglas explícitas, límites de cambio de precio (≤15%/día), y manejo de señales `demand_modifier`, `supply_modifier`, `price_sensitivity`.

### 🌪️ Escenarios de Prueba
1. **`calm-market.json`**: `demand_modifier: 1.0`, sin disrupciones. Grupo control.
2. **`holiday-rush.json`**: Eventos superpuestos.
```json
{
  "scenario_name": "Q4 Holiday + Chip Shortage",
  "base_demand": {"mean": 5, "variance": 2},
  "events": [
    {"name":"normal", "start_day":1, "end_day":10, "demand_modifier":1.0},
    {"name":"black_friday", "start_day":11, "end_day":13, "demand_modifier":3.0, "price_sensitivity":"high"},
    {"name":"chip_shortage", "start_day":14, "end_day":20, "demand_modifier":1.5, "supply_modifier":0.4, "lead_time_modifier":2.0},
    {"name":"christmas", "start_day":18, "end_day":25, "demand_modifier":2.5, "supply_modifier":0.6}
  ]
}
```
*Nota*: Eventos superpuestos (días 18-20) deben multiplicar o tomar el máximo de modificadores. Documentar la decisión.

### 📊 Métricas y Análisis
- **Snapshot por día**: Inventario (partes, productos terminados, retail), precios (proveedor, mayorista, retail), órdenes cumplidas/backordeadas.
- **Gráficos obligatorios**:
  1. Inventario a lo largo del tiempo (3 líneas)
  2. Precios a lo largo del tiempo (3 líneas)
  3. Cumplimiento de pedidos diario (barras: placed vs fulfilled vs backordered)
  4. Overlay de eventos de escenario
- **Interpretación**: Cadenas causales, efecto bullwhip, oscilaciones de precios, causas de stockouts.

### 📦 Entregables Finales (Lab 8)
- Repo completo con 3 apps, motor, 3 skills, 2+ escenarios, seeds, docs finales
- Reporte Final (5-8 págs): Arquitectura, diseño de agentes, resultados simulados (gráficos + interpretación), reflexión vibe-coding
- Presentación (max 10 slides) + Demo en vivo (2-3 turnos)

---

## 📂 ESTRUCTURA DE DIRECTORIOS ESPERADA
```
printer-sim/
├── provider/
│   ├── services/ (catalog, orders, simulation)
│   ├── api.py, cli.py, db.py
│   └── seed-provider.json
├── manufacturer/
│   ├── services/ (production, purchases, sales, simulation)
│   ├── api.py, cli.py, db.py
│   └── seed-manufacturer.json
├── retailer/
│   ├── services/ (customers, purchases, fulfillment, pricing)
│   ├── api.py, cli.py, db.py
│   └── seed-retailer.json
├── engine/
│   └── turn_engine.py
├── skills/
│   ├── manufacturer-manager.md
│   ├── provider-manager.md
│   └── retail-manager.md
├── scenarios/
│   ├── calm-market.json
│   └── holiday-rush.json
├── config/
│   └── sim.json
├── logs/ (ignore en git)
├── docs/PRD.md
├── CLAUDE.md
├── README.md
└── .gitignore
```

---

## ✅ CHECKLIST DE VERIFICACIÓN FINAL
- [ ] Las 3 apps inician en puertos distintos y sirven APIs REST documentadas (`/docs`)
- [ ] CLI funciona en los 3 apps con el patrón `<app>-cli <resource> <action>`
- [ ] El motor de turnos ejecuta 15+ días sin intervención humana
- [ ] Los 3 archivos de skill existen y han sido probados en aislamiento
- [ ] Se ejecutaron al menos 2 escenarios (calmo y volátil)
- [ ] Logs por día/rol guardados en `logs/`
- [ ] Tablas `events` y `metrics` en las 3 BDs contienen datos coherentes
- [ ] Reporte final (PDF) y presentación listos
- [ ] `.env` y `*.db` excluidos de git. Commit history referencia issues.

---

## 📝 INSTRUCCIONES ESPECÍFICAS PARA LA IA EJECUTORA
1. **PRD-First Workflow**: Nunca escribas código sin actualizar `docs/PRD.md` y `CLAUDE.md` primero. Usa `/compact` si el contexto se satura.
2. **Capa de Servicios**: Extrae toda la lógica de negocio a `services/`. La API y el CLI deben ser wrappers delgados que llamen a esta capa.
3. **Contratos REST**: Define Pydantic models para cada request/response. Usa `httpx` con `timeout=10.0` y manejo explícito de errores entre apps.
4. **Motor de Turnos**: Implementa primero la versión determinista (stubs). Solo cuando fluya sin errores, integra `claude --print` para un rol. Usa `subprocess.run` con `capture_output=True`.
5. **Iteración de Skills**: Si un agente falla, **reescribe el skill**, no el agente. Pide razonamiento antes de mutaciones y exige un resumen final de 3-5 bullets.
6. **Observabilidad**: En `day advance`, guarda un snapshot de métricas clave en una tabla `metrics`. Sin esto, el análisis es imposible.
7. **Demo Ready**: Mantén un escenario de 3 días (`smoke-test.json`) listo para ejecución en vivo. El fallo parcial es aceptable si se puede explicar la causa emergente.

> 🚀 **Prompt inicial para arrancar el proyecto:**
> "Read `CLAUDE.md` and `docs/PRD.md`. Initialize the Lab 5 skeleton following the PRD-first workflow. Create the FastAPI server, SQLite models via Pydantic, Streamlit dashboard stub, and basic CLI. Commit as `feat: lab5-skeleton`. Then, generate the Lab 6 provider app specification and integrate it into the repo structure. Wait for confirmation before proceeding to Lab 7 turn engine implementation."

Este documento contiene todas las especificaciones técnicas, restricciones de diseño, flujos de trabajo y entregables de los Laboratorios 5 a 8. Úsalo como la fuente única de verdad para guiar la construcción paso a paso.