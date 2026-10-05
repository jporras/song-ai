# Plan de sprints — AI Music Studio
Fecha: 2026-10-04. Estado: planificación; ningún sprint nuevo se declara completado.
Este documento es el backlog operativo de evolución del estudio. IMPLEMENTATION_PLAN.md conserva los sprints históricos; ROADMAPP.md resume prioridades. README.md registra entregas verificadas.

## Alcance y fuentes
Integra los requerimientos funcionales completos (17 apartados), la definición arquitectónica (20 apartados), la filosofía de aprendizaje universal y AI Music Copilot bidireccional aportados en esta conversación. Los contratos AMATEUR_USER_FLOW_REVIEW.md, AMATEUR_AUDIO_VOICE_STEERING.md y SONG_SPEC_GEMMA_QWEN_CONTRACT.md mantienen recorrido, calidad y trazabilidad.
No se reescribe desde cero. Se conserva Windows nativo, Python/FastAPI, SQLite, Vue 3/Vite, separación de assets y providers intercambiables.
Decisión de alcance del usuario: la propuesta de servicios pagos y su módulo histórico ProfessionalSongService quedan fuera del desarrollo activo y se conservan para posible reconsideración futura. El objetivo de estos sprints es el estudio local. Los puertos mantienen extensibilidad; no se implementan suscripciones, cobros ni integración remota paga.
El código actual todavía llama a ProfessionalSongService para operaciones locales de Production, ficha, ACE-Step y exportación. Su conservación es compatibilidad temporal, no una decisión de seguir ampliándolo. S00 inventaría esas dependencias; S02/S03 trasladan incrementalmente responsabilidades locales a casos de uso con puertos, manteniendo acceso a datos y rutas compatibles. El módulo histórico no se borra ni se renombra masivamente; se retira del circuito activo cuando sus consumidores locales tengan reemplazo verificado.
Una interfaz común para todos: términos profesionales con explicaciones progresivas, navegación por tarea y acceso libre. No hay modos que oculten controles según experiencia.
La guía no limita el estudio. Una función ausente se identifica como tal; no se muestra un control que simule procesamiento.

## Auditoría de la solución actual
Auditoría estática del árbol de trabajo, incluyendo cambios locales. No se ejecutaron motores, builds, pruebas ni evaluaciones auditivas durante esta planificación. Resultados de pruebas de turnos anteriores no certifican estas nuevas funciones.
Estados: IMPLEMENTED = existe comportamiento concreto en código; PARTIAL = alcance incompleto; MISSING = no localizado; UNSUPPORTED = sin soporte en la ruta examinada; EXPERIMENTAL = necesita validación técnica y auditiva.

| Función | Estado | Motor / evidencia | Acción |
| --- | --- | --- | --- |
| Persistencia de sets, fases y eventos | IMPLEMENTED | core/storage.py; adapters/sqlite/set_repository.py | Reutilizar; añadir revisión transaccional de sesión |
| Ficha versionada y confirmación | PARTIAL | song_specification_service.py; song_workflow_repository.py | Completar esquema, restricciones, edición y fidelidad |
| Gemma/Qwen | PARTIAL | creative_agent_service.py, technical_director_service.py, model_orchestrator.py, providers/llamacpp.py | Separar extracción por reglas de inferencia; compilar respuestas tipadas |
| ACE-Step canción completa | PARTIAL | professional_full_song_service.py; tools/acestep_generate.py | Acreditar ejecución instalada y calidad real |
| Modelo efectivo ACE-Step | PARTIAL | Wrapper predetermina acestep-v15-turbo y LM 0.6B; configuración puede sustituirlos | Registrar versión/checkpoint/hash efectivos; no afirmar modelo cargado desde defaults |
| Repaint / Cover | MISSING | Wrapper solo envía task_type=text2music | Adaptadores por capacidades, originales y propuestas |
| Extract / Lego / Complete | UNSUPPORTED | No expuestos por integración actual | Detectar soporte por checkpoint/API; evaluar alternativa Base; no habilitar por nombre |
| Sample por set y aprobación | PARTIAL | sample_builder.py; storage.py; professional_song_service.py | Mock sin audio representativo; completar aprobación por artefacto/provider/revisión y todas las rutas |
| Mixer | PARTIAL | mixing_service.py | Dos entradas, ganancias prefijadas y salida mono; implementar canales reales |
| Master básico | PARTIAL | mastering_service.py | Procesamiento PCM/normalización y export; falta medición LUFS/true peak y aceptación |
| Exportación y descargas | PARTIAL | professional_export_service.py; audio_download_service.py | Reutilizar aislamiento; añadir revisión aprobada, formatos/configuración y renders parciales |
| Waveform / piano roll | PARTIAL | frontend/src/app.js e index.html | Hay representación/configuración visual; no acredita waveform del archivo ni transporte multipista |
| Timeline, clips no destructivos y transporte | MISSING | No localizado motor de sesión | Implementar reproducción, selección y operaciones |
| Versiones de audio, undo/redo de sesión | MISSING | Revisiones de ficha y eventos no son historial reversible del DAW | Incorporar comandos y renders inmutables |
| Jobs persistentes y cancelación | PARTIAL | FastAPI usa Thread/Lock en memoria; tasks/model_runs persistidos | Ejecutor recuperable por proyecto, cancelación y resultados tardíos |
| Tools, propuestas y Action Router | MISSING | Handoffs existentes no equivalen a herramientas ejecutables | Contratos y flujo vertical de tempo |
| Enciclopedia/tutor educativo compartido | MISSING | Ayuda textual del catálogo | Base canónica, referencias, componentes y contexto |
| Grabación, corrección vocal precisa y voz de referencia | MISSING | Providers vocales configurables no acreditan esas capacidades | Integraciones posteriores con evaluación separada |

