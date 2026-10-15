# S05-03: regresión Qwen resuelta — 2026-10-09

Arranque PowerShell ahora respeta .env y overrides; revisión larga real completada con perfil vigente. [Evidencia](QWEN_STARTUP_PROFILE_FIX_20261009.md). S05-03 V0,5→1; D/V90,5%, aceptación posterior y audio al final.

# S06-01: lote de presentación — 2026-10-09

Contraste exploratorio de siete pasos sin incidencias detectadas; seis estados de generación simulados verificados. Cancelar generación reemplaza etiqueta ambigua. Build y prueba focalizada aprobados. [Evidencia y cobertura restante](BUILDER_ACCESSIBILITY_BATCH_20261009.md). D/V89,9%, sin cambio de estado; siguiente lote UI/backend de corrección/entrega.

# Lote ligero UI/backend — 2026-10-09

S01-01/S06-01/S10-07: eliminado bloqueo residual de sample en producción, guía sin requisito MIDI, siete pasos/recarga/ayuda verificados con Playwright. 59frontend/20backend/build aprobados. [Evidencia y pendientes](BUILDER_BATCH_QA_20261009.md). D/V89,9%, estados sin cambio; contraste integral/modelos/audio pendientes.

# Orden de trabajo vigente — 2026-10-09

Por indicacion del usuario: revisar y completar desarrollo; verificar componentes ligeros por criticidad y flujo UI/backend end to end en lotes; despues Gemma/Qwen reales y finalmente ACE-Step/audio real. Este orden aplica independientemente de la fase del sprint. Seleccion, gates y cobertura por componentes en [VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md). Aceptacion despues de D/V100%; evidencia historica no se borra. [Revision transversal y pendientes](DEVELOPMENT_REVIEW_AUDIO_LAST_20261009.md). [Porcentaje vigente](SPRINT_PROGRESS.md). Las entradas anteriores de progreso son historicas.

# Plan de sprints — AI Music Studio

## Seguimiento calculado por entregables — 2026-10-08

### S03-04: extracción completada y verificada — 2026-10-08

Siete comandos pequeños con contexto persistido y composición local sustituyen las últimas delegaciones. SongService no reconstruye la ficha automáticamente ni simula carga Qwen; ProfessionalSongService queda diferido y conserva compatibilidad usando los mismos comandos. Cero delegaciones directas al monolito y cero inicialización histórica al arrancar. Master usa letra activa; no se añade MIDI como requisito de ACE-Step ni se modifica la política de sample. 33 pruebas backend agrupadas aprobadas, compileall/diff correctos; smoke ASGI temporal de UI/catálogo/proyectos devuelve 200. Providers de prueba, sin inferencia/audio real ni suite completa. [Evidencia y límites](S03_LOCAL_SERVICE_EXTRACTION_STATUS.md). S03-04: D/V completos, aceptación pendiente; **avance global 66,9%** (antes 65,7%).


### S03-04: consultas, regeneración y exportación locales — 2026-10-08

LocalProductionArtifactQueries comparte siete lecturas sin instanciar generación; servicios previos reutilizan el lector. ArtifactRegeneration despacha handlers actuales, preservando propuesta/revisión explícitas de letra. ExportLocalProject mantiene ficha confirmada, SampleGate, archivos de master y verificaciones locales sin reconstrucción histórica; guard de ficha compartido. 16 pruebas backend agrupadas aprobadas, compileall correcto; fixtures/dobles no acreditan audio real. Delegaciones directas a ProfessionalSongService: **16 → 7**, quedan comandos históricos de generación y su inicialización. Inventario en docs/S03_LOCAL_SERVICE_EXTRACTION_STATUS.md. Global 65,7%; S03-04 sigue parcial hasta extraer los siete restantes.


### S03-04: recopilación de intención local sin guardar sugerencias — 2026-10-08

CollectLocalIntent sustituye la recopilación histórica por tarea assistant/Gemma con contexto/revisión persistidos. Sin autoeditar ficha, aprobación Qwen simulada ni modelos encadenados. Errores/mock no se anuncian como éxito; UI conserva revisión, bloquea cambios pendientes y respuestas de otro proyecto. Catálogo de fases usa consulta local. 15 pruebas backend, 2 Node y 1 compatibilidad histórica aprobadas; build/compileall correctos, providers simulados. [Inventario y pendientes](S03_LOCAL_SERVICE_EXTRACTION_STATUS.md): quedan 16 delegaciones históricas de plan/MIDI/audio/export/regeneración y su inicialización; servicio conservado. D/V de S03-04 permanece parcial, global 65,7%.


### S03-04: propuesta de letra verificada en interfaz — 2026-10-08

Playwright MCP verificó propuesta sin persistencia, incorporación como borrador, guardado explícito con traza SQLite, recarga, descarte, protección y respuesta tardía; Production dirige a revisión en Letra. Generación simulada identificada, backend/SQLite reales solo en QA. Backend amplía protección a líneas/dirección, rechaza formato vacío, explicación inicial y texto que supera el límite conectado de 4096 caracteres; mensajes de fallo distinguen propuesta de compilación. Evidencia y límites en [QA_FULL_LYRICS_PROPOSAL_2026-10-08.md](QA_FULL_LYRICS_PROPOSAL_2026-10-08.md). 21 pruebas backend agrupadas aprobadas, build Vite y compileall correctos; inferencia real y consumidores históricos pendientes, global 65,7%.


### S03-04: revisión y guardado de propuesta de letra en UI — 2026-10-08

La fase Letra permite solicitar una propuesta desde la ficha guardada, leerla, descartarla o incorporarla como borrador. Incorporar no persiste: Guardar letra confirma explícitamente. Se bloquea sustitución con contenido protegido o cambios pendientes; proyecto/revisión se comprueban al aplicar. El guardado resuelve task persistida en backend, exige tarea completada de tipo propose_full_lyrics y misma ficha/revisión; conserva texto propuesto, hash del texto guardado y transformaciones Markdown→secciones→guardado. Rechaza tareas fallidas o revisión ajena. Prueba SQLite de propuesta/traza aprobada, compileall y build Vite correctos. Pendiente batch Playwright del recorrido nuevo e inferencia real Gemma; global permanece 65,7%, sin cerrar S03-04.


### S03-04: propuesta de letra mediante orquestador — 2026-10-08

PrepareFullLyricsProposal usa MusicSpec persistida y revisión de origen, tarea propose_full_lyrics con rol assistant/Gemma por registry y steering; entrega propuesta separada sin editar ficha ni archivos de letra. Resultado mock/error/sin formato o que omite frases requeridas/incluye contenido excluido deja task failed, sin éxito simulado. Letra protegida dirige a asistencia por sección. SongService.generate_professional_lyrics usa tarea local, servicio histórico conservado. Prueba integrada con provider simulado cubre task persistida/estado/spec intacta y rechazo de mock/restricciones; no prueba inferencia real. Falta presentar/guardar propuesta en UI y verificar Gemma real; global 65,7%.

### S03-04: revisión local de letra sin aprobación simulada — 2026-10-08

LocalLyricsReview evalúa mediante reglas públicas compartidas la letra activa SQLite (o snapshot identificado), sin servicio histórico ni ModelManager simulado. Reporte/evento registra revisión, checksum, issues/métricas y recomendaciones; model_review_executed=false, approved_by_qwen=false, user_approval=false. No escribe lyrics_approved.json ni avanza fase/revisión. Detecta cambio de revisión entre lectura de ficha y letra. SongService.review_professional_lyrics usa revisión local; ProfessionalSongService conserva compatibilidad histórica. Cuatro pruebas agrupadas aprobadas y compileall correcto. Generación de letra/recopilación de intención históricas aún pendientes; global 65,7%.

### S03-04: creación concurrente protegida en SQLite — 2026-10-08

Creación local vinculada usa reuse_linked: BEGIN IMMEDIATE serializa comprobación e inserción, rechaza vínculos ambiguos y devuelve ficha existente sin nuevo evento de creación. CreateLocalProject identifica carrera perdida y no sobrescribe spec/export/eventos del ganador. Nueve pruebas agrupadas aprobadas: dos conexiones independientes y barrier producen un ID y un evento, revisión conservada, vínculos inválidos/ambiguos rechazados, carrera perdida sin upsert. Protección aplica a creación local con reuse_linked; escritores históricos compatibles no se migran automáticamente. La preparación posterior no es una transacción única: una segunda respuesta puede observar proyecto aún preparándose, pero no lo reescribe. Global 65,7%; S03-04 sigue parcial por consumidores históricos.

### S03-04: reutilización de fichas y regresión local agrupada — 2026-10-08

Pruebas SQLite nuevas: preparar repetidamente un set vinculado conserva ID, título, revisión y eventos, incluso con título distinto enviado; dos vínculos ambiguos bloquean sin escribir. Comprobación QA real repite preparación de Isabella/Alma y conserva exactamente dos proyectos y revisiones. Batch agrupado creación/consulta/letras/export/revisiones: 11 pruebas aprobadas. La comprobación cubre llamadas secuenciales; no acredita exclusión entre workers concurrentes. S03-04 conserva pendiente creación concurrente y consumidores históricos de generación/revisión. Global 65,7%; sin cambios en proyectos de producción ni generación de audio.

### S03-04: creación y validación UI verificadas en QA — 2026-10-08

Prueba desde acción Vue de creación y controles visibles: proyecto temporal song_570e11111217, revisión 1 pending/invalid; configurar y guardar crea revisión 2 valid/pending/Qwen false; confirmar crea revisión 3 confirmed/valid/Qwen false, respuestas 200. Detectado duplicado vinculado al reutilizar un set QA: lectura Builder 400 por varias fichas. Creación ahora devuelve vínculo existente sin sembrar otra ficha y rechaza vínculos ambiguos. Ficha temporal QA retirada tras verificar identidad; archivos de evidencia conservados, proyectos originales intactos. Corregido mensaje que pedía Enviar intent para aprobar. Tres pruebas creación y build aprobados; falta regresión de idempotencia y generación/revisión histórica. Global 65,7%.

### S03-04: validación inicial explícita desde set — 2026-10-08

Preparación guarda creative_brief desde descripción y lista real de campos obligatorios pendientes. Marcador _preparation conserva necesidad de revisión hasta tener cobertura válida. Guardar configuración entrega modelo/tarea/API visibles aunque no hayan cambiado; edición valida campos presentes, motor y fuente/referencia, recalcula campos pendientes y registra validez determinista sin aprobación Qwen ni confirmación automática. UI explica la acción siguiente. Batch previo ocho pruebas aprobado más nueva prueba SQLite de ficha completa/incompleta (tres casos creación aprobados); build correcto. Pendiente recorrido de creación UI y extracción de generación/revisión histórica. Global 65,7%.

### S03-04: creación local desde set sin aprobación implícita — 2026-10-08

CreateLocalProject valida las tres piezas disponibles antes de crear; prepara ficha, intenciones separadas, fases y documento de letra desde set persistido; guarda pending/valid=false/approved_by_qwen=false y evento de preparación sin ejecución de modelo. Proyección histórica extraída a SetMusicSpecProjection y compartida por compatibilidad, sin borrar ProfessionalSongService. SongService.create_professional_project usa preparación local. Dos pruebas del contrato y regresión de consulta aprobadas, compileall correcto. Falta integrar revisión/validación inicial y probar creación desde UI; no cerrar S03-04. Global 65,7%.

### S03-04: consultas locales de proyectos sin mutación — 2026-10-08

Nuevo LocalProjectQueries con puerto de lectura; SongService lista proyectos, obtiene proyecto y consulta eventos sin ProfessionalSongService ni preparación implícita. La ruta de compatibilidad histórica conserva su preparación; las lecturas locales no siembran artefactos ni reconstruyen intención al abrir. Prueba SQLite verifica dos proyectos, revisiones/eventos intactos y rechazo de ID inexistente; QA consolidada Alma/Isabella también confirma revisiones sin cambios. Compileall correcto. S03-04 conserva parcial por creación vinculada al set y generación/revisión históricas; global 65,7%.

### S03-04: acceso local a letras con prioridad SQLite — 2026-10-08

LocalLyricsAccess permite consultar letras sin ProfessionalSongService. Si la revisión contiene _lyrics_document, devuelve su markdown, documento, idioma y revision_id desde SQLite, aunque el archivo derivado discrepe. Sin documento activo mantiene compatibilidad explícita legacy_snapshot. La edición histórica queda bloqueada cuando hay documento activo y dirige al editor de fase, evitando sobrescritura silenciosa; ruta antigua sin documento conserva edición. SongService consulta/edita mediante servicio local. Dos pruebas aprobadas (DB prevalece sobre archivo, rechazo intacto y compatibilidad), compileall correcto. Generación/revisión históricas aún no extraídas; S03-04 parcial y global 65,7%.

### S03-04: exportables locales y descarga verificada — 2026-10-08

LocalProjectExportService contiene lógica compartida de exportables, verificación y descarga; ProfessionalExportService conserva entrada compatible por herencia. SongService usa servicio local para get_export, descarga, listado/verificación y facade de última descarga. Corregido confinamiento de ruta: pertenencia real al proyecto en vez de prefijo, rechaza carpeta hermana. Dos pruebas locales aprobadas (ruta externa, descarga propia y modificación checksum); regresión histórica ejecutada: dos casos aprobados y dos omitidos por gate de entorno, no acreditados como pass. Compileall correcto. Se preservan gates de sample/calidad existentes. S03-04 sigue parcial por composición de proyectos/letra y acciones históricas; global 65,7%. Sin generar audio.

