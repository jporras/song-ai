# Estrategia de verificación por costo y criticidad

Decisión del usuario, 2026-10-09. Aplica a todos los sprints y a la selección de pruebas en cada continuación. Los sprints organizan entregables; el costo, las dependencias y la criticidad organizan la verificación.

## Orden de ejecución

Antes de los lotes, revisar y completar el desarrollo necesario. Agrupar cambios relacionados y mantener un registro de pendientes para evitar repetir pruebas por cada continuación.

1. **Componentes y contratos ligeros:** reglas deterministas, compilación/build y pruebas de componentes afectados. Priorizar pérdida de intención, escritura no autorizada, aislamiento de proyectos, revisiones, integridad y recuperación sobre detalles visuales.
2. **Interfaz y backend de extremo a extremo:** Playwright con backend y SQLite reales aislados, providers simulados y archivos sintéticos identificados. Recorrer idea → tres piezas → revisión/confirmación → job simulado → Studio/descarga; incluir recarga, propuestas, corrección y errores. Verificar controles, ayuda, teclado y presentación dentro del mismo lote.
3. **Gemma y Qwen reales:** comprobar contexto del proyecto, steering, roles, fidelidad, restricciones, propuestas sin guardado automático, handoffs y tiempos observados. Usar la configuración Vulkan vigente y agrupar casos para aprovechar cada carga. No generar audio en esta etapa.
4. **ACE-Step real, último bloque de verificación:** ejecutar casos pendientes de los seis modos y rutas soportadas, cotejar entradas efectivas con request confirmado, comprobar artefactos, cancelación con pesos y recuperación. Preparar fuentes y confirmar recursos antes de cargar el motor. Reutilizar evidencia real válida, incluida Isabella; una ruta o modo no verificado conserva ese estado.
5. **Aceptación:** después de desarrollo y verificación al 100%, escucha y decisión musical del usuario, revisión del recorrido y piloto con participantes según los criterios correspondientes. Conservar aceptaciones previas. La calidad percibida es evidencia distinta de integridad técnica. Reclasificación 2026-10-15: las evaluaciones perceptuales de S10-02 a S10-06 y el piloto de S10-08 pertenecen a esta etapa; su preparación técnica se mide en D/V.

Un fallo bloquea las pruebas costosas que dependen de él; corregirlo y repetir el subconjunto afectado antes de avanzar. Puede continuar trabajo independiente. No adelantar ACE-Step por haber terminado un sprint.

## Lotes por complejidad — 2026-10-15

Los lotes se ejecutan en este orden; cada uno conserva sus resultados y fallos por separado. La aceptación del usuario ocurre después y no se cuenta como un cuarto lote de verificación técnica.

| Nivel | Ejecución | IDs abiertos que puede cerrar | Evidencia mínima y criterio para avanzar |
| --- | --- | --- | --- |
| P — Python e interfaz, sin modelos | `python -m unittest discover -s tests -p "test_*.py" -q`; `node --test frontend/tests/*.test.js`; `npx vite build --configLoader runner` si el cargador Vite predeterminado falla por permisos. ASGI/SQLite/Playwright aislados solo para los flujos afectados. | Contratos y bloqueos previos de S00-04, S01-03/04, S06-05/06 y S10-07. Por sí solo no cierra su ejecución real. | Conteo exacto de aprobadas/fallidas/omitidas, build, artefactos de QA, conservación de decisiones USER y rechazo de revisión/checksum incorrectos. Resolver fallos antes de modelos. |
| L — Gemma y Qwen reales | Registry/orquestador con modelos locales gestionados y SQLite QA; solicitudes acotadas de contexto, propuesta sin autoguardado y revisión técnica. Registrar task, revisión, hashes de steering, provider_executed, fallback y duración. | Handoffs y fidelidad textual previos a S10-07; no equivale a S00-04 (LM interno de ACE-Step). | Ambas ejecuciones reales completas, sin fallback presentado como éxito; restricciones y ficha USER intactas. Cerrar y liberar solo los procesos gestionados antes del siguiente nivel. |
| A — ACE-Step real | Preflight de pesos/recursos, request confirmado en QA, carga única y jobs serializados. Reutilizar seis modos ya generados; ejecutar solo ruta LM opcional y recorrido real aún no cubiertos. Medir plan→wrapper→motor, checksums, reproducción/descarga y corrección. | S00-04, S01-03/04, S06-05/06, S10-07. | Configuración y parámetros efectivos observados; sample representativo solo si se usa; artefactos íntegros y asociados a revisión, corrección y descarga. Una traza del wrapper sin informe del motor deja S06-05 parcial. Sin escucha/aprobación musical automática. |