### Brechas prioritarias reproducibles desde código
- song_service.py contiene una instrucción para no presentar sample/checkpoint como requisito del flujo principal.
- _require_approved_linked_sample omite el gate cuando user_id no empieza por set: y acepta aprobación de mock sin verificar representatividad para producción real.
- La huella de sample incluye phase_data completo y todos los archivos del draft: cambios administrativos pueden invalidar; tampoco incorpora por sí sola todas las revisiones profesionales, provider y artefacto escuchado.
- La generación vuelve a usar rutas de salida estables: conservar ficha/eventos no garantiza preservar renders anteriores.
- Las acciones globales compatibles y los jobs en memoria necesitan identidad explícita, comprobación de revisión y rechazo de resultados tardíos.
- La cadena de mezcla lee PCM y reduce canales: verificar formato/sample rate antes de mezclar y conservar estéreo.
- La arquitectura del nuevo documento omite set/sample en su diagrama: aplicar invariantes AGENTS a creación y edición.

## Arquitectura objetivo y contratos
Gemma interpreta/enseña; Qwen compila especificación y plan; ModelOrchestrator administra modelos/tasks; MusicActionRouter valida y despacha; los adaptadores ACE-Step, DSP, MIDI y DAW ejecutan.
MusicProjectState es una proyección de SQLite, no un segundo almacén mutable. UI y chat usan las mismas operaciones de dominio.
Reutilizar repositorios con migraciones aditivas. Proponer project_revisions, media_sources, tracks, clips, effect_chains, automation_lanes, action_proposals, operations, audio_renders, evaluations y jobs; decidir tablas exactas en S02.
Las tres piezas obligatorias se mantienen separadas. La sesión referencia set/selecciones; ninguna importación de mezcla crea stems o MIDI ficticios. La idea tiene identidad persistida antes de formar un set completo.

Cada tool define ID, esquema, unidades/rangos, motor, precondiciones, capacidades, efectos, preview, reversibilidad, autorización y conceptos educativos.
Cada propuesta incluye project_id, base_revision_id, proposal_id, acciones ordenadas, IDs de targets, controles afectados, valor anterior/propuesto, motivo, coste estimado y alcance.
Distinguir SET_TRACK_VOLUME_DB de ADJUST_TRACK_VOLUME_DB. El backend decide el engine; no confía en el LLM.
Confirmación explícita vincula propuesta/revisión. Una propuesta editada se revalida. Reject no ejecuta. Idempotency key impide repetición. Cancelación no publica audio parcial.
Preview generativo autorizado y aceptación final son estados distintos. Una comparación A/B no altera el render activo hasta aceptar.
IDs de controles se basan en IDs reales: tracks/{track_id}/volume_db; nombres como guitar pueden ser ambiguos.
Operaciones sobre audio requieren referencias/checksums, tiempo en segundos o ticks definido, sample rate, canales y revisión. Preservar originales y exterior de región mediante composición controlada; registrar tolerancias de transiciones.
Undo de una edición activa restaura referencias; no vuelve a ejecutar generación aleatoria. Restaurar una versión crea una revisión nueva.
Exportar audio aprobado requiere evidencia técnica y aceptación por artefacto. Mock solo valida recorrido mock.

## Arquitectura hexagonal, SOLID y DRY: reglas de implementación
Esta ampliación conserva la arquitectura existente y explicita su evolución. La separación de carpetas no demuestra por sí sola inversión de dependencias.

### Evidencia del código actual
- adapters/http/fastapi_app.py expone casos de uso y adapters/sqlite/ contiene repositorios: separación de adaptadores ya existente.
- providers/base.py define ABC por rol; MusicProvider/VoiceProvider/LyricsProvider exponen nombre/capacidades, pero no un contrato completo de ejecución. Extender contratos estrechos por operación cuando sea necesario; no asumir intercambiabilidad de ejecución solo por heredar esas ABC.
- application/audio_download_service.py usa ProfessionalArtifactSource (Protocol): patrón existente reutilizable para inversión de dependencias.
- SongService y ProfessionalSongService construyen providers, builders y servicios concretos en sus constructores. SongService conserva compatibilidad de entrada; ProfessionalSongService es una implementación histórica a conservar sin ampliar y con consumidores locales pendientes de transición.
- core/storage.py importa repositorios SQLite concretos y combina persistencia, archivos y validación. Mantenerlo como fachada compatible mientras los nuevos casos de uso dependen de puertos pequeños.
- Servicios de mezcla/mastering y generación contienen I/O o ejecución de motor. Separar esos detalles al intervenir sus operaciones; no efectuar una refactorización global previa.
El estado actual es modular con bases hexagonales y acoplamientos pendientes. No se declara conformidad completa con SOLID/DRY mediante esta auditoría estática.

### Límites y dirección de dependencias
- Dominio: entidades, revisiones, unidades, invariantes y políticas; independiente de FastAPI, SQLite, subprocess, ACE-Step y UI.
- Aplicación: casos de uso y coordinación mediante puertos; no importa clases de adaptadores concretos para los módulos nuevos.
- Puertos de salida: protocolos mínimos de repositorio, fuente de medios, generación, DSP/render y ejecución de jobs. Introducirlos por consumidor, reutilizando contratos existentes que sean compatibles.
- Adaptadores: implementan persistencia SQLite, archivos, motores y transporte HTTP. El adaptador HTTP traduce DTO/errores e invoca casos de uso; no contiene reglas musicales.
- Composición: bootstrap/fábrica conecta implementaciones con casos de uso. Las fachadas SongService/StorageManager conservan API y menú durante la transición.
- Frontend: vistas/controladores invocan contratos de API; no ejecutan reglas de autorización ni selección definitiva de engine. La reproducción inmediata puede usar su adaptador local con paridad de render verificada.
El grafo permitido es adaptadores → aplicación → dominio; aplicación depende de abstracciones de salida. La composición conoce ambos lados.

