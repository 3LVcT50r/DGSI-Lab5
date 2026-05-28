---
marp: true
title: "Simulador Multi-Agente de Cadena de Suministro 3D"
description: "DGSI · Labs 5–8 — Victor Hernandez, Ana Poveda, Mariam Delgado, Adria Irigarai"
paginate: true
theme: default
---

# Simulador Multi-Agente de Cadena de Suministro

### Impresoras 3D · DGSI · Labs 5–8

**Victor Hernandez · Ana Poveda · Mariam Delgado · Adria Irigarai**
28 de mayo de 2026

> *“Deterministic plumbing hosts non-deterministic strategy.”*
> Tres servicios FastAPI deterministas + agentes LLM tomando las decisiones diarias.

---

## 1 · El problema

Modelar una cadena de suministro de impresoras 3D con **tres actores independientes** que se comunican por REST y se comportan como agentes autónomos día a día.

- **Provider** (`:8001`) — vende piezas a fabricantes.
- **Manufacturer** (`:8002`) — ensambla impresoras y las vende a minoristas.
- **Retailer** (`:8003`) — vende al cliente final.

Sobre todo ello, un **turn engine** orquesta el día simulado, inyecta señales de mercado y llama a un agente Claude Code por rol.

---

## 2 · Arquitectura general

```
┌──────────────┐  POST /orders   ┌────────────────┐  POST /orders   ┌──────────────┐
│   Retailer   │ ───────────────►│  Manufacturer  │ ───────────────►│   Provider   │
│    :8003     │  (clientes)     │     :8002      │  (compras)      │    :8001     │
│ retailer.db  │                 │  database.db   │                 │ provider.db  │
└──────┬───────┘                 └────────┬───────┘                 └──────┬───────┘
       ▲                                  ▲                                ▲
       └──────────────── turn_engine.py ──┴────────────────────────────────┘
                                  │
                 scenarios/*.json · skills/*.md · logs/ · runs/
```

- Cada servicio tiene **su propia SQLite**. No leen las DBs ajenas.
- Solo se comunican vía REST (`/api/v1/...`).
- El engine pasa la **señal de mercado**, dispara los **agentes** y avanza el día.

---

## 3 · Stack técnico

| Capa | Tecnología | Por qué |
|------|-----------|---------|
| Lenguaje | Python 3.11+ | Requisito del lab |
| API | FastAPI + Pydantic | OpenAPI gratis, validación tipada |
| Persistencia | SQLite + SQLAlchemy | Una DB por app, file-based |
| CLI | argparse + wrappers `.sh`/`.cmd` | Mismo verbo en los tres apps |
| Orquestación | `turn_engine.py` | Loop diario y composición de señales |
| Agentes | Claude Code skills (`skills/*.md`) | Decisión LLM por rol |
| UI | Streamlit (fabricante + retailer) | Dashboards humanos |
| Gráficas | matplotlib | `analyze_sim.py` / `compare_scenarios.py` |

---

## 4 · Modelo de datos común

Cada app tiene su propio ER, pero comparten cinco piezas:

- **Productos + inventario** (con `pricing_tiers` en provider y `BOM` en manufacturer).
- **Pedidos** con máquina de estados: `pending → confirmed → in_progress → shipped → delivered`.
- **`events`** — log append-only de cada mutación (auditoría).
- **`sim_state`** — singleton con `current_day`.
- **`signal_state`** (Semana 8) — modifiers del día actual.
- **`metrics`** (Semana 8) — un snapshot por `(día, producto)` al final de `advance_day`. Es lo que consume `analyze_sim.py`.

---

## 5 · APIs principales

**Provider** `:8001`
`GET /catalog · /stock · /orders` · `POST /orders · /day/advance · /signal`

**Manufacturer** `:8002`
`GET /inventory · /sales-orders · /capacity · /pricing` · `POST /orders · /purchase-orders · /simulate/advance · /signal`

**Retailer** `:8003`
`GET /catalog · /stock · /orders` · `POST /orders · /purchases · /day/advance · /signal · /day/summary`

> Cada app expone Swagger en `/docs`. Las rutas son finas; toda la lógica vive en `src/services/*.py`.

---

## 6 · Turn engine — orden estricto del día