El nivel A requiere presupuesto de memoria confirmado, exclusividad de modelos y fuente QA verificable; un preflight favorable no autoriza inferir éxito. Si el LM opcional 1.7B o el motor no caben de forma segura, registrar bloqueo medido y conservar el ID parcial. Los WAV reales previos de los seis modos se reutilizan sin volver a generarlos por rutina. La suite completa P solo se repite si un cambio posterior afecta su evidencia; las regresiones focalizadas bastan para cambios acotados.

## Cobertura por componentes

| Componente / riesgo | Criticidad | Evidencia ligera y UI/backend | Evidencia real posterior |
| --- | --- | --- | --- |
| MusicSpec, intención USER, locks y compilador | Crítica: alterar una decisión confirmada | Persistencia/reapertura; revisión obsoleta rechazada; cada input conectado llega al request; transformación trazable; edición/confirmación desde UI | Gemma/Qwen respetan restricciones; ACE recibe valores efectivos |
| SQLite, proyectos, fuentes y exportaciones | Crítica: pérdida, cruce de datos o archivo incorrecto | Aislamiento, snapshots regenerables, checksums, descarga y recarga | Artefacto real vinculado al proyecto, revisión y request |
| Orquestador, jobs, memoria y procesos | Crítica: duplicación, bloqueo o proceso huérfano | Retry/idempotencia, estados, cancelación con proceso ligero, errores y recuperación UI/backend | Handoffs reales; cancelación y restauración tras ACE con pesos |
| Builder, formularios, chat y Studio | Alta: impedir completar el recorrido o guardar una propuesta sin permiso | Navegación, todos los controles aplicables, tooltips/teclado, guardado explícito, sample opcional, feedback/corrección/descarga | Respuesta real de modelos integrada; resultado real visible y descargable |
| Registry y steering Gemma/Qwen | Alta: consejo incompatible o aprobación simulada | Inyección de contexto/hashes, schemas, permisos y rechazo de fallback/mock como inferencia real | Obediencia, coherencia, fidelidad y latencia observada de ambos modelos |
| Adapter/wrapper ACE-Step y sus modos | Crítica: ejecutar otra configuración o anunciar capacidad inexistente | Matriz de entradas, compatibilidad, traducciones, fuentes, traza y rechazo antes de cargar pesos | Ejecución por modo/ruta pendiente, parámetros nativos y diagnóstico ligado al plan |
| Diseño visual y ayuda | Media; elevar si impide acceder a una acción | Componentes/tokens aprobados, contraste, reflow, foco y mensajes en el lote UI | Piloto y revisión de usuario en aceptación |

## Selección y registro de los lotes

- Seleccionar por componentes modificados, consumidores y dependencias, riesgo y evidencia existente; registrar casos pendientes con IDs del ledger. Un cambio documental no obliga a repetir inferencia ni audio.
- Reutilizar evidencia si sigue siendo aplicable a la revisión/configuración evaluada. Repetir pruebas por un cambio que invalida esa evidencia, un defecto concreto o un gate pendiente; no por el número de continuaciones.
- Preparar cada lote con casos, resultado esperado, entorno y criterio de salida. El lote UI/backend debe resolver los bloqueos deterministas del recorrido antes de iniciar modelos reales; estos deben resolver los bloqueos de especificación/handoff antes de ACE-Step.
- Registrar aprobadas, fallidas, omitidas y bloqueadas; distinguir mocks, inferencia real y audio real. Incluir revisión/hash, configuración/provider, artefactos y límites de cobertura cuando correspondan. Un health HTTP200 no acredita inferencia.
- Actualizar D/V solo con evidencia que cubra el entregable. Esta política no cambia pesos ni estados. El reporte calculado está en [SPRINT_PROGRESS.md](SPRINT_PROGRESS.md); la política operativa del ledger referencia este documento.

La revisión de código, los tests y Playwright no sustituyen escucha completa ni validación con usuarios amateur. Tras la correspondencia técnica de sample real de S01-03 y la exportación integrada de S01-04, los pendientes técnicos de S00-04, S06-05, S06-06 y S10-07 siguen en verificación; no moverlos a aceptación por conveniencia. No cargar modelos ni generar canciones para verificar un cambio exclusivamente documental.