### Criterios SOLID
- S: separar propuesta, validación, ejecución, conocimiento y render; cada módulo tiene una responsabilidad y motivo de cambio definidos.
- O: registrar nuevas tools/providers mediante contratos y registro; evitar ampliar un router monolítico con lógica específica de cada motor.
- L: implementar pruebas contractuales comunes entre mock y motor real; una operación no soportada se declara antes de despacharla y no devuelve éxito simulado.
- I: contratos por capacidad/consumidor; evitar una interfaz universal que obligue a cada provider a implementar grabación, MIDI, DSP y generación.
- D: inyectar puertos y configuración; construir implementaciones concretas en la composición, no en los nuevos casos de uso.

### Criterios DRY
- Una política de set/sample/aprobación por etapa, reutilizada desde todas las entradas.
- Un esquema canónico por parámetro/tool: unidades, rango, ID, validación y vínculo educativo; UI/chat/documento derivan de él sin duplicar reglas como autoridades independientes.
- Un contrato de estado/revisión y persistencia de decisiones; ningún almacén paralelo para el copilot.
- Reutilizar pipeline de validación de audio, render y export cuando sus semánticas coincidan. No fusionar mezcla integrada y stems si sus capacidades difieren.
- Extraer duplicaciones comprobadas al trabajar la funcionalidad; no crear abstracciones genéricas para necesidades hipotéticas.

### Tareas y puertas por sprint
- S00: registrar grafo de imports, composición, acoplamientos y duplicaciones con archivos concretos; distinguir evidencia de código de conformidad arquitectónica.
- S01: centralizar la política de cierre para rutas guiadas/avanzadas/legadas sin copiar gates.
- S02: puertos de estado/revisión/medios y adaptadores SQLite/archivos con migraciones; fachadas compatibles.
- S02/S03: extraer los casos de uso locales actualmente alojados en ProfessionalSongService y conectarlos desde la composición; las nuevas tools no dependen de esa clase. Conservar código histórico y verificar consumidores antes de desconectarlo.
- S03: tools/router y conocimiento consumen protocolos; metadatos canónicos y handlers independientes.
- S04: puertos JobExecutor/AudioProcessor y composición de implementaciones mock/reales.
- S05 en adelante: pruebas de casos de uso con dobles sin motor externo; pruebas contractuales del adaptador y verificación de imports sobre límites acordados.
Cada entrega revisa dirección de dependencias, responsabilidad, reutilización de políticas y compatibilidad. No se acepta duplicar una validación de dominio dentro de endpoints o prompts ni introducir dependencia del SDK ACE-Step en entidades musicales.

## Secuencia y dependencias
Cadencia sugerida: iteraciones de 1–2 semanas, sin compromiso de calendario hasta conocer equipo, hardware y mediciones. Dividir un sprint si no cabe su criterio de salida; no reducir aceptación.
Camino inicial: S00 → S01 → S02 → S03 → S04 → S05 → S06.
S04 entrega transporte mínimo para comparar tempo; S07 amplía timeline. La arquitectura mínima del copilot se construye temprano; sus skills amplias llegan después.
Cada sprint entrega backend + UI + ayuda + pruebas apropiadas + documentación, cuando aplica. No acumular interfaces sin motor.

### S00 — Auditoría ejecutable y capacidades instaladas
Contrato del motor investigado con fuentes oficiales y código instalado: ACE_STEP_CAPABILITIES.md diferencia APIs y tareas documentadas/conectadas. Steering externo por rol e inyección por solicitud implementados, con hashes y estado del wrapper. S06 aún debe compilar la ficha aprobada, validar esquema y mapear BPM/key/compás/idioma; no se habilitan modos nuevos por documentarlos.
El auditor incorpora defaults y alternativas de configuración del wrapper sin importarlo, e inventaría imports directos y relativos. Trece pruebas aprobadas; los valores efectivos no se deducen de defaults.
Continuación 2026-10-04: importación de AceStepHandler 1.5 confirmada con `.venv` en 29,53 segundos; once pruebas del registro/auditor aprobadas. El probe distingue timeout y fallo, sin cargar pesos. La resolución perfil/configuración/checkpoint presenta una discrepancia documentada para S06; falta acreditar el checkpoint efectivo y completar trazabilidad de controles para cerrar S00.
Nueva evidencia: comparación AST de firmas instaladas y wrapper, inventario de lecturas candidatas por v-model y probe opcional de import. La matriz documenta campos guardados sin consumo audible y parámetros ACE-Step estructurados omitidos; estos alimentan S01/S06/S09/S12/S13. Nueve pruebas aprobadas. La generación y aceptación real siguen pendientes.
Ampliación: auditoría de bindings UI, checkpoints/configs y diagnósticos históricos; probes opt-in de hardware y health local con timeouts. STUDIO_CAPABILITY_AUDIT.md documenta matriz y evidencia del entorno .venv. Seis pruebas aprobadas. Sigue pendiente la trazabilidad exhaustiva de parámetros y compatibilidad API/checkpoint efectiva; detección XPU no se presenta como generación verificada.
Avance 2026-10-04: CapabilityRegistry y adaptador RuntimeAudit implementados; CLI scripts/audit_studio.py genera STUDIO_CAPABILITY_AUDIT.json. Tres pruebas validan separación entre configuración, disponibilidad y verificación. Pendiente: inventario exhaustivo de controles/handlers, probes de API/hardware/checkpoints efectivos y decisión de motores. S00 permanece en progreso.
Dependencia: ninguna.
- Inventariar endpoints, tablas, controles/handlers, providers, jobs y artefactos; contrastar contra esta matriz.
- Detectar paquete/API/checkpoint ACE-Step efectivos y hardware, comandos Gemma/Qwen, DSP y soporte de tareas.
- CapabilityRegistry con configured/available/verified/experimental, motivos y evidencia fechada.
- Probar contratos sin descargar modelos ni ejecutar generación larga automáticamente.
Aceptación: matriz por control y motor; capacidades desconocidas quedan no verificadas; ningún default se anuncia como ejecución real.
Salida: reporte técnico y registro reutilizable, decisión sobre motores tempo/stems.