### S03-04: ejecutor de audio local compartido — 2026-10-08

Extraído LocalAudioProcessService: preparación y presupuesto de recursos, proceso/timeout/cancelación, eventos, entorno, diagnóstico y helpers de argumentos. SongService compone ejecutor local y lo entrega al runner de candidatos directamente; ya no obtiene full_song_service desde ProfessionalSongService. ProfessionalFullSongService reutiliza el ejecutor por herencia conservando generación final y gates. No se duplica el lifecycle ni se elimina ruta histórica. Batch 18 pruebas ejecución/candidatos/jobs aprobado; compileall correcto. Tres comprobaciones adicionales de compatibilidad de comandos finales aprobadas. S03-04 sigue parcial por consumidores históricos de proyectos/letra/artefactos/export. Global 65,7%; sin audio real ni cambios hardware.

### S03-04: servicio local de revisiones — 2026-10-08

Extraído MusicSpecRevisionService con puerto de storage: consulta de ficha/historial, confirmación con concurrencia optimista, evento y progreso. SongService consulta/confirma/prepara catálogo directamente en servicio local; edición ACE y migración exportan desde DB mediante export_music_spec, sin método privado del servicio histórico. ProfessionalSongService conserva compatibilidad delegando consulta/confirmación/progreso al mismo código. Prueba local confirma sin instancia histórica, preserva validez/aprobación separadas y rechaza revisión obsoleta; batch siete pruebas aprobado y compileall correcto. S03-04 permanece parcial: generación histórica de letra/audio/export y runner aún dependen de composición anterior. Global 65,7%.

### S02-03: recuperación integrada verificada — 2026-10-08

Playwright sobre QA: revisión 8 recuperada pending/valid=false; botón Revisar configuración recuperada y Guardar para revisar sin cambios crean revisión 9 valid=true/pending/approved_by_qwen=false; Confirmar crea revisión 10 confirmed/valid=true, sin aprobación Qwen, plan previo stale, diez revisiones conservadas. Tres respuestas HTTP 200. Complementa recarga persistente, navegación y aislamiento Alma-Isabella ya verificados y 27 pruebas backend. No se llamaron acciones de aprobación de audio ni generación. S02-03 verified 0,5→1, accepted sigue 0. Global calculado 65,7% (antes 65,2%). Solo QA modificada; aceptación del usuario pendiente.

### S02-03: separar validación de aprobación del modelo — 2026-10-08

Storage/repository aceptan deterministic_valid independiente de approved_by_qwen; compatibilidad anterior conserva el default cuando no se entrega evidencia explícita. Cambios en esa evidencia crean nueva revisión aunque JSON no cambie. Edición manual y fases no atribuyen aprobación Qwen; confirmación conserva validez determinista y usa concurrencia optimista. Recuperación conserva origen de validación histórica, exige revalidar campos editables y entradas de motor/fuentes antes de habilitar confirmación, sin aprobar automáticamente. Prueba SQLite recupera, revalida y mantiene approved_by_qwen=false/user pending. Batch de 27 pruebas de recuperación/edición/fases/configuración aprobado (51,36 s); diff check sin errores. Pendiente repetir recorrido UI final; global 65,2%.

### S02-03: recarga, aislamiento y revalidación — 2026-10-08

Playwright QA confirma revisión recuperada 6 pending después de recargar, historial de seis versiones, plan stale y navegación Alma→Isabella sin modificar revisión de Alma. Nueva acción visible Revisar configuración recuperada abre editor. Detectado bloqueo de guardado sin cambios; corregido para enviar mismo ace_step_config cuando requiere revalidación, manteniendo valores y pasando validación backend. Build aprobado. PATCH API responde 200 pero deterministic_valid sigue false: queda resolver desacople de validación determinista y aprobación Qwen antes de cerrar el recorrido. Falta repetir click UI con bundle final. Global 65,2%; no se afirma cierre ni generación real.

### S02-03: batch Playwright de recuperación — 2026-10-08

Base QA aislada: selección y comparación visibles, dirty bloquea recuperación, POST final 200 crea revisión 6 pending sin validación/aprobación; origen registrado y seis revisiones conservadas, plan anterior stale. Detectado fallo de firma al exportar después de guardar (dos intentos QA 500, revisiones conservadas); corregido a export_music_spec(storage, song_id), prueba de servicio SQLite ahora comprueba snapshot y misma revisión. Corregida comparación por orden de claves JSON y ocultadas rutas derivadas. Dos pruebas frontend y una integrada backend aprobadas; build aprobado. Falta recarga/navegación completa y aceptación; verified S02-03 conserva 0,5, global 65,2%. Sin modificar datos de producción ni generar audio.

### S02-03: recuperación de versiones desde la interfaz — 2026-10-08

Panel de versiones anteriores integrado en revisión de definición: selección, comparación de campos con etiquetas, vista de letra/dirección guardadas y acción explícita para crear nueva revisión. Bloqueado con cambios abiertos; petición conserva IDs de origen y revisión vigente, respuesta tardía no cambia otro proyecto. Backend regenera snapshots desde SQLite tras recuperar, sin aprobación automática. Prueba SQLite y prueba de comparación frontend aprobadas; build Vite aprobado. S02-03 developed 0,5→1, verified permanece 0,5 hasta batch navegador; accepted 0. Global calculado 65,2% (antes 64,4%).

### S02-03: restauración de definición en backend — 2026-10-08

Nuevo RestoreMusicSpec y POST /api/pro/projects/{song_id}/spec/restore. Selección de revisión limitada al proyecto, concurrencia optimista en SQLite, recuperación como nueva revisión pending sin aprobación Qwen y trazabilidad del origen/revisión reemplazada. Historial anterior intacto; decisiones bloqueadas no se cambian ni desbloquean silenciosamente. Prueba SQLite verifica recuperación, historial, rechazo de revisión ajena y petición obsoleta. Falta interfaz de revisión/restauración y comprobación integrada; S02-03 conserva developed/verified 0,5. Global 64,4%.

### S06-04: liberación de modelos verificable — 2026-10-08

ResourceMonitor ya aplicaba presupuesto de pesos antes de iniciar ACE-Step. Corregidos dos defectos: released_llm solo es true tras ejecutar correctamente el comando de cierre; comando ausente, salida no cero, timeout o fallo de ejecución bloquean audio con diagnóstico y acción concreta. No se cierran procesos ajenos ni se reduce el presupuesto para forzar una generación. Batch 14 pruebas aprobadas de readiness, integridad y ejecución, incluyendo timeout/permisos, comando ausente, cierre desactivado y presupuesto posterior a cierre correcto. Sin audio real. Global permanece 64,4%; falta memoria disponible y ejecución instalada por modo.

### S06-04: importación directa del handler — 2026-10-08

Prueba real check-only: PyTorch 2.9.1+xpu detecta Intel Graphics. Importación previa del pipeline Gradio no terminó y fue interrumpida sin cargar pesos; inspección muestra dependencias UI/entrenamiento innecesarias. Wrapper corregido para importar acestep.handler directamente, sin fallback silencioso. Dos pruebas específicas aprobadas. Check-only repetido completado: API real acestep.handler.AceStepHandler y dispositivo solicitado/activo xpu; 17.453 s. El handler aún importa componentes de entrenamiento propios; se elimina la dependencia adicional de Gradio. Memoria libre inicial 3,83 GiB frente a presupuesto conservador 7049 MiB: no se inicia generación. No acredita carga de pesos ni seis modos ejecutados. Global 64,4%.

### S06-04: contrato instalado reproducible — 2026-10-08

Nuevo `tools/check_acestep_contract.py`: inspecciona AST de fuentes instaladas sin importar torch ni cargar pesos; contrasta argumentos explícitos del handler y GenerationParams, instruction y catálogo de tareas Base/Turbo. Devuelve hashes de fuentes y código de salida no cero ante incompatibilidad. Comprobación instalada compatible: seis modos Base y tres modos conectados Turbo. No habilita modos ni acredita ejecución, semántica completa o calidad. Batch de ejecución/configuración/adaptadores: 23 pruebas aprobadas. La primera ejecución detectó un mock de referencia sin artifact_id; actualizado al contrato vigente y batch repetido completo con éxito. Global 64,4%; S06-04 conserva pendiente la ejecución real por modo.

### S06-04: correspondencia de parámetros en API de alto nivel — 2026-10-08

El adaptador ahora rechaza discrepancias reportadas en todos los inputs conectados que envía: tarea, texto, metadatos musicales, duración, audios, opciones de inferencia y edición. Conserva en diagnóstico campos coincidentes, discrepantes y no reportados; la ausencia de evidencia no se convierte en verificación. Se mantienen las comprobaciones obligatorias de caption/letra/idioma y códigos LM. Seis pruebas del adaptador aprobadas, con diez escenarios de alteración rechazados. Inspección local sin cargar pesos: archivos requeridos presentes para Base/Turbo y las tres rutas (LM 1.7B); modelo cargado y generación real siguen sin verificar. El paquete instalado devuelve parámetros por audio y semilla individual, compatibles con esta comprobación. No se generó audio. Global permanece 64,4%: S06-04 aún necesita ejecución por modo y evidencia de audio.

### S06-02: verificación local completa de inputs conectados — 2026-10-08

Recorrido QA: WAV previamente importado → selección UI fuente/referencia → Guardar crea revisión pendiente USER → confirmación → plan Cover. Artefactos y checksum llegan intactos, conservación 0,75 preservada. Detectada procedencia antigua en ruta derivada: input_trace ahora enlaza ID USER con explicit_user_control y ruta SYSTEM con system_artifact_resolution. Recompilación API tras reiniciar backend confirma ambos argumentos/verificación/checksum. 10 pruebas aceptación/revisión aprobadas (4+6, aceptación cubre 13 combinaciones y 21 inputs); complementa matriz seis modos, LM y pruebas de importación previas. Timeout del harness por esperar /preview resuelto: UI usa POST /ace-plan y la operación ya había completado; no fallo producto. Sin ejecutar ACE-Step. S06-02 verified pasa a 1 para controles/mapping locales; accepted sigue 0. Global calculado 64,4%. Validación instalada/audio real se conserva en S06-04/S10.

### S06-02: importar fuentes/referencias WAV — 2026-10-08

ImportSourceAudio con puerto de storage e inspector inyectado; endpoint raw con límite 64 MiB y guardado exclusivo por UUID dentro del proyecto. WAV PCM verificado, original conservado, metadata de nombre original/permiso/checksum/integridad; música no aprobada. UI exige permiso y deja seleccionar fuente/referencia después de importar, sin autoaplicar. Eventos SQLite registran importación. Dos pruebas backend aprobadas (original bytes/spec intactos, aislamiento y rechazo sin archivos/artefactos residuales), build y Playwright QA upload aprobados: autorización requerida, opción visible por nombre original, misma revisión y decisiones vacías intactas; checksum 9d7ff0669f61b76fe14c25021d23dc27797af79bcaead296dd361b14c235a6dd. Sin audio ACE-Step. Global 64,2%; falta completar cobertura importación→selección→MusicSpec→request.

### S06-02: inventario conectado y checksum en traza — 2026-10-08

Inventario de los 21 inputs emitidos documentado en docs/ACE_STEP_CONNECTED_INPUT_INVENTORY.md. Corregido desfase: fuentes/referencias inspeccionadas actualizan input_trace con estado verificado, artefacto y sha256 antes del hash del plan. La regla rechaza evidencia de otro artefacto. 16 pruebas aprobadas: aceptación 4 (13 combinaciones), compilador 6 y revisión 6; WAV sintético con checksum y sustitución antes de aprobar. Primer ensayo detectó import faltante, corregido y regresión pasó. Sin audio ACE-Step nuevo. Global 64,2%; importación de fuentes nuevas y cobertura UI→request completa siguen pendientes de S06-02.

### S06-02: transición LM y fuentes — 2026-10-08

Ruta high_level_lm conservada al cambiar a edición, con bloqueo explicativo para elegir Directa/API sin LM; no modificación automática USER. Cuatro pruebas frontend y seis backend de configuración aprobadas, build aprobado. Playwright: modelo LM visible en text2music, Cover bloqueado y elección intacta; Directa resuelve incidencia y oculta LM, fuente required y referencia opcional. Primer intento esperó mounted 30 s y expiró; reintento después de carga completada pasó. Sin guardado/audio/inferencia real. Global 64,2%; S06-02 sigue pendiente de inventario completo de inputs y evidencia de fuentes integradas.

### S06-02: seis modos y cardinalidad de pistas — 2026-10-08

Playwright comprobó requisitos/controles condicionales de text2music/cover/repaint/lego/extract/complete contra catálogo backend. Detectó selección múltiple en acciones de una pista; corregida a select único para lego/extract, complete mantiene selección múltiple. Incompatibilidad Base/Turbo y cardinalidad muestran explicación y bloquean Guardar sin cambiar decisiones USER. Tres pruebas frontend y build aprobados; reensayo MCP preservó Turbo+dos pistas originales mientras bloqueaba, usuario eligió Base+vocals y desaparecieron incidencias. No guardado de fixture ni audio real. Global 64,2%; S06-02 verificación parcial: cobertura total de inputs, rutas LM y fuentes todavía pendiente.

