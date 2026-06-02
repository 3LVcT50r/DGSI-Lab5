# Reporte de respuestas a los enunciados (Weeks 6, 7, 8)

Estado real del proyecto tras analizarlo:
- **Week 6**: hecho. `provider-app` funciona y `factory-app` (manufacturer) le compra por REST con polling de entregas.
- **Week 7**: hecho. Existen las 3 apps + `turn_engine.py` (con `claude --print` y fallback a `mock_agent.py`) + 1er skill (de hecho los 3) + escenarios + `config/sim.json`.
- **Week 8**: infraestructura hecha (3 skills, 2+ escenarios, métricas, señales, `analyze_sim.py` con 4 gráficos, `compare_scenarios.py`). PERO **no consta una ejecución real** commiteada (no hay `logs/`, `runs/`, `reports/`, ni gráficos), así que las preguntas de interpretación se responden en teoría, no con datos.

---

## Week 6 (challenge.pdf)

**1. ¿Por qué procesos separados en vez de una sola app?**
Aislamiento (un fallo del provider no tira al manufacturer), independencia (cada equipo despliega lo suyo), claridad (obliga a un contrato real) y realismo. El coste es complejidad: puertos, errores de red y tiempo simulado coherente.

**2. ¿Qué endpoints necesito (contrato REST)?**
Provider: `GET /api/catalog`, `GET /api/stock`, `POST /api/orders`, `GET /api/orders` (+`?status`), `GET /api/orders/{id}`, `POST /api/day/advance`, `GET /api/day/current`. Todos implementados.

**3. ¿Forma del request body?**
`POST /api/orders` recibe `{buyer, product_id|product_name, quantity}`. El manufacturer manda `{product_id, quantity}`. Validado con Pydantic.

**4. ¿Forma del response?**
Devuelve la orden creada: id, product_id, quantity, total_price, status (`pending`), expected_delivery_day, etc. Mismo esquema al listar/consultar.

**5. ¿Qué pasa cuando algo falla?**
Errores de negocio → `ValueError` → HTTPException 400/404. Las llamadas HTTP usan `httpx` con `timeout=10s` y `raise_for_status()`.

**6. Checklist de verificación.**
Provider sirve catalog/stock/orders/day - HECHO; manufacturer llama al provider - HECHO; CLIs (`provider-cli`, `manufacturer-cli`) - HECHO; export/import JSON - HECHO; Swagger en `/docs` - HECHO; `.env` en `.gitignore` - HECHO (usa `*.sqlite` en vez de `*.db`). El escenario de 5 días se cubre con los scripts de integración.

**7. Reporte – Arquitectura (cómo se conectan las 2 apps).**
Dos procesos FastAPI con su propia BD SQLite. Manufacturer (8002) llama al Provider (8001) por HTTP. Cada uno tiene su `sim_day` y se avanzan por separado.

**8. Reporte – Contrato REST del provider y por qué.**
Endpoints REST por recurso (catalog/stock/orders/day) porque mapea directo al modelo y se autodocumenta en Swagger. El manufacturer nunca toca la BD del provider, solo el contrato.

**9. Reporte – El escenario (qué pasó, qué sorprendió).**
No hay log del escenario manual de 5 días; existen `integration-test.ps1/.sh` y `run-integration-test.py` que prueban pedido→pending→shipped→delivered y la suma al inventario.

**10. Reporte – Notas vibe-coding.**
Bien: estructura por capas (models/schemas/services/api) y CLIs por app. A corregir: rutas inconsistentes (provider `/api`, manufacturer `/api/v1`) y en `factory-app/.../simulation.py` (línea ~226) queda un `requests.get(provider/api/v1/orders?status=delivered)` con ruta equivocada, duplicado del polling correcto que sí funciona.

---

## Week 7 (week7.pdf)

**1. ¿Por qué un turn engine?**
Avanzar a mano sirve para 5 días, no para 25 ni con agentes. **Hecho** en `turn_engine.py`: lee señales del escenario, inyecta demanda, ejecuta cada rol y avanza todas las apps en lock-step, guardando logs.

**2. ¿Qué orden de operaciones por turno y por qué?**
`broadcast_signal` → inyectar demanda de clientes → agente retailer → agente manufacturer → agente provider → `advance` a todos → resumen del día. Downstream decide primero y upstream reacciona (tal cual el enunciado). Implementado así.

**3. ¿Qué es un skill file?**
Un .md que enseña a Claude Code un rol (rol, comandos, marco de decisión, DO NOT, señales). Es el "contrato" con el agente. **Hay 3** (ver sección final), aunque la semana solo pedía 1.

**4. Checklist de verificación Week 7.**
3 apps en sus puertos - HECHO; CLI retailer - HECHO; manufacturer acepta pedidos entrantes (`POST /api/v1/orders`→SalesOrder) - HECHO; generador de demanda - HECHO; motor determinista (mock) - HECHO; skill(s) - HECHO; logs de agente a `logs/day-XXX-rol.log` - HECHO; export/import - HECHO. Único pero: no hay un run concreto commiteado (la carpeta `logs/` está en .gitignore y vacía).

**5. Reporte – Diagrama de las 3 apps + motor.**
Retailer (8003) → Manufacturer (8002) → Provider (8001); el retailer vende a clientes. El `turn_engine.py` es el director que orquesta señales, demanda y avances.