### S01 — Invariantes, sample y fidelidad de cierre
UI/API de revisión: reproducción por set/sample/checksum, confirmación explícita de escucha y aprobación de la versión vigente. Checkpoint sin audio se identifica como mock y no habilita cierre real. La confirmación registra declaración del usuario; no acredita escucha observada, calidad ni generación representativa.
Evidencia WAV interna: integridad PCM/frames, formato/duración/tamaño/checksum y aislamiento de carpeta. Registro en SQLite, aprobación vinculada a checksum, reemplazo revoca aprobación y genera evento; gate verifica el archivo vigente. Pendientes: generación real y reproducción/escucha, representatividad de provider/configuración y exposición del flujo en UI/API. El cierre real sigue bloqueado.
Huella versión 3 incorpora contenido/schema de fichas SQLite vinculadas al set, conservando independencia frente a confirmación y otros sets. Incluye todas las fichas vinculadas por precaución; selección por render, perfil/configuración efectivos y artefacto real siguen pendientes. Las aprobaciones previas requieren regeneración.
Huella versión 2: las fases contribuyen con su contenido, sin metadatos de persistencia ni campos conocidos de navegación. Cambios musicales y campos nuevos siguen invalidando; las aprobaciones anteriores requieren regeneración. Pendientes: semántica de archivos de assets y revisión de spec/provider. Pruebas unitarias e integración SQLite cubren guardar los mismos datos, progreso de Production y cambio de BPM.
Continuación: las llamadas directas a mastering/export y las descargas finales WAV/MP3/FLAC/ZIP verifican la política. La consulta de exportación calcula disponibilidad vigente desde SQLite, incluso si hay manifiesto anterior. Veinte pruebas aprobadas de sets, política y guía; faltan sample real, evidencia de artefacto y revisión de spec/provider antes de habilitar producción real.
Avance: política `SampleGate` con puerto de lectura, compartida por builder mock y cierre histórico; protección adicional en el servicio full-song directo. Rechaza proyectos sin set y aprobación mock para producción real. El cierre real permanece bloqueado hasta implementar evidencia verificable del sample representativo. Pendientes: artefacto/checksum, revisión de spec/provider, huella semántica y cobertura de mastering/export. No se declara S01 completo.
Verificación del avance: 16 pruebas de sets, política y guía aprobadas; conserva recorrido mock y rechaza llamada real directa antes de crear artefactos. La fachada histórica solo delega la política compartida como corrección de compatibilidad.
Corrección preparatoria 2026-10-04: la guía de Gemma en SongService exige set válido y sample vigente escuchado/aprobado en los contextos con y sin set; distingue mock de producción real y explica preparación de las tres piezas. Dos pruebas de regresión aprobadas. Esto corrige la contradicción conversacional detectada en S00; S01 no está completo y todavía requiere aplicar las invariantes a todas las rutas finales del backend.
Dependencia: S00.
- Corregir guía del assistant; exigir set válido y sample en todas las rutas finales.
- Separar aprobación mock/real; sample real representativo con artifact_id/checksum, revisión de spec/inputs y provider/configuración.
- Huella semántica; dependencias explícitas; invalidar confirmaciones/resultados afectados, conservar históricos.
- Sample corto real, reproducción y aceptación; distinguir continuidad deseada de continuidad garantizada.
Aceptación: absent/foreign/stale/mock rechazados en cierre real; configuración administrativa no invalida audio; cambio musical sí; errores indican acción concreta.

### S02 — Proyecto editable y versiones no destructivas
Dependencias: S00–S01.
- MusicProjectState, identidad de idea/proyecto/set/canción/sesión; revisiones y control optimista de concurrencia.
- Fuentes originales inmutables con checksums; renders por versión; tracks/clips mínimos y referencias.
- Command history, undo/redo persistido, restore y autosave de edición manual; propuestas IA no se autoguardan como aceptadas.
- Migración de proyectos existentes sin perder assets, exportables ni eventos; snapshots JSON/Markdown derivados.
Aceptación: reiniciar conserva sesión e historial; undo/redo exacto; dos pestañas no sobrescriben revisión; originales siguen intactos.

### S03 — Tools, Router, propuestas y conocimiento mínimo
Dependencia: S02.
- MusicToolRegistry/MusicActionRouter, esquemas tipados y estados de propuesta.
- Endpoints leer/proponer/editar/confirmar/rechazar/ejecutar/undo, IDs estables de controles.
- MusicKnowledgeService y EducationalField mínimos para BPM/tempo, gain y pan; fuente única versionada.
- Adaptador de propuesta mock y salida Gemma/Qwen validada bajo ModelOrchestrator.
Aceptación: rechazar tool inexistente, parámetros fuera de rango, destino ambiguo, falta de autorización y revisión obsoleta; explicación recupera decisiones reales.

