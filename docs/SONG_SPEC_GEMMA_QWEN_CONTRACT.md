# Contrato: especificación completa de canción con Gemma y Qwen

Fecha: 2026-10-03. Estado: **implementación iniciada el 2026-10-04**. Este documento define el trabajo conjunto del assistant creativo y el director técnico para preservar los deseos del usuario y producir una especificación ejecutable. Complementa [el recorrido amateur](AMATEUR_USER_FLOW_REVIEW.md) y [los criterios de audio y voz](AMATEUR_AUDIO_VOICE_STEERING.md); no sustituye sus criterios de calidad.

Entregas iniciales: existe historial inmutable `song_spec_revisions`, endpoint de consulta de ficha/revisiones, catálogo backend versionado, snapshots `song_spec.json`/`song_spec.md` y vista de cobertura en Production. La compilación registra task/model run/evento para la revisión técnica y diferencia provider real, mock y fallback. Los campos iniciales conservan procedencia básica. El usuario puede confirmar la revisión activa y se rechaza una confirmación obsoleta. La revisión completa permanece en la fase de ficha hasta confirmarse; backend y UI bloquean las fases profesionales posteriores mientras siga pendiente. Quedan pendientes la inferencia real de Gemma en esta ruta, respuesta estructurada de Qwen que pueda proponer cambios, procedencia por requisito/decisión, editor completo y gates dependientes del sample o de cambios creativos posteriores.

## Objetivo y brecha actual

### Integración de la definición de fidelidad — 2026-10-04

Se incorpora el adjunto «Implementar un sistema de fidelidad a la intención musical en Song-AI». Su alcance es integrar los seis modos en el recorrido completo, con entradas revisables y trazabilidad del resultado. `MusicSpec` designa la especificación versionada existente en SQLite (`song_specs`/`song_spec_revisions`); no crear un archivo o servicio paralelo como fuente activa. `ACEPlan` evoluciona el compilador existente. La aprobación de especificación, la del plan, la del sample y la del audio final son decisiones diferentes.

#### Diagnóstico del código actual

| Componente existente | Reutilización y brecha |
| --- | --- |
| `SongSpecificationService` | Catálogo y procedencia básica; faltan entradas específicas por modo y procedencia por decisión/requisito con obligatoriedad y confirmación. |
| `TechnicalDirectorService` | Validación de completitud determinista; no equivale a revisión Qwen real ni mide fidelidad. Evitar atribuir autoridad del modelo al campo histórico `approved_by_qwen`. |
| SQLite: `song_specs`, `song_spec_revisions` | Revisiones y confirmación existentes; ampliar trazabilidad sin duplicar estado. |
| `AceStepPlanCompiler` / `PreviewAceStepPlan` | Seis candidatos, mapeo musical, conservación de ficha, verificación opcional de fuente; falta almacenamiento/aprobación/invalidación del plan y selección pública. |
| `tools/acestep_generate.py` | Seis tareas enviadas al handler y flags musicales; falta consumo de un plan aprobado mediante adaptador seguro. |
| `ProfessionalFullSongService` | Construye todavía un prompt y comando históricos; conectar ejecución local desde el plan vigente. El `ProfessionalSongService` histórico permanece congelado. |
| MIDI / instrumental / voz | Servicios existentes no demuestran conservación exacta de notas, stems ni identidad vocal; distinguir representación, guía acústica y resultado. |
| `SampleGate`, evidencia WAV y ResourceMonitor | Reutilizar controles de vigencia, integridad y recursos; faltan sample real representativo, prueba de memoria liberada y evaluación de fidelidad. |

#### Insumos y acciones visibles por modo

| Acción para el usuario | Modo | Insumos del proyecto | Qué revisar |
| --- | --- | --- | --- |
| Crear desde mi idea | text2music | Ficha aprobada, descripción condicionante, letra y metadatos | Voz, letra, estilo y restricciones; no exige WAV guía. |
| Crear otra versión de este audio | cover | Audio fuente registrado, objetivo creativo, fuerza de conservación | Qué se conserva/cambia; no promete identidad de notas o voz. |
| Corregir esta parte | repaint | Fuente registrada, región temporal, descripción y letra aplicable | Región, contexto y audio exterior; conservar original. |
| Añadir un instrumento o voz | lego | Fuente de contexto, una pista objetivo, instrucción y descripción | Entrada/salida y concordancia con el arreglo; Base requerido. |
| Separar una parte del audio | extract | Mezcla registrada, una pista objetivo e instrucción | Fugas y artefactos; no denominarla stem original; Base requerido. |
| Completar el arreglo | complete | Audio parcial registrado, pistas a completar, instrucción y descripción | Arreglo propuesto y convivencia con material previo; Base requerido. |