### Contraste condicional y requisitos visibles por modo — 2026-10-08

S06-01: contraste computado en estados seleccionados/error/dialog destructivo: 13,1/14,52/7,81 y botón primario 6,21, cancelar 15,31. Atajos de zoom MCP no alteraron viewport ni devicePixelRatio; zoom nativo y lector de pantalla siguen manuales, sin contarlos como probados. S06-02: resumen de insumos por acción desde capability_profile backend (fuente/Base/intervalo/cardinalidad), referencia opcional y separación de contrato/disponibilidad real. No se modifican decisiones USER. Build aprobado, prueba agrupada de seis modos pendiente. Global 64,2%; estados del ledger conservados.

### Texto ampliado y protección frente al asistente fijo — 2026-10-08

Ensayo exploratorio MCP duplicando tamaños computados de texto a 768 px: Idea/Sonido/Composición/Letra/Studio sin overflow horizontal. Es simulación de texto al 200%, no zoom nativo de navegador. Se detectó riesgo de oclusión por altura variable del copiloto; ResizeObserver reserva altura real + margen, scroll-padding protege desplazamiento y footer limita altura con scroll propio. Build y Playwright final: footer 335 px, reserva 367 px, scroll-padding 359 px, documento 757 px en viewport 768. Global 64,2%; pendientes: zoom nativo/tecnología asistiva y contraste completo de estados condicionales. No audio ni modelos ejecutados.

### Accesibilidad Studio: reproductores y análisis — 2026-10-08

Reproductores A, B y sample tienen nombres accesibles diferenciados; waveform anuncia aria-busy durante análisis. Build y Playwright confirmaron nombre A, estado inactivo del análisis, movimiento reducido (transición 0,00001 s) y sin overflow a 320 px. Exploración de contraste computado de 999 elementos textuales visibles del workspace/copliloto cargados no encontró valores inferiores al umbral sobre composición de fondos; no incluye evaluación visual de gradientes/imagenes, todos los estados ni certifica WCAG. Global 64,2%, S06-01 desarrollo completo/verificación parcial; pendientes de verificación explícitos: zoom/texto 200% y contraste de estados condicionales, lectura con tecnología asistiva/aceptación.

### Preferencias de paneles por proyecto; S06-01 desarrollo completo — 2026-10-08

SQLite conserva apertura/cierre de paneles estables (familias de ficha, comparación, criterios de escucha, fidelidad, niveles de sample, actividad, recursos y procesos anteriores). Migración aditiva open_panels_json; validación de identificadores/booleanos; solicitudes de navegación antiguas conservan preferencias. UI usa el proyecto activo y snapshot de preferencias en escrituras serializadas; MusicSpec y datos creativos intactos. Prueba backend de reapertura/conservación/rechazo/borrado de preferencias aprobada, build aprobado y Playwright QA confirmó actividad de Alma abierta tras recarga e Isabella independiente. Sin generación audio. S06-01 desarrollo pasa de 0,5 a 1 con las superficies implementadas; verificación permanece 0,5 y aceptación 0 por revisión integral de contraste/accesibilidad pendiente. Global calculado: 64,2% (antes 63,7%).

### Regresión agrupada Builder/Studio — 2026-10-08

46 pruebas frontend aprobadas y matriz MCP de seis estados de generación, opinión histórica y notas obligatorias comprobada. Error de decodificación en inglés corregido a español con recuperación; reensayo conserva reintento/reproductor. Build final aprobado. Evidencia y límites en docs/BUILDER_STUDIO_REGRESSION_20261008.md. No audio ACE-Step real. Global 63,7%; pendiente concreto siguiente: restauración de paneles abiertos por proyecto prevista en UX, además de revisión integral de contraste/aceptación de accesibilidad.

### Studio: resumen de entrega y archivos disponibles — 2026-10-08

S06-01: StudioDelivery presenta sample, canción completa y siguiente acción desde estados existentes, sin acreditar calidad por presencia de archivo. Enlace al panel relevante lleva foco; Guardar MP3 deshabilitado sin URL disponible. MIDI retirado solo de placeholders de formatos pendientes, artefactos existentes conservados; pipeline anterior plegado y descrito como controles previos, sin añadir requisitos ACE-Step. Tres pruebas de estados, build y Playwright fixtures aprobados: sin/enlace MP3 cambia disponibilidad, destinos sample/final y sin overflow a 320/768/1440. No se descargó archivo fixture ni generó audio; validaciones backend de sample/final intactas. Global 63,7%; sigue pendiente regresión integral de Builder/Studio y estados condicionales para acreditar S06-01 completo.

### BuilderShell y transición Generar → Studio — 2026-10-08

S06-01: shell extraído a componente Vue con contexto de proyecto, revisión guardada, estado de borrador, siete pasos, anterior/siguiente y acceso a voz. Título humano corresponde al paso, no al nombre de herramienta anterior. Generar enfoca su propio preflight; Revisar conserva ficha. Una task del proyecto que pasa de pending/running/cancelling a completed abre Studio solo si el usuario sigue en Generar y no tiene cambios sin guardar. No navega por cargar historial. Build y Playwright fixture aprobados: destino preflight, volver Revisar, transición completada conserva proyecto, guard dirty conserva Generar y reflow 320px. Sin audio ACE-Step nuevo. Global 63,7%; S06-01 conserva estado parcial: aún faltan superficies finales de Studio y revisión de estados condicionales/regresión integral.

### Studio: revisión histórica, estructura y reflow del recorrido — 2026-10-08

S06-01: StudioCandidateContext muestra revisión y estructura del informe del candidato; no sustituye datos históricos por MusicSpec actual ni inventa alineación observada. Dos pruebas aprobadas y Playwright con fixture histórico comprobó estructura Intro/Verso/Coro y aviso sin alineación. Corregido overflow a 320 px de Idea/Sonido/Composición/Letra (grid mínimo, rangos y barras decorativas), además de Studio. CSS final ensayado en navegador; build aprobado. Las barras antiguas de Instrumental/Voice ahora declaran que son decoración, distintas del análisis real en Studio. Contraste de tokens medido: texto principal/surface 15,31; secundario 9,2; muted 7,36; botón primario 6,21; foco 9,99; borde de control 4,85. No acredita todos los estados ni auditoría WCAG. Global 63,7%; falta completar shell/superficies, estados condicionales y regresión integral de accesibilidad. Sin audio ACE-Step nuevo.

### Accesibilidad: tres diálogos y controles visibles — 2026-10-08

S06-01: gestión compartida `syncDialog`/`containDialogTab` para cambios sin guardar, borrar proyecto y eliminar sección; foco seguro inicial, ciclo Tab/Shift+Tab, Escape y retorno al origen/fallback al contenido. Borrado conserva bloqueo mientras está en curso; error anunciado. Cinco controles reciben nombre accesible: inspiración, tipo de sección, búsqueda de plantilla, instrumentación y mensaje al asistente. Playwright sobre build final: tres diálogos cancelados sin acciones destructivas, ciclos y retorno correctos; cero campos visibles sin etiqueta/nombre en Idea/Sonido/Composición/Letra/Studio. Esta comprobación determinista no sustituye lector de pantalla, contraste ni estados condicionales. Global 63,7%; pendientes de S06-01 ahora: superficies Builder/Studio completas, contraste/reflow y accesibilidad de estados condicionales.

### Builder: navegación por teclado y protección de cambios — 2026-10-08

S06-01: enlace Saltar al contenido, navegación con pantalla activa anunciada, foco en destino Builder/Studio y respeto de movimiento reducido. El aviso de cambios sin guardar ahora es un diálogo nativo con nombre accesible, foco inicial en Cancelar, ciclo Tab/Shift+Tab y Escape sin pérdida de cambios; devuelve foco al origen. Build y Playwright sobre versión compilada aprobados: siete Tab permanecen dentro, retroceso dentro, Escape conserva dirty y pantalla. Primer ensayo detectó escape de foco y se corrigió antes de cerrar. Global 63,7%; no acredita auditoría integral WCAG ni pantallas completas. Pendientes de S06-01: resto de diálogos, controles/contraste/reflow integral y completar superficies Builder/Studio.

### Studio: forma de onda real e intervalo manual — 2026-10-08

S06-01/S06D: AudioWaveform decodifica el archivo bajo acción explícita, calcula amplitud en todos los canales y permite seleccionar inicio/final dentro de duración. El botón traslada segundos a controles de corrección sin guardar ni generar. Cambio de candidato cancela análisis y reinicia selección; errores conservan reproductor disponible. Dos pruebas de cálculo/límites y build aprobados. Playwright con WAV sintético válido de un segundo verificó decodificación, traslado 0,2–0,8 s y bloqueo de final fuera del archivo; no acredita música ni calidad ACE-Step. Defecto previo de overflow a 320 px corregido: CSS final comprobado en navegador a 320/390/768/1440. Global 63,7%; S06-01 sigue parcial por pantallas y accesibilidad integral pendientes, con waveform/intervalo ya implementados.

### Navegación Builder/Studio persistida — 2026-10-08

S06-01: SQLite conserva el paso concreto del Builder por proyecto; migración aditiva de `project_ui_state.builder_step`, validación fase/paso y escrituras UI serializadas. Studio se restaura al recargar y el regreso a Revisar mantiene el proyecto. Prueba backend de persistencia/reapertura, rechazo de paso incompatible y conservación de datos creativos aprobada; build Vite aprobado. Playwright en DB QA confirmó guardado → recarga → Studio → Revisar; candidato fixture visible con definición pendiente y sin plan, sin overflow a 390/768/1440. Sin audio real. Global 63,7%: S06-01 sigue parcial por pantallas completas/accesibilidad integral; navegación persistida ya no es pendiente.

### Studio independiente de la definición — 2026-10-08

S06-01: escucha, comparación A/B y opiniones se muestran en un contenedor Studio independiente de la confirmación creativa y del plan visible. El paso Studio navega a ese contenedor y permite regresar a la definición del mismo proyecto. No se duplican MusicSpec ni candidatos; las validaciones de guardado y generación siguen en sus servicios actuales. Build Vite aprobado; revisión visual agrupada pendiente. Global 63,7%, sin cambio de estado parcial.

S06-01 defecto A/B responsive cerrado: track grid minmax(0,1fr), min-width:0 del hijo, scroll interno. Build y Playwright con fixture/CSS final a 390/768/1440 sin overflow, foco de tabla comprobado. Esperar final de mounted resuelve carrera restante de harness; refresco desactivado solo allí. Global 63,7% sin cambio de estados parciales; no aceptación integral del sprint.

S06-01 batch pendiente request/A-B/escucha resuelto: fixture estabilizado desactivando refresco en harness; request/tabla con foco/opinión histórica/bindings comprobados. Overflow móvil al abrir A/B aún pendiente: ajuste de mínimos compilado, reensayo conserva ancho 572 px frente a 390 px. Sin persistencia/audio real. Global 63,7%, revisión integral/pantallas completas aún pendientes.

S06-01 incremental: request humano y comparación A/B extraídos en componentes, tabla accesible/desplazable; batch de escucha intentado con fixtures, interrumpido por timeout del selector A/B; verificación visual todavía pendiente. 39 pruebas/build aprobados, sin audio real ni persistencia. Global 63,7%; estado parcial del conjunto preservado. Siguiente bloque: separar contenedores Builder/Studio y restauración de navegación aprobada, manteniendo acceso al mismo proyecto.

S06-01 incremental: ListeningDecision/ListeningReviewSummary extraídos, vigencia audio/config explícita y opinión histórica accesible sin reproductor en candidato mostrado. 38 pruebas/build aprobados, Playwright agrupado pendiente. Evidencia y pendientes concretos de S06-01 actualizados en ledger sin cambiar estados parciales; global 63,7%. No confundir opinión aceptada con entrega aprobada.

S06-01 incremental: GenerationStatus reusable con mensajes/acción de recuperación, progreso solo reportado, cero válido, estados desconocidos sin suponer éxito y accesible sin plan confirmado. Batch 37 pruebas/build/Playwright QA de estados/preflight móvil aprobado; fixtures no acreditan cancelación/recuperación real. Global 63,7%, estados parciales conservados. Próximo bloque de producto: extracción y claridad del panel de escucha/aceptación, sin expandir DAW.

S06-01 incremental: GenerationPreflight reutilizable separa preparación creativa y diagnóstico técnico; plan vigente y borrador comprobados antes de habilitar botón candidato. Ready de recursos no se anuncia carga del motor. 36 pruebas/build; Playwright agrupado con siguiente bloque de estados de generación. Sin cerrar D/V del conjunto ni alterar gates backend/sample; global 63,7%.

S06-01 incremental: DecisionCard reusable para revisión por familias; ayuda/procedencia/aplicabilidad/delegación conservadas, false/0 representados sin perder decisiones y contador «con valor». 34 pruebas/build/Playwright QA agrupados. No cambia D/V parciales del entregable completo; global 63,7%. Siguiente bloque: preflight legible y separación de preparación creativa/disponibilidad técnica, preservando gates backend.

S06-01 incremental: BuilderProjectSummary reutilizable y estado puro con pendientes/acción relevante de proyecto persistido; assets/ficha/plan separados de aprobación audible. Navegación secundaria, guardado explícito ante borrador. 33 pruebas frontend/build y Playwright QA. Entregable completo sigue parcial por pantallas/primitives/accesibilidad pendientes; global 63,7% sin delta artificial.