### S04 — Jobs recuperables, transporte y render de tempo
Dependencias: S02–S03.
- Jobs persistentes por proyecto, progreso, cancelación, idempotencia, recuperación y aislamiento.
- Transporte mínimo Play/Pause/Stop/Seek y A/B sobre audio real.
- Tool set_tempo: metadato para proyecto sin audio; MIDI por mapa temporal; audio mediante time-stretch compatible o regeneración declarada.
- Seleccionar motor DSP con evidencia; preservar pitch cuando se solicita; nuevo render y duración/marcadores coherentes.
Aceptación: 120→108 BPM no se presenta como cambio audible sin render; original intacto; jobs tardíos no reemplazan activo; cancelar permite continuar.

### S05 — Primer flujo vertical Copilot de tempo
Dependencias: S03–S04.
- Chat contextual → propuesta 120→108 → explicación/diff → resaltar Tempo → editar propuesta → confirmar → ejecutar → UI/audio actualizados → A/B → undo.
- Control manual llama a la misma tool y validaciones; IA nunca opera DOM ni código arbitrario.
- MusicTutor explica BPM, consecuencias y límites desde datos persistidos.
Aceptación: prueba integral con motor simulado y evidencia real del motor elegido; recarga, rechazo, error, doble confirmación, cambio concurrente y undo cubiertos.
Hito: primer coproductor operativo; no ampliar tools hasta cumplirlo.

### S06 — Creación guiada, ficha completa y ACE-Step real
Ampliación de contratos compartida con S10: preview y wrapper con seis tasks, validación por modelo/fuente/pistas/intervalo y audit del enum realmente enviado. Sigue sin selección pública de task ni ejecución verificada; requiere Base, artefactos, plan aprobado y UI. No declarar S06/S10 completos.
Avance: compilador determinista y endpoint de preview para seis tareas desde ficha confirmada SQLite; flags musicales/tareas enviados al handler; Base 1.5 instalado con checksum de peso verificado. Fuente opcional vinculada a artefacto propio, integridad/duración/hash e intervalos comprobados. Pendientes: controles públicos, persistir/aprobar plan y letra, conexión a ejecución, carga efectiva, sample representativo y generación real.
Dependencias: S01–S05.
- Idea persistida, tres piezas propuestas/seleccionadas, set, ficha editable y revisiones compartidas con chat.
- Catálogo por esquema/capacidades: título/artista/género/subgénero, BPM/compás/escala, estructura, voz, requisitos/exclusiones, audio y export.
- Gemma recoge; Qwen produce especificación estructurada y comprobación de viabilidad, con provenance y deseos obligatorios.
- Adapter ACE-Step text2music desde revisión confirmada; sample/final ligados a condiciones relevantes; guardar seed/modelo/parámetros y fidelidad.
Aceptación: crear una canción cantada real desde idea con sample aprobado; letra/restricciones verificadas y escucha registrada; fallos no pierden trabajo.
Hito: creación completa evaluable, sin afirmar calidad universal por archivo generado.

#### S06-A — Decisiones e insumos compartidos (en progreso)

Avance inicial: catálogo 1.1 incluye las entradas de tareas ya soportadas por el compilador, aplicabilidad y requisitos condicionales. La ficha muestra esas entradas y señala ejecución pendiente; nueve pruebas aprobadas. Todavía es consulta de cobertura: falta edición sincronizada con chat, referencia autorizada y trazabilidad por decisión.

Continuación: editor visible para seis acciones y entradas específicas; guardado explícito en revisiones existentes, procedencia y comprobación transaccional de revisión. Fuentes seleccionadas desde registros del proyecto con WAV/duración comprobados. Mantiene confirmación pendiente. Falta edición completa por requisito, tools del chat, referencia e importación.

- Evolucionar catálogo/esquema existentes con modo, config, fuente/referencia por artefacto, pistas, intervalo, fuerza de conservación y controles técnicos validados. Por campo: disponibilidad, dependencia, origen, obligatoriedad y confirmación.
- Migración compatible de decisiones/requisitos; distinguir dato histórico sin procedencia de deseo explícito. Mantener revisiones existentes y tres intenciones.
- UI progresiva con seis acciones comprensibles y motivo de bloqueo; mostrar campos aplicables, propuestas, configuración guardada y pendientes. Chat y controles usan la misma revisión.
- Validar contradicciones y requisitos sin ruta efectiva; no ocultar exclusiones o estructura que el caption actual no transporta.
- Aceptación: se pueden definir/revisar las entradas de los seis modos sin ejecutar audio; decisiones confirmadas no cambian por una propuesta y no se confirman campos por silencio.

#### S06-B — Plan persistido, aprobación e invalidación

Avance: `ace_step_plans` SQLite, snapshot y eventos; preparar/consultar/aprobar con revisión/hash y confirmación de letra. Recompilación detecta ficha/fuente cambiadas; UI recupera estado y diferencia aprobación histórica/efectiva. Falta vincular letra del plan al asset/set y completar dependencias de configuración/provider/sample. No autoriza ejecución final.