1. **Resolver la señal** del día desde los `events` activos del escenario.
2. **Difundir** la señal con `POST /api/v1/signal` a los tres apps.
3. **Generar demanda** de clientes y POSTearla al retailer.
4. **Ejecutar agentes** en orden *downstream-first*: **retailer → manufacturer → provider**.
5. **Avanzar día** (`/advance`) en el mismo orden.
6. **Resumen** vía `GET /day/summary` → log de una línea por día.

> **¿Por qué downstream-first?** El retailer decide primero, sus POs llegan al fabricante antes de que planifique, y las del fabricante llegan al provider antes de que envíe. Reacción en el mismo turno.

---

## 7 · Señales de mercado

Cada escenario define una lista de `events` con modifiers:

```json
{"name":"chip_shortage", "start_day":14, "end_day":20,
 "demand_modifier":1.5, "supply_modifier":0.4, "lead_time_modifier":2.0}
```

Cuando dos eventos se solapan (p. ej. *chip_shortage* + *christmas_season* en días 18-20), los modifiers se **componen conservadoramente**:

- `demand_modifier`, `lead_time_modifier` → **`max`**
- `supply_modifier` → **`min`**
- `price_sensitivity` → último evento gana (string)

> Elegido sobre la multiplicación para evitar picos irreales (3.0 × 2.5 = 7.5x).

---

## 8 · Agentes — los skill files

Tres archivos en `skills/`, uno por rol. **El skill es el contrato con el LLM**: si el agente hace una tontería, se reescribe el skill, no el agente.

Cada uno contiene:

1. Rol (1–2 frases)
2. Lista enumerada de comandos CLI disponibles
3. **Decision framework** numerado
4. Sección **DO NOT** (límites duros)
5. Guía de interpretación de señales

> Llamados con `claude --print` y el skill como prompt. Si no hay `claude` CLI en `PATH` (o `FORCE_MOCK_AGENT=1`), el engine cae a `mock_agent.py` (determinista).

---

## 9 · Resumen de cada skill

- **Provider manager** — repone si stock < 50% del inicial, sube top-tier 5–10% si stock <30%, baja 5–10% si stock >150%. **Tope 15%/día**.
- **Manufacturer manager** — libera pedidos pendientes con material, compra piezas si stock < 2 días de consumo, sube mayorista 5–10% si demanda > capacidad ×1.5 durante 2+ días.
- **Retail manager** — fulfill / backorder, recompra si stock < 3 días de demanda media, sube retail 5% si va corto, baja 5% si se acumula >5 días. **Suelo: wholesale + 20%**.

Reglas comunes:
- *Do NOT call `day advance`* — eso lo hace el engine.
- Tope diario de cambio de precio del 15%.

---

## 10 · Escenarios incluidos

| Scenario | Días | Carácter |
|----------|------|----------|
| `calm-market.json` | 25 | Control: todos los modifiers = 1.0 |
| `holiday-rush.json` | 25 | Volátil: Black Friday + chip shortage + Christmas (con solapamientos) |
| `smoke-test.json` | 10 | Plumbing check |

**Holiday rush — línea temporal:**
- Días 1–10: `normal`
- Días 11–13: `black_friday` (demand ×3, alta sensibilidad al precio)
- Días 14–20: `chip_shortage` (supply ×0.4, lead_time ×2)
- Días 18–25: `christmas_season` (demand ×2.5, supply ×0.6) ← **solapamiento**

---

## 11 · Observabilidad — 3 capas

1. **Logs por agente/día** — `logs/day-{NNN}-{role}.log` (stdout de `claude --print` o `mock_agent`).
2. **Tabla `events`** en cada DB — log append-only, queryable con SQL.
3. **Tabla `metrics`** — un snapshot por `(sim_day, product_id)` escrito al final de `advance_day`. Es la fuente para las gráficas.
4. **Resumen diario del engine** — `Day 7: 12 placed / 9 fulfilled / 2 backordered / 1 stockout`.

`--run-tag NAME` archiva las tres SQLite en `runs/<NAME>/` → simulaciones reproducibles y comparables sin colisión.

---

## 12 · Análisis y gráficas

`analyze_sim.py` consume las tablas `metrics` y produce cuatro PNGs por run:

1. **Inventario** en el tiempo (3 líneas: partes, impresoras en fábrica, impresoras en retailer) con bandas sombreadas por evento.
2. **Precios** en el tiempo (provider top-tier · wholesale · retail).
3. **Cumplimiento de pedidos** (barras agrupadas: placed / fulfilled / backordered).
4. **Strip de eventos** del escenario.