Actualización: global **63,7%** (+0,94 puntos exactos respecto a baseline, +0,9 en valores mostrados); S05 **76,2%**. S05-03/S05-04 verificación 0,5→1 con panel Playwright y lock real registrado. Aceptación sigue pendiente. Fuente vigente regenerada en SPRINT_PROGRESS.md.

Fuente vigente: [SPRINT_PROGRESS.md](SPRINT_PROGRESS.md), generado desde [sprint_progress.json](sprint_progress.json) con `scripts/sprint_progress.py`.

Baseline: **62,8%**, 39 entregables S00–S06/S10. Desarrollo 50%, verificación 30%, aceptación 20%; estados por entregable 0/0,5/1. Igual peso de entregables dentro del sprint e igual peso de los ocho sprints en global. Es evaluación explícita de cobertura, no horas ni calidad. Aceptación aún sin cierre acreditado; mocks no sustituyen gates reales.

Este inventario sustituye el 75% estimado sin relación directa con tareas. Porcentajes de entradas antiguas se conservan como histórico, no estado vigente. Cambiar la baseline no constituye avance ni retroceso del producto. Ampliaciones diferidas y subdivisiones DS/S06 no se cuentan otra vez.

Cada continuación debe identificar IDs afectados, transición de estado/evidencia y delta calculado. Si no cambia un estado, informar que el avance fue parcial y qué falta para completarlo. Cambios de alcance se registran explícitamente antes de recalcular. No se sube el indicador por repetir tests.

Próximo bloque: S05-03 comentario técnico visible y S05-04 locks con inferencia real, agrupados; después S06-01 componentes/pantallas pendientes. Se priorizan criterios abiertos sin repetir casos ya acreditados.

## Avance S02/S03/S05 — 2026-10-08

S05-03/S05-04: panel técnico Playwright con evidencia Qwen previa vía fixture comprobado (real/respaldo/resumen/no autoguardado). Lock con Gemma real: fallo inicial rechazado por backend, prompt reforzado con literales/posiciones y reintento 61,91 s mantiene texto y línea protegida sin modificar ficha. No mejora creativa en este resultado; alcance real limitado a ese caso. Ambos estados de verificación 0,5→1, aceptación 0. Global 63,7%; siguiente desarrollo S06-01, sin repetir estos ensayos salvo regresión concreta.

S05 revisión Qwen real comprobada por orquestador con propuesta previa Gemma: Vulkan Intel 37/37 capas, 98,64 s, 6.708 tokens, provider ejecutado sin fallback y task/result/steering persistidos en QA. Conserva ficha activa. Detecta acortamiento/adjetivos retirados; opiniones sobre canto no verificadas. No acredita sesión simultánea, locks en inferencia ni aprobación de usuario. S05 75%, S06 70%, global 75%; criterio real textual deja de pendiente total a evidencia parcial de un caso. Siguiente: locks con Gemma real y revisión visual del comentario técnico, sin repetir este caso salvo regresión.

S05 handoff técnico de letra corregido: task incluye texto original/propuesta/contexto/revisión, antes solo conteos. UI expone comentario y estado real/respaldo; control de revisión después del handoff. 15 pruebas de fases/build y contrato mock del contexto aprobados. Qwen real y Playwright de panel pendientes; S05 75%, S06 70%, global 75% sin aumento hasta completar evidencia real/cobertura. No considerar la task completada una aprobación musical.

S05 ensayo real Gemma/Vulkan Intel por servicio en SQLite QA: letra `llama_cpp`, 63,72 s, tema/nombre Alma conservados, sección acortada y sin autoguardado. Detectado y corregido exceso de contexto (12.501→6.115 tokens; límite 8.192) retirando diagnósticos/metadatos duplicados y preservando campos creativos públicos. Tres pruebas de proyección/contexto aprobadas. Qwen real y obediencia a locks en inferencia/aceptación creativa pendientes. S05 75%, S06 70%, global 75% sin cambio; gate de inferencia real solo parcialmente comprobado. No repetir este caso salvo regresión concreta.

S05 contexto de assets completado: set, instrumental/melodía/letra con manifests/intenciones derivados, ficha activa compacta y referencias de snapshot, prioridad SQLite. Prueba integrada mock de contexto/sin autoguardado y batch Playwright QA de revisión/ID/borrador enviado y descarte/restauración. No acredita inferencia real. S05 75%, S06 70%, global 75% mantenidos: falta gate real de obediencia/fidelidad y cobertura total; próximos bloques deben avanzar esos criterios, no repetir contratos ya comprobados.

S05: contexto de transformación parcial resuelto desde proyecto/revisión persistidos; incluye instrumental/voz/dirección y protecciones. Rechaza revisión obsoleta, sección ajena y alteración de líneas protegidas antes de devolver propuesta. Propuestas se limpian tras guardado/recarga/descarte. Build y pruebas dirigidas; inferencia real/Playwright del nuevo contexto pendientes de batch. S05 75%, S06 70%, global 75% conservados. Pendientes contexto de assets/manifiestos y validación del recorrido completo, sin cierre por incremento de tests.

S05: transformaciones parciales de letra pasan a propuesta antes/después, fuente explícita y aplicar/descartar sin autoguardado. Guardas de proyecto/contexto/revisión/sección y líneas protegidas antes de recibir/aplicar. 31 pruebas frontend/build y batch Playwright con API simulada; inferencia real no ejercitada. S05 75%, S06 70%, global 75%: bloque implementado sin completar cobertura general. Próximo: estado de propuestas al navegar y cobertura del contexto musical enviado al asistente por sección.

UI de trazas de dirección implementada en revisión del plan: literal por sección, protección, no envío al motor y detalle técnico; histórico sin traza distinto de lista vacía. Build y batch Playwright QA de controles de dirección/desbloqueo guardado aprobados; panel verificado con fixture local y viewport 390 px. No acredita traducción ni audio. S05 75%, S06 70%, global 75%: avance de visibilidad y verificación sin completar mapping ni aceptación. Siguiente bloque: propuestas parciales revisables y protección de decisiones antes de aplicar.

Dirección por bloque protegible en UI/SQLite con desbloqueo USER explícito trazable y bloqueo de eliminación/sustitución. Plan incorpora traza literal por sección, origen y ruta `retained_not_sent_to_engine`; notas no se mezclan con letra ni se añaden al caption sin mapping validado. Build y pruebas dirigidas; batch Playwright pendiente de agrupar. S05 75%, S06 70%, global 75% se mantienen: aún faltan UI de trazas y traducción con evidencia del motor. No considerar cerrado el requisito de dirección ejecutable.

Continuación: cuatro controles de dirección creativa por bloque de letra (dirección/energía/voz/instrumentos), notas persistidas en MusicSpec y conservadas en plantillas, separadas del markdown cantado. Prueba integrada de persistencia y separación de letra, rechazo de tipo inválido. Pendientes Playwright agrupado, locks de dirección y mapping explícito al caption/plan según capacidad; no acreditan ejecución por sección. S05 permanece 75%, S06 70%, global 75%: avance parcial sin justificar aún un incremento de cinco puntos.

DS3/S03/S05: protección por línea implementada en editor y SQLite; conserva literal/posición, permite editar otras líneas, exige desbloqueo explícito trazable y bloquea sustituciones hasta guardarlo. Rechaza transformaciones IA incompatibles. Batch 30 frontend/14 backend dirigidas/build aprobado; Playwright QA comprobó rechazo de edición y desbloqueo guardado. Prueba pendiente de plantilla completada mediante navegación y descarte explícito: borrador sin persistencia y recuperación al volver al editor. Pendientes dirección completa por sección y validación amateur; no cierre de sprint. Metadata editorial preservada en MusicSpec, sin inventar parámetros de ACE-Step.

DS3/S03/S05: protección de texto/tipo por sección en UI y SQLite, desbloqueo USER explícito y rechazo de respuestas IA tardías sobre texto cambiado. Sustitución por plantilla/borrador requiere desbloquear y guardar, con aviso visible y guardas ante carga tardía. Build, 29 pruebas frontend y 11 de fases aprobadas; Playwright QA verificó persistencia y desbloqueo guardado. Prueba adicional de descarte de plantilla interrumpida por beforeunload: pendiente. Locks por línea y ampliación de importación pendientes; no cierre de sprint.

DS3/S06B incremental: timeline estructural de letra, edición accesible por bloque, reordenación/duplicación sincronizadas y eliminación confirmada en diálogo nativo; mínimo una sección. Batch build/Playwright QA de controles y descarte aprobado. Sin tiempos reales ni partitura; locks granulares/dirección por sección y validación amateur pendientes. No cierre de sprint.

Batch DS1/DS2: acentos/fondos heredados comunes migrados; paso Builder conservado tras modal de cambios. Build y Playwright QA de siete pasos/navegación protegida/paleta computada/reduced-motion/layouts 390–1440 aprobados. Foco por teclado pendiente; foco programático tras clic no acredita focus-visible. No overflow observado en esos estados. Pendiente cobertura global de componentes, contraste por pantalla, timeline y Studio completo; sin cierre DS ni UX amateur.

DS1/DS2 incremental autorizado e implementado: tokens de paleta oscura/aliases, estilos comunes y shell de siete pasos sobre editores vigentes, protección de borradores y acceso a voz. Verificación agrupada: build/28 pruebas frontend/diff. Pendientes Playwright visual, contraste computado, extracción de primitives, migración de literales y pantallas Builder/Studio completas. Ningún gate funcional se sustituye por navegación.

S06C: validación antes de modelos de overrides/modelo contra contexto del plan, con rechazo de discrepancias y contexto inválido. 15 pruebas dirigidas/CLI/compilación Python aprobados. Ruta sin contexto compatible pero sin evidencia de revisión vinculada. Pendiente ejecución instalada; no cierre de audio/fidelidad.

Playwright del panel S06C aprobado con fixture de API en navegador: solicitado/wrapper/motor separados, cero y delegación preservados, otra revisión sin datos inventados. Corregido panel oculto por plan/propuesta vigente; ahora evidencia del candidato puede consultarse independientemente. Build correcto; runtime real sigue pendiente y fixture no acredita audio.

S06C/UI: metadata SQLite conserva traza de opciones por candidato y Production muestra solicitado/wrapper/origen/motor. Falta de dato y candidato histórico explícitos, sin deducir valores desde ficha actual. 2 pruebas backend/28 frontend/build; Playwright del panel y runtime real pendientes. No cierre de fidelidad ni calidad audible.

S06C: contexto plan/revisión/perfil/overrides/procedencia exportado al wrapper y traza de cuatro opciones resueltas; resolución compartida entre Directa/alto nivel. Default omitido guidance Turbo corregido a 1; Base 15. Observaciones del motor alto nivel separadas sin inventar campos ausentes. Pruebas con mocks; pendientes runtime real, observación del handler directo y UI de trazas. No cierre de fidelidad/audio.

Cobertura de ayudas específica completada para los 49 campos del catálogo: significado/efecto/ejemplo, sin aplicar defaults por mostrar ejemplos. 6 pruebas dirigidas aprobadas y Playwright de ayuda de velocidad en viewport móvil 390×844 sin overflow horizontal observado. Pendientes otros estados móviles/táctiles y validación amateur; completar los textos no cierra esos criterios. Siguiente trabajo técnico: traza de valores efectivos resueltos por runtime.

Ayudas de controles ACE-Step completas en catálogo: 17 campos con significado/efecto/ejemplo desde contrato común y etiquetas comprensibles en ficha/editor. 10 pruebas backend/build y Playwright de referencia por teclado aprobados. No cierra ayuda universal: faltan otras familias musicales, móvil y comprobación amateur. Sigue pendiente traza de defaults efectivos en runtime.

Delegación explícita implementada para los cuatro controles opcionales del perfil ACE-Step. Guardado con revisión/procedencia/valor anterior, restablecimiento manual y protección de borradores. 10 pruebas backend dirigidas/26 frontend/build; Playwright QA delegación de semilla y recuperación tras recarga. Pendientes ayudas específicas con significado/efecto/ejemplo, delegación de otras familias bajo contratos reales y trazas de defaults efectivos en runtime. No cierre de sprint ni prueba de fidelidad audible.

Ayudas/cobertura S03/S05: estados de revisión separados de presencia de valor y confirmación; ayuda por campo con acción concreta, sin convertir delegaciones propuestas en decisiones aceptadas. 4 pruebas backend nuevas/24 frontend/build; Playwright de etiquetas y apertura por teclado. Pendiente comando explícito de delegación con procedencia/revisión, ayudas específicas con efecto/ejemplo y comprobación móvil/amateur. No cierre de sprint.

Propuestas múltiples implementadas: lista ordenada (máximo 20) revisada y persistida dentro de una única revisión; rechazo completo si alguna traza es inválida. 19 pruebas backend/24 frontend/build aprobados; Playwright QA 113 → 115 → 117 conservó ambas propuestas y distinción sustitución/edición manual. Criterio de múltiples patches deterministas resuelto; pendiente acumulación de propuestas LLM y ayudas/cobertura. No cierre de sprints.

Playwright del guardado desde chat aprobado sobre QA: propuesta BPM 109 → aplicación → edición 111 → guardado/revisión pendiente → recarga; traza alterada HTTP 400 sin mutación. [Evidencia](PLAYWRIGHT_CHAT_MUSIC_SPEC_20261008.md). Resuelve la comprobación del recorrido determinista individual; pendientes propuestas múltiples y origen LLM, cobertura/ayudas y generación integral. No cierre de sprints.