Las tres piezas instrumental/melodía/letra siguen obligatorias en el proyecto; una operación sobre una pista no requiere fusionarlas ni sustituye el set. La referencia opcional de estilo/timbre tiene identidad y función distintas del audio fuente. MIDI se conserva como composición verificable y solo se renderiza a WAV cuando la estrategia elegida necesita audio. No exigir MIDI o WAV guía para text2music.

#### Autoridad, estados y evaluación

Cada decisión tendrá ID estable, valor, origen `explicit/approved/suggested/inferred/default`, obligatoriedad, confirmación, justificación y referencia al mensaje/decisión que la produjo. `approved` como origen conserva además la procedencia inicial: una sugerencia aceptada no se reescribe como deseo explícito. Defaults creativos necesitan aprobación o delegación explícita; los defaults técnicos se identifican y revisan con el plan. Los campos vacíos no autorizan completar silenciosamente.

Los estados `draft → needs_clarification → proposed → approved → ready → generated → evaluated` describen el ciclo de especificación/plan; se mapean a estados existentes con revisión y eventos, sin sustituir fases del proyecto. `ready` exige validación determinista, decisión del usuario, entradas íntegras y preflight aplicable. Un borrador exploratorio autorizado no aprueba sample/final ni relaja los gates finales.

Cada requisito tendrá método de evaluación: objetiva medida, estimación identificada, escucha del usuario o no verificable todavía. El informe conserva esperado/observado, tolerancia aprobada, método/versión y evidencia del artefacto; nunca un porcentaje global inventado. Integridad/duración no acreditan tempo, tonalidad, letra cantada, instrumentos, melodía o naturalidad. Un incumplimiento obligatorio impide cierre y propone una corrección compatible; cambiar requisito necesita una nueva decisión.

Antes de cada ejecución, comprobar revisiones de ficha/plan/letra/set, checksum de fuente/referencia, config efectiva y recursos. Persistir task, inputs y plan; liberar modelos de planificación y ejecutar ACE-Step de forma exclusiva. Revalidar inputs antes de registrar resultado para no asociarlo a una revisión cambiada. Mantener el original y salidas candidatas, comparación A/B, rechazo y recuperación. En el portátil de 16 GB, medir viabilidad por tarea; no inferirla de la descarga de pesos.

El orden de implementación y aceptación se detalla en S06-A–S06-E/S10 del plan de sprints. Esta incorporación define el contrato; no declara ejecución real, fidelidad audible ni seis modos disponibles en UI.

Gemma recoge y confirma lo que el usuario quiere transmitir. Qwen convierte esa intención en una especificación musical y técnica completa para la etapa correspondiente, identifica contradicciones y comprueba viabilidad con las capacidades reales del sistema. Gemma devuelve un resumen comprensible para que el usuario decida. Los providers generan desde la versión aprobada y los evaluadores comparan el resultado con ella.

Ya existe `song_specs` en SQLite y un snapshot `song_spec.json` en el flujo profesional. En `ProfessionalSongService.collect_spec`, la especificación se construye mediante reglas de `CreativeAgentService` y se valida mediante `TechnicalDirectorService`. `ModelManagerService.run_model` registra una simulación de carga/ejecución; no ejecuta una inferencia de Gemma o Qwen en esa ruta. El booleano `approved_by_qwen` actual se calcula por presencia de campos, no demuestra una revisión real del modelo, confirmación del usuario o fidelidad del audio. Otros caminos del assistant pueden consultar llama.cpp; eso no completa este contrato de especificación integral.

La ampliación debe evolucionar esa persistencia y el snapshot existentes, sin crear una segunda fuente activa. El documento es una especificación de la canción del usuario; no es código generado ni una modificación automática de la aplicación.