- Guardar versiones ACEPlan en SQLite con ficha/letra/set/fuentes, decisiones de origen, defaults y rutas por requisito. Snapshots regenerables.
- Aprobar exactamente revisión/hash mostrado; rechazar aprobación obsoleta. Cambios creativos/fuentes/config invalidan plan y sample relevantes.
- Distinguir plan creativo aprobado de disponibilidad técnica y autorización exploratoria. Conservar candidato, original y eventos de rechazo.
- Aceptación: recarga, cambios concurrentes, sustitución de audio, confirmación duplicada y restauración no reutilizan un plan obsoleto.

#### S06-C — Adaptador de ejecución de los seis modos

Inicio: traductor de payload a lista de argumentos y archivos de texto, con coincidencia de perfil y rechazo de campos sin traducción. Sin procesos ni conexión al runner todavía; no declarar S06-C completo.

Continuación: runner de canción completa local consume plan text2music aprobado/vigente y letra idéntica a la del proyecto, con `shell=False` y trazabilidad en artefactos. Mantiene gate real de sample y recursos. Falta runner de candidatos para las otras cinco tareas, revalidación al arrancar/registrar resultado, sample real y pruebas de audio; S06-C sigue en progreso.

Avance posterior: runner exploratorio para seis tareas reutiliza proceso/recursos, autorización explícita, plan vigente, carpeta única, revalidación previa/posterior, integridad WAV y trazabilidad sin sustituir original/sample/final. Exclusividad local compartida con final. Pendientes: cola/UI/cancelación, orquestación integral, preflight y audio real. Contrato en sección 20 de `ACE_STEP_CAPABILITIES.md`.

Continuación: dispatcher local con tasks/model runs persistidos, consulta por proyecto, recuperación de interrupciones y UI de autorización/estado/reproducción con checksum. 21 pruebas y build aprobados. Falta cancelación, orquestación/preflight completos y validación real; S06-C sigue en progreso. Contrato en sección 21 de `ACE_STEP_CAPABILITIES.md`.

Cancelación implementada: control UI y endpoint por trabajo/proyecto; pendiente/cancelling/cancelled, señal cooperativa al runner, terminación de árbol/grupo y restauración. 24 pruebas con procesos simulados y build aprobados. Falta validación con ACE-Step real, orquestación/preflight y evaluación; no cerrar S06-C. Contrato en sección 22.

Preflight inicial: archivos/config/arquitectura/compartidos comprobados antes de task y en runner; reporte persistido. Gate explicito de disponibilidad negativa antes de Popen con restauración de modelos. Base pasó presencia local; 27 pruebas aprobadas. No acredita hardware/carga; orquestación integral y mediciones reales siguen pendientes. Contrato en sección 23.

Orquestación inicial: puerto de lifecycle conecta jobs con ModelOrchestrator; pausa/retorno persistidos, estado según task y bloqueo de handoffs/Gemma real mientras hay audio activo. 33 pruebas aprobadas. Falta cobertura de llamadas directas a providers, medición física de memoria y validación real; S06-C no está completo. Contrato en sección 24.

Registry: guard inyectado desde orquestador bloquea nuevas inferencias Gemma/Qwen directas ante task activa o lock de candidato/final. 29 pruebas aprobadas. Quedan inferencias concurrentes ya iniciadas, medición física, procesos huérfanos y validación musical; no cerrar S06-C.

Reserva local completa: registry mantiene exclusividad de planificación durante inferencia; audio rechaza inicio concurrente y adquisición vuelve a comprobar conflicto tras guard. 32 pruebas aprobadas; falta coordinación externa/distribuida, medición física y validación real. No cerrar S06-C.

- Reutilizar wrapper y política de tareas; traducir el plan validado mediante argumentos estructurados/archivo de entrada, sin interpolar texto creativo en shell.
- Revalidar artefactos, checksums, duración, rangos, config/capacidades y revisiones antes del proceso. Registrar payload efectivo, seed, checkpoint y task.
- Orquestar exclusividad, descarga real de Gemma/Qwen, recursos y recuperación; LM interno solo cuando la ruta lo implemente explícitamente.
- Mantener compatibilidad del servicio local activo; no desarrollar el servicio histórico de APIs pagas.
- Aceptación: contrato mock de las seis tareas hasta handler, entradas sin omisiones silenciosas y recuperación sin perder originales; prueba separada de carga efectiva en este hardware.

#### S06-D — Sample y evaluación de fidelidad

Inicio: informe persistido por candidato con revision/hash y duracion objetiva. Comparacion text2music solo con tolerancia aprobada; edicion y resto de requisitos pendientes de analisis/escucha. Vista UI de comparacion; 12 pruebas aprobadas. Falta aceptacion musical, evaluadores adicionales y sample real; no cerrar S06-D.

Continuación: control visible para definir/eliminar tolerancia de duracion; guardado en revision pendiente, sin default y con validacion numerica. 12 pruebas y build aprobados. Pendientes criterios adicionales, revision de escucha persistida, evaluadores musicales y sample real; S06-D sigue en progreso.

- Generar sample real representativo desde plan/set vigentes, escuchar y aprobar artefacto específico. No usar audio guía/mock para autorizar final real.
- Informe por requisito vinculado a audio/revisión: integridad/duración medidas primero; tempo/tonalidad/letra/instrumentos/voz/melodía con métodos disponibles y límites explícitos.
- UI comparación intención/resultado y A/B, requisitos pendientes/incumplidos y corrección propuesta por modo; sin porcentaje global ficticio.
- Aceptación: ninguna evaluación desconocida se anuncia cumplida y ninguna task completada sustituye aprobación por escucha.

#### S06-E / S10 — Validación real y cierre gradual