Continuación aplicada: guardar una propuesta revisada conserva origen/transformación, valores propuestos y finales en `_editor_phases` de la revisión MusicSpec; distingue aceptación y modificación USER. Revalidación backend desde petición y revisión vigente, sin inferencia adicional. 9 pruebas fases + 7 propuestas backend, 22 frontend y build aprobados. Pendiente Playwright del recorrido chat → aplicar → modificar → guardar y trazas equivalentes para propuestas de modelos no deterministas. No cierre de sprint.

Continuación S03: patches conversacionales con contrato versionado y origen verificable; guardia de revisión previa a modelos. Cuatro pruebas backend adicionales. Sigue pendiente el comando que conserve la traza propuesta → aplicación → revisión guardada; no cerrar ese criterio por el envelope de respuesta.

Implementada revisión compartida para formularios vinculados y ficha, guardado concurrente protegido, letra literal y exportaciones con invalidación de aprobación. El contexto del asistente usa esa revisión; propuestas se mantienen sin guardar y la UI rechaza resultados que pertenecen a una revisión o borrador anterior. [Contrato/evidencia](MUSIC_SPEC_SHARED_PHASES.md): 32 pruebas backend, 22 frontend y Playwright aislado. No cierre de sprints ni validación musical por estos resultados.

Siguiente bloque: comandos de propuestas compartidos del chat, cobertura/delegación y ayudas restantes; después flujo integral de generación/Studio y aceptación. La política de sample requiere reconciliar las instrucciones actuales con la decisión opcional documentada antes de cambiar gates.

## Avance aplicado — 2026-10-07: consolidación y S03

- S02/S03/S05, datos reales: cerrada consolidación de Isabella/Alma en los dos proyectos existentes; seis assets independientes, fuentes/decisiones dentro de tasks SQLite, textos correctos en Production y seis audios originales preservados. Fixture/drafts sustituidos recuperables fuera de listados activos. No queda otro paso de migración para esos dos proyectos.
- S03, implementación: patch creativo compartido y controles derivados del catálogo, validación de listas/textos, bloqueo de cambios a decisiones con lock y envío de cambios exclusivamente. Revisiones pendientes de confirmar; no atribuir propuestas Codex a deseos USER ni inferencia Qwen.
- Evidencia: 14 pruebas backend, 18 frontend, build; Playwright en copia realista y comprobación posterior DB real. No ejecución/audio nuevo ni escucha.
- Siguiente bloque: sincronizar formularios anteriores/chat con la revisión MusicSpec, explicar delegación en cobertura y completar ayudas de los controles. Retirar bloqueo obligatorio de sample conforme al contrato vigente y revisar todas las rutas afectadas. Estas entregas no cierran sprints enteros ni criterios de validación musical/amateur.

## Decisiones vigentes del usuario — 2026-10-07

[Contrato de decisiones](SONG_BUILDER_APPROVED_DECISIONS_20261007.md): **sample previo opcional, sin bloqueo de generación completa**; instrumental como intención soportada con ejecución condicionada a validación; dirección por sección en MusicSpec aunque su traducción tenga límites; referencia audio opcional/avanzada, sin clonación; perfil ACE-Step automático por defecto y manual disponible para cualquiera. Esta decisión sustituye requisitos anteriores incompatibles en este documento. Las descripciones de pruebas/gates del árbol anterior son históricas; retirar el bloqueo de sample sigue pendiente de implementación y regresión. Mantener set válido, request confirmado y evaluación/aceptación de audio separadas.
Fecha de alcance vigente: 2026-10-06. Estado: desarrollo parcial; ningún sprint se cierra por esta corrección documental.
Este documento es el backlog operativo de evolución del estudio. IMPLEMENTATION_PLAN.md conserva los sprints históricos; ROADMAPP.md resume prioridades. README.md registra entregas verificadas.

Actualización de verificación 2026-10-07: fase 1 de Gemma/Qwen y UI comprobada con modelos reales y SQLite aislado. Compilación revisable de 49 campos, recuperación, protección frente a resultados tardíos, cuatro casos de letra y revisión dirigida de incompatibilidades; perfil GPU de Qwen estable en los ensayos. La revisión creativa del usuario permanece pendiente. Esto aporta evidencia a S00/S02/S03/S04 y la preparación de S06; no cierra los criterios pendientes de audio real, escucha, representatividad del sample ni uso amateur. README y el reporte de fase 1 contienen resultados, correcciones y límites.

## Alcance y fuentes
Integra los requerimientos funcionales completos (17 apartados), la definición arquitectónica (20 apartados), la filosofía de aprendizaje universal y AI Music Copilot bidireccional aportados en esta conversación. Los contratos AMATEUR_USER_FLOW_REVIEW.md, AMATEUR_AUDIO_VOICE_STEERING.md y SONG_SPEC_GEMMA_QWEN_CONTRACT.md mantienen recorrido, calidad y trazabilidad.
No se reescribe desde cero. Se conserva Windows nativo, Python/FastAPI, SQLite, Vue 3/Vite, separación de assets y providers intercambiables.
Decisión de alcance del usuario: la propuesta de servicios pagos y su módulo histórico ProfessionalSongService quedan fuera del desarrollo activo y se conservan para posible reconsideración futura. El objetivo de estos sprints es el estudio local. Los puertos mantienen extensibilidad; no se implementan suscripciones, cobros ni integración remota paga.
El código actual todavía llama a ProfessionalSongService para operaciones locales de Production, ficha, ACE-Step y exportación. Su conservación es compatibilidad temporal, no una decisión de seguir ampliándolo. S00 inventaría esas dependencias; S02/S03 trasladan incrementalmente responsabilidades locales a casos de uso con puertos, manteniendo acceso a datos y rutas compatibles. El módulo histórico no se borra ni se renombra masivamente; se retira del circuito activo cuando sus consumidores locales tengan reemplazo verificado.
Una interfaz común asistida para todas las personas, sin niveles de experiencia. Controles musicales visibles con etiquetas claras y tooltips que explican significado, efecto y ejemplo; ayuda disponible por teclado y toque. Los ajustes adicionales se agrupan por tarea/relevancia y están accesibles para cualquiera. La IA recomienda y explica sin reemplazar decisiones USER; la misma MusicSpec alimenta controles y chat.

## Ampliación pendiente: Song Builder — 2026-10-07

S02/S03/S05: migración histórica revisable inicial implementada ([contrato/evidencia](LEGACY_INTENT_MIGRATION.md)). Recupera contexto, propone faltantes, conserva conflictos y aplica con revisión/hash/procedencia/task. 20 pruebas backend/15 frontend/build y preview Playwright aprobados. Inferencia determinista, no LLM real; cobertura semántica total y retirada de consumidores históricos siguen pendientes. No cierre de sprint ni borrado de código por esta entrega.

Bloque S03/S05/S06A: primer patch musical compartido implementado, cinco metadatos + motor sobre revisión SQLite existente y editor en Production. 16 pruebas backend/15 frontend/build aprobados; Playwright aislado guardó y recuperó BPM 97 con revisión pendiente. Casos de request/revisión antigua/valores inválidos/respuesta tardía cubiertos. No cierra SP-09/S05: faltan otros campos creativos, chat, fases históricas, locks y flujo integral.

### Agrupación operativa para avanzar varios sprints

El plan general conserva 19 IDs S00–S18; el alcance activo Builder/ACE-Step se concentra en 8: S00–S06 y S10. No son 8 sprints nuevos desde cero: contienen avances y gates pendientes. Las fases S06A–S06F son subdivisiones, no IDs de sprint adicionales.

| Bloque | Sprints que avanzan juntos | Dependencia/gate |
| --- | --- | --- |
| 1. Contratos y edición | S00/S02/S03/S05 | Perfil compartido, revisión y patch creativo; conservar USER y trazas. |
| 2. Builder y ayudas | S03/S05/S06A–S06B | Revisión compartida para formularios/chat; controles comunes, letra y estructura. |
| 3. Generación y Studio | S01/S04/S06C–S06F | Plan vigente, jobs, sample opcional sin gate, importación/feedback/artefactos. |
| 4. Verificación integral | S06/S10 | Recorrido completo, audio real separado y piloto amateur. |

Se pueden ejecutar cambios independientes dentro de cada bloque en una entrega; no declarar sprints completos por agruparlos. LLM y ACE-Step no deben inferir simultáneamente cuando la política de memoria requiere exclusión.

Avance de bloque 1/2: Playwright MCP sobre copia SQLite confirmó rangos Turbo (pasos máximo 20, guidance 1), fuente/pistas de Lego y descarte. Añadidas cuatro ayudas de significado/efecto/ejemplo desde contrato; Playwright comprobó su presencia y apertura por teclado de la primera. 14 pruebas backend dirigidas y build aprobados; controles/frontend restantes y comprobación móvil siguen pendientes. No audio/modelos reales en esta revisión.

Tercer bloque S00/S06A implementado: formulario de configuración consume opciones, rangos principales y reglas de visibilidad del perfil backend; sin contrato no edita ni inventa opciones. 13 pruebas frontend y build aprobados; Playwright de este cambio pendiente. Migración de controles históricos/restantes y disponibilidad observada sigue abierta.

Segundo bloque implementado S00: `AceStepCapabilityProfile` compartido por catálogo/validadores, con reglas de modos/pistas/rutas/rangos, políticas de campo y versión/hash en planes nuevos. 38 pruebas dirigidas aprobadas. Disponibilidad observada/preflight y consumidores frontend siguen pendientes de unificación; no cierra S00 ni acredita audio. Siguiente: migrar consumidores de reglas y edición creativa a la revisión compartida.

Primer bloque implementado de S00/S06C: traza por input en planes nuevos, mapping versionado, procedencia y rechazo de entradas sin regla. 23 pruebas dirigidas aprobadas; aceptación captura 13 combinaciones de rutas/modos y los 21 inputs emitidos, sin modelos/audio. S00 permanece abierto: perfil compartido observado y cobertura de condiciones/extremos pendientes. AC-ACE-USER-01 parcial; no cierra la fidelidad desde UI ni audio. Siguiente bloque: consolidar perfil y conectar patch creativo compartido; retirar gate obligatorio de sample según decisión vigente.

Aceptación transversal obligatoria: [AC-ACE-USER-01](ACE_STEP_USER_INPUT_ACCEPTANCE.md). S00 mantiene matriz/cobertura; S03–S05 prueban decisiones persistidas; S06A–S06B origen UI/chat; S06C request/wrapper por ruta/modo; S06D vigencia tras feedback. Cada input conectado exige test de conservación USER y transformaciones trazables. Incorporar el criterio no cierra las pruebas pendientes.

Capa visual pendiente de aprobación: [Design System A–Q](SONG_AI_DESIGN_SYSTEM_PROPOSAL_20261007.md). Fases DS0–DS6 se vinculan a S00/S06A–S06E/S10 en su sección P. Son tareas propuestas de tokens, componentes, estados, responsive y accesibilidad; no inician rediseño ni cierran sprints por documentación.

Diseño de interacción complementario, pendiente de autorización: [UX/UI A–M](SONG_BUILDER_UX_ARCHITECTURE_20261007.md). La creación inicial se centra en Custom/text2music; las otras acciones pasan al Studio. La sección L conserva la alineación de fases con estos sprints. No inicia una implementación ni cierra criterios de aceptación.

El [análisis A–H](SONG_BUILDER_ACE_STEP_ANALYSIS_20261007.md) incorpora el documento adjunto del usuario y la auditoría actual con Playwright. No se ha iniciado una reescritura ni se cierra un sprint por esta ampliación. Su sección H define aceptación y orden incremental:

- S00: perfil central observado, inventario y matriz de traducción.
- S03–S05: edición creativa compartida, revisión/procedencia y sincronización formulario/chat/request; resolver BPM de fase distinto de ficha.
- S06A–S06B: Builder progresivo y controles comunes con ayuda; catálogo editable, delegación explícita, selección de tres assets sin MIDI obligatorio.
- S06C: importación de fuente/referencia, seis acciones condicionadas por capacidades, booleano instrumental y ejecución exclusiva; separar contrato mock de inferencia real.
- S06D: feedback como propuesta de diff, revisión explícita y sample vigente.
- S06E: final, aceptación de audio y descarga verificada.
- S10: regresión integral, evidencias reales por modo disponible y piloto amateur.

Se reutilizan servicios, repositorios, jobs y validaciones existentes. El módulo histórico de servicios pagos se conserva fuera del alcance. La configuración Vulkan vigente no cambia.
La guía no limita el estudio. Una función ausente se identifica como tal; no se muestra un control que simule procesamiento.

## Alcance vigente: canción mediante ACE-Step

Esta corrección sustituye la ampliación a un DAW como condición de cierre. El objetivo activo es idea → instrumental/melodía vocal/letra → set válido → especificación compatible → plan aprobado → ACE-Step → sample representativo revisado → canción completa y descarga verificada. Se mantienen arquitectura hexagonal, SOLID/DRY, SQLite y providers intercambiables.