Revisar también la configuración de roles y prompts: hay caminos donde Qwen se describe como ayuda de código/debugging y el extractor está asociado al intérprete Gemma. El director técnico de canción debe poder revisar composición, cantabilidad, audio, capacidades y fidelidad sin reemplazar las decisiones creativas del usuario. Resolver ese mapeo explícitamente al implementar SP-02; no dar por cumplido el rol porque aparece el nombre Qwen en un evento.

## Responsabilidades y handoff

### Alineación con el motor — implementación 2026-10-04

`docs/ACE_STEP_CAPABILITIES.md` es el contrato del motor: sección de alto nivel, diferencias handler/HTTP y estado local conectado. `AceStepSteering` lo lee sin importar motores y el registry lo suministra por solicitud a ambos roles, con hashes y metadatos observados del wrapper. Qwen se describe ahora como director musical/técnico; su revisión conserva el contexto de capacidades en el resultado del handoff. Las consultas Gemma del proyecto registran la revisión de steering suministrada en el histórico SQLite. Esto no implementa el compilador ACEPlan ni demuestra obediencia de los modelos; requiere evaluación real posterior.

Cada campo de la ficha debe indicar ruta de ejecución: parámetro estructurado del motor, descripción condicionante, procesador externo o requisito pendiente/no soportado. La interfaz muestra el estado y explica la consecuencia; un campo configurable guardado no promete efecto audible. El plan conserva requisito, origen, revisión y validación; no reduce la ficha a un caption ni transforma restricciones incumplidas en valores aceptados.

| Actor | Responsabilidad | Entrega persistida |
| --- | --- | --- |
| Usuario | Describe deseos, fija preferencias esenciales, revisa propuestas y escucha resultados. | Decisiones, restricciones y aprobaciones asociadas a una versión. |
| Gemma / assistant creativo | Mantiene conversación, interpreta emoción y propósito, propone opciones, conserva cambios solicitados y pregunta solo lo necesario. | Brief, decisiones creativas y preguntas/respuestas con referencias de origen. |
| Qwen / director técnico | Compila el documento, completa propuestas técnicas, revisa coherencia musical, capacidades, dependencias y plan de producción/evaluación. | Especificación candidata, faltantes, conflictos, supuestos, requisitos no soportados y validación técnica. |
| Servicios de dominio | Validan esquema, rangos, tipos, relaciones, revisiones, autorizaciones y requisitos por etapa. | Informe determinista independiente de la respuesta del modelo. |
| ModelOrchestrator | Coordina tasks, recursos, carga real y resultados; registra qué modelo o fallback se ejecutó. | Tasks/model runs y eventos con sus versiones de entrada/salida. |
| Builders/providers/pipeline | Producen y exportan desde la revisión aprobada, preservando las tres intenciones. | Artefactos con huella de inputs y especificación de origen. |
| Evaluación y usuario | Comprueban audio real, fidelidad y satisfacción según la especificación. | Informes y decisiones por sample/render/export. |

El assistant persiste el brief revisable. El orquestador entrega a Qwen una task con identidad de preparación/proyecto, revisión de contexto y referencias a los datos activos. Qwen lee ese estado y persiste una propuesta estructurada. Gemma retoma desde el resultado persistido y explica las decisiones. No encadenar salidas de un modelo directamente como prompts libres al siguiente ni usar memoria privada del modelo como estado activo.

Los roles se mantienen intercambiables mediante providers. Para una ejecución identificada como Gemma/Qwen real, registrar la inferencia, versión de modelo, parámetros, respuesta validada y task correspondiente. Si falta el modelo, usar un fallback explícito para avanzar el prototipo sin atribuirle revisión Qwen real; mantener pendiente la evidencia del director técnico hasta una revisión válida.

## Contenido mínimo del documento completo

Qwen debe construir y mantener los siguientes bloques. Un campo puede ser propuesto por IA y confirmado sin preguntarle al usuario un dato técnico. Destinatario, ocasión, identidad de voz personalizada y stems son condicionales, no exigencias universales.