**6. Reporte – Diseño del turn engine (orden y por qué).**
Orden del punto 2 (downstream primero). Avances: retailer/provider `/api/v1/day/advance`, manufacturer `/api/v1/simulate/advance`. Agentes vía `claude --print --dangerously-skip-permissions` con `cwd` por app y `timeout=180s`; si no hay `claude`, cae a `mock_agent.py`.

**7. Reporte – Skill file + 2 decisiones al escribirlo.**
Existe `skills/manufacturer-manager.md`. Dos decisiones: (1) DO NOT explícito de no llamar `day advance` (el motor lo hace) y respetar capacidad; (2) exigir "log de razonamiento antes de cada mutación" + resumen final de 3–5 bullets para tener auditoría.

**8. Reporte – Run de prueba (excerpts del agente + comentario).**
El motor está listo para el POC (1 día con manufacturer-as-agent y el resto en stub), pero **no hay output de un run guardado** en el repo, así que no se pueden pegar excerpts reales.

**9. Reporte – Notas vibe-coding Week 7.**
Bien: el motor separa señal/demanda/decisión/avance y persiste logs por rol; el `mock_agent.py` permite probar el flujo sin gastar LLM. Pendiente: ejecutar y commitear un run real para tener evidencia.

---

## Week 8 (week8.pdf)

> La infraestructura está completa, pero **no consta un run de 15–25 días** con datos/gráficos. Las interpretaciones van en teoría.

**1. Eventos solapados: ¿multiplicar o tomar el máximo?**
Decidido y documentado en `turn_engine.todays_signal`: `demand_modifier` y `lead_time_modifier` → **máximo**; `supply_modifier` → **mínimo** (gana el evento más agresivo en el solape, p.ej. chip_shortage × christmas días 18–20).

**2a. ¿El manufacturer construyó stock antes de Black Friday?**
No evaluable (sin run). El skill lo prevé: con `demand_modifier > 1.5` debe "build inventory" y comprar partes antes, respetando lead time.

**2b. Stockouts: ¿causa próxima vs raíz?**
No evaluable. Esperado: causa próxima = retailer sin impresoras; causa raíz = manufacturer/provider que no anticiparon partes ante la señal (reacción tardía o lead time alargado).

**2c. ¿Precios se estabilizan u oscilan?**
No evaluable. Riesgo típico: oscilan si todos reaccionan el mismo día al mismo estado; los skills acotan el cambio (provider ≤15%/día, retailer ±5%) para amortiguarlo.

**2d. ¿Hay un momento bullwhip?**
No evaluable sin datos. Sería: pico pequeño en el retailer → pedido mayor al manufacturer → pedido aún mayor al provider, visible en los gráficos de inventario.

**3. Comparación escenario calmo vs volátil.**
Tooling listo: `calm-market.json` (25 días estables, control) y `holiday-rush.json` (normal→black_friday→chip_shortage→christmas, con solape) + `compare_scenarios.py`. Falta ejecutarlos y comparar.

**4. Checklist de verificación final.**
3 skills - HECHO; 2+ escenarios - HECHO; señales `/api/v1/signal` - HECHO; métricas server-side (`snapshot_metrics` en cada `advance_day`, tabla `metrics`, endpoint `/api/v1/metrics`) - HECHO; resumen diario (`/api/v1/day/summary`) - HECHO; gráficos vía `analyze_sim.py` (inventario, precios, fulfillment, strip de eventos) - HECHO a nivel de código. Falta: turno con 3 agentes ejecutado, run 15+ días, gráficos/logs commiteados, slides/demo.

**5. Reporte final (estructura a/b/c/d).**
a) Arquitectura: 3 apps + modelo por app + motor + flujo de señales (broadcast antes de decidir). b) Diseño de agentes: 3 skills (abajo) con DO NOT y marcos de decisión. c) Resultados: pendientes (no hay run con datos/charts). d) Reflexión vibe-coding: la base (apps, REST, motor, skills, análisis) salió completa; lo que falta es disciplina de ejecución (correr la simulación y guardar evidencias).

---

## Las 3 Skills (resumen)

**`skills/manufacturer-manager.md` — Manufacturer Manager.**
Rol: produce impresoras (revisa pedidos, stock, libera producción, compra partes, ajusta precios). DO NOT: no `day advance`, no exceder capacidad, no comprar partes que lleguen tarde. Marco: assess→fulfill→order(si stock<2 días)→ajustar precio(si demanda>capacidad×1.5)→log. Señales: `demand>1.5` construir inventario; `supply<0.7` comprar antes.

**`skills/provider-manager.md` — Provider Manager.**
Rol: vende partes (procesa POs, gestiona stock, ajusta precios, envía al cumplir lead time). DO NOT: no `day advance`, no cambiar precio >15%/día, no dejar a 0 un producto con pedidos pendientes. Marco: assess→restock(si <50% del inicial)→ajustar precio(±5–10% según stock vs 150%/30%)→resumen. Señales: `supply<0.7` subir precios; `demand>1.5` construir stock.

**`skills/retail-manager.md` — Retail Manager.**
Rol: vende impresoras a clientes (cumple/backordea, recompra al manufacturer, fija precio retail). DO NOT: no `day advance`, no precio < mayorista+20%, no dejar pedidos en `pending`. Marco: fulfill→reorder(si stock<3 días de demanda)→precio(±5% según stock vs demanda)→resumen. Señales: `demand>1.5` comprar más; `demand<0.8` bajar; `price_sensitivity:high` cuidado al subir.