Una tarea entra al desarrollo activo si: (a) recoge una decisión musical y la traduce a una entrada comprobada del wrapper/API instalada; (b) prepara un audio fuente/referencia o intervalo requerido por un modo; (c) coordina y protege generación, versiones y aprobaciones; o (d) verifica fidelidad, audio y descarga. Cada tarea registra deseo/campo, parámetro u operación, adaptador y evidencia de aceptación. Un deseo expresado en caption/lyrics es condicionamiento aproximado, no un control determinista. Si no hay traducción viable, explicar la limitación y conservar el deseo; no fabricar controles ejecutables.

MIDI, piano roll, sintetizadores, mixer multipista, DSP general, automatización, grabación avanzada y DAW completo quedan diferidos. No son dependencias del cierre actual. La melodía vocal es una intención del proyecto, no una obligación de crear MIDI. Tampoco se exige WAV guía para text2music. La referencia musical no acredita clonación de voz. Los componentes existentes se conservan por compatibilidad; cambiar el backlog no cambia automáticamente las rutas del código.

### Matriz de trabajo activo

| Necesidad | Insumo/operación real | Entrega |
| --- | --- | --- |
| Género, emoción, instrumentación y carácter vocal | caption compilado con límites y prioridades | S03/S05/S06-A/B |
| Letra, idioma y estructura sugerida | lyrics y vocal_language; etiquetas sin tiempos exactos garantizados | S06-A/B |
| Tempo, tonalidad, compás, duración | campos estructurados traducidos por el adaptador instalado | S00/S03/S06 |
| Crear desde idea | text2music, perfil/configuración y seed registrados | S06-C |
| Transformar estilo | cover, src_audio/caption y controles traducidos | S06-C/S10 |
| Corregir fragmento | repaint, fuente e intervalo en segundos | S06-C/S10 |
| Añadir, extraer o completar pistas | lego/extract/complete, fuente, instruction/pistas compatibles y Base | S06-C/S10 |
| Referencia de audio | reference_audio solo cuando su traducción esté conectada/verificada; importación mínima validada | S06-A/C |
| Sample, escucha, correcciones y final | artefactos/checksums, configuración representativa, aprobación vigente y política backend | S01/S06-D/E |
| Descarga y ayuda amateur | export del audio aprobado, formatos comprobados y explicación de controles reales | S06-E/S10 |

No todos los parámetros documentados están necesariamente expuestos por el wrapper. S00 mantiene la matriz documentado/traducido/ejecutado/verificado; la UI y los modelos consumen ese estado.

## Auditoría histórica de la solución — 2026-10-04
Esta matriz conserva el diagnóstico inicial, no el estado actualizado ni una lista de tareas activas. Sus acciones DAW están diferidas; la tabla consolidada S06 y la evidencia de 2026-10-06 describen los avances posteriores.

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
Gemma interpreta/enseña; Qwen compila especificación y plan; ModelOrchestrator administra modelos/tasks; MusicActionRouter valida y despacha operaciones compatibles; el adaptador ACE-Step genera y los adaptadores de medios/exportación verifican archivos. Adaptadores MIDI/DSP/DAW generales quedan fuera de la entrega activa.
MusicProjectState es una proyección de SQLite, no un segundo almacén mutable. UI y chat usan las mismas operaciones de dominio.
Reutilizar repositorios con migraciones aditivas para revisiones, fuentes, propuestas, operaciones, candidatos/renders, evaluaciones y jobs; decidir cambios concretos en S02. Tablas de clips, effect_chains y automation_lanes no son requisitos activos.
Las tres piezas obligatorias se mantienen separadas. La sesión referencia set/selecciones; ninguna importación de mezcla crea stems o MIDI ficticios. La idea tiene identidad persistida antes de formar un set completo.

Cada tool define ID, esquema, unidades/rangos, motor, precondiciones, capacidades, efectos, preview, reversibilidad, autorización y conceptos educativos.
Cada propuesta incluye project_id, base_revision_id, proposal_id, acciones ordenadas, IDs de targets, controles afectados, valor anterior/propuesto, motivo, coste estimado y alcance.
Distinguir cambiar un objetivo de la ficha de ejecutar una generación. El backend comprueba capacidades y decide la operación; no confía en que una instrucción del LLM sea ejecutable.
Confirmación explícita vincula propuesta/revisión. Una propuesta editada se revalida. Reject no ejecuta. Idempotency key impide repetición. Cancelación no publica audio parcial.
Preview generativo autorizado y aceptación final son estados distintos. Una comparación A/B no altera el render activo hasta aceptar.
IDs de controles referencian campos de ficha, fuentes y artefactos reales; una etiqueta de pista soportada por ACE-Step no acredita que ya exista una pista aislada.
Operaciones sobre audio requieren referencias/checksums, tiempo en segundos o ticks definido, sample rate, canales y revisión. Preservar originales y exterior de región mediante composición controlada; registrar tolerancias de transiciones.
Restaurar una revisión o candidato recupera sus referencias; no vuelve a ejecutar generación aleatoria. Restaurar una versión crea una revisión nueva.
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
- S04: puertos JobExecutor/generación/medios y composición de implementaciones mock/reales.
- S05 en adelante: pruebas de casos de uso con dobles sin motor externo; pruebas contractuales del adaptador y verificación de imports sobre límites acordados.
Cada entrega revisa dirección de dependencias, responsabilidad, reutilización de políticas y compatibilidad. No se acepta duplicar una validación de dominio dentro de endpoints o prompts ni introducir dependencia del SDK ACE-Step en entidades musicales.

## Secuencia y dependencias
Cadencia sugerida: iteraciones de 1–2 semanas, sin compromiso de calendario hasta conocer equipo, hardware y mediciones. Dividir un sprint si no cabe su criterio de salida; no reducir aceptación.
Camino activo: S00 → S01 → S02 → S03 → S04 → S05 → S06-A/B/C/D/E → S10. Las partes ya implementadas se verifican y reutilizan; no se reinician. S10 completa evaluación/edición de los seis modos sin depender de un DAW. Exportación mínima y ayuda contextual pertenecen al cierre S06-E/S10; S07–S09 y S11–S18 no bloquean ese cierre.
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
- Detectar paquete/API/checkpoint ACE-Step efectivos y hardware, comandos Gemma/Qwen y soporte/traducción de tareas.
- CapabilityRegistry con configured/available/verified/experimental, motivos y evidencia fechada.
- Probar contratos sin descargar modelos ni ejecutar generación larga automáticamente.
Aceptación: matriz por control y motor; capacidades desconocidas quedan no verificadas; ningún default se anuncia como ejecución real.
Salida: reporte técnico y registro reutilizable de entradas, traducción, perfil efectivo y seis modos ACE-Step.

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
- Fuentes originales inmutables con checksums, candidatos/renders por versión y referencias de audio para ACE-Step; sin modelo de sesión multipista obligatorio.
- Historial de decisiones y restauración de revisiones/artefactos; guardado explícito de propuestas IA. Undo/redo de clips DAW queda diferido.
- Migración de proyectos existentes sin perder assets, exportables ni eventos; snapshots JSON/Markdown derivados.
Aceptación: reiniciar conserva proyecto e historial; restaurar crea revisión trazable e invalida aprobaciones afectadas; dos pestañas no sobrescriben revisión; originales siguen intactos.

### S03 — Tools, Router, propuestas y conocimiento mínimo
Dependencia: S02.
- MusicToolRegistry/MusicActionRouter, esquemas tipados y estados de propuesta.
- Endpoints leer/proponer/editar/confirmar/rechazar/ejecutar/undo, IDs estables de controles.
- Catálogo y ayuda únicos para caption/letra, BPM, tonalidad, compás, duración, voz descrita, fuentes, intervalos y pistas soportadas; gain/pan no se ofrecen como controles ACE-Step sin traducción comprobada.
- Adaptador de propuesta mock y salida Gemma/Qwen validada bajo ModelOrchestrator.
Aceptación: rechazar tool inexistente, parámetros fuera de rango, destino ambiguo, falta de autorización y revisión obsoleta; explicación recupera decisiones reales.

### S04 — Jobs ACE-Step recuperables y reproducción de revisión
Dependencias: S02–S03.
- Jobs por proyecto con progreso, cancelación, idempotencia, recuperación, aislamiento y revalidación de revisión.
- Reproducción del archivo real con Play/Pause/Seek y A/B; sin transporte multipista obligatorio.
- Recursos y lifecycle del orquestador: suspender/restaurar modelos y registrar configuración efectiva; rechazar resultados tardíos.
Aceptación: cancelar permite continuar, reiniciar recupera estado sin publicar salidas parciales y un resultado obsoleto no reemplaza el activo. La reproducción corresponde al artefacto/checksum mostrado.

### S05 — Copilot y controles compartidos para entradas ACE-Step
Dependencias: S03–S04.
- Gemma recoge/explica deseos; Qwen propone especificación y cambios estructurados bajo ModelOrchestrator.
- Chat y formulario usan revisión, catálogo, validación y autorización comunes. Propuesta → explicación/diff → edición → confirmación → plan → ejecución autorizada → revisión del audio.
- Caso vertical: cambiar BPM objetivo exige nueva revisión/plan y generación ACE-Step; editar el número no transforma el audio existente. No exige time-stretch, MIDI ni fidelidad exacta de tempo.
Aceptación: propuestas no se autoguardan, límites del motor visibles, rechazo/error/doble confirmación/cambio concurrente/recarga cubiertos. Comprobar inferencia real de Gemma/Qwen por separado del fallback.
Hito: asistencia operativa sobre entradas compatibles; sin herramientas DAW genéricas como requisito.

### S06 — Creación guiada, ficha completa y ACE-Step real

#### Estado consolidado del sprint — 2026-10-04

Verificacion final de la continuacion: suite completa de 186 pruebas aprobada (312,071 s), mas cuatro pruebas nuevas aprobadas por separado; 8 pruebas frontend Node, build y compilacion correctos. La primera suite (184 pruebas) detecto cinco errores resueltos: steering excedido y fixture de export que dependia de RAM local. Este registro reemplaza el estado "regresion en curso" del avance narrativo. Sin inferencia/audio real, escucha ni validacion visual/amateur; el sprint conserva los pendientes de la tabla.

Esta tabla resume el estado actual; los avances narrados debajo conservan el historial y pueden describir pendientes ya implementados posteriormente.

| Fase | Implementado y verificable en contratos | Pendiente para aceptacion |
| --- | --- | --- |
| S06-A | Controles para seis modos, pistas compartidas, fuentes propias, revisiones pendientes y propuestas explicitas de correccion | Editor completo por requisito, referencia autorizada/importacion, tools de chat y validacion amateur |
| S06-B | Plan SQLite, hash/revision, confirmacion de letra, revalidacion de fuente y huella del set activo | Reconciliacion de letra del plan con asset seleccionado y trazabilidad completa por decision |
| S06-C | Runner exploratorio de seis modos, preflight, recursos, cancelacion, tasks, exclusividad y diagnosticos | Inferencia real de cada modo, memoria física durante carga y coordinacion externa/recuperacion de procesos |
| S06-D | Escucha persistida, A/B por requisito, criterios por modo, propuestas recuperables, contexto de correccion para Gemma/Qwen y sample con evidencia tecnica | Ajustes musicales estructurados revisables de Qwen, evaluadores musicales calibrados, representatividad, audio real escuchado y usabilidad |
| Aceptacion integral | Pruebas con SQLite temporal, WAV sinteticos y mocks; guardas de final real conservadas | Cancion cantada real desde idea, sample representativo aprobado, descarga verificada y prueba con usuarios amateur |

Handoff de correccion implementado: solicitud explicita por propuesta vigente, contexto del set y tres intenciones, ficha y notas hacia ModelOrchestrator; tasks/runs y respuesta persistidos. UI recupera sugerencias, identifica ejecucion o respaldo y datos historicos. Nunca aplica output ni sustituye aprobaciones. Tres pruebas específicas verifican contexto, autorización explicita y cambio de inputs durante la revision; siguen pendientes cambios musicales estructurados revisables por requisito y pruebas de obediencia real.

Restriccion local observada: ~1124 MB RAM disponible frente a presupuesto de 7049 MB por perfil (6025 MB de archivos de pesos +1024 MB reserva); no es medicion de working set. No iniciar inferencia con esta disponibilidad ni cerrar el sprint por aprobar contratos. No se requiere normalizacion/alineacion A/B para registrar opinion; implementarlas solo si la evaluacion audible demuestra necesidad.

Continuacion transversal: propuestas de correccion cubren las seis tareas. Lego/Extract/Complete exigen pistas e instruccion concordante y proponen Base explicitamente; Lego usa toda la fuente como contexto. Se reutiliza politica de tareas y editor existentes. El plan vinculado al set incorpora su fingerprint en el hash. El informe agrega criterios especificos de cover/repaint/lego/extract/complete, pendientes de escucha/analisis. El contexto de asistencia incluye la propuesta persistida; no aplica cambios creativos por silencio. Steering comun deduplicado dentro de su limite y archivos de rol incluidos por las reglas de Git. 55 pruebas backend específicas y 7 frontend aprobadas; build/compilacion correctos. Regresion completa en curso, sin atribuirle aprobacion.

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

Opinión de escucha: declarar escucha, aceptar candidato o pedir cambios con notas, vinculado a audio/checksum/task/plan/revision y guardado en eventos SQLite. UI recupera ultima opinion; no aprueba sample/final. 21 pruebas específicas y build aprobados. Falta escuchar/evaluar audio real, criterios adicionales y sample representativo; no cerrar S06-D.