| Bloque | Contenido necesario |
| --- | --- |
| Identidad y revisión | `schema_version`, ID y revisión de especificación, identidad de preparación antes del set, proyecto/set/song relacionados cuando existan, fecha, autor/model run y huella de inputs. |
| Intención del usuario | Brief original, descripción activa, propósito, emoción, idioma, público/destinatario si aplica, estilo deseado, preferencias, elementos que deben conservarse y elementos que deben evitarse. |
| Restricciones y decisiones | Requisitos obligatorios frente a preferencias flexibles, alternativas aprobadas, límites de duración/recursos si los fija el usuario, supuestos y dudas aún pendientes. |
| Intención instrumental | Género o combinación, mood, tempo, tonalidad/modalidad, instrumentos y función, textura, energía por sección, arreglo, transiciones y restricciones. |
| Intención vocal | Canto frente a guía hablada, timbre, carácter, registro/tesitura propuesta, melodía y fraseo, energía, idioma/pronunciación, solista/coros, selección y versión de voz; referencia autorizada si se usa. |
| Intención lírica | Tema, narrador, tono, contenido deseado/excluido, idioma, nombres y pronunciación, texto aprobado y versión, estructura, métrica/prosodia, repetición y placeholders resueltos para el render. |
| Forma y compatibilidad | Secciones ordenadas, duración aproximada, cambios de energía, correspondencia letra/melodía/arreglo, validación de rango y cantabilidad, assets elegidos y versiones; incompatibilidades sin resolver. |
| Producción | Ruta Full Song o stems según capacidades verificadas; providers/modelos, parámetros relevantes, dependencias, recursos/preflight, formato interno y plan de mezcla. No inventar precisión o control que el motor no ofrece. |
| Sample y final | Fragmento representativo, parámetros comunes y específicos de longitud, selección de voz, reglas de invalidación, aprobación requerida y relación del sample con la revisión final. |
| Calidad y fidelidad | Perfil de calidad versionado, umbrales/tolerancias calibrados, métricas y revisión por escucha exigidas, criterios por requisito, quién verifica y qué pasa ante incumplimiento. |
| Exportación y reproducibilidad | Entregables pedidos y soportados, formatos, metadatos, parámetros/seed cuando exista, huellas de entrada, versiones y referencias a tasks/artefactos. Reproducibilidad documenta el proceso sin prometer audio idéntico de motores no deterministas. |

El `intent.json` conserva las tres intenciones; `set.json` conserva las selecciones; `manifest.json` documenta artefactos y procedencia. La especificación enlaza esos datos y los compila en una revisión coherente. Los exportadores usan el estado SQLite y la misma revisión para evitar copias divergentes. Generar `song_spec.json` para consumo técnico y `song_spec.md` como documento completo legible desde esa revisión; regenerarlos no modifica decisiones activas.

## Procedencia y fidelidad a los deseos

Cada requisito debe tener ID estable, valor o descripción, prioridad obligatoria/preferida, origen (petición explícita, propuesta IA, dato importado o decisión técnica), referencia al mensaje/decisión, justificación, confirmación y criterio de verificación. Un valor inferido permanece como propuesta hasta confirmarse; no atribuirlo al usuario como si lo hubiera pedido.

El documento incluye una matriz de trazabilidad: deseo → requisito → bloque musical/técnico → asset/selección → parámetros enviados al provider → evidencia de sample/final → decisión del usuario. Preservar texto original y significado, aunque el prompt del motor requiera traducción. Si no hay forma fiable de verificar un requisito, señalar evaluación pendiente o pedir escucha; no anunciarlo como cumplido.

Ejemplo de trazabilidad: «Quiero una canción tierna, en español, sin batería y que diga Lucía» produce requisitos verificables separados para emoción, idioma, ausencia de batería y nombre/pronunciación. «Sin batería» no se convierte silenciosamente en «percusión suave». BPM, tonalidad y arreglo pueden proponerse para lograr ternura; no se convierten en deseos originales ni se exige al usuario escogerlos manualmente. Cambiar letra/arreglo después requiere mostrar el efecto sobre esos requisitos.

Si una petición obligatoria no es soportada por el provider —por ejemplo conservar una voz específica— Qwen marca inviabilidad y Gemma ofrece alternativas. Una capacidad desconocida permanece pendiente. Cambiar motor o flexibilizar un requisito necesita confirmación; ningún fallback puede eliminarlo y conservar el estado de aprobación. Los límites deben comunicarse antes de ejecutar procesos largos.

## Completar progresivamente sin bloquear a un amateur

Las IA deben mostrar **todo el camino y todos los parámetros del contrato de canción**, explicar su efecto y ayudar a decidir. El usuario no necesita conocerlos previamente. Gemma orienta en lenguaje común y Qwen mantiene el inventario completo, las propuestas y sus dependencias. Preguntar solo lo necesario no permite omitir decisiones: las restantes se explican y pueden delegarse explícitamente.

