# S03 — Inventario ejecutable de herramientas musicales

## Contrato

`MusicToolRegistry` registra handlers explícitos y esquemas de parámetros. `MusicActionRouter` valida herramienta, tipos, destino único por `song_id`, autorización explícita y revisión SQLite antes de despachar. No recibe nombres arbitrarios de métodos, rutas de archivos o listas ambiguas de proyectos. Los casos de uso originales siguen validando rangos, locks, concurrencia, artefactos, plan y recursos.

La consulta `GET /api/music-tools` devuelve doce herramientas y sus controles canónicos. `POST /api/pro/projects/{song_id}/music-actions` recibe `tool_id`, `revision_id`, `user_authorized` y `parameters`. Leer no exige autorización creativa; cualquier otro efecto requiere autorización y revisión vigente. El catálogo marca `model_can_execute=false`: Qwen recibe conocimiento de operaciones para proponer; no se conecta su respuesta al dispatcher ni se infiere autorización del texto del modelo.

Las rutas existentes de guardar/confirmar/restaurar MusicSpec usan el router conservando sus respuestas para la UI. La autorización de estas rutas proviene de la acción explícita de guardar/confirmar/restaurar del usuario. Sus casos de uso mantienen la comprobación transaccional de revisión. El historial registra herramienta, parámetros solicitados, revisión fuente y autorización; un dispatch completado no acredita calidad del audio.

## Herramientas registradas

| ID estable | Operación | Destino |
| --- | --- | --- |
| spec.read | Leer ficha y propuesta vigente | Proyecto SQLite |
| spec.propose | Solicitar compilación técnica | Handoff Qwen existente; propuesta sin guardar |
| spec.edit | Guardar valores revisados | Controles editables canónicos de MusicSpec |
| spec.confirm | Confirmar revisión válida | Revisión activa |
| spec.reject_proposal | Rechazar propuesta técnica | Task vigente del mismo proyecto/revisión |
| spec.restore | Recuperar una revisión como nueva | Revisión histórica del mismo proyecto |
| plan.read | Leer el último plan | Plan persistido del proyecto |
| plan.prepare | Preparar plan | Ficha y letra mediante compilador existente |
| plan.approve | Aprobar plan y letra | Plan ID/hash y revisión vigente |
| candidate.start | Generar audio | Job con preflight y autorización exploratoria existentes |
| candidate.read | Consultar job | Task del proyecto activo |
| candidate.cancel | Cancelar job | Task del proyecto activo |

Undo de configuración consiste en `spec.restore`: crea revisión pendiente y conserva historia, sin recuperar aprobaciones. Cancelar una generación no equivale a deshacer decisiones musicales. Rechazar una propuesta registra un evento y la oculta en la consulta actual; no borra task/resultados ni edita la ficha. Una propuesta nueva puede mostrarse normalmente.

## Destinos especializados conservados

Guardar fases, propuestas por sección/línea, letras completas, importación de audio, evaluación de escucha, sample opcional, correcciones y exportación conservan sus endpoints y casos de uso específicos. No se publican como tools genéricas en este catálogo. Sus pruebas previas y contratos siguen vigentes; la verificación integral de estos destinos, UI y modelos permanece abierta en S03-03. MIDI/DSP generales no se añaden como operaciones ejecutables de ACE-Step. El servicio histórico pausado no se construye para consultar/despachar estas herramientas.

## Evidencia

- 47 pruebas backend aprobadas: router, rechazo, propuestas, edición/restauración, plan y jobs. SQLite real verifica rangos, proyecto ajeno, revisión obsoleta, rechazo tras recarga, ficha sin cambios y auditoría. Handlers de modelo/audio se prueban con dobles; no acredita inferencia.
- 54 pruebas frontend aprobadas: rechazo explícito, fallo conservando propuesta y respuesta tardía sin afectar otro proyecto, además de regresiones existentes. Primer intento del test nuevo falló por `window` ausente en Node; se corrigió el harness y se volvió a ejecutar el lote.
- Build Vite, compileall y diff check correctos.
- Smoke HTTP aislado: catálogo, PATCH utilizado por UI (200), revisión obsoleta y falta de autorización (400), sin inicializar servicio histórico. Ese smoke se ejecutó con el registro inicial de once herramientas; la herramienta adicional de rechazo se comprobó con SQLite y tests frontend, sin ensayo de navegador ni modelo real.

S03-03: desarrollo 0.5→1, verificación sigue 0.5, aceptación 0. Sin sumar cierre de destinos secundarios o ensayo real no ejecutado. Avance global 68,2%→69,0%. La API activa anterior debe reiniciarse para cargar estos cambios backend.

## Verificación posterior

El bloque siguiente corrigió la selección de contexto canción/set y el steering realmente inyectado. Playwright verificó el rechazo explícito y su persistencia; 51 pruebas backend aprobaron el contrato y la inyección en ambos roles usando dobles de provider. Verificación S03-03 pasa a 1 para registry/router; los ensayos de inferencia real siguen en S00/S05, sin acreditarse por este bloque. Ver `S03_ASSISTANT_ALIGNMENT_QA_20261009.md`.