- Generar sample real representativo desde plan/set vigentes, escuchar y aprobar artefacto específico. No usar audio guía/mock para autorizar final real.
- Informe por requisito vinculado a audio/revisión: integridad/duración medidas primero; tempo/tonalidad/letra/instrumentos/voz/melodía con métodos disponibles y límites explícitos.
- UI comparación intención/resultado y A/B, requisitos pendientes/incumplidos y corrección propuesta por modo; sin porcentaje global ficticio.
- Avance A/B: historial por proyecto (20 trabajos), reproductor B para candidatos completados y pausa mutua. Comparacion por requisito implementada: objetivos, cambios de plan/revision y duracion medida; los aspectos musicales sin evidencia quedan pendientes de analisis o escucha. Verificacion anterior: 37 pruebas backend; continuacion: 5 pruebas frontend y build aprobados. Pendientes correccion por modo, normalizacion/alineacion si se requieren y validacion visual/escucha amateur. No se calcula ganador ni se modifica la aprobacion del sample.
- Correccion inicial: controles de alcance y propuesta SQLite para repaint/cover/text2music desde opinion vigente y audio verificado; repaint exige intervalo dentro de duracion medida. 14 pruebas backend y build aprobados. No cambia ficha ni plan ni genera audio. Pendientes recuperacion visible, handoff al compilador, controles de pistas Base y edicion/escucha real; S06-D permanece abierto.
- Continuacion de correccion: recuperacion visible implementada con estado vigente/historico y carga explicita en el editor existente; el usuario guarda, confirma la ficha y prepara el plan por la ruta validada existente. No sobrescribe borradores abiertos ni transforma notas musicales automaticamente. 16 pruebas backend específicas, 7 frontend y build aprobados. Pendientes ajustes musicales revisables mediante handoff, pistas Base, edicion real y validacion visual/amateur; S06-D abierto.
- Aceptación: ninguna evaluación desconocida se anuncia cumplida y ninguna task completada sustituye aprobación por escucha.

#### S06-E / S10 — Validación real y cierre gradual

- Un caso real por modo, con recursos/tiempo/config/inputs/outputs y escucha registrados. Desbloquear disponibilidad por modo según evidencia, sin esperar que todos tengan el mismo rendimiento.
- Repaint/Lego conservan originales y evalúan contexto/joins; Extract evalúa fugas; Complete evalúa convivencia del arreglo; Cover evalúa objetivo/conservación; text2music evalúa canción y letra.
- Ejemplo trazable desde idea hasta descarga con set/sample vigentes, errores recuperables y correcciones parciales. Prueba con personas sin experiencia musical para validar UX.
- Aceptación: seis modos integrados y estado de verificación visible; calidad/fidelidad aprobadas para los casos probados, sin prometer resultados universales.

Este desglose incorpora el adjunto de fidelidad del usuario y sustituye las dependencias DAW del alcance activo. La integración de entradas y ejecución corresponde a S06; S10 verifica correcciones por modo usando audio fuente e intervalos, sin exigir timeline, mixer ni DSP general.

### S10 — Cierre de los seis modos y corrección contextual ACE-Step
Dependencias activas: S00–S06; no S07–S09.
- Ejecutar un caso trazable por modo con perfil compatible, fuentes verificadas, autorización, recursos/configuración y artefactos registrados.
- Importación mínima de audio válido, selección de fuente/pistas y controles de intervalo en segundos; no exige editor multipista ni extracción de MIDI.
- Repaint: evaluar región, conservación exterior y transiciones; preservar original. Si el resultado exige composición/crossfade, implementar solo la operación necesaria con evidencia, sin abrir un DSP general.
- Cover: evaluar transformación/conservación; Lego: nueva pista y contexto; Extract: pista/fugas; Complete: arreglo/coherencia; text2music: letra, canto e intención.
- Corrección revisable de Qwen → revisión confirmada → plan vigente → candidato → comparación/escucha; aceptar/rechazar sin perder originales.
- Final y descarga con sample representativo vigente, revisión completa y formatos verificados. Ayuda contextual y piloto amateur sobre este recorrido.
Aceptación: seis modos realmente probados, límites por modo visibles, incompatibilidades rechazadas antes de ejecutar y ejemplo reproducible de idea a descarga. Escucha y aceptación vinculadas al audio/versiones; no se promete identidad nota por nota ni calidad universal.


### S06-F — Cobertura adicional de entradas ACE-Step — 2026-10-06

Dependencias: S00, S06-A/B/C; misma ficha SQLite y aprobación, sin nueva fuente de verdad.

| Tarea | Entrega y estado |
| --- | --- |
| IN-01 Referencia musical | Implementado para WAV ya registrado del proyecto: selección UI, ruta derivada/validada, evidencia/hash en plan y --reference-audio. Importación de nuevos archivos y generación real pendientes. |
| IN-02 Variaciones | Semilla entera opcional editable; persistida en revisión pendiente y traducida a --seed. Vacío delega al wrapper (42 actualmente). No garantiza identidad entre versiones/hardware. |
| IN-03 Ajustes por modelo | Pasos, guidance y shift opcionales con validación compartida; Turbo limita pasos a 20 y guidance a 1, Base pasos a 200. Wrapper aplica shift de perfil (Turbo 3/Base 1) si se delega y batch_size=1. Límites shift 0.1–10 son política conservadora Song-AI, no rango universal del motor. |
| IN-04 Ausencia de voz | Handler directo instalado no expone booleano instrumental. Mantener tres intenciones y canto final; pendiente adaptación comprobada de candidato instrumental mediante letra [Instrumental] y evaluación, sin presentar booleano inexistente como control conectado. |
| IN-05 LM interno | Evaluación de alto nivel documentada en ACE_STEP_CAPABILITIES.md: códigos 5 Hz útiles para ensayo text2music; sin mejora audible demostrada. Política explícita direct_handler_no_lm_rewrite en plan/diagnóstico; esta ruta no ejecuta el LM de alto nivel. No exponer thinking/use_cot/lm_negative_prompt como controles efectivos. Integración LM solo si se decide usar esa API, con preservación de deseos y evidencia. |
| IN-06 Caption y restricciones | Amplía condicionamiento con groove, rango vocal y balance; conserva especificación completa y rechaza exceso de longitud. Pendientes compilación revisable de exclusiones/prioridades y reconciliación de letra exacta con asset. No convertir exclusiones en negative prompt ficticio. |

Aceptación por tarea: edición explícita → revisión pendiente → confirmación → plan con parámetros/evidencia → argumentos efectivos → diagnóstico → audio evaluado. Sustituir referencia/seed/ajustes invalida el plan; referencia se revalida al preparar/aprobar/ejecutar. Los pasos esperados del informe runtime usan el override aprobado. Controles vacíos delegan al perfil y no acreditan calidad. Se deben probar inferencia, memoria, voz/fidelidad y usabilidad; S06-F y S06 siguen abiertos hasta esa evidencia.

## Ampliaciones diferidas: fuera del cierre y desarrollo activo

El siguiente bloque conserva el backlog anterior y su numeración para trazabilidad. Sus dependencias/criterios son históricos y NO se aplican al camino activo. No programar estas ampliaciones sin nueva priorización explícita. S10 histórico queda sustituido por el S10 activo anterior. Voz personalizada S18 es una ampliación opcional con provider/evidencia propios; no bloquea canto generado ACE-Step.

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

### S10 histórico — Edición generativa dependiente de DAW (sustituido)
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
Riesgos activos: compatibilidad API/checkpoint, recursos durante generación, obediencia Gemma/Qwen, fidelidad aproximada, canto, conservación de fuente/transiciones/fugas por modo y representatividad del sample. S00/S04/S06/S10 aportan evidencia. Stretch, monitor y DAW no son riesgos de cierre del alcance actual.

Continuacion S06-D: vigencia derivada de opiniones por plan/revision e inputs actuales, sin reescribir decisiones historicas. UI muestra contexto y notas guardadas. 22 pruebas específicas y build aprobados; pendiente audio real, validacion visual y sample representativo.

### Revision musical por aspectos — S06-D

El formulario de escucha permite respuestas opcionales por criterio del informe del candidato: acorde a mi idea, necesita cambios o no estoy seguro. No hay respuestas por defecto. Backend acepta solo criterios no medidos presentes en ese candidato; no permite sustituir mediciones objetivas ni inventar criterios. Marcar un cambio exige decision changes_requested y notas. Respuestas se guardan en el mismo evento SQLite con criteria_method=user_listening, vinculadas al audio/revision; no modifican el informe tecnico ni aprueban sample/final. La UI muestra las respuestas guardadas.

25 pruebas específicas aprobadas y build frontend correcto. Avance local; S06-D sigue en progreso. Pendientes validacion visual/amateur, evaluadores musicales, audio ACE-Step real escuchado y sample representativo.

### Contexto de escucha para asistencia — S06-D

Gemma recibe candidate_listening desde SQLite para el ultimo candidato completado del proyecto activo: decision, notas, criterios y vigencia. El mismo contexto acompaña handoffs del orquestador hacia revision tecnica. Si no hay proyecto/candidato o revision de escucha, queda pendiente sin aceptacion implicita. Steering Gemma/Qwen identifica evidencia subjetiva/historica y exige propuestas revisables, sin cambios automaticos ni aprobacion de sample/final. No acredita inferencia ni obediencia real de modelos. Avance local; sprint sigue en progreso.

Verificacion del contexto: 30 pruebas específicas aprobadas (incluidas dos regresiones Gemma), compilacion Python y diff correctos. No se ejecuto inferencia real, audio ACE-Step ni validacion visual.

### Integridad del audio revisado — S06-D

Al recuperar la opinion se verifica el archivo contra el checksum y evidencia del candidato. audio_current=false indica archivo cambiado/ausente; el assistant recibe audio_unavailable y la UI orienta a generar otro candidato. El evento original permanece intacto. Prueba de integracion con SQLite temporal y WAV sintetico verifica recarga, notas, identidad de audio, sustitucion e aislamiento entre proyectos. 29 pruebas específicas aprobadas, build frontend correcto. No se ejecuto ACE-Step real ni se valido la escucha o UX; sprint abierto y cambios locales.

### Vinculo del candidato al set — S06-D

Los nuevos candidatos de proyectos vinculados a set registran set_id y set_fingerprint calculada antes de generar audio. El runner comprueba el mismo vinculo y huella antes de ejecutar y tras inspeccionar la salida; cambios bloquean el registro del candidato. Proyectos sin set siguen permitiendo exploracion con vinculo nulo; no habilitan sample/final. No se asigna una huella retrospectiva a candidatos historicos. Esta trazabilidad prepara el sample representativo, sin promover ni aprobar candidatos automaticamente.

33 pruebas específicas aprobadas, incluyendo cambio del set tras salida y revinculacion del proyecto; compilacion y diff correctos. No hubo ejecucion ACE-Step real. Pendientes: crear sample desde un candidato vigente, verificar representatividad de plan/provider/voz, escucha/aprobacion separada y validacion UX. Sprint abierto; avance local.

### Sample desde candidato vigente — S06-D

POST /api/pro/projects/{song_id}/ace-candidates/{task_id}/sample y accion visible crean una copia WAV independiente del candidato, con confirmacion explicita, set vinculado, huella de generacion, plan aprobado vigente y checksum verificados. Revalida despues de copiar; conserva origen task/artefacto/revision/configuracion. Guarda sample/audio en SQLite y snapshot regenerable. Candidatos historicos sin huella no se promueven. El nuevo sample tiene approval_status=pending y representativity_verified=false: exige escucha/aprobacion propias y no habilita produccion real. Se copia el audio completo, sin recorte ni inferencia nueva; no promete que represente la configuracion del final.

37 pruebas específicas aprobadas con SQLite temporal y WAV sintetico; build frontend correcto. Incluye cambio del set durante copia, aislamiento, checksum, persistencia y aprobacion separada con gate real cerrado. Sin audio ACE-Step real ni validacion visual/amateur. Avance local; S06-D permanece abierto. Pendientes: contrato/validacion de representatividad y configuracion final, audio real y UX.

### Informe de correspondencia del sample — S06-D

Accion UI y POST /api/pro/projects/{song_id}/samples/{sample_id}/representativity verifican propiedad y audio del sample, comparan set/plan aprobado vigente/revision/configuracion/modo/checksum y guardan informe como evento SQLite. Una coincidencia de configuracion no verifica representatividad audible: ejecucion efectiva, voz/canto y calidad/fidelidad por escucha quedan pendientes. No altera aprobacion ni abre gate real. La UI presenta el informe como comprobacion registrada y pide repetirla tras cambios.

40 pruebas específicas aprobadas, incluida persistencia/propiedad del informe y aprobacion intacta; build frontend correcto. Avance local sin inferencia ni audio ACE-Step real ni validacion visual. S06-D sigue abierto.

### Evidencia de ejecucion del candidato — S06-D

El adapter del runner lee diagnostico del wrapper limitado a 2 MB dentro del directorio del candidato. Conserva hashes de diagnostico/WAV, estado reportado, configuracion solicitada/reportada, dispositivo activo, fallback, pasos y tarea. Solo reported_completion si el diagnostico indica completed, inicializacion habilitada y salida con ruta/tamano coincidentes. Ausencia, formato invalido o check-only dejan evidencia pendiente. Se persiste en metadata SQLite del candidato y se conserva en la copia sample. El informe solo muestra ejecucion reportada si el hash corresponde al sample; sigue sin verificar voz, fidelidad audible ni representatividad y no habilita final real.