### Catálogo completo de parámetros

Derivar el catálogo del esquema versionado de la especificación y de las capacidades declaradas por cada provider. Incluir todos los campos musicales y de producción del esquema, también los opcionales, y los controles específicos del motor elegido. IDs/checksums son consultables como trazabilidad, sin presentarlos como elecciones creativas. Un nuevo campo requiere entrada de catálogo y presentación en la ficha; evitar listas incompletas de UI que diverjan del backend.

| Familia | Decisiones que la guía y la ficha deben cubrir |
| --- | --- |
| Idea y estilo | Propósito, emoción, destinatario/ocasión si aplican, idioma, género, referencias descriptivas, duración y elementos deseados/excluidos. |
| Ritmo y armonía | Tempo/BPM, compás, groove/swing, tonalidad/modalidad, progresiones y cambios de ritmo/armonía cuando apliquen. |
| Base y arreglo | Instrumentos y funciones, textura, densidad, registro, energía/dinámica, secciones, entradas, transiciones e inicio/cierre. |
| Melodía y voz | Melodía, rango/tesitura, timbre, identidad vocal, fraseo, articulación, pronunciación, expresión, afinación estilística, solista/coros/dobles y referencia opcional. |
| Letra | Tema, narrador, tono, idioma, vocabulario, nombres, métrica/prosodia, rima si procede, secciones, repeticiones, exclusiones y placeholders. |
| Mezcla y producción | Balance voz/base, panorámica, espacio/reverberación, ecualización, dinámica/compresión, efectos, automatización si se soporta, ruta integrada/stems y controles de generación del motor. |
| Sample y calidad | Fragmento, duración de muestra, fidelidad al set/voz, aprobación, revisión, inteligibilidad, naturalidad, sonoridad/picos y verificaciones del perfil de calidad. |
| Entrega | Formatos, frecuencia de muestreo, profundidad de bits y bitrate cuando apliquen, canales, archivos separados disponibles, metadatos y descarga. |

Estas familias no prometen control exacto de cualquier motor. Qwen distingue intención expresable, parámetro configurable, elección automática del motor y capacidad no soportada/desconocida. Gemma y la UI explican qué puede elegir el usuario y qué puede comprobarse. Una preferencia enviada en un prompt no se presenta como garantía de control numérico. Si una restricción obligatoria exige una capacidad ausente, se aplica el bloqueo de viabilidad.

Cada entrada debe incluir: identificador, familia/etapa, nombre humano y técnico, significado, efecto audible esperado, unidad/rango/opciones, recomendación justificada según la idea, valor propuesto y guardado, procedencia, disponibilidad, dependencias, efecto del cambio sobre sample/final, estado de revisión y modo editable/delegado/informativo. Los ejemplos audibles se ofrecen cuando existan, identificados como ejemplos; si no hay audio, explicarlo por texto.

### Deber de guía y decisiones delegadas

1. Mostrar desde el inicio los cinco hitos, qué se decidirá en cada uno y el estado real. Gemma introduce las familias y ofrece «Recorrer las decisiones conmigo»; la app ofrece «Ver configuración completa».
2. En cada hito, explicar decisiones con ejemplos breves y proponer una combinación coherente con la idea. Ofrecer elegir, ajustar o «Que la IA lo proponga», sin depender de preguntas musicales que el usuario no sabe formular.
3. Mostrar un índice de todas las familias con progreso y detalle desplegable. La ficha completa permite buscar/revisar cualquier parámetro, incluidos no aplicables/no soportados con su motivo. Controles técnicos viven en ajustes avanzados, y la guía explica las consecuencias relevantes.
4. Permitir aceptar propuestas por grupo o delegar, mostrando antes resumen y restricciones. Registrar delegación y valores aprobados; «no sé» o silencio no son consentimiento. La delegación no habilita envío externo ni cambio de identidad vocal sin la confirmación exigida.
5. Antes de confirmar una etapa, mostrar elecciones, propuestas que se aprobarán, delegaciones, pendientes y conflictos. Una aprobación grupal no convierte una sugerencia IA en preferencia originalmente expresada por el usuario.
6. Persistir avance de la guía y permitir retomarlo tras recarga, consultar «¿Por qué elegiste esto?» y volver a cualquier decisión. Señalar cambios que requieren nueva aprobación.