- Un caso real por modo, con recursos/tiempo/config/inputs/outputs y escucha registrados. Desbloquear disponibilidad por modo según evidencia, sin esperar que todos tengan el mismo rendimiento.
- Repaint/Lego conservan originales y evalúan contexto/joins; Extract evalúa fugas; Complete evalúa convivencia del arreglo; Cover evalúa objetivo/conservación; text2music evalúa canción y letra.
- Ejemplo trazable desde idea hasta descarga con set/sample vigentes, errores recuperables y correcciones parciales. Prueba con personas sin experiencia musical para validar UX.
- Aceptación: seis modos integrados y estado de verificación visible; calidad/fidelidad aprobadas para los casos probados, sin prometer resultados universales.

Este desglose incorpora el adjunto de fidelidad del usuario y no altera las dependencias de timeline/mixer/DSP de S07–S13. La integración inicial de entradas y ejecución de las seis tareas puede avanzar en S06; la edición contextual completa requiere los componentes de S10.

### S07 — Timeline y edición de clips
Dependencias: S02, S04, S06.
- Waveform derivada del archivo, ruler, zoom horizontal/vertical, selección, secciones/markers, loop, snap/grid.
- Split/trim/move/copy/paste/duplicate/delete/silenciar/bloquear, fades/crossfades y reproducción por región.
- Editar/duplicar/reordenar secciones, duraciones, repeticiones y transiciones con dependencias claras.
Aceptación: export coincide con reproducción; edición no destructiva, undo/redo y límites temporales; cambios de estructura afectan material real o se identifican pendientes.

### S08 — Importación, stems y pistas verificadas
Dependencias: S00, S02, S07.
- Import audio/MIDI con validación de formato, sample rate, canales, duración, metadata/checksum.
- Separación de fuentes por provider compatible; evaluar extract sin asumir soporte; conservar mezcla fuente.
- Tracks por material real: lead/backing/drums/bass/guitar/etc.; renombrar/color/agrupar/lock/duplicate/delete.
Aceptación: no inventar pista guitarra desde un mix; sincronía de stems verificada; extracción con fugas identificada; jobs cancelables.

### S09 — Mixer básico audible y export coherente
Dependencias: S07–S08.
- Gain/volume dB, pan, mute/solo, master bus, medidores RMS/peak.
- Motor estéreo, conversión validada de sample rate, headroom, persistencia y render offline equivalente.
- Tools compartidas con UI; context learning y A/B.
Aceptación: cambio de guitarra solo afecta pista disponible; pan/mute/solo audibles; clipping detectado; render y playback coinciden dentro de tolerancia documentada.

### S10 — ACE-Step edición generativa
Dependencias: S00, S02, S07–S09.
- Repaint/cover; extract/lego/complete solo con variante/API probada.
- Selección temporal/track, contexto mínimo, restricciones, preview autorizado y aceptación/rechazo.
- Componer fragmento preservando audio exterior; joins/crossfades; mantener revisión y provider.
Aceptación: original recuperable, fuera de selección conservado según política, transición escuchada; task incompatible rechazada antes de job.
La salida generativa no promete edición exacta de nota/sílaba/acorde.

### S11 — DSP principal y routing
Dependencia: S09.
- EQ paramétrico y filtros/shelves; compresor threshold/ratio/attack/release/knee/makeup/mix; reverb/delay/limiter/gate.
- Inserts ordenados, sends/returns, aux buses y sidechain; bypass/A/B.
- Todos los parámetros con unidades/rangos/ayuda común y tools operativas.
Aceptación: procesamiento medible, estado persistido, routing sin ciclos no soportados, edición manual e IA equivalentes.

### S12 — MIDI, armonía e instrumentos
Dependencias: S02, S07, S09.
- Piano roll operativo: pitch/octava/duración/velocity, snap, transpose, quantize/humanize.
- Editor de acordes/progresiones, arpegios, patrones/fills/articulaciones y presets con instrumento virtual compatible.
- Render/bounce/freeze y export MIDI; mapear arreglo/secciones a notas.
Aceptación: notas editadas se escuchan y exportan; congelar restaura fuente editable; audio a MIDI sigue experimental hasta evaluación.

### S13 — Vocal, grabación y efectos adicionales
Dependencias: S08–S09, S11–S12 según operación.
- Record/monitor/metrónomo/count-in, permisos de micrófono, latencia y alineación.
- Pitch/time/formant y corrección vocal con motor especializado; nota por nota solo cuando probado.
- De-esser/noise/click/resonancias, respiraciones selectivas, dobles/coros/armonías y timing.
- Chorus/flanger/phaser/saturation/distortion/doubler/width mediante DSP verificado.
Aceptación: referencia/original intactos; límites/artifacts documentados; nunca llamar canto a TTS ni prometer corrección perfecta.

### S14 — Copilot general y skills musicales
Dependencias: S05 y tools de S09–S13.
- Selección/pantalla/track/región/valores/análisis/historial disponibles; localizar y explicar controles.
- Planes multiacción y skills improve_vocals/make_chorus_powerful/balance_mix usando tools disponibles.
- Orden/dependencias y recuperación ante fallo parcial; decisiones artísticas identificadas como recomendaciones.
Aceptación: “coro más épico y guitarra -3 dB” produce plan validado, efectos reales, límites y aprobación; no procesa elementos no autorizados.

### S15 — Automatización
Dependencias: S07, S09, S11–S12.
- Lanes y puntos/curvas por track/clip/sección, interpolación, unidades, bypass y modes documentados.
- Volume/pan/gain/efectos/EQ/MIDI y cambios de instrumentos compatibles.
Aceptación: playback/render iguales; undo/reordenar secciones preserva anclajes definidos; automatización no pelea con fader sin regla explícita.