`compare_scenarios.py` toma dos `runs/<tag>/` archivados y produce los paneles side-by-side **calm vs holiday**.

---

## 13 · Cómo lo construimos (workflow)

**PRD-First** — antes de cada fase escribimos en `docs/PRD.md` qué endpoints, modelos y contratos íbamos a tocar; commits sólo después.

| Lab | Entregable |
|-----|-----------|
| **Lab 5** | Manufacturer monolítico: FastAPI + SQLite + Streamlit + CLI |
| **Lab 6** | App Provider separada; comunicación REST entre dos procesos |
| **Lab 7** | App Retailer + `turn_engine.py` + primer skill (manufacturer) |
| **Lab 8** | Tres agentes activos · `SignalState` y `Metric` · `holiday-rush` · charts |

Hooks de la Semana 8: `signal_state`, `metrics`, `/signal`, `/day/summary`, lead_time aplicado en `place_order`, `--run-tag`, `compare_scenarios.py`.

---

## 14 · Resultados — escenario volátil

![w:900](../reports/holiday-fix3/inventory_over_time.png)

- Día 11 (Black Friday): triplicado de demanda → primeras roturas de stock en el retailer.
- Día 14 (chip shortage): el provider tarda el doble, el inventario de piezas del fabricante cae.
- Días 18-20: solapamiento chip+Christmas → el peor stretch de backorders.

---

## 15 · Resultados — precios

![w:900](../reports/holiday-fix3/prices_over_time.png)

- El provider sube top-tier durante la escasez (límite 15%/día → curva escalonada).
- El fabricante propaga la subida al mayorista cuando demanda > capacidad ×1.5.
- El retailer respeta el suelo `wholesale + 20%`.

---

## 16 · Calm vs Holiday — side by side

![w:780](../reports/comparison/inventory_compare.png)

En el escenario calmo los agentes mantienen cadencia regular; en el volátil aparece el **efecto bullwhip**: pequeñas oscilaciones del cliente se amplifican aguas arriba.

---

## 17 · Comportamiento emergente

- **Bullwhip** — un pico de demanda de N unidades en el retailer se traduce en M >> N piezas pedidas al provider dos días después.
- **Cascada de stockout** — la rotura del retailer fuerza backorder → el fabricante los libera en bloque cuando llegan piezas → satura capacidad → más backorders.
- **Inercia de precios** — el límite de 15%/día crea un retardo: cuando el retailer reacciona, el evento ya ha pasado y se queda con precio “demasiado alto”.

> El brief lo pedía explícitamente: **no esconder lo inesperado, explicarlo**.

---

## 18 · Reflexión vibe-coding

Qué funcionó:
- **PRD-first** mantuvo el alcance acotado y el contexto de Claude relevante.
- **Skill files cortos y numerados** → agentes mucho más predecibles que prompts libres.
- Separar **plumbing determinista** de **estrategia LLM** facilitó el debugging: un fallo casi siempre era del skill o del scenario, no del código.

Qué no:
- Plumbing residual del Lab 5 (doble demanda, doble `advance_day` del provider) tardó en aflorar hasta tener corridas largas.
- Falta de un dashboard live → análisis post-hoc con CSVs y PNGs.

---

## 19 · Lo que rediseñaríamos

- **Un solo `advance_day` central** orquestado por el engine (no que el fabricante avance al provider).
- **Seeds reproducibles** con inventarios iniciales razonables (ahora días 1-3 bloquean por `waiting_for_materials`).
- **Streamlit live** leyendo `metrics` en vez de generar PNGs offline.
- **Multi-retailer** para ver competencia, no sólo la cadena vertical.

---

## 20 · Demo & cierre

Comandos de la demo:

```bash
# 3 servicios en 3 terminales
./provider-cli serve --port 8001
./manufacturer-cli serve --port 8002
./retailer-cli serve --port 8003

# Run determinista 3 días para enseñar el flujo
FORCE_MOCK_AGENT=1 python turn_engine.py \
    config/sim.json scenarios/smoke-test.json 3

# Charts
python analyze_sim.py scenarios/holiday-rush.json \
    --db-dir runs/holiday-fix3 --out reports/holiday-fix3
```

**Gracias.** Preguntas en `/docs/PRD.md` y en `/api/v1/docs` de cada servicio.