Estados de cobertura por parámetro: por presentar, presentado con explicación, propuesta pendiente, decidido por el usuario, delegado con propuesta aprobada, no aplicable con motivo y no soportado con alternativa pendiente/resuelta. Son independientes de generación y calidad. Una delegación por familia identifica los campos incluidos y permite consultar sus valores; un botón genérico sin resumen accesible no acredita revisión.

No exigir una pregunta/clic por cada campo: aprobación grupal y delegación permiten completar la ficha sin convertir el recorrido en una clase obligatoria de teoría musical. Para declarar una etapa revisada, sus parámetros requeridos deben tener decisión confirmada, delegación aprobada o no aplicabilidad justificada. Requisitos obligatorios no soportados bloquean; parámetros futuros se muestran pendientes de otra etapa sin bloquear drafts anticipadamente.

### Contrato entre interfaz y conversación

La guía necesita controles visibles además de conversación. Formularios, catálogo, propuestas de Gemma/Qwen y documento técnico comparten identificadores, validaciones y revisión persistida. El assistant toma como contexto los valores guardados y, cuando corresponde, el borrador visible identificado; no presenta ese borrador como configuración ya guardada.

Una propuesta llega como cambio estructurado revisable: mostrar valor actual/propuesto, motivo, origen y dependencias afectadas. La UI permite aceptar, editar o descartar; aceptar actualiza el borrador y Guardar persiste con validación. No sobrescribir una edición local posterior por respuesta tardía de la IA: presentar conflicto y dejar elegir. Cada campo editable de la especificación debe tener control en la ruta guiada o avanzada, y cada campo delegado/informativo debe ser consultable. Un control de chat aislado no cumple este requisito.

| Etapa | Condición para avanzar |
| --- | --- |
| Preparación | Brief útil y propuestas separadas de decisiones. Puede tener campos técnicos pendientes y no crea un set. Gemma pregunta únicamente dudas creativas que cambian materialmente el resultado. |
| Generación de drafts | Intenciones suficientes y configuración válida para el draft solicitado, con propuestas aceptadas para esa acción. No exige todos los IDs de assets, letra final ni aprobación de calidad todavía. |
| Confirmación del set | Tres drafts seleccionados y válidos, compatibilidad revisada, decisiones creativas confirmadas y versiones identificadas. |
| Generación del sample | Especificación de producción completa para esa etapa, validación técnica y determinista, capacidades/preflight disponibles y requisitos obligatorios viables. |
| Producción final | Revisión ejecutable completa y aprobada por el usuario, más sample representativo vigente y aprobado para sus inputs. |
| Final y descarga | Audio completo evaluado, fidelidad comprobada y aceptación según el contrato de audio/voz; exportables verificados de la misma revisión. |

No exigir destinatario para una canción sin destinatario ni una tonalidad elegida manualmente para un usuario que acepta propuestas. Qwen propone los detalles musicales/técnicos y Gemma explica sus efectos durante el recorrido. La UI ofrece resumen creativo antes de confirmar, controles de configuración y acceso a la ficha y documento completos. Aprobar el documento no equivale a haber aprobado un sample ni la canción final.

## Versiones y aprobaciones

Separar: estado de compilación (`draft`, `needs_information`, `needs_resolution`, `complete_for_stage`), validación determinista, revisión técnica del modelo, confirmación del usuario y evaluación del audio. `complete_for_stage` no autoriza por sí solo la siguiente acción. La autorización la resuelve el servicio de dominio con todas las condiciones de la etapa.

La especificación es inmutable por revisión: una modificación crea una candidata con diff y relación a su antecesora. La confirmación del usuario fija la revisión activa; se puede rechazar una candidata sin perder el trabajo previo. Cambios creativos relevantes invalidan aprobaciones dependientes. Un resultado de Qwen tardío o de otro proyecto nunca reemplaza el activo ni recibe aprobación automáticamente.

Migrar el booleano legado `approved_by_qwen` sin reinterpretarlo como inferencia real o consentimiento. Preservar su significado histórico de validación por reglas y añadir evidencia de revisión/ejecución y decisiones por etapa. Los registros antiguos requieren comprobar qué pueden acreditar antes de habilitar la ruta ampliada.

