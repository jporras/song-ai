# Mapa de documentación

Este índice indica qué documento consultar antes de cambiar Song AI. El README de la raíz describe el estado ejecutable y cómo iniciarlo; `AGENTS.md` fija las reglas del proyecto. Los planes y reportes fechados no demuestran por sí solos que una función esté implementada: hay que comprobar el código y las pruebas del árbol actual.

## Documentos de trabajo

El backlog operativo del estudio editable y del copilot bidireccional está en [AI_MUSIC_STUDIO_SPRINT_PLAN.md](AI_MUSIC_STUDIO_SPRINT_PLAN.md). Incluye auditoría estática, arquitectura incremental, S00–S18, dependencias, cobertura funcional y aceptación. La nueva filosofía establece una interfaz común sin ocultar controles por experiencia; las capacidades reales determinan disponibilidad.

| Documento | Para qué sirve | Estado y límite |
| --- | --- | --- |
| [AMATEUR_USER_FLOW_REVIEW.md](AMATEUR_USER_FLOW_REVIEW.md) | Contrato y criterios de aceptación del recorrido para principiantes. | Propuesta pendiente; no equivale a funcionalidad implementada ni a prueba con usuarios. Prevalece para decisiones de este recorrido frente a los flujos antiguos. |
| [AMATEUR_AUDIO_VOICE_STEERING.md](AMATEUR_AUDIO_VOICE_STEERING.md) | Calidad técnica y de escucha, sample representativo, revisión final y voz personalizada opcional. | Contrato pendiente con aceptación UX/QA/VO. No acredita canto real validado ni clonación disponible. |
| [SONG_SPEC_GEMMA_QWEN_CONTRACT.md](SONG_SPEC_GEMMA_QWEN_CONTRACT.md) | Roles Gemma/Qwen, especificación integral, catálogo completo de parámetros, guía e interfaz sincronizada y fidelidad del resultado. | Ampliación pendiente SP-01 a SP-09. Evoluciona `song_specs`/`song_spec.json`; distingue reglas, revisión del modelo y aprobación del usuario. |
| [PHASE_INFORMATION_FLOW.md](PHASE_INFORMATION_FLOW.md) | Persistencia activa en SQLite, estados de fase, ejecución y artefacto, eventos y regeneración. | Referencia técnica para cambios en formularios y artefactos; contrastar endpoints y esquemas con el código. |
| [MULTI_MODEL_MASTER_SPEC.md](MULTI_MODEL_MASTER_SPEC.md) | Visión de roles, límites y handoffs entre modelos. | Arquitectura objetivo, no inventario de funciones disponibles. `AGENTS.md` y el estado actual del README tienen prioridad. |
| [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) | Reglas visuales y de interacción de la interfaz actual. | Referencia de UI; el recorrido amateur añade requisitos de lenguaje y progreso. |
| [ROADMAPP.md](ROADMAPP.md) | Próximos bloques de trabajo y su orden. | Plan actual, no registro de sprints completados. |
| [RUNTIME_DEPLOYMENT_STRATEGY.md](RUNTIME_DEPLOYMENT_STRATEGY.md) | Criterios de runtime y decisión local para Song AI. | La ruta operativa actual es Windows nativo; sus ejemplos genéricos de Docker no son instrucciones de ejecución de este proyecto. |

## Evidencia y diagnósticos

[ACE_STEP_CAPABILITIES.md](ACE_STEP_CAPABILITIES.md) define tareas documentadas, parámetros por interfaz, límites y estado conectado en Song AI. Su sección marcada se inyecta en solicitudes a Gemma/Qwen con el estado del wrapper; los roles externos viven en `docs/steering/GEMMA_SONG_ROLE.md` y `QWEN_SONG_ROLE.md`. Es referencia obligatoria antes de modificar compilación, generación o consejos sobre audio. Las capacidades documentadas no equivalen a funciones habilitadas.

[STUDIO_CAPABILITY_AUDIT.md](STUDIO_CAPABILITY_AUDIT.md) explica el entorno observado, la matriz de controles y los límites de evidencia de S00. La ejecución de probes se realiza con el Python del proyecto y el argumento explícito --probe-runtime.

