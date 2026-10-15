# Revision transversal de desarrollo — 2026-10-09

## Orden aprobado

1. Revisar y corregir desarrollo e integracion.
2. Componentes/contratos ligeros por criticidad y lote end to end de UI/backend, persistencia y accesibilidad, con modelos simulados.
3. Gemma/Qwen reales: contexto, fidelidad, handoffs y tiempos; sin generar audio.
4. Al final, lote ACE-Step real: configuracion, cancelacion, modos y artefactos.
5. Aceptacion final despues de D/V100%. Conservar aceptacion previa de Isabella.

Orden independiente de la fase del sprint; aplicar cobertura y seleccion de lotes de [VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md).

No se inicio el ensayo preparado de audio. Gemma/Qwen se habian liberado; restaurados en Vulkan con scripts administrados, health8081/8082 HTTP200 ok. No se modificaron perfiles ni se detuvieron otras aplicaciones.

## Revision de fuentes y contratos

Auditoria RuntimeAudit actual:167 modulos backend y119 rutas; seis modos presentes en wrapper. Inventario incluye configuraciones, API, parametros, bindings UI y dependencias. Evidencia DEVELOPMENT_AUDIT_20261009.json; estatica/metadata, no certificacion funcional de cada rama ni generacion.

| Area | Resultado del desarrollo revisado | Verificacion restante |
| --- | --- | --- |
| Arquitectura | Casos de uso/adapters/providers separados; servicios locales, registry y tasks; unico consumidor textual del servicio profesional es propiedad diferida de compatibilidad. Conservarla, no borrarla. | Regresion global agrupada; la inspeccion no prueba SOLID automaticamente. |
| Intencion/inputs | MusicSpec SQLite/versiones/procedencia;21inputs compilados y validados hasta wrapper; propuestas explicitas. | Obediencia real de modelos y parametros nativos efectivos. |
| Persistencia | Snapshots derivan de DB; fuentes con checksum; aprobaciones vinculadas a revision/plan/artefacto. | Recorrido completo de recarga/recuperacion en lote. |
| Builder | Siete pasos comunes y asistidos, componentes/tokens existentes; faltaba eliminar seleccion automatica de fase MIDI antigua. | Accesibilidad/contraste integral y comprobacion visual del ajuste de apertura. |
| Correccion/entrega | Escucha por candidato, feedback, propuestas, carga de propuesta en formulario sin guardar, confirmacion/nuevo plan, jobs y descarga WAV por checksum presentes. | Recorrido integrado con correccion/resultado real al final; no nuevas piezas de codigo identificadas para S10-07. |
| Lifecycle | Orquestador/monitor/exclusion/procesos/cancelacion/retry implementados; traza diagnostica ligada al plan. | Cancelacion con pesos y recuperacion reales al final. |
| Piloto | Protocolo y hoja de observacion disponibles; no participantes ni estudio ejecutado. | Preparacion restante/participantes y piloto; no llamar validacion UX a pruebas de codigo. |

## Correccion realizada

phaseToOpenAfterLoad elegia primera fase vacia de phaseDefinitions legado: un proyecto con idea/letra/composicion preparadas caia automaticamente en MIDI. Ahora usa orden Builder (Idea, Sonido, Composicion, Letra, Revisar/Generar/Studio), sin exigir fase MIDI. Conserva navegacion anterior explicitamente guardada; las herramientas historicas siguen accesibles.

Dos casos de regresion concretos: orden de preparacion y respeto de ruta guardada/fallback desconocido. Lote59pruebasfrontend aprobado y build Vite aprobado. No nueva auditoria visual en esta revision ni audio.

## Balance

S10-07 desarrollo0.5→1: superficies/casos de uso del recorrido implementados, incluida apertura guiada corregida. Verificacion permanece0.5 para recorrido integrado real pendiente, situado al final. Esto separa codigo faltante de prueba de audio pendiente; no lo declara aceptado. S10-08 continua desarrollo parcial por preparacion/realizacion del piloto pendientes; no se inventa cierre. Resto de pendientes siguen en ledger.

Sin nueva generacion ni cambios en los proyectos de produccion, sin commit/push. Cambios locales anteriores conservados; inventario git amplio incluye trabajo previo y no equivale al diff de esta revision.