42 pruebas específicas aprobadas, build frontend/compilacion/diff correctos. Diagnosticos y WAV de pruebas son sinteticos; no se cargo ACE-Step ni se genero/escucho audio real. S06-D abierto; cambios locales.

### Comparacion del runtime reportado — S06-D

El informe compara hash WAV, configuracion inicializada, modo y pasos reportados contra el plan/perfil actuales. execution_configuration_matches solo se cumple cuando los cuatro datos estan presentes y coinciden desde wrapper_diagnostics con reported_completion. Ausencia/perfil desconocido queda pendiente; diferencia queda mismatch. No reutiliza coincidencia de datos guardados como evidencia de ejecucion. La UI muestra diferencias y fallback. Voz, calidad/fidelidad por escucha y representatividad siguen pendientes; no abre gate final.

45 pruebas específicas aprobadas, build frontend/compilacion/diff correctos. Incluye diferencias por campo y rechazo de booleano como pasos. Diagnosticos sinteticos; sin ejecucion de motor ni escucha real ni validacion visual. Cambios locales, S06-D abierto.

### Recuperacion y vigencia del informe — S06-D

GET /api/pro/projects/{song_id}/samples/{sample_id}/representativity recupera la ultima evaluacion desde eventos SQLite y compara con los datos/evidencias actuales. No registra una nueva evaluacion ni reescribe el historial. assessment_current=false e invalid_reason identifican cambio del plan/aprobacion/audio o evidencia no verificable; desactiva las coincidencias derivadas vigentes conservando el resultado historico. La UI recupera informe al cargar Production y muestra su vigencia. POST sigue siendo la accion explicita para evaluar y guardar de nuevo.

45 pruebas específicas aprobadas, incluyendo recuperacion, plan desactualizado, audio sustituido y ausencia de eventos adicionales; build/compilacion/diff correctos. Cambios locales, sprint abierto; pendientes audio real y validacion visual/amateur.

### Contexto del sample para asistencia — S06-D

SampleEvaluationContext entrega desde SQLite el sample del proyecto seleccionado, estado de aprobacion, ultimo informe y vigencia al readiness de Gemma y handoffs tecnicos del orquestador. Distingue set/sample/evaluacion pendientes e informe historico; no utiliza samples de otro proyecto del mismo set. No crea evaluaciones al consultar ni autoriza final real. Steering Gemma/Qwen exige explicar diferencias/pendientes y proponer correcciones revisables sin alterar deseos aprobados. Cambios locales; pendiente obediencia/inferencia real de modelos y validacion de audio/UX.

Verificacion: 50 pruebas específicas aprobadas, incluidas dos regresiones de Gemma; compilacion Python y diff correctos. No hubo inferencia Gemma/Qwen ni audio ACE-Step reales. S06-D sigue abierto.

### Siguiente accion desde evidencia — S06-D

NextAudioAction selecciona una accion desde contextos SQLite de candidato/sample: completar set, escuchar, revisar opinion historica/cambios, crear sample, repetir/completar evaluacion o resolver evidencias pendientes. Gemma devuelve esa accion en guia determinista y la prioriza en recomendaciones/fallback, evitando consejo tecnico antiguo que sugiera final antes de revisar sample. No ejecuta ni guarda decisiones del usuario; ninguna rama autoriza final real.

52 pruebas específicas aprobadas, incluida prioridad de escucha ante consejo de mastering/export; compilacion/diff correctos. Cambios locales; pendiente validacion real de modelos, audio y UX. S06-D sigue abierto.

### Opinion propia del sample — S06-D

POST /api/pro/projects/{song_id}/samples/{sample_id}/review y formulario visible guardan opinion accepted/changes_requested, notas, declaracion de escucha, checksum y huella del set. Contrato comun de validacion con la opinion del candidato; datos persistidos en sample SQLite y eventos historicos propios. Verifica propietario, audio y vigencia. Solicitar cambios retira aprobacion previa y bloquea aprobar hasta registrar otra opinion; accepted no aprueba automaticamente. Gemma recibe notas y prioriza revisar cambios del sample. Ninguna opinion verifica representatividad ni calidad final.

54 pruebas específicas aprobadas, build/compilacion/diff correctos; prueba SQLite comprueba persistencia, retiro de aprobacion y bloqueo ante cambios. El evento de fase distingue SAMPLE_LISTENING_REVIEWED de creacion. Sin audio ACE-Step real ni validacion visual/amateur. S06-D abierto; cambios locales.

### Vigencia de la opinion del sample — S06-D

GET de review del sample verifica huella del set y audio; devuelve review_current/invalid_reason sin modificar decisiones ni eventos. UI muestra opiniones historicas y Gemma las distingue al elegir siguiente accion. SampleGate rechaza cambios solicitados incluso ante un registro inconsistentemente approved. La opinion permanece vinculada al audio original.

55 pruebas específicas aprobadas y prueba adicional del gate aprobada en su modulo (10 pruebas); build frontend/compilacion/diff correctos. Sin audio real ni validacion visual/amateur. Cambios locales; S06-D sigue abierto.

### Mediciones tecnicas PCM del sample — S06-D

El informe incluye signal_metrics vinculadas al checksum: pico/RMS dBFS, silencio digital, numero/proporcion de valores en limites de amplitud. Adapter procesa bloques PCM enteros de 8/16/24/32 bits, reconoce offset unsigned de 8 bits y revalida archivo tras medir. No son LUFS, true peak, deteccion de canto ni calificacion musical. Silencio digital vigente orienta a regenerar; tocar amplitud limite solo es indicio para escuchar, no confirma clipping audible. UI separa indicaciones comunes y niveles avanzados; medidas se guardan en la evaluacion SQLite y conservan vigencia del informe.

58 pruebas específicas aprobadas, build/compilacion/diff correctos. Audio de pruebas sintetico; no se ejecuto ACE-Step ni se valido escucha o UX reales. Cambios locales; S06-D abierto.

### Bloqueo de silencio digital — S06-D

La aprobacion de samples con audio requiere medicion PCM vigente y rechaza silencio digital. SampleGate revalida señal al revisar un sample aprobado, bloqueando tambien aprobaciones antiguas de WAV silencioso. Comparacion/checksum evita usar medidas de otro audio. La aprobacion guarda signal_metrics; señal presente no verifica musica/canto, calidad o representatividad. Checkpoints mock sin audio conservan su ruta de prueba y no autorizan produccion real.

61 pruebas específicas aprobadas, compilacion/diff correctos. Integracion SQLite verifica rechazo sin cambiar pending y rechazo de registro historico aprobado con silencio. Fixtures de aprobacion usan señal sintetica no nula; no acreditan voz ni musica. Cambios locales, sprint abierto; sin ejecucion ACE-Step, escucha ni validacion UX reales.

### Diagnostico local y bloqueo de RAM — S06-C/D

2026-10-04: wrapper ejecutado offline con --check-only. Base/CPU y Turbo/XPU terminaron con exit 0 y check_only_completed; handler ACE-Step 1.5 importado, torch 2.9.1+xpu, Intel Graphics detectada. Turbo selecciono xpu con --require-device true; Base selecciono cpu. Evidencia local en data/diagnostics/runtime-check/base-cpu.json y turbo-xpu.json (datos ignorados por Git). No se cargaron pesos, no se generaron WAV ni se probaron los seis modos por inferencia. La presencia del backend no acredita memoria para el modelo ni calidad audible.

El diagnostico Base observo RAM libre 2281,77 MB antes y 1640,27 MB tras imports. ResourceMonitor ahora devuelve ready=false/blocked_ram por debajo del minimo configurado (3500 MB por defecto); se debe liberar memoria y repetir comprobacion. El runner ya respeta este bloqueo y restaura modelos al cerrar. Minimo configurado no demuestra suficiencia por perfil; esa medicion sigue pendiente. Se retiro el consejo de sustituir ACE-Step por RVC, porque conversion vocal no sustituye generacion musical.

5 pruebas específicas aprobadas de recursos/runner, compilacion/diff correctos. Cambios locales; sprint abierto y pendientes carga efectiva, generacion/escucha real y validacion UX.

### Presupuesto conservador por perfil — S06-C/D

Preflight y runner ACE-Step estiman memoria por bytes locales de DiT seleccionado, VAE y Qwen3-Embedding, mas 1024 MB de reserva. Antes del proceso, tras liberar modelos de texto, ResourceMonitor exige el mayor entre ese presupuesto y el minimo configurado. Pesos ausentes impiden calcular presupuesto; psutil ausente bloquea verificacion. No es working set medido ni garantia de carga: activaciones, temporales, offload y memoria compartida pueden necesitar mas; LM interno no se incluye porque esta ruta no lo inicializa. Otros providers conservan chequeo generico.

Lectura local 2026-10-04: Base y Turbo suman 6025 MB de archivos y presupuesto 7049 MB. RAM del diagnostico previo (~1,6 GB tras imports) queda por debajo; no se inicio inferencia. Evidencia de presupuesto se conserva en payload preflight de task y evento del runner. 17 pruebas específicas aprobadas, compilacion/diff correctos. Cambios locales; pendientes medir carga/generacion real, escuchar y validar UX.

### Corrección de alcance y evidencia vigente — 2026-10-06

MIDI/DAW retirados del camino activo; historial conservado en ampliaciones diferidas. S00–S06/S10 permanecen abiertos según criterios pendientes, no por ausencia de piano roll/mixer. Auditoría Playwright actual: navegación, controles de seis modos, fichas/planes, A/B, correcciones, sample y bloqueos con SQLite temporal/WAV sintéticos; dos fallos UI corregidos. 9 pruebas frontend y build aprobados. Backend completo anterior: 190 pruebas aprobadas. Ver `HANDOFF_PLAYWRIGHT_2026-10-02.md`; falta inferencia/audio real, aceptación audible y piloto amateur. Los pendientes visuales narrativos previos son históricos para los recorridos ya auditados; no se extiende esa evidencia a funciones no probadas.

### IN-07 — Experimento de API alto nivel (propuesto tras evaluación)

Dentro de S00/S06-C/F, sin sprint nuevo ni dependencia MIDI/DAW. Adaptador opcional GenerationParams/GenerationConfig; ruta directa conservada. Política inicial: text2music con códigos LM, reescritura caption/idioma/metadatos desactivada, inputs confirmados, batch 1, config.seeds explícitas, evidencia de LM solicitado/ejecutado y entradas efectivas. Medir presupuesto conjunto y lifecycle antes de cargar. A/B real con varias seeds, letra/fidelidad/canto/estructura/tiempos y memoria; usuario revisa resultado. Lego/Complete requieren ensayo separado; Cover/Repaint/Extract omiten LM instalado. No habilitar por defecto ni cerrar IN-07 mediante mocks; Evaluación inicial seguida de autorización del usuario para dejar rutas opcionales conectadas. Estado actualizado abajo; inferencia/escucha reales siguen pendientes.

### IN-07 conectado como opción — 2026-10-06

Selector UI direct (default), high_level (sin LM) y high_level_lm (experimental text2music). Elección/modelo guardados en la ficha pendiente y payload/hash del plan; traductor ejecuta --generation-api/--lm-model-path. Adaptador tools/acestep_high_level.py consume dataclasses instaladas y produce audio compatible con el pipeline existente. Config.seeds explícitas, batch=1, caption/letra/idioma comprobados sin reescritura; LM inicializado con backend pt/CPU/offload y descargado al terminar. Fallo o falta de códigos deja task fallida, sin fallback oculto. No ampliar LM a otros modos sin evaluación.

Preflight exige pesos/config/tokenizer del LM seleccionado; presupuesto y guarda previa al proceso agregan pesos LM y reserva adicional. Exclusividad, suspensión/restauración y cancelación existentes se reutilizan. Diagnóstico persiste API solicitada, LM solicitado/usado, modelo, estado y tiempos; evidencia de candidato/sample conserva esos datos y evaluación rechaza ruta/LM discrepantes. Calidad no acreditada por diagnóstico. 38 pruebas backend específicas y 9 frontend aprobadas; build/compilación/diff correctos. AST confirma campos GenerationParams/GenerationConfig contra instalación. Sin carga/inferencia real ni Playwright de estos controles nuevos. Conectado y listo para ensayo con recursos suficientes; sprint abierto por validación musical/amateur.

## Cierre de verificación S06-01 — 2026-10-09

Matriz de componentes del Builder cerrada en Chromium: navegación/persistencia, reflow/texto200%, labels/estado/teclado, sliders numéricos, errores, contraste campos/texto/dialogos y estados CTA. Correcciones y límites en `BUILDER_ACCESSIBILITY_CLOSURE_20261009.md`. V0,5→1; aceptación separada. Global90,8%. S06 restante se concentra en integración runtime/handoffs/LM/entrega, sin reabrir accesibilidad ya cubierta salvo defecto concreto.

## S04-02/03 verificación real cerrada — 2026-10-09

Cancelación Turbo/XPU con pipeline_loaded, worker terminado sin WAV y recuperación administrada Gemma/Qwen con inferencia real breve. Cierra cancelación/lifecycle local combinando evidencia de jobs y física, sin cerrar otros modos/trazas. `REAL_CANCELLATION_HANDOFF_20261009.md`; global92,0%. Próximo lote real: APIalto nivel sinLM.