[STUDIO_CAPABILITY_AUDIT.json](STUDIO_CAPABILITY_AUDIT.json) contiene la inspección reproducible de S00. Es una instantánea del intérprete y configuración de ejecución del auditor; no demuestra generación, checkpoint cargado ni calidad audible. Regenerar con scripts/audit_studio.py cuando cambie el entorno.

| Documento | Para qué sirve | Cómo leerlo |
| --- | --- | --- |
| [HANDOFF_PLAYWRIGHT_2026-10-02.md](HANDOFF_PLAYWRIGHT_2026-10-02.md) | Reproducciones PW-01 a PW-10 y verificación posterior. | Leer primero «Implementacion posterior»: el orden propuesto y las reproducciones describen fallos históricos, no diez pendientes actuales. |
| [HANDOFF_5_5_SOL.md](HANDOFF_5_5_SOL.md) | Alcance, aceptación y resultado de P1 a P3. | P1 a P3 constan como completados en su encabezado; las propuestas posteriores son evidencia histórica. |
| [ACE_STEP_DIAGNOSTIC_REPORT.md](ACE_STEP_DIAGNOSTIC_REPORT.md) | Diagnóstico de entrada en español, recursos y timeout de ACE-Step. | Evidencia de una prueba concreta; no acredita calidad de audio final ni velocidad actual. |
| [ACE_STEP_INTEL_XPU_REPORT.md](ACE_STEP_INTEL_XPU_REPORT.md) | Prerrequisitos, comprobación y diagnósticos XPU. | La integración está preparada; la ejecución final real en este equipo figura como pendiente en el reporte. |

## Planes iniciales: contexto histórico

| Documento | Aporte que conserva | Contenido repetido o desactualizado |
| --- | --- | --- |
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | Motivación original y definición de instrumental, melodía y letra como assets reutilizables. | Repite el flujo de `MULTI_MODEL_MASTER_SPEC.md` y `AGENTS.md`; no define el recorrido de usuario vigente. |
| [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) | Boceto inicial de puertos, providers, builders y formatos. | Repite la arquitectura multi-modelo y menciona Docker como runtime operativo; esa decisión fue sustituida. La descripción de SQLite como índice de JSON también quedó corta frente a `PHASE_INFORMATION_FLOW.md`. |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Registro histórico de objetivos y entregables de los sprints 1 a 12. | No sirve como backlog actual; «completado» en mock/local no significa audio real o flujo amateur completo. |

## Qué documento manda en cada cambio

1. **Reglas y estado:** `AGENTS.md` para invariantes; README raíz para capacidades verificadas y ejecución. Si el código contradice cualquiera de los dos, registrar la diferencia y corregir código o documentación según corresponda.
2. **Experiencia guiada:** `AMATEUR_USER_FLOW_REVIEW.md` para recorrido; `AMATEUR_AUDIO_VOICE_STEERING.md` para calidad, revisión y voz personalizada; `DESIGN_SYSTEM.md` para presentación; `ROADMAPP.md` para secuencia de implementación.
3. **Persistencia y modelos:** `PHASE_INFORMATION_FLOW.md` para estado y artefactos; `MULTI_MODEL_MASTER_SPEC.md` para responsabilidades; `SONG_SPEC_GEMMA_QWEN_CONTRACT.md` para el documento completo y su trazabilidad. Las rutas, tablas y funciones concretas se confirman en código.
4. **Runtime y audio:** `RUNTIME_DEPLOYMENT_STRATEGY.md` para la decisión local; los dos reportes ACE-Step para diagnóstico específico, con sus límites de prueba.
5. **Defectos históricos:** los handoffs guardan reproducción y aceptación; consultar su estado inicial y la implementación posterior antes de abrir una tarea nueva.

Al completar un cambio funcional, actualizar el README raíz y el documento de contrato afectado. Los reportes fechados conservan su evidencia; añadir una nota de resultado en lugar de reescribir la observación original. Los Markdown de `docs/` son versionables para que estas referencias existan también en un checkout limpio.