### S16 — Análisis, master y export avanzado
Dependencias: S09, S11, S15.
- LUFS/true peak/peak/RMS/clipping/espectro/estéreo/dinámica; BPM/key/chords/notes como estimaciones con confianza.
- Master EQ/compression/multiband si soportado/saturation/width/limiter, referencia/A-B y perfiles calibrados.
- Export WAV/MP3/FLAC/MIDI/stems/acapella/instrumental por pista/sección con rate/bit depth/bitrate/dither/metadata.
Aceptación: métricas por versión, formatos técnicamente verificados, escucha completa/aceptación separadas; export pertenece al render aprobado.

### S17 — Biblioteca educativa y validación universal
Dependencias: S03 y controles implementados; contenido se amplía durante cada sprint.
- ConceptRelationshipGraph, ContextualLearningPanel, AudioExamplePlayer y AIActionExplanation.
- Teoría, ritmo, armonía, composición, instrumentos, voz, acústica, síntesis, MIDI, audio, mezcla/master e IA.
- Fuentes/licencias/revisión editorial, accesibilidad teclado/lector de pantalla y navegación libre.
Aceptación: todo control responde qué/para qué/cómo/efecto/uso/evaluación/fuentes; tutor y formularios no contradicen unidades ni capacidades; piloto con amateurs y revisión de productores.
No requiere curso previo para crear o editar.

### S18 — Voz personalizada opcional
Dependencias: S01–S02, S06, S08, S13, S16.
- Referencia autorizada importada/grabada, checksums/originales, perfil/versionado y borrado con dependencias.
- Provider de canto/referencia o conversión evaluado; sample representativo y aceptación de identidad.
Aceptación: canto real, naturalidad/parecido evaluados; referencia de estilo no se etiqueta clonación; ruta generada sigue disponible.

## Cobertura del inventario funcional
| Requerimiento original | Sprints responsables |
| --- | --- |
| 1 Proyecto, autosave, versiones e import/export | S02, S06, S08, S16 |
| 2 Estructura/secciones/transiciones | S06, S07, S10, S15 |
| 3 Pistas, buses, record/monitor, freeze/bounce | S08, S09, S11, S12, S13 |
| 4 Editor audio, stretch/pitch/alineación | S04, S07, S13 |
| 5 Afinación, timing, limpieza y creatividad vocal | S11, S13, S18 |
| 6 MIDI, piano roll, armonía, instrumentos virtuales | S12, S15 |
| 7 Instrumentos y arreglos | S06, S10, S12 |
| 8 Mixer, EQ, compresión, FX/routing/sidechain | S09, S11, S13 |
| 9 Automatización | S15 |
| 10 Master | S16 |
| 11 IA generativa/correctiva y alcance de cambios | S03, S05, S06, S10, S13, S14 |
| 12 Análisis | S13, S16 |
| 13 Transporte, navegación, grabación | S04, S07, S13 |
| 14 Exportación | S12, S16 |
| 15 Vistas | S05–S17: evolución por tarea de la UI existente, sin rediseño masivo |
| 16 Requisitos técnicos | S01–S04, todos los criterios de salida |
| 17 Auditoría y límites de modelos | S00 y registro de capacidades continuo |
Filosofía universal: S03/S17 y todos los controles. Copilot bidireccional: S03–S05/S14. Arquitectura ACE/DSP/DAW: S02–S04 y adaptadores posteriores.

## Verificación y definición de terminado

Avance S06/S10 (2026-10-04): Base 1.5 instalado con revisión fijada y SHA-256 de pesos verificado; perfiles Base/Turbo y traducción de plantillas históricas corregidos. 57 pruebas de regresión aprobadas. Evidencia y límites en la sección 16 de `ACE_STEP_CAPABILITIES.md`. Ambos sprints siguen en progreso: falta carga efectiva, conexión de planes aprobados a ejecución/UI y generación/evaluación real por modo.

Continuación S06: vista previa enlaza artefacto fuente del proyecto, verifica integridad WAV PCM/duración/SHA-256 y limita intervalos Repaint/Lego a la duración real. Evidencia incorporada al hash del candidato mediante puerto y adaptador; 25 pruebas aprobadas. Falta persistencia/aprobación, revalidación al ejecutar y selección visible de artefactos en UI. Contrato en sección 17 de `ACE_STEP_CAPABILITIES.md`.

- Migraciones repetibles y restauración de proyectos antiguos; SQLite activo y snapshots regenerables.
- Pruebas de dominio: unidades/rangos/identidad/revisión/idempotencia/autorización y dependencias.
- Contratos de motor con mocks; audio sintético conocido para DSP; integración real separada y fechada.
- Flujos UI para propuesta/edit/confirm/reject/progreso/errores/recarga/undo, controles manuales y aislamiento entre proyectos.
- Build frontend y checks Python apropiados; menú y ejecución local funcionales.
- Audio: integridad, métricas y escucha; fidelidad evaluada por requisitos de la revisión. Registrar hardware/provider/seed.
- Usabilidad/accesibilidad: evidencia con personas sin experiencia; no declarar experiencia validada por tests.
- README y contrato afectado actualizados; entregas indican implementado/mock/experimental/real verificado.
- Ninguna task completada equivale por sí sola a aceptación creativa o aprobación del audio.
Riesgos abiertos: compatibilidad del paquete ACE-Step instalado, recursos de hardware, calidad de stems, artefactos de stretch, latencia de reproducción/monitor, motores vocales y alcance del DAW. S00 resuelve inventario y S04/S08/S13 aportan evidencia; no se promete fidelidad absoluta.