## Generación y evaluación desde el contrato

Los prompt builders compilan instrucciones desde la especificación activa, las tres intenciones y los archivos derivados `intent.json`, `profile.json` y `lyrics.md` de esa revisión. Los prompts no sustituyen la especificación ni se hardcodean por canción. Registrar requisitos representados y cualquier pérdida de control al mapearlos al provider; rechazar un plan que omita un requisito obligatorio sin decisión del usuario.

La evaluación compara los requisitos con el resultado real y registra cumple/no cumple/no evaluado por requisito. Gemma explica diferencias y propone ajustes concretos; Qwen prepara una nueva revisión o un plan de corrección. Limitar reintentos mediante configuración y decisión del usuario, conservando versiones y recursos consumidos. Si el modelo solo admite generación integrada, no prometer corregir una pista aislada.

El documento completo permite dirigir y auditar calidad y fidelidad; ningún LLM garantiza por sí solo una buena interpretación vocal o mezcla. La evidencia proviene también de capacidades del provider, señal de audio, escucha y aceptación del usuario. Mantener explícito qué fue verificado con mocks y qué con inferencia/audio reales.

## Entregas y aceptación

| ID | Prioridad | Entrega | Verificación necesaria |
| --- | --- | --- | --- |
| SP-01 | P0 | Esquema estructurado versionado, completitud por etapa y exportación JSON/Markdown desde SQLite. | Guardar, recargar y regenerar snapshots sin cambiar estado; datos inválidos no sustituyen una revisión válida; preparación sin set ni IDs aún inexistentes. |
| SP-02 | P0 | Handoff real Gemma → task persistida → Qwen → propuesta → Gemma → decisión del usuario. | Distinguir inferencia real, reglas y mock; registrar model runs; fallo, timeout o respuesta inválida conserva la revisión previa y explica la recuperación. |
| SP-03 | P0 | Requisitos, procedencia, restricciones y confirmación con diff. | Brief en español con exclusiones, nombre y preferencias: no perder ni invertir requisitos. Dudas y campos condicionales no obligan preguntas técnicas innecesarias; decisiones IA no aparecen como deseos confirmados. |
| SP-04 | P0 | Revisión de viabilidad, versionado y gates por etapa. | Rechazar requisito obligatorio no soportado, revisión antigua, contexto ajeno y aprobación faltante; mantener inválido sample afectado; migrar booleanos legados sin atribuir aprobación real. |
| SP-05 | P1 | Compilación a providers y matriz de fidelidad. | Prompts y parámetros trazables a una revisión aprobada; cambios/fallback no eliminan restricciones; evaluación real registra evidencia o estado no evaluado por requisito. |
| SP-06 | P1 | Evaluación del circuito completo y uso amateur. | Desde idea hasta documento, tres piezas, sample y final; usuario puede explicar qué aprobó, pedir cambios y recuperar el proyecto. Prueba de audio real y escucha según el contrato de calidad. |
| SP-07 | P0 | Catálogo de parámetros derivado del esquema y capacidades. | Cada campo musical/técnico y control del provider tiene significado, opciones, propuesta, procedencia, disponibilidad, dependencias y estado. Un cambio de esquema detecta entradas sin cobertura antes de publicar la guía. |
| SP-08 | P1 | Guía proactiva de todas las decisiones y delegación explícita. | Usuario que dice «No sé de música» recibe recorrido/propuestas, revisa las familias, acepta grupos o delega y retoma tras recarga. Puede consultar todo parámetro; no se confirma por silencio ni se promete control no soportado. |
| SP-09 | P1 | Interfaz de configuración completa sincronizada con IA y especificación. | Todo campo editable tiene control accesible; formularios y conversación convergen en la misma revisión. Propuesta no guardada, conflicto de edición, fallo de persistencia y respuesta tardía se resuelven sin pérdida. El recorrido se completa también con controles visibles sin depender exclusivamente del chat. |

Fixtures/mocks prueban estructura y estados; casos de inferencia real prueban extracción y compilación con los mismos briefs y versiones de modelos registrados. Incluir exclusiones, nombres/acentos, propuestas contradictorias, cambio de deseos, dos proyectos, respuesta tardía y provider incapaz. No medir fidelidad solo por tener campos llenos. Los resultados de esta evaluación deben quedar en README con límites y pendientes.
