# Estado de publicación del sprint — 2026-10-15

Tras preparar la propuesta técnica, Revisar muestra el siguiente paso según la revisión guardada. Si ya está confirmada, ofrece «Ir a Generar y preparar el plan» y explica que la propuesta es opcional y no cambia la ficha; si no, indica que debe confirmarse. El resumen técnico original queda desplegable para evitar que su texto sugiera una confirmación inexistente.

La propuesta técnica indica el paso real de tres etapas: preparar/registrar solicitud, consultar el modelo y validar/guardar la respuesta. El navegador consulta una ruta de estado ligada a un identificador único de solicitud; no usa tiempo transcurrido como porcentaje ni confunde tareas históricas con la actual. Al finalizar muestra 3 de 3 y la propuesta, o un error explícito. **Reinicia el lanzador** para cargar la nueva ruta backend antes de usar el seguimiento. Verificación: 383 pruebas Python, 378 aprobadas y 5 omitidas; 64 frontend aprobadas y build correcto.

La preparación de la propuesta técnica muestra tiempo transcurrido y confirma que la solicitud sigue esperando respuesta del modelo. El indicador no inventa un porcentaje: esta llamada devuelve el resultado al terminar. El estado se retira al recibir propuesta o error; la ficha guardada permanece intacta.

La barra lateral permite desplazamiento independiente cuando los pasos y estados exceden la altura de la ventana. En pantallas estrechas vuelve al flujo normal de la página, sin un área de desplazamiento anidada.

Generar abre ahora directamente con el estado real de la canción y una acción para ir al plan. Se retiraron de Revisar/Generar/Studio la segunda barra de siete pasos y la tarjeta extensa de preparación, duplicadas con la barra lateral. En Generar el recorrido y las estimaciones quedan disponibles en un detalle desplegable; las advertencias siguen visibles. La ficha, plan y controles de ejecución no cambian.

El refresco automático de 10 s en Generar consulta únicamente actividad y diagnóstico de recursos; ya no vuelve a cargar proyectos, ficha, plan ni exportaciones mientras se navega o edita. La actividad también puede actualizarse con su botón. Al finalizar un candidato, la app conserva la vista actual y deja Studio como paso explícito del usuario. Esto evita saltos de navegación y cambios visuales de la ficha durante el polling.

Los pasos 5, 6 y 7 tienen ahora vistas y rutas separadas: `/review` muestra la ficha y sus decisiones; `/generate` muestra el plan, la generación y el diagnóstico; `/studio` muestra escucha, sample opcional y descargas. Los tres conservan el proyecto activo y los controles de revisión/plan vigentes. `/production` abre la revisión para enlaces antiguos. Se verificaron navegación directa y contenido visible de las tres rutas en navegador; la aceptación amateur sigue pendiente.

Production presenta el estado de la revisión y el siguiente paso en lenguaje común. El contador de campos del catálogo ya explica que los vacíos no son necesariamente pendientes; una ficha confirmada dirige al plan. El título de archivos disponibles exige canción final verificada del plan y revisión activos, evitando que exportaciones históricas se anuncien como listas para la canción actual. Verificación y aceptación del audio siguen separadas.

La navegación lateral y la barra superior comparten ahora los mismos siete pasos y destinos: Idea, Sonido, Composición, Estructura y letra, Revisar, Generar y Studio. «Mis proyectos» abre la biblioteca; MIDI y melodía/voz quedan bajo «Herramientas adicionales». La tarjeta «Preparación de esta canción» muestra requisitos y aprobaciones, no pasos de navegación. Este ajuste de interfaz no modifica el estado de generación ni equivale a aceptación de usuario.

Desarrollo 100 %; avance de desarrollo/verificación 98,5 %. Cuatro verificaciones técnicas siguen parciales (S00-04, S06-05, S06-06 y S10-07). La escucha, la aprobación del audio y el piloto amateur se harán después de completar D/V. Para abrir la aplicación con doble clic y crear el acceso directo, consulta [Abrir Song AI con doble clic en Windows](#abrir-song-ai-con-doble-clic-en-windows). El [handoff de pendientes](docs/PENDING_SPRINT_HANDOFF_20261015.md) indica evidencia exigida, bloqueo de RAM para LM opcional y orden de continuación; el [avance calculado](docs/SPRINT_PROGRESS.md) conserva los estados por entregable. Pruebas agrupadas en Python/UI, Gemma/Qwen reales y ACE-Step real en el [lote de verificación](docs/SPRINT_VERIFICATION_BATCH_20261015.md).

Production muestra ahora un **Siguiente paso** con enlace a ficha, plan, generación o descargas según la revisión y el plan activos. La tarjeta **Generar canción completa** se habilita en la ruta ACE-Step `text2music` cuando ficha y plan vigentes están confirmados, sin exigir fases MIDI heredadas ni sample previo. [Guía para generar una canción](docs/PRODUCTION_FIRST_SONG_GUIDE_20261015.md). No se confirmó ni generó Alma durante este cambio.

Corrección del primer uso del lanzador: la petición «quiero modificar la voz» de Alma producía HTTP 400 en Gemma por 11 906 tokens enviados a un contexto de 8192. El contexto conversacional conserva ficha y procedencia vigentes sin duplicar historial; la misma petición recompuesta quedó en 5771 tokens y llama.cpp respondió HTTP 200. [Evidencia y límite](docs/GEMMA_CONTEXT_OVERFLOW_20261015.md). Reinicia Song AI para cargar el backend corregido; la ficha pendiente y las descargas históricas siguen protegidas.

Continuación S01-04: la ruta ACE-Step exporta desde el plan aprobado de QA y la revisión vigente de MusicSpec, sin exigir MIDI heredado ni marcar la letra pendiente como aprobada. En QA se verificaron manifest, ZIP con CRC, descargas ASGI de MP3/FLAC/ZIP y checksums de SQLite sobre audio real. S01-04 pasa V0,5→1; la escucha y aceptación siguen pendientes. [Evidencia](docs/REAL_FINAL_EXPORT_QA_20261015.md).

Hito previo de exportación: se corrigió la verificación repetida de checksums y se bloquea el ZIP si un artefacto registrado cambia. [Evidencia](docs/EXPORT_INTEGRITY_20261015.md): 372 pruebas Python ejecutadas, 367 aprobadas y 5 omitidas en ese corte.

La ruta local heredada de canción final también quedó alineada con el sample opcional: exige set y ficha confirmada, conserva revisión/huella del request y migra SQLite sin perder canciones antiguas. [Evidencia](docs/LEGACY_FINAL_SAMPLE_MIGRATION_20261015.md): suite completa posterior de 375 pruebas Python, 370 aprobadas, 5 omitidas. La exportación y descarga integradas de un resultado final real siguen pendientes; D/V 97,9 %.

Se generaron WAV/MP3/FLAC reales de 15 s en QA con ACE-Step Turbo y se verificaron checksum, formato y descarga individual. Se corrigió la búsqueda del `ffmpeg` administrado. [Evidencia y continuación](docs/REAL_FINAL_EXPORT_QA_20261015.md): el primer intento de manifest/ZIP falló por requisitos heredados; la continuación lo completó desde el plan ACE-Step vigente. Regresión de ese primer corte: 377 Python, 372 aprobadas, 5 omitidas.

# Intención emocional: controles numéricos y ayudas — 2026-10-09

Idea ofrece alternativa numérica0–100 a cada slider, con ayuda visible. Frontend/backend rechazan inválidos antes de guardar. 18 pruebas backend, 3 frontend y build aprobados; Playwright sincronización/rechazo/guardar/recarga63 verificados. [Evidencia](docs/EMOTIONAL_CONTROLS_QA_20261009.md). S06-01 parcial; D/V90,5%. Sin modelos/audio ni cambios a proyectos de producción.

# S06-01: comprobación agrupada de accesibilidad — 2026-10-09

Playwright: siete pasos sin controles observados sin nombre; texto200% sin overflow; seis estados de generación con contraste de texto/progreso/anuncios revisados. [Cobertura y límites](docs/ACCESSIBILITY_GROUPED_CHECK_20261009.md). Sin cambio funcional ni repetición de suites; S06-01 sigue parcial, D/V90,5%.

# Biblioteca: nombres y estados de favoritos — 2026-10-09

Botones de estrella con acción accesible y aria-pressed. Build aprobado; Playwright verificó Enter, recarga y eliminación en QA. [Evidencia](docs/LIBRARY_FAVORITES_ACCESSIBILITY_20261009.md). S06-01 sigue parcial, D/V90,5%, sin modelos/audio nuevos.

# Qwen: arranque manual con el perfil guardado — 2026-10-09

Los scripts LLM cargan ahora .env con precedencia del entorno; antes el arranque manual omitía batch/ubatch/flash-attn guardados. Sin modificar Vulkan/perfiles. Prueba del cargador aprobada; revisión Qwen real de6874tokens completada en109,67s sin fallback, con ambos modelos cargados. [Causa/evidencia](docs/QWEN_STARTUP_PROFILE_FIX_20261009.md). S05-03 V0,5→1; global89,9→90,5%. Audio al final.

# Lote real de modelos: Gemma verificada, Qwen reabierto — 2026-10-09

Gemma completa dos escenarios protegidos sin alterar ficha (S05-02 V0,5→1). Qwen falla la revisión real con desconexiones incluso aislado; fallback identificado, S05-03 V1→0,5. Perfiles Vulkan conservados y restauración de ambos solicitada. [Evidencia/diagnóstico pendiente](docs/REAL_TEXT_MODEL_BATCH_20261009.md). Global89,9%, mejora y regresión compensadas; audio real al final.

# Corrección hasta segundo candidato QA — 2026-10-09

Playwright completó nuevo plan/revisión vigente, aprobación y autorización explícitas, job simulado, segundo artefacto, descarga y recarga; original conservado. Corregidos mensajes residuales de sample obligatorio; build aprobado. [Evidencia y límites](docs/SECOND_CANDIDATE_QA_20261009.md). Tramo ligero de corrección/entrega comprobado; ejecución/escucha real pendiente, D/V89,9%.

# Corrección/entrega comprobadas con Playwright — 2026-10-09

UI/backend QA verificaron opinión, propuesta cover, incorporación sin guardar, guardado explícito, nueva confirmación y bloqueo de propuesta anterior. Descarga del candidato sintético: HTTP200, WAV RIFF192044bytes, sin fallo. [Evidencia y límites](docs/CORRECTION_DELIVERY_PLAYWRIGHT_20261009.md). No nuevo plan/job ni modelos/audio reales; D/V89,9%, verificación de S06-06/S10-07 sigue parcial.

# Corrección vinculada a la revisión vigente — 2026-10-09

La UI rechaza aplicar una propuesta de corrección si cambió la revisión de la ficha. Aplicar conserva MusicSpec y solo prepara un borrador. 3 pruebas frontend y 22 backend aprobadas; build Vite aprobado. [Evidencia y límites](docs/CORRECTION_REVISION_GUARD_20261009.md). E2E completo de corrección/entrega pendiente; D/V89,9%, sin modelos/audio reales.

# S06-01: contraste exploratorio y estados de generación — 2026-10-09

Playwright revisó textos de siete pasos y seis estados simulados de generación. Etiqueta aclarada a Cancelar generación; build y prueba focalizada aprobados. [Cobertura y límites](docs/BUILDER_ACCESSIBILITY_BATCH_20261009.md). No auditoría WCAG integral ni modelos/audio reales; D/V89,9%. Próximo lote UI/backend: corrección y entrega simuladas.

# Lote UI/backend: sample opcional y navegación — 2026-10-09

Corregido bloqueo residual por sample en controles MASTERING/EXPORT y mensajes que exigían sample/MIDI. Se conserva confirmación de ficha y validación backend. 59 pruebas frontend, 20 backend y build aprobados; Playwright verificó siete pasos, 21 combinaciones de anchura, guardado/recarga Studio y ayuda por teclado. [Evidencia y límites](docs/BUILDER_BATCH_QA_20261009.md). D/V89,9%; sin inferencia/audio nuevo.

# Verificación por costo y criticidad — 2026-10-09

Política transversal aprobada: componentes ligeros por criticidad y recorrido UI/backend end to end primero; Gemma/Qwen reales después; ACE-Step/audio real en el último bloque de verificación, independientemente del sprint. Agrupar pendientes, reutilizar evidencia vigente y repetir por impacto; aceptación posterior a D/V100%. [Cobertura, gates y selección de lotes](docs/VERIFICATION_STRATEGY.md). AGENTS, plan y ledger alineados; D/V permanece 89,9%, sin nuevas pruebas de modelos ni audio por este cambio documental.

# Revision de desarrollo; audio al final — 2026-10-09

Se revisaron fuentes/contratos/rutas de arquitectura, inputs, SQLite, Builder, correccion/entrega y lifecycle; auditoria estatica de167modulos/119rutas, sin motor ni certificacion funcional total. Corregida apertura automatica que podia elegir MIDI: usa orden Builder y conserva navegacion guardada. 59 pruebas frontend y build aprobados. S10-07 desarrollo0,5→1, verificacion sigue parcial por recorrido real; audio reservado al ultimo lote segun usuario. Gemma/Qwen restaurados Vulkan, healthHTTP200; no se inicio ensayo ni se genero audio. [Revision y pendientes](docs/DEVELOPMENT_REVIEW_AUDIO_LAST_20261009.md).

# S06: traza del wrapper vinculada al candidato — 2026-10-09

Se conserva runtime_input_trace en evidencia persistida y se coteja con revision/hash/payload/checksums del plan. Nuevas generaciones requieren traza coincidente para registrar candidato; historicos no se reescriben y ausencia no se presenta como verificacion. 22 pruebas backend aprobadas. [Evidencia y limites](docs/S06_WRAPPER_INPUT_OBSERVATION_20261009.md). S06-05 permanece parcial por observacion nativa real y direccion; D/V89,4%, sin nueva generacion de audio.

# S00-03: matriz de entradas conectadas verificada — 2026-10-09

Chat QA/parser determinista: propuesta no cambia DB, aplicar solo cambia formulario, guardar/confirmar lleva BPM97 al request con traza. Nueve campos UI conservados en caption. Extremos numericos:20 combinaciones compatibles modelo/modo/API,40 escenarios;39 pruebas backend del lote aprobadas. [Matriz consolidada de21inputs y limites](docs/S00_CONNECTED_INPUT_MATRIX_20261009.md). S00-03 V0,5→1 por contrato UI/persistencia/compilacion/wrapper; no acredita modelos reales/audio/usabilidad. D/V88,9→89,4%. Ejecucion real sigue en entregables especificos.

# S00: editor de letra y origen del texto — 2026-10-09

Playwright QA verifico texto Unicode/proteccion de linea/guardado/recarga, rechazo de cambio protegido y edicion de linea libre. Navegacion a Revisar y confirmacion por boton conservan markdown hasta preview; letra distinta rechazada400. Corregida etiqueta lyrics_source para documento MusicSpec confirmado, manteniendo aprobacion de letra en plan independiente. 33 pruebas backend aprobadas. [Evidencia](docs/S00_LYRICS_EDITOR_PLAYWRIGHT_20261009.md). S00-03 parcial por chat/condiciones restantes; D/V88,9%, sin nueva generacion.

# S00: selector LM y letra protegida hasta wrapper — 2026-10-09

Playwright confirma que cambiar selector LM envia y conserva modelo/procedencia USER en preview. LM0.6B elegido solo en QA para comprobar control, sin cargarlo ni recomendarlo. Nueva prueba integrada de letra Unicode/protegida recorre fase, SQLite/reapertura, confirmacion real y archivos/contexto del wrapper; rechaza cambio protegido y letra distinta. 28 pruebas backend aprobadas. [Evidencia](docs/S00_LM_LYRICS_VERIFICATION_20261009.md). S00-03 sigue parcial por editor visible/chat/matriz de condiciones; D/V88,9%.

# S00: fuentes, intervalos y pistas comprobados — 2026-10-09

Playwright QA verifico importacion autorizada sin autoseleccion, fuente/referencia y checksum, Repaint0.5–1.5, pistas e instrucciones de Lego/Extract/Complete. Cover0.75 guardado/confirmado se verifico compilando su snapshot historico, sin reclamar vigencia. Guardado con revision antigua rechazado. Sin inferencia, WAV sintetico. [Evidencia y limites](docs/S00_SOURCE_CONTROLS_PLAYWRIGHT_20261009.md). S00-03 permanece parcial por LM/letra/chat/condiciones, avance D/V88,9%.

# S00: opciones de ejecucion comprobadas en navegador — 2026-10-09

Playwright QA verifico ruta LM, semilla24680, pasos32, guidance5 y shift1.5 mediante controles visibles, guardado y confirmacion; preview conserva valores/procedencia. Cover con ruta LM bloquea guardado con explicacion sin reescribir decisiones. LM1.7B mostrado sin cambio sigue default SYSTEM, no se acredita edicion de ese selector. Sin inferencia ni nueva cancion. [Evidencia](docs/S00_EXECUTION_CONTROLS_PLAYWRIGHT_20261009.md). S00-03 permanece parcial, D/V88,9%; fuentes/intervalos/letra/chat aun pendientes.

# S00: controles musicales verificados en navegador — 2026-10-09

Playwright QA verifico diez campos mediante controles visibles, PATCH, confirmacion y recarga; preview API conserva BPM97/D Major/123s y traza Spanish→es/6-8→6, ademas de caption y requisitos retenidos. Seleccion inicial Vue preparada; letra argumento de preview, sin inferencia. Corregido pendiente representative_real_sample residual del compilador: sample opcional. 18 pruebas backend aprobadas. [Evidencia y limites](docs/S00_USER_CONTROLS_PLAYWRIGHT_20261009.md). S00-03 sigue parcial por matriz completa; avance D/V 88,9%.

# S00: decisiones USER guardadas y confirmadas en SQLite — 2026-10-09

Corregida procedencia de controles guardados explicitamente con valor igual al anterior: ahora registra explicit_user_control, conserva locked y declara previous_source cuando corresponde. La eleccion explicita de una sugerencia cuenta como decision del usuario; sigue pendiente de confirmacion. Nueva prueba integrada sin mocks de persistencia: router autorizado, SQLite/reapertura, confirmacion real, compilacion y contexto/argv del wrapper. Cubiertos 20 controles musicales/creativos y de ejecucion, aliases idioma/compas, aislamiento de proyectos y revision antigua rechazada. Lyrics de prueba sigue argumento de preview, no acredita editor/locks de letra. 27 pruebas backend aprobadas. Mensaje de set alineado con ACE-Step, sin exigir MIDI/mastering ni sample. S00-03 verificacion permanece parcial por UI/chat/referencias y condiciones pendientes; D/V 88,9%.

# S10: resumen de entrega y descarga comprobados en navegador — 2026-10-09

Studio reconoce candidatos disponibles y en generacion; la accion lleva a escucha/descarga de esa version. Sin candidato ni sample, lleva a revisar definicion y requisitos. Playwright QA comprobo descarga adjunta, checksum/proyecto invalidos rechazados, foco y ausencia de overflow a 390/768/1440 px. WAV sintetico y seleccion Vue preparada; no acredita recorrido completo ni nueva generacion. 57 pruebas frontend y build aprobados. S10-07 sigue parcial; D/V 88,9%. [Evidencia y limites](docs/S10_STUDIO_DOWNLOAD_QA_20261009.md).

# S10: descarga de la versión ACE-Step escuchada — 2026-10-09

Studio ofrece descargar el WAV del candidato seleccionado mediante la misma ruta y checksum de reproducción. El backend valida pertenencia, estado completado e integridad antes de servirlo como adjunto con nombre por artefacto. No exige sample ni aceptación para conservar una versión; descargar no aprueba audio ni actualiza una versión histórica. 56 pruebas frontend, 31 backend del bloque y build aprobados. Revisión HTTP/browser del adjunto y recorrido integrado de corrección pendientes para el próximo lote. S10-07 permanece parcial; avance D/V 88,9%.

# S00: inventario local de checkpoints compartido — 2026-10-09

Inspección ligera compartida por auditoría, steering Gemma/Qwen y catálogo de archivos del preflight. Registra configuración, SHA256 de config, tamaño/presencia de pesos y dependencias por ruta sin leer pesos ni importar motores. Observados Base, Turbo y LM 1.7B completos; LM 0.6B incompleto. No acredita carga, integridad de pesos ni audio. S00-04 desarrollo 0,5→1; verificación permanece parcial por ejecuciones efectivas pendientes. 17 pruebas del bloque aprobadas. Evidencia: [observación](docs/S00_CHECKPOINT_OBSERVATION_20261009.json).

# Medición de avance D/V — 2026-10-09

Por decisión del usuario, el avance global considera únicamente desarrollo y verificación. Se conserva la proporción anterior 50:30, normalizada a 62,5% y 37,5%. La aceptación queda fuera del porcentaje y se revisará después de completar ambas dimensiones al 100%; las decisiones ya registradas se conservan. El cambio de fórmula no representa desarrollo adicional. Reporte vigente: [SPRINT_PROGRESS.md](docs/SPRINT_PROGRESS.md). Los porcentajes anteriores son históricos bajo su fórmula original.

# Song AI

Revisión visual del recorrido Generar y exportar (2026-10-17): [pasos y evidencia Playwright](docs/GENERATE_VISUAL_JOURNEY_20261017.md). El plan se prepara y aprueba con acciones consecutivas; al aprobarlo, el botón de canción completa aparece al inicio del panel. La carga del proyecto conserva una navegación posterior del usuario. Studio ofrece ahora «Preparar archivos para descargar»: se comprobó `POST /export` real en una copia QA con audio preexistente, cinco descargas HTTP 200, ZIP descargado e integridad de archivos. La solicitud `/master` del primer ensayo fue interceptada; no se repitió ACE-Step ni se evaluó la escucha.

Actualización de interfaz (2026-10-17): en el paso «Generar», la revisión de la ficha y la aprobación del plan ACE-Step se muestran como decisiones distintas. El plan inicial se prepara desde «Preparar el plan de esta canción»; tras revisar la letra y aprobar el plan vigente, «Generar canción completa» aparece en el mismo panel y se habilita si la configuración y los recursos cumplen las verificaciones. El botón de siguiente paso lleva a esa acción visible; el diagnóstico de recursos abre su panel. El borrador exploratorio y el sample siguen siendo opcionales. Verificación P: 64/64 pruebas Node, build Vite de 41 módulos y `git diff --check` correctos. No se ejecutó ACE-Step ni se evaluó la canción de Alma en esta corrección; la escucha y la aceptación del usuario siguen separadas.

Song AI es un estudio musical local asistido por IA para crear canciones completas desde una idea creativa hasta exportables finales. La aplicacion corre localmente sin Docker, guarda el trabajo en SQLite dentro de `data/` y mantiene separados los artefactos de letra, plan musical, MIDI, audio y exportacion.

El objetivo actual es generar canciones locales con herramientas gratuitas. El modo pro/pago esta pausado.

La [guía de documentación](docs/README.md) indica qué especificación usar para cada cambio y separa planes vigentes de reportes históricos.

## Estado Actual

### Sample real opcional y avance D/V — 2026-10-15

En QA se copió un candidato ACE-Step real como sample pendiente. La reapertura SQLite confirmó set/plan/revisión/checksum y coincidencia de configuración/ejecución; no se registró escucha ni aprobación. S01-03 pasa de verificación 0,5 a 1 **solo para correspondencia técnica**; la representatividad audible sigue en aceptación. [Evidencia](docs/REAL_SAMPLE_CORRESPONDENCE_20261015.md). El avance D/V calculado sube **97,3%→97,9%**, con desarrollo 100% y cinco verificaciones técnicas parciales: S00-04, S01-04, S06-05, S06-06 y S10-07. El sample sigue siendo opcional.

### Nivel L ejecutado y preflight ACE-Step limitado por memoria — 2026-10-15

Con 8132 MB de RAM disponibles se iniciaron los dos LLM locales gestionados. Gemma (18,75 s) y Qwen (50,42 s) respondieron mediante registry y steering desde MusicSpec QA de Alma leída en modo solo lectura; Qwen propuso campos, sin guardar ni aprobar decisiones. Después de la carga conjunta quedaron ~301 MB libres. El cierre normal encontró CIM denegado en este entorno; se verificaron y cerraron solo los dos PID iniciados aquí. `stop-local-llms.ps1` incorpora ahora un fallback por PID, ejecutable y hora comprobados; sin PID exige puertos de modelos cerrados. Seis escenarios PowerShell aprobaron cierre normal, fallback y rechazos de PID/rutas/puertos ajenos o antiguos.

El preflight real de Turbo `high_level_lm` con LM1.7B calcula 9561 MB de pesos y 2048 MB de reserva: **11609 MB requeridos frente a 10540 MB disponibles**. El estimador ya incluía el LM; no se cambió. La carga se detuvo antes de inferencia. Resultados y límites en [SPRINT_VERIFICATION_BATCH_20261015.md](docs/SPRINT_VERIFICATION_BATCH_20261015.md). Este preflight no cambia el porcentaje; el cierre técnico posterior de S01-03 se registra arriba.

### Avance D/V reclasificado — 2026-10-15

El [reporte calculado](docs/SPRINT_PROGRESS.md) registró en este corte desarrollo 100% y avance conjunto desarrollo/verificación 97,3% para los 39 entregables del alcance activo. La escucha musical de Cover, Repaint, Lego, Extract y Complete y el piloto amateur se reservaron para aceptación final, como indicó el usuario; los archivos y la preparación técnica no se presentan como aceptación. S04-04 y S06-04 pasaron a verificación completa por reproducción A/B real y ejecución técnica real de los seis modos, respectivamente. S10-02 a S10-06 se delimitaron a ejecución/integridad técnica y S10-08 a preparación técnica del piloto. Este cambio de clasificación explica el aumento desde 93,8%; no representa nueva generación de audio.

La verificación técnica aún no llega a 100%: S00-04 (LM opcional efectivo), S06-05 (parámetros efectivos del motor), S06-06 (corrección integrada con audio real) y S10-07 (idea a entrega real con corrección). S01-03 y S01-04 ya cerraron su parte técnica; la escucha del sample y del final pertenece a aceptación. La aceptación del usuario sigue fuera del porcentaje y se evalúa al terminar D/V. La continuación por niveles y sus resultados exactos están en [SPRINT_VERIFICATION_BATCH_20261015.md](docs/SPRINT_VERIFICATION_BATCH_20261015.md).

### Verificación P completada y modelos sujetos a recursos — 2026-10-15

Las pruebas se agrupan en P (Python/interfaz sin modelos), L (Gemma/Qwen reales) y A (ACE-Step real), en ese orden según [VERIFICATION_STRATEGY.md](docs/VERIFICATION_STRATEGY.md). P pasó: 370 pruebas Python, 365 aprobadas y 5 omitidas; 63/63 frontend; build Vite con `--configLoader runner`; `compileall`; contrato instalado ACE-Step compatible sin cargar pesos. Esto resuelve el resultado incompleto de la continuación anterior. La evidencia real previa de Gemma/Qwen y los seis modos se conserva sin atribuirle una nueva corrida.

En la primera medición, tras P, había 1147 MB de RAM disponibles frente al mínimo configurado de 3500 MB para audio; L y A quedaron pendientes. La memoria se liberó después y permitió el nivel L descrito arriba, pero el presupuesto de la ruta LM de ACE-Step siguió sin alcanzarse. El avance posterior de S01-03 se registra al inicio de esta sección.

### Continuación de verificación — 2026-10-15

La primera ejecución de la suite Python completa tuvo 370 casos: 360 aprobados, 5 omitidos y 5 fallidos. Los fallos se aislaron a dos fixtures antiguas: la evidencia simulada de audio fuente no incluía `artifact_id`, ahora obligatorio para vincular la traza al artefacto seleccionado, y las pruebas de preparación de recursos dependían de que `psutil` estuviera instalado en el host. Se corrigieron las fixtures sin relajar las comprobaciones de producción. La repetición focalizada de esos módulos pasó: 7/7; la repetición completa posterior aprobó 365/365 con 5 omitidas, detallada arriba.

Frontend: 63/63 pruebas Node aprobadas. `npm run build` tropezó con un error de acceso del cargador de configuración de Vite en este entorno; `npx vite build --configLoader runner` compiló 40 módulos correctamente. Estas comprobaciones no acreditan escucha, fidelidad de los seis modos ni piloto amateur. Los cinco WAV QA existentes y las preguntas concretas de escucha se reúnen en [PENDING_AUDIO_LISTENING_20261015.md](docs/PENDING_AUDIO_LISTENING_20261015.md).

### S00: request completo cotejado antes de cargar ACE-Step — 2026-10-09

El contexto de ejecución incluye todos los inputs aprobados, revisión/hash de plan y checksums de fuentes verificadas. El wrapper compara sus 21 campos conectados, caption/letra y archivos contra ese contexto antes de cargar pesos o eliminar un output anterior. Registra `runtime_input_trace` aparte de opciones y evidencia del motor; no acredita obediencia musical. Contextos anteriores siguen identificados como parciales.

41 pruebas backend aprobadas: igualdad de los 21 campos, cambio no autorizado por campo, sustitución de audio, contexto inválido y prueba del CLI real que rechaza BPM alterado conservando un output previo. Trece combinaciones compatibles del contrato de aceptación mantienen payload completo en el contexto. Sin generación de música ni nueva prueba con modelos/UI. S00-03 desarrollo 0.5→1; cobertura integral de controles UI y aceptación continúan pendientes. [Detalle](docs/S00_FULL_INPUT_RUNTIME_CONTRACT_20261009.md).

### S04: reintentos seguros y limpieza; S10: piloto preparado — 2026-10-09

Generación acepta identidad de solicitud persistida: reintentar los mismos parámetros recupera el mismo job sin nueva generación, incluso al reabrir SQLite; identidades conflictivas se rechazan. La UI conserva identidad durante reintentos en la sesión y crea otra al cambiar canción/plan. El runner termina procesos todavía activos antes de restaurar modelos, también cuando falla el monitor.

38 pruebas backend, 55 frontend y build Vite aprobados; escenarios de cancelación/fallo usan hijos Python reales sin pesos ACE-Step ni GPU. S04 conserva pendiente la cancelación del motor cargado; la cobertura adicional no suma avance duplicado. S10-08 entrega [protocolo del piloto amateur](docs/AMATEUR_PILOT_PROTOCOL.md), desarrollo 0→0.5, sin participantes ni aceptación acreditados. [Detalle del bloque](docs/S04_RETRY_PROCESS_CLEANUP_20261009.md).

### S03: contexto único del asistente y verificación de herramientas — 2026-10-09

Gemma recibe el catálogo compacto de acciones ligado a canción/revisión, también en los handoffs internos. Se rechazan ficha/set de canciones distintas antes de consultar modelos; consultar solo una canción deriva su set y no selecciona otro por defecto. Los prompts de Gemma, roles Gemma/Qwen y la sección ACE-Step realmente inyectada se alinean con sample opcional; contratos de rol conservan el presupuesto existente.

51 pruebas backend aprobadas. Playwright con SQLite QA y propuesta fixture: rechazo desde botón HTTP 200, ficha intacta, rechazo persistente tras recarga y catálogo de doce operaciones. Servidor QA y navegador cerrados; no se modificaron Isabella/Alma ni se ejecutaron modelos/audio. S03-03 verificación 0.5→1 para el contrato de registry/router; aceptación sigue pendiente y ensayos de inferencia pertenecen a S00/S05. [Evidencia y límites](docs/S03_ASSISTANT_ALIGNMENT_QA_20261009.md).

### S03: registro de herramientas y rechazo de propuestas — 2026-10-09

`MusicToolRegistry`/`MusicActionRouter` conectan doce herramientas de ficha, plan y jobs a los casos de uso existentes, con contratos de parámetros, proyecto explícito, revisión vigente, autorización y trazas SQLite. `/api/music-tools` expone catálogo y `/api/pro/projects/{song_id}/music-actions` despacha acciones autorizadas. Guardar, confirmar y restaurar desde los endpoints de la UI usan el mismo router y conservan su respuesta. El catálogo se incluye en la compilación técnica de Qwen, sin habilitar ejecución automática del modelo.

La UI puede rechazar una propuesta técnica: se registra el rechazo, no cambia MusicSpec y no reaparece tras recargar. Se preservan task, resultado y eventos originales. Lote de 47 pruebas backend aprobado, 54 frontend y build Vite aprobados; smoke HTTP con SQLite temporal verifica guardado/revisión obsoleta/autorización. Sin nueva inferencia ni generación de audio. S03-03 desarrollo pasa 0.5→1; verificación integral y aceptación permanecen pendientes. [Inventario y límites](docs/S03_MUSIC_TOOL_INVENTORY_20261009.md).

### Isabella aceptada y cierre S10-01 — 2026-10-09

El usuario acepta expresamente la canción generada y deja el ajuste de naturalidad vocal alrededor de 20 s para después. Aceptación vigente guardada en SQLite (`event_428c59b47301`), conservando el feedback anterior. S10-01 pasa V=0.5/A=0 a V=1/A=1 para este caso text2music real; no se cierran otros modos, exportación integrada ni piloto amateur. Balance regenerado en [SPRINT_PROGRESS](docs/SPRINT_PROGRESS.md). La aceptación del usuario se registra separada de verificaciones objetivas exhaustivas de calidad.

### S01: sample opcional y preparación de proyectos antiguos — 2026-10-09

Producción, mastering y descargas finales validan el set y la ficha confirmada mediante `FinalProductionGate`, sin exigir sample. La aprobación/evidencia del sample continúa separada. Se corrigieron mensajes de UI/asistencia y se eliminó el anuncio de calidad aprobada basado solo en la procedencia del provider. Preparar un proyecto desde secciones antiguas sin ID conserva el texto, asigna IDs sin colisiones y registra la transformación en MusicSpec; no aprueba la ficha ni ejecuta Qwen automáticamente.

Verificación agrupada: 90 casos backend, 85 aprobados y 5 omitidos; regresión final de 27 casos aprobada, incluida migración de IDs; 52 pruebas frontend y build Vite aprobados. No es la suite completa ni aceptación de audio/usabilidad. [Detalle del bloque](docs/S01_OPTIONAL_SAMPLE_ALIGNMENT_20261009.md). Balance actualizado en [avance de sprints](docs/SPRINT_PROGRESS.md).

### Isabella: generación real terminada, pendiente de escucha — 2026-10-09

Letra existente incorporada a MusicSpec sin cambio de texto o campos creativos; ficha y plan confirmados conforme a la solicitud de generar Isabella. Presupuesto RAM disponible, PyTorch XPU detecta iGPU Intel. Primer intento detenido por permisos CIM del entorno; API reiniciada con permisos aprobados. Job `ace_job_5bb476f652cc4f5a9835c918bceb9b54` completado: WAV de 120 s, 48 kHz/16 bits estéreo, checksum y frames verificados; Turbo/XPU, 328,1 s. Presión de memoria registrada. Candidato pendiente de escucha/aceptación, sin export final aceptada. [Evidencia y estado de la corrida](docs/ISABELLA_GENERATION_20261009.md). No se modifica el porcentaje de sprints por iniciar un job.


### S03-04: extracción completada y verificada — 2026-10-08

Siete comandos pequeños con contexto persistido y composición local sustituyen las últimas delegaciones. SongService no reconstruye la ficha automáticamente ni simula carga Qwen; ProfessionalSongService queda diferido y conserva compatibilidad usando los mismos comandos. Cero delegaciones directas al monolito y cero inicialización histórica al arrancar. Master usa letra activa; no se añade MIDI como requisito de ACE-Step ni se modifica la política de sample. 33 pruebas backend agrupadas aprobadas, compileall/diff correctos; smoke ASGI temporal de UI/catálogo/proyectos devuelve 200. Providers de prueba, sin inferencia/audio real ni suite completa. [Evidencia y límites](docs/S03_LOCAL_SERVICE_EXTRACTION_STATUS.md). S03-04: D/V completos, aceptación pendiente; **avance global 66,9%** (antes 65,7%).


### S03-04: consultas, regeneración y exportación locales — 2026-10-08

LocalProductionArtifactQueries comparte siete lecturas sin instanciar generación; servicios previos reutilizan el lector. ArtifactRegeneration despacha handlers actuales, preservando propuesta/revisión explícitas de letra. ExportLocalProject mantiene ficha confirmada, SampleGate, archivos de master y verificaciones locales sin reconstrucción histórica; guard de ficha compartido. 16 pruebas backend agrupadas aprobadas, compileall correcto; fixtures/dobles no acreditan audio real. Delegaciones directas a ProfessionalSongService: **16 → 7**, quedan comandos históricos de generación y su inicialización. Inventario en docs/S03_LOCAL_SERVICE_EXTRACTION_STATUS.md. Global 65,7%; S03-04 sigue parcial hasta extraer los siete restantes.


### S03-04: recopilación de intención local sin guardar sugerencias — 2026-10-08

CollectLocalIntent sustituye la recopilación histórica por tarea assistant/Gemma con contexto/revisión persistidos. Sin autoeditar ficha, aprobación Qwen simulada ni modelos encadenados. Errores/mock no se anuncian como éxito; UI conserva revisión, bloquea cambios pendientes y respuestas de otro proyecto. Catálogo de fases usa consulta local. 15 pruebas backend, 2 Node y 1 compatibilidad histórica aprobadas; build/compileall correctos, providers simulados. [Inventario y pendientes](docs/S03_LOCAL_SERVICE_EXTRACTION_STATUS.md): quedan 16 delegaciones históricas de plan/MIDI/audio/export/regeneración y su inicialización; servicio conservado. D/V de S03-04 permanece parcial, global 65,7%.


### S03-04: propuesta de letra verificada en interfaz — 2026-10-08

Playwright MCP verificó propuesta sin persistencia, incorporación como borrador, guardado explícito con traza SQLite, recarga, descarte, protección y respuesta tardía; Production dirige a revisión en Letra. Generación simulada identificada, backend/SQLite reales solo en QA. Backend amplía protección a líneas/dirección, rechaza formato vacío, explicación inicial y texto que supera el límite conectado de 4096 caracteres; mensajes de fallo distinguen propuesta de compilación. Evidencia y límites en [QA_FULL_LYRICS_PROPOSAL_2026-10-08.md](docs/QA_FULL_LYRICS_PROPOSAL_2026-10-08.md). 21 pruebas backend agrupadas aprobadas, build Vite y compileall correctos; inferencia real y consumidores históricos pendientes, global 65,7%.


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

### Desbordamiento móvil A/B corregido — 2026-10-08

La columna grid automática de specification-groups crecía a 506 px por ancho intrínseco de tabla. Corregida con minmax(0,1fr) y sección hija min-width:0; tabla conserva 480 px de contenido dentro de scroll local. Build final aprobado. Playwright del mismo fixture con CSS final comprobó 390/768/1440 sin overflow de página: a 390 tabla visible 261 px, contenido 480 px, foco accesible. Harness espera reloj UI (fin del mounted) antes de inyectar y desactiva refresco solo en prueba. No audio real ni persistencia. S06-01 conserva estado parcial y global 63,7%: defecto responsive cerrado, faltan pantallas completas/accesibilidad integral.

### Batch request/A-B/escucha resuelto — 2026-10-08

Timeout anterior era carrera del fixture con refresco de Production cada 10 s; harness desactiva refresco sin cambiar comportamiento de aplicación. Playwright QA comprobó request caption/intervalo cero, tabla con foco, opinión histórica y bindings declaración/decisión/notas, sin guardar. Detectado overflow móvil al abrir A/B; ajustados mínimos intrínsecos de contenedores Production y build aprobado, pero el reensayo sigue mostrando 572 px de página en viewport 390 px: corrección responsive pendiente. Sin escucha/audio real: archivo ficticio solo monta controles. S06-01 sigue parcial y global 63,7%; batch de estos componentes ya verificado, sin auditoría integral de accesibilidad.

### S06-01 revisión de request y comparación A/B — 2026-10-08

PlanRequestReview presenta operación, parámetros presentes/unidades, caption y letra exacta sin JSON obligatorio; cero de intervalo preservado, datos omitidos no inventados. CandidateComparisonView reutilizable conserva informes/objetivos/observaciones y advierte diferencias de plan/revisión, sin ganador automático. Tabla desplazable con caption/filas semánticas y foco por teclado. 39 pruebas frontend/build aprobados. Batch Playwright interrumpido: el fixture no hizo visible el selector A/B antes del timeout; quedan pendientes request/A-B/opinión histórica y controles de escucha en navegador. No se acredita móvil ni escucha real en este batch. Global 63,7%, S06-01 todavía parcial: faltan pantallas Builder/Studio completas y revisión integral de accesibilidad.

### S06-01 controles de escucha y opinión vigente — 2026-10-08

ListeningDecision y ListeningReviewSummary reutilizables: declaración de escucha, aceptación/cambios y notas; guardas/endpoint por candidato/checksum existentes conservados. Opinión se clasifica vigente solo con audio_current e inputs_current positivos; pérdida de audio, otra revisión y datos desconocidos se explican con acción concreta. Resumen fuera del formulario condicionado al reproductor para conservar explicación cuando falta audio. Opinión aceptada no aprueba sample ni final. 38 pruebas frontend/build aprobados; Playwright de estos componentes pendiente de siguiente batch. Global 63,7%, S06-01 D/V parciales: componentes entregados registrados, pantallas y accesibilidad del conjunto pendientes.

### S06-01 estado de generación reutilizable — 2026-10-08

GenerationStatus muestra espera/ejecución/cancelación solicitada/cancelado/fallo/completado/desconocido, porcentaje reportado válido (incluido cero), ausencia de dato explícita, actualización y cancelación por estados admitidos. Está fuera de la rama del plan confirmado, para consultar historial aunque falte plan vigente; reproductores/evaluación conservan su ubicación. Completed se identifica como candidato, no aceptación. Guardia de preparación creativa aplicada también al método de inicio frontend. 37 pruebas/build y batch Playwright QA con fixtures de estados/preflight/390 px, sin overflow observado. No prueba cancelación real ni recuperación de proceso. S06-01 sigue parcial por componentes/pantallas/accesibilidad pendientes; global 63,7%.

### S06-01 revisión previa a generar separada — 2026-10-08

GenerationPreflight reutilizable muestra preparación creativa (ficha/plan vigentes, sin borrador) separada de disponibilidad técnica. Diagnóstico de recursos positivo no acredita carga/inferencia; bloqueo negativo se explica con recomendaciones. UI no inicia candidato con borrador o plan de otra revisión; autorización explícita y comprobaciones finales backend conservadas. 36 pruebas frontend/build aprobados. Playwright se acumula con estados de generación del siguiente bloque. Sin inferencia/audio ni cambio de política de sample. S06-01 permanece parcial por pantallas/componentes y accesibilidad restantes; global 63,7%.

### S06-01 tarjetas de decisión reutilizables — 2026-10-08

DecisionCard extraída de la ficha agrupada con ayuda significado/efecto/ejemplo, procedencia, aplicabilidad y delegación explícita; conserva guardas de borrador/editor ocupado. Corregido booleano false mostrado como vacío: ahora No; cero permanece 0 y objetos se muestran legibles sin cambiar datos. Contador familiar indica «con valor», no confirmación. 34 pruebas frontend/build y Playwright QA de tarjetas, ayuda y fixtures false/0 en móvil; sin persistencia de fixtures. Global 63,7%, S06-01 todavía parcial: faltan otras pantallas/componentes y accesibilidad completa. No nuevo sprint ni cambio de alcance.

### S06-01 resumen reutilizable del Builder — 2026-10-08

Componente BuilderProjectSummary separado de app y función pura de estado: idea, tres assets vinculados al set, ficha confirmada y plan de revisión vigente. Muestra pendiente y acción principal guardar/revisar; navegación de pasos permanece secundaria. Selección no acredita calidad, confirmación no acredita audio y plan obsoleto no aparece aprobado. Estados derivados de proyecto SQLite; borrador se identifica sin alterar resumen guardado. 33 pruebas frontend/build; Playwright QA de resumen, acción de guardado al editar, descarte y viewport 390 px. Sin inferencia/audio. S06-01 continúa D/V parciales: quedan componentes/pantallas/accesibilidad completos. Global 63,7% sin cambio de estado; este bloque es una parte del entregable.

### S05-03/S05-04 verificación entregada — 2026-10-08

Playwright QA del comentario técnico con resultado previo Qwen real inyectado en API: resumen visible, distinción real/respaldo y sin aplicación automática. Gemma real falló inicialmente una línea protegida; backend rechazó propuesta sin cambiar MusicSpec. Corregido prompt con lista literal/posición de líneas al final. Reintento `llama_cpp` 61,91 s conserva texto completo sin cambios, incluida la línea protegida; QA restaurado. No acredita mejora creativa ni obediencia universal. Modelos iniciados para ensayo cerrados. Tres pruebas de contexto aprobadas. Verificación S05-03/S05-04 0,5→1, aceptación 0; global **62,8→63,7%**, S05 **68,8→76,2%**. Siguiente: S06-01 componentes/pantallas, con gates musicales aún pendientes.

### Seguimiento corregido por entregables — 2026-10-08

**Avance calculado: 62,8%**, desde 39 entregables identificados en los ocho sprints activos. Sustituye el 75% estimado; no representa pérdida de trabajo. [Reporte vigente](docs/SPRINT_PROGRESS.md) separa desarrollo/verificación/aceptación, evidencia y pendiente por ID. [Ledger](docs/sprint_progress.json) revisable con estados 0/0,5/1; cálculo reproducible: `.venv/Scripts/python.exe scripts/sprint_progress.py`. Pesos: desarrollo 50%, verificación 30%, aceptación 20%; entregables iguales dentro del sprint y sprints iguales en global. No son pesos de esfuerzo ni medición de calidad. Porcentajes en entradas anteriores son históricos y quedan sustituidos por este reporte. Ningún sprint se declara cerrado; aceptación final aún pendiente. Esta continuación cambia el seguimiento, no suma desarrollo de producto.

### Qwen real revisa la propuesta de Gemma — 2026-10-08

Ensayo por ModelOrchestrator/SQLite QA con propuesta Gemma guardada como evidencia, no como ficha activa. Qwen3 4B/Vulkan Intel (37/37 capas GPU) respondió `provider_handoff`, `provider_executed=true`, en 98,64 s; task `task_e3590c8626bd`, steering/hash y resultado persistidos. Contexto 6.708 tokens dentro de 8.192. Identifica pérdida de adjetivos y posible efecto estructural del acortamiento; opinión de cantabilidad no acreditada por audio. MusicSpec permanece intacta. Evidencia `.playwright-mcp/section_qwen_probe_result.json`. No prueba una sesión simultánea Gemma/Qwen ni aceptación creativa, y no acredita obediencia a locks en inferencia. S05 75%, S06 70%, global 75% mantenidos: gate real de revisión textual comprobado para un caso; cobertura restante y piloto siguen abiertos.

### Revisión técnica de propuestas por sección conectada — 2026-10-08

Corregida brecha del handoff: Qwen recibía solo conteos de palabras. La task persistida ahora conserva original/propuesta/revisión y contexto compacto del proyecto, con petición de revisar intención, nombre, idioma, dirección y protecciones sin reescribir ni aprobar por el usuario. Resultado se muestra en propuesta con distinción provider ejecutado/respaldo; revisión no acredita audio. Se revalida revisión después del handoff para rechazar resultados obsoletos. 15 pruebas de fases/build aprobados; prueba integrada inspecciona los textos/revisión/contexto recibidos por el orquestador mock. Qwen real y Playwright del comentario técnico pendientes de batch. S05 75%, S06 70%, global 75% mantenidos: integración corregida, gate real pendiente.

### Ensayo real de asistencia por sección — 2026-10-08

Gemma local mediante Vulkan/Intel produjo propuesta real `llama_cpp` sobre proyecto Alma en SQLite QA, sin autoguardado ni fallback de letra: 63,72 s totales. Conserva nombre/tema de cuna; acorta la sección, cambio sujeto a revisión creativa. Primer intento falló HTTP 400 por 12.501 tokens frente a contexto 8.192; corregida proyección para conservar campos creativos públicos y quitar historial/provenance/diagnósticos duplicados, sin modificar la ficha persistida. Reintento 6.115 tokens/HTTP 200; MusicSpec intacta. Tres pruebas de contexto/proyección aprobadas. Evidencia local `.playwright-mcp/section_real_probe_result.json`; ensayo por servicio, no browser. Qwen real, líneas protegidas en inferencia, demás modos y aceptación usuario no acreditados. S05 75%, S06 70%, global 75% mantenidos: un caso no cierra el gate real completo.

### Contexto completo de assets y recorrido de propuesta — 2026-10-08

Asistencia de sección incluye set, tres assets seleccionados, manifests/intenciones/metadata derivados, ficha activa compacta y referencias de snapshots. Prioridad explícita de SQLite sobre histórico; datos técnicos separados de letra. Prueba integrada con provider/orquestador mock verifica IDs/contexto y ausencia de cambios en MusicSpec. Playwright QA con API simulada verifica revisión/ID/borrador enviado, original intacto al recibir y restauración/limpieza tras descartar navegación. No acredita obediencia real de Gemma/Qwen ni audio. S05 75%, S06 70%, global 75%; siguiente gate: ensayo real del asistente y revisión de fidelidad de propuesta, junto a cobertura restante del recorrido.

### Contexto persistido de propuestas por sección — 2026-10-08

La solicitud lleva ID de sección, borrador y revisión activa. Backend resuelve identidad/intenciones desde el proyecto SQLite, rechaza revisión obsoleta/sección ajena/protección sin desbloqueo guardado y comprueba líneas protegidas del resultado; revisa vigencia antes de devolverlo. Prompt incluye voz, instrumental y dirección separada de letra. Propuestas locales se limpian al capturar baseline o descartar cambios. Build y pruebas dirigidas aprobadas; inferencia real y Playwright de este contexto se acumulan para próximo batch. S05 75%, S06 70%, global 75%; pendiente contexto completo de assets/manifiestos y validación real del asistente.

### Propuestas parciales de letra revisables — 2026-10-08

Mejorar/recrear/expandir/acortar/variantes ya no reemplazan texto directamente: muestran antes/después y fuente (Gemma o guía/fallback), con aplicar al borrador o descartar. Aplicación revalida proyecto, snapshot de sección/protecciones y contexto/revisión; rechaza líneas protegidas alteradas. Aplicar no guarda SQLite ni aprueba audio. Batch 31 pruebas frontend/build; Playwright con respuesta API simulada comprobó texto original intacto al recibir, descarte, aplicación sin modificar baseline y bloqueo tras proteger sección. No acredita inferencia real; datos reales intactos. S05 75%, S06 70%, global 75% se mantienen: falta completar cobertura de propuestas y traducción/validación musical.

### Revisión visible de dirección por sección — 2026-10-08

El plan muestra las notas literales por bloque, protección, limitación de envío y detalle de trazabilidad; usa datos de la revisión del plan, sin sustituirlos por el borrador actual. Planes anteriores sin traza y planes sin notas tienen mensajes distintos. Batch build/Playwright QA: dirección protegida deshabilita inputs y plantillas; desbloqueo requiere guardado; panel con fixture local de plan conserva literal, aviso de no envío y protección; histórico sin traza explicado. Sin overflow observado a 390 px en ese estado. Fixture de panel no acredita compilación ni audio; SQLite QA usada para controles, proyectos reales intactos. S05 75%, S06 70%, global 75% se mantienen; mapping real y aceptación musical pendientes.

### Protección y trazabilidad de dirección — 2026-10-08

La dirección por bloque se puede proteger independientemente del texto. Formularios deshabilitan sus cuatro campos; sustitución/eliminación requiere desbloqueo, y SQLite exige IDs explícitos y registra el acto USER. El compilador incluye `section_direction_trace` con ID/tipo, ruta de origen, valores literales, protección y transformaciones vacías: `retained_not_sent_to_engine`. No introduce notas en caption/letra ni promete interpretación audible. Build correcto y pruebas dirigidas; Playwright de dirección se acumula con el siguiente bloque visual. S05 75%, S06 70%, global 75%; falta traducción validada, UI de trazas y aceptación real.

### Dirección creativa en el editor de letra — 2026-10-08

Verificación del bloque: 13 pruebas de fases aprobadas, build final correcto y diff sin errores. Playwright se agrupa con los siguientes cambios del editor.

Cada bloque ofrece dirección libre, energía, voz e instrumentos, con ejemplos y aviso de ejecución no garantizada por sección. SQLite conserva las notas en `_lyrics_document.sections` de la misma MusicSpec; letra cantada/markdown no incluye las notas. Validación de tipo/límite por campo y revisión nueva al guardar; plantillas reutilizables conservan estas notas. La distribución vocal existente sigue en `section_direction`: estos campos son notas asociadas al bloque de letra, no reemplazan esa configuración ni añaden argumentos del motor. Pendiente revisión visual agrupada, locks de dirección y traducción explícita con límites hacia caption/plan. No afirmar ejecución audible de estas notas.

### Seguimiento de avance — 2026-10-08

La baseline estimada anterior queda sustituida por el [reporte calculado por entregables](docs/SPRINT_PROGRESS.md): 62,8%. Ver metodología y pendientes en ese reporte.

### Protección por línea y sustitución de plantillas — 2026-10-08

Cada sección permite proteger líneas concretas, conservando texto literal y posición; las demás siguen editables. Insertar/eliminar líneas anteriores requiere desbloquear las afectadas. UI rechaza ediciones y respuestas IA que alteren líneas protegidas; SQLite valida índices, rechaza eliminación/desbloqueo implícito y registra IDs de desbloqueo USER en la revisión. Plantillas/borradores requieren guardar esos desbloqueos. Esta metadata de edición no se envía como comandos a ACE-Step: el motor recibe la letra compilada.

Batch aprobado: 30 pruebas frontend, 12 de fases y 2 de protección por línea; build correcto. Playwright QA verificó protección guardada, rechazo de edición y desbloqueo guardado antes de permitir plantillas. La prueba pendiente de plantilla se completó mediante navegación y descarte explícito: carga queda como borrador, sin cambiar baseline, y volver al editor recupera la letra guardada. Sin inferencia/audio ni cambios en proyectos reales. No cierra el sprint ni valida experiencia amateur.

### Protección por sección de letra — 2026-10-08

El editor permite proteger/desbloquear texto y tipo por sección; mantiene accesible reordenar y duplicar. El guardado SQLite rechaza edición/eliminación/desbloqueo implícito de una sección protegida, exige ID de desbloqueo explícito y conserva ese acto en la revisión. UI deshabilita transformaciones IA y eliminación, con texto readonly; respuestas tardías no reemplazan secciones bloqueadas, sustituidas o editadas durante la consulta.

Carga de borradores y plantillas bloqueada mientras haya secciones protegidas o desbloqueos sin guardar, con explicación visible. Las cargas quedan en borrador; una respuesta de carga tardía no sustituye texto editado mientras se esperaba.

Build aprobado; 29 pruebas frontend y 11 pruebas dirigidas de fases aprobadas en batch. Playwright con SQLite QA confirmó protección persistida tras recarga, texto readonly, bloqueo de plantilla y desbloqueo que requiere guardado antes de permitir sustituciones. La comprobación adicional de descarte de plantilla quedó interrumpida por el diálogo beforeunload; no se cuenta como aprobada. Pendientes locks por línea y ampliación del batch de importación. Sin modelos/audio ni edición de datos reales.

### Bloque estructura/letra — 2026-10-08

Timeline de estructura prevista con bloques seleccionables y foco en el texto, sin tiempos de audio ficticios. Reordenación con botones etiquetados y límites deshabilitados; duplicación conserva texto con ID nuevo. Cambios de orden/tipo/añadido/duplicación mantienen la estructura del borrador sincronizada. Eliminar pide confirmación en diálogo nativo con Escape/foco modal y conserva al menos una sección; revisión guardada intacta hasta guardar explícitamente.

Build aprobado. Batch Playwright QA verificó selección/foco, reordenación preservando texto, duplicación, cancelación con Escape, eliminación y descarte al navegar. Sin inferencia ni cambios de letra en DB real. Pendientes locks por línea/sección, direcciones completas por sección y validación con usuarios amateur.

### Bloque visual Builder comprobado — 2026-10-08

Migrados acentos/fondos rgba heredados más repetidos a tokens semánticos y corregida continuidad del paso elegido tras resolver cambios pendientes. Playwright QA comprobó siete pasos, cambio hacia Studio tras descartar, restauración de BPM guardado y layouts 390/768/1440 sin overflow horizontal observado. Verificó colores computados del CTA/fondo contra paleta, contraste del CTA 6,21:1 y reduced motion. La comprobación del foco requiere repetir con navegación real por teclado; el foco programático tras clic no activó focus-visible. Evidencia limitada a estos estados; no auditoría global WCAG ni validación amateur.

Build del bloque aprobado. Siguen pendientes timeline/editor por sección, nuevas pantallas Builder/Studio, extracción de componentes y migración de otros literales históricos. No se generó audio ni se modificó la intención real de Isabella/Alma.

### Bloque visual y recorrido Builder — 2026-10-08

Aplicación incremental del UX autorizada: paleta oscura semántica del Design System y aliases compatibles, botones/campos/ayudas/estados/foco/reduced-motion/forced-colors compartidos. Recorrido visible Idea → Sonido → Composición → Estructura y letra → Revisar → Generar → Studio; reutiliza editores y revisión MusicSpec existentes. Sonido permite revisar voz; navegar no guarda ni confirma ni genera, y mantiene protección de cambios pendientes. Herramientas anteriores conservadas en navegación secundaria.

Verificación conjunta del bloque: build y 28 pruebas frontend aprobados, diff correcto. Pendiente Playwright visual/responsive y contraste computado de todos los componentes. No implementación completa de las nuevas pantallas, timeline, componentes Vue reutilizables o Studio; algunos estilos históricos mantienen literales que requieren migración. Sin modelos/audio nuevos.

### Validación previa de la traza de ejecución — 2026-10-08

Antes de cargar modelos, el wrapper comprueba que opciones explícitas y modelo coinciden con el contexto exportado del plan. Diferencias detienen la ejecución; los defaults no pueden presentarse como overrides aprobados distintos. El lector valida estructura/tamaño/campos del contexto y conserva compatibilidad con invocaciones anteriores sin archivo de contexto.

15 pruebas backend dirigidas aprobadas (resolución, argv, alto nivel y evidencia), CLI `--help`, compilación Python y diff correctos. Sin modelos/audio reales. Pendiente ejecutar el recorrido con el entorno ACE-Step instalado; las pruebas actuales no acreditan fidelidad musical.

### Playwright del panel de trazas — 2026-10-08

Corregido acceso: el panel de ajustes del candidato se muestra fuera de propuestas y aprobación del plan vigente, permitiendo consultar evidencia histórica. Playwright con respuesta API simulada en QA comprobó apertura por teclado, semilla 0 preservada, ajuste delegado con wrapper 3 y motor «No reportado». Una traza de otra revisión mostró ausencia de evidencia, sin heredar la ficha actual. No es evidencia de generación real; no se guardaron fixtures en SQLite.

Build aprobado. Pendiente ejecución real de ACE-Step y contraste de sus diagnósticos; sprints abiertos.

### Opciones del runtime visibles por candidato — 2026-10-08

La evidencia del candidato conserva la traza del wrapper en metadata SQLite. Production incorpora una tabla que distingue configuración solicitada, valor enviado, origen y observación del motor. Cero se conserva como valor; datos ausentes se muestran sin inventarlos. Candidatos antiguos o trazas de otra revisión no heredan valores de la ficha actual. La tabla no acredita calidad audible.

2 pruebas backend de evidencia y 28 frontend aprobadas; build correcto. Pendiente Playwright de este panel y ejecución real para poblar trazas observadas. Sin audio nuevo ni cambios creativos en DB original.

### Traza de opciones del wrapper ACE-Step — 2026-10-08

La ejecución de planes exporta contexto de revisión, overrides solicitados, perfil y procedencia al wrapper. Su diagnóstico registra semilla/pasos/intensidad/shift resueltos y la fuente de cada valor. Directa y alto nivel usan la misma resolución. La ruta de alto nivel conserva por separado los valores que el motor realmente reporta; no completa observaciones ausentes con defaults.

Corregido default omitido de intensidad: Turbo usa 1, Base conserva 15; overrides explícitos no se sustituyen. Pruebas dirigidas de traducción/resolución/API aprobadas con mocks, sin cargar ACE-Step ni generar audio. No se afirma observación interna del handler directo ni fidelidad audible. Pendiente ejecución real, exposición UI de estas trazas y ampliar otras rutas históricas.

### Ayudas para todas las familias musicales — 2026-10-08

Los 49 campos de la ficha completa incluyen significado, efecto y ejemplo, compartidos desde el catálogo backend. Las nuevas ayudas cubren idea/estilo, ritmo/arreglo, voz, letra y entrega; distinguen intención de ejecución, referencia de clonación y requisito de evidencia audible. Los ejemplos no se persisten como defaults ni decisiones USER.

6 pruebas dirigidas del catálogo/revisión aprobadas. Playwright QA con viewport móvil 390×844 abrió la ayuda de velocidad, verificó sus tres textos y no observó desbordamiento horizontal en esa pantalla. Backend sirve las nuevas ayudas al frontend compilado existente; no cambio de bundle requerido. Pendientes revisión de todos los estados móviles, prueba táctil en equipo real y validación con usuarios amateur; sin modelos/audio nuevos.

### Ayudas de los 17 controles ACE-Step — 2026-10-08

El contrato compartido ahora incluye significado, efecto y ejemplo para todos los campos del motor. La ficha los muestra en ayudas desplegables; el editor utiliza las mismas ayudas y etiquetas del catálogo. Explican fuentes/referencias, modos/modelos, pistas/intervalos, rutas/LM y opciones de inferencia, sin prometer disponibilidad ni fidelidad por ajustar un valor.

10 pruebas backend dirigidas y build aprobados. Playwright QA abrió con teclado la ayuda de referencia musical y comprobó significado/efecto/ejemplo y ausencia de promesa de clonación. No modelos/audio ni escritura creativa. Pendientes ayudas equivalentes de otras familias musicales, revisión móvil/amateur y evidencia de defaults efectivos del runtime.

### Delegación explícita al perfil — 2026-10-08

La ficha permite guardar la decisión de dejar semilla, pasos, intensidad de condicionamiento y distribución de pasos al perfil automático. Se usa la revisión vigente; SQLite conserva procedencia USER, valor anterior y transformación de omitir override, sin confirmar la canción. Volver a guardar un número restaura la elección manual y elimina la disposición delegada. Los borradores abiertos bloquean esta acción para proteger sus cambios.

Verificado: 6 pruebas de configuración y 4 de estados backend, 26 frontend y build aprobados. Playwright QA delegó semilla con HTTP 200, comprobó ausencia del override, procedencia y revisión pendiente; la recarga conservó la delegación. Sin modelos/audio ni edición de DB original. Otros campos no ofrecen delegación automática sin contrato conectado.

### Cobertura y ayuda de revisión — 2026-10-08

La ficha distingue elección USER guardada, valor propuesto por revisar, delegación pendiente, campo sin valor y ajuste no aplicable. El contador indica valores presentes, sin atribuirles confirmación. Cada campo ofrece ayuda accesible con acción de revisión; una delegación heredada no oculta una elección USER posterior. Solo semilla/pasos/guidance/shift ofrecen dejar el ajuste al perfil automático; referencias y opciones vocales no prometen una capacidad automática.

4 pruebas backend nuevas, 24 frontend y build aprobados. Playwright QA comprobó etiqueta de elección guardada, contador, delegaciones pendientes y apertura de ayuda de velocidad por teclado. No cambios de datos ni modelos/audio. Son ayudas de revisión; falta el comando de delegación explícita, más ejemplos específicos y comprobación móvil/amateur.

### Varias propuestas antes de guardar — 2026-10-08

S03/S05: el formulario conserva hasta 20 propuestas aplicadas en orden y las guarda juntas en una revisión MusicSpec. La traza distingue valores aceptados, edición manual y sustitución por otra propuesta; valida toda la lista antes de escribir. La ruta singular anterior conserva compatibilidad. Descartar, cambiar de proyecto y guardar limpian la lista local.

19 pruebas backend dirigidas y 24 frontend aprobadas; build/sintaxis/diff correctos. Playwright QA comprobó propuestas 113 → 115 → elección manual 117, guardado HTTP 200 y ambas trazas persistidas con confirmación pendiente. Sin modelos reales ni generación de audio; no cambia la DB original. Próximo bloque: cobertura/delegación y ayudas de los controles; propuestas LLM siguen requiriendo evidencia y contrato específicos.

### Playwright del guardado desde chat — 2026-10-08

Verificado en copia QA: el chat propuso BPM 109, se aplicó al formulario y se modificó a 111; guardado HTTP 200 conservó ambos valores con resultado `user_modified` y confirmación pendiente. Recarga recuperó 111. Una traza alterada recibió HTTP 400 sin cambiar la revisión. [Reporte](docs/PLAYWRIGHT_CHAT_MUSIC_SPEC_20261008.md). Sin modelos reales, audio ni cambios creativos en DB original. El criterio de un patch determinista revisado queda comprobado; S03/S05 siguen abiertos por propuestas múltiples/LLM, cobertura y recorrido integral.

### Guardado trazable de propuestas revisadas — 2026-10-08

S03/S05: aplicar una propuesta del chat conserva su origen hasta el guardado explícito. El backend vuelve a derivar los campos desde la petición y la revisión vigente; rechaza trazas alteradas/desactualizadas. La revisión MusicSpec guarda propuesta, valores finales y resultado por campo (aceptado o modificado por usuario), sin confirmar automáticamente la canción. Descartar/cambiar de proyecto limpia la propuesta aplicada. El parser admite «105 BPM» y «BPM a 105».

Verificación de esta entrega: 9 pruebas de fases y 7 de propuestas backend, 22 frontend, build y revisión de sintaxis/diff aprobados. No Playwright nuevo ni modelos/audio reales en esta continuación. La traza corresponde al parser determinista y al guardado; no demuestra ejecución LLM. [Límites](docs/MUSIC_SPEC_SHARED_PHASES.md).

### Origen y vigencia de propuestas del chat — 2026-10-08

El asistente valida la revisión antes de inferir y devuelve patches con proyecto/revisión, hash de la fase, petición, transformación y estado propuesto sin guardar. Identifica el parser determinista que produce esos campos; no los atribuye a Gemma/Qwen ni a aprobación del usuario. El frontend envía y comprueba la revisión. Cuatro pruebas backend adicionales verifican trazas y rechazo previo a modelos. Persiste pendiente el vínculo completo propuesta/aplicación/guardado. [Detalle](docs/MUSIC_SPEC_SHARED_PHASES.md).

### Formularios y asistente sincronizados — 2026-10-08

S02/S03/S05: los formularios vinculados y la ficha comparten una revisión MusicSpec SQLite. Guardar refleja cambios en las otras fases, conserva detalles expresivos y procedencia, protege revisiones antiguas y decisiones bloqueadas. La letra literal queda vinculada a la revisión; cambiarla invalida su aprobación y el compilador rechaza otra letra. Las propuestas IA requieren revisión y guardado explícitos; el chat rechaza propuestas si cambia el proyecto, revisión, fase o borrador.

Verificación dirigida: 32 pruebas backend y 22 frontend aprobadas; Playwright MCP en copia QA comprobó sincronización bidireccional, recarga y rechazo de escritura antigua. Sin inferencia real, audio nuevo, escucha ni publicación Git. [Contrato y límites](docs/MUSIC_SPEC_SHARED_PHASES.md). Sprints siguen abiertos: comandos integrales del chat, ayudas/cobertura y flujo completo pendiente.

### Consolidación real de Isabella y Alma y avance S03 — 2026-10-07

Migración aplicada a `data/song_ai.sqlite`: dos proyectos/set activos, seis assets independientes. Se mantienen los IDs originales; la letra editada SQLite prevalece sobre los assets compartidos y las plantillas. Alma ya no hereda el destinatario Isabella. Las fichas incorporan intención recuperada, propuestas Codex, dirección de las secciones reales y detalles expresivos conservados. Las fuentes completas quedan vinculadas a una task de cada proyecto; no hace falta un recorrido histórico separado. El fixture de prueba y drafts sustituidos permanecen recuperables, fuera de la biblioteca de trabajo. No se borró información.

WAV/MP3/FLAC originales de ambas canciones conservados: seis checksums iguales al respaldo, WAV de 120 segundos cada uno. La revisión creativa sigue pendiente; los audios recuperados no acreditan fidelidad a la nueva revisión. Los documentos de letra de Production se regeneran con la letra correcta y sin aprobación automática. Informe: `data/rescue_20261007/consolidation_report.json`; respaldo previo de DB/archivos: `data/rescue_20261007/before_consolidation/`. [Detalle de migración](docs/LEGACY_INTENT_MIGRATION.md).

S03: edición compartida ampliada a campos creativos del catálogo (idea, estilo, instrumentos, estructura, voz, frases/exclusiones y entrega), con controles visibles y ayuda; tipos/listas y decisiones bloqueadas validados en backend. Solo se envían valores modificados, evitando convertir defaults al abrir el editor en decisiones USER. Guardar crea revisión pendiente; no genera audio. Formularios anteriores/chat aún requieren sincronización completa y el bloqueo obligatorio de sample sigue pendiente de retirada.

Verificación: 14 pruebas backend dirigidas y 18 frontend aprobadas; build correcto. Playwright MCP sobre copia de la DB verificó dos proyectos/seis assets, ficha Alma, ausencia del botón de migración, guardado HTTP 200 de exclusiones, recuperación tras recarga y envío exclusivo del campo cambiado. La DB real se comprobó además por lectura, compilación sobre copias de revisión y checksums; ninguna confirmación sintética se persistió. Sin inferencia de modelos, nueva generación, escucha o publicación Git. Sprints abiertos por los criterios restantes.

### Entrega inicial de migración revisable — 2026-10-07 (superada para Isabella y Alma)

Implementada [primera migración de intención](docs/LEGACY_INTENT_MIGRATION.md): propone campos faltantes desde fases guardadas y conserva contexto del set/los tres assets. Preserva valores actuales, locks declarados y conflictos; verifica revisión/hash de fuentes antes de aplicar. La aplicación explícita crea revisión pendiente con procedencia/task SQLite, sin borrar historial. Inferencia determinista identificada; no se atribuye a Gemma/Qwen ni a deseos USER confirmados.

20 pruebas backend/15 frontend y build aprobados. Playwright en copia QA verificó tres añadidos y tres conflictos con fuentes/asset context conservados; la aplicación se probó en SQLite temporal. No se migraron masivamente proyectos reales ni se ejecutó audio. El circuito histórico todavía no se retira: faltan revisión semántica de toda la intención, resolución de conflictos y consumidores MusicSpec completos.

### Edición musical sobre la revisión compartida — 2026-10-07

`PATCH /api/pro/projects/{song_id}/spec` permite guardar BPM, tonalidad, compás, idioma y duración junto a controles del motor en la revisión SQLite existente. Reutiliza validación/persistencia de configuración, protege revisión concurrente, conserva intenciones y marca cambios USER; guardar requiere nueva confirmación. La ficha de Production incorpora los cinco controles; indica explícitamente que las fases históricas aún no se sincronizan automáticamente. No se crea otra fuente de verdad.

16 pruebas backend y 15 frontend aprobadas, build correcto. Playwright con SQLite aislado guardó BPM 97, recibió HTTP 200/revisión pendiente y recuperó 97 tras recarga. Prueba backend comprueba BPM 97 en el request tras confirmar, sin mutar otras intenciones; no acredita aprobación real del usuario ni audio. Cobertura creativa completa/chat, locks y sincronización de formularios históricos siguen pendientes. No audio ni publicación Git.

### Bloque conjunto S00/S06A: navegador y primeras ayudas — 2026-10-07

Playwright MCP con SQLite aislado confirmó límites de Turbo, fuente/pistas al elegir Lego y descarte de configuración. El contrato ahora incluye significado, efecto y ejemplo para seed/pasos/guidance/shift; la UI muestra cuatro ayudas desplegables, y se comprobó apertura de la primera con teclado. No se modificaron datos del proyecto original ni se cargaron modelos/audio. 14 pruebas backend dirigidas y build aprobados; adaptación móvil y ayuda en otros controles pendientes.

El plan general tiene 19 IDs; 8 relevantes para este alcance (S00–S06/S10), agrupados en cuatro bloques de entrega en el plan de sprints. Agrupar trabajo no cierra criterios pendientes ni elimina exclusión de memoria entre LLM y ACE-Step.

### Controles ACE-Step conectados al contrato — 2026-10-07

El formulario de configuración usa el perfil recibido en catálogo para opciones de acción/modelo/API/LM/pistas, límites de seed/pasos/guidance/shift y visibilidad de fuente/pistas/intervalo/LM. Un módulo de presentación no modifica decisiones USER; sin contrato bloquea edición y conserva Descartar disponible. No deduce disponibilidad real de modelos por su presencia en opciones.

13 pruebas frontend aprobadas y build Vite correcto. No se realizó una nueva revisión Playwright ni inferencia/audio. Otros controles históricos, límites adicionales y rutas de correcciones aún requieren migración; no se declara el frontend entero unificado. La interfaz permanece común/asistida, sin niveles de experiencia.

### Perfil de capacidades compartido — 2026-10-07

Implementado `AceStepCapabilityProfile` como contrato puro/versionado de reglas conectadas, usado por catálogo, validación de tareas y opciones de generación. Centraliza modos, pistas, rutas/LM, compatibilidad Base, intervalos y rangos de controles; catálogo incorpora política por campo y contrato público. LM deja de aparecer aplicable cuando la ruta no lo usa. Planes nuevos registran versión/hash del contrato junto a traza de inputs. No presume pesos presentes, carga ni calidad real: preflight y audio siguen separados.

38 pruebas dirigidas aprobadas sobre perfil/catálogo, modos, opciones, compilador, configuración, propuesta Qwen y conservación USER. El frontend todavía tiene controles/reglas que deben migrar al contrato; no se afirma sincronización completa. S00 sigue abierto y continúan pendientes patch creativo compartido, ayudas y retirada del requisito de sample. No se cambió Vulkan ni se generó audio.

### Primer bloque del sprint: trazabilidad de inputs ACE-Step — 2026-10-07

Implementada `input_trace` en los planes nuevos: por input conserva fuentes/valores/procedencia, resultado, regla versionada y revisión; referencias registran ID y verificación pendiente en preview. La traza forma parte del hash del plan. Un input nuevo sin regla de mapping se rechaza. Módulo puro separado del compilador/provider, sin carga de modelos.

23 pruebas backend dirigidas aprobadas. La nueva aceptación cubre los 21 nombres de inputs emitidos actualmente (incluidos caption/lyrics), 13 combinaciones compatibles de seis modos y rutas directa/alto nivel/LM, conservación de valores/procedencia y archivos/argumentos del wrapper; también rechazo de inputs sin regla, valores inválidos y texto excesivo. Capturas/mocks no acreditan inferencia ni audio. AC-ACE-USER-01 sigue parcial: faltan origen UI/chat y persistencia, autorización de cambios creativos, locks, verificación real de artefactos y vigencia integral. Perfil central compartido, retirada del gate de sample y Builder/ayudas siguen pendientes. No se publica en Git por esta entrega.

### Interfaz común asistida reafirmada — 2026-10-07

Se corrigieron contratos, matrices, wireframes y sprints para retirar niveles de experiencia. Song Builder propone los mismos controles para todas las personas, con tooltip de significado/efecto/ejemplo y ayuda accesible por teclado/móvil. Perfil automático por defecto y ajuste manual disponible para cualquiera; IA recomienda sin reemplazar decisiones USER. [Decisión y aceptación](docs/SONG_BUILDER_APPROVED_DECISIONS_20261007.md). Esta entrega alinea documentación; Builder y ayudas nuevas siguen pendientes de implementación. No modifica componentes ni estilos del frontend.

### Decisiones actualizadas del Song Builder — 2026-10-07

El usuario definió [cinco decisiones vigentes](docs/SONG_BUILDER_APPROVED_DECISIONS_20261007.md): sample previo opcional sin bloqueo de generación completa; instrumental como intención con ejecución condicionada a validación; dirección por sección persistida en MusicSpec; referencia audio opcional/avanzada sin clonación; perfil ACE-Step automático y manual disponible para cualquiera. Se alinearon AGENTS y contratos/planes. El código actual todavía requiere migrar gates/consejos de sample: no se ha implementado esa retirada ni se ha aprobado el rediseño completo. Se mantienen tres assets, set válido, request confirmado y evaluación de audio separada.

### Aceptación de inputs USER — 2026-10-07

Se incorporó [AC-ACE-USER-01](docs/ACE_STEP_USER_INPUT_ACCEPTANCE.md) a contratos y sprints: por cada input ACE-Step conectado, probar conservación de la decisión USER desde MusicSpec hasta request y trazabilidad de toda transformación. Define casos de overrides IA/defaults, conversiones, texto protegido/límites, referencias y vigencia. Es un gate añadido; las pruebas de este criterio siguen pendientes y no acreditan fidelidad acústica por sí solas.

### Design System propuesto para Song Builder/Studio — 2026-10-07

Se documentó la [propuesta visual A–Q](docs/SONG_AI_DESIGN_SYSTEM_PROPOSAL_20261007.md), pendiente de aprobación: paleta semántica Dark/Light, tipografía/spacing/geometry, componentes y estados, Builder progresivo, Studio mínimo, responsive y accesibilidad. El inventario estático encontró 17 tokens raíz y 158 expresiones literales de color; el CTA actual calcula 2,85:1 entre texto y fondo. La propuesta pasó 66 pares de contraste evaluados por cálculo sRGB; esto no certifica pantallas renderizadas ni conformidad WCAG global. No se modificaron estilos/componentes del frontend, instalaron librerías ni ejecutaron modelos. Los tokens de diseño no se cargan en la app; Vue y Vulkan permanecen vigentes.

### Diseño UX/UI de Song Builder para revisión — 2026-10-07

Se documentó la [arquitectura de interacción A–M](docs/SONG_BUILDER_UX_ARCHITECTURE_20261007.md): creación inicial Custom/text2music, matriz de inputs, autoridad/procedencia, controles comunes asistidos sobre una MusicSpec, letra por secciones, preguntas dinámicas, preflight y transición a Studio mínimo. Las otras acciones ACE-Step se ofrecen posteriormente según capacidad disponible; MIDI y audio guía no son requisitos iniciales. Es una propuesta pendiente de revisión y autorización del usuario, sin implementación de componentes ni cambio de Vue/Vulkan. Se contrastaron código y contratos actuales; no se hicieron nuevas inferencias, pruebas de navegador ni validación amateur en esta tarea.

### Análisis de Song Builder — 2026-10-07

Se completó el análisis previo al rediseño solicitado, con recorrido de usuario, arquitectura incremental, MusicSpec compartida, perfil de capacidades ACE-Step, migración y tareas alineadas con S00/S03–S06/S10. [Documento y evidencia](docs/SONG_BUILDER_ACE_STEP_ANALYSIS_20261007.md). La propuesta interfaz común asistida está pendiente de implementación; todos los niveles editarán la misma revisión.

Playwright sobre SQLite aislado comprobó 49 campos de catálogo sin editores dentro de la ficha, cambios condicionales en seis acciones y persistencia de cuatro controles del motor. Se reprodujo una separación: Music Plan guarda BPM 97, pero la ficha de ACE-Step permanece en 72. La importación de audio propio y el booleano instrumental siguen pendientes de conexión. Vite compiló; no se generó audio ni se validó experiencia con personas amateur. Se conserva Vulkan y el módulo histórico de servicios pagos.


### Preparación OpenVINO y prueba NPU — 2026-10-07

OpenVINO 2026.0 y llama.cpp b9442 están compilados en una carpeta aislada, con checksum oficial del SDK y ejecutables CLI, servidor y benchmark. Windows reconoce Intel AI Boost. La primera prueba Qwen en NPU seleccionó el dispositivo real, pero falló al decodificar el warmup tras 135,34 s. OpenVINO GPU tampoco completó el ensayo: Qwen alcanzó 180 s y Gemma falló en warmup tras 30,25 s. Se preparó también la build oficial b11476 / OpenVINO 2026.4.1: Qwen NPU siguió sin responder, incluso con memoria optimizada, chunk64 y fit desactivado. El último diagnóstico solicitó un límite180s y terminó a481,50s por el retraso del cierre nativo. El driver NPU observado es32.0.100.3717; revisar su actualización es el siguiente paso de compatibilidad. La combinación Qwen NPU + Gemma Vulkan sigue sin validarse; se conserva el runtime activo. [Configuración, diagnóstico y criterios de aceptación](docs/OPENVINO_CONFIGURATION_20261007.md).

### Exploración rápida de backends Intel — 2026-10-07

El runner aislado `tools/benchmark_llm_backends.py` compara ejecutables externos con `pp512`/`tg32`, dos repeticiones y timeout por modelo, sin modificar providers ni configuración activa. Seis casos Vulkan/SYCL terminaron correctamente, incluyendo un control de la misma versión b5377. Vulkan b9442 conserva la preferencia: Qwen generó 10,37 frente a 4,89 tokens/s de SYCL b5377; Gemma 14,32 frente a 7,35. SYCL moderno/FP16 sigue sin evaluar. En esa serie OpenVINO todavía estaba pendiente de preparación Windows; la evaluación posterior se describe arriba. [Método, tablas y evidencia](docs/LLM_BACKEND_EXPLORATION_20261007.md). Estos benchmarks cortos no acreditan fidelidad, audio ni estabilidad prolongada; la configuración de la aplicación se conserva.

### Optimización GPU de Gemma y Qwen — 2026-10-07

Se compararon perfiles reales con los mismos prompts del proyecto QA, steering, esquema y límites de salida. Qwen usa ahora `--threads 6 --flash-attn off --batch-size 512 --ubatch-size 256 --fit off`: la ficha completa válida pasó de 132,17 a 119,02 segundos en el ensayo sin caché. Flash Attention fue más lento y permanece desactivado para Qwen.

Gemma conserva su perfil base: los alternativos no aportaron una mejora aceptable. Su prompt coloca el contexto estable primero y la pregunta una sola vez al final. Para una pregunta distinta del mismo proyecto, dos comparaciones pasaron de 16,63/16,66 a 2,94/2,92 segundos, conservando nombres, exclusiones y cuatro versos. Se reutilizaron 3384 tokens y solo se procesaron 37. El primer pedido todavía tarda unos 23 segundos; la reducción depende de que el contexto siga vigente.

Se completaron 34 solicitudes reales: 33 cumplieron las comprobaciones y una incumplió el formato de versos; su perfil fue descartado. La comprobación final con ambos modelos residentes pasó: Qwen 117,47 s para ficha completa y Gemma 26,11 s para versos, sin caché previa ni cierre espontáneo. Los procesos del ensayo se cerraron al terminar. Ocho pruebas de regresión dirigidas y compilación Python aprobadas. No se redujeron los límites de respuesta ni los datos creativos. Los detalles, resultados desfavorables, método y límites están en [rendimiento local de modelos](docs/LLM_GPU_PERFORMANCE_20261007.md). Las propuestas requieren revisión/guardado explícitos; no se generó audio en estos ensayos.

### Fase 1: modelos reales, ficha revisable y GPU — 2026-10-07

Completada la verificación técnica de los casos de fase 1 con Playwright MCP, Gemma y Qwen reales, usando SQLite aislado en `data/qa_two_phase_20261006`. **La revisión creativa del usuario sigue pendiente.** No se generó audio ACE-Step ni se aprobó sample o canción final; la fase 2 y la validación con personas amateur siguen separadas. Los ensayos fallidos descritos más abajo son históricos y conservan su evidencia.

Gemma respondió a cuatro variantes: tarde/casa, primera persona con frase literal, exclusiones y nombres con acentos. Se verificaron cuatro versos, ausencia de placeholders no pedidos y conservación de «Ana María»/«José». La presentación elimina encabezados/numeración cuando conserva exactamente los versos solicitados; no reescribe la letra. La última respuesta apareció en el footer con sus cuatro líneas. Las propuestas de configuración se revisan antes de usarlas en el formulario y requieren guardado explícito.

Production permite **Preparar propuesta técnica completa**. Qwen contempla los 49 campos del catálogo y propone parámetros desde la revisión persistida, con decodificación JSON Schema y comprobaciones independientes de tipos, opciones, valores vigentes y compatibilidad ACE-Step. Propuestas, tasks, runs y hashes del steering quedan en SQLite; la ficha activa permaneció idéntica. La lectura por familias distingue sugerencias y valores guardados, recupera la propuesta tras recarga y rechaza respuestas de otro proyecto/revisión. Opcionales delegados no son faltantes obligatorios. Compilaciones inválidas quedan fallidas; sus fallbacks no se muestran como fichas completas. El resumen visible describe el estado comprobado, sin asumir las garantías escritas por el modelo. La revisión real del contraejemplo detectó Lego/Turbo incompatible, tres versos frente a cuatro, palabras excluidas y nombre propio no solicitado. La guía de esta ruta no exige MIDI.

| Ensayo real | Resultado |
|---|---|
| Gemma GPU, contexto nuevo / reutilizado | 37,50 s / 4,42 s; nombres, exclusiones y cuatro versos visibles. |
| Qwen CPU, ficha completa | 276,77 s; 49/49 campos, sin faltantes obligatorios ni conflictos declarados. |
| Qwen GPU, ficha completa | 142,58 s; 49/49 campos, sin faltantes obligatorios ni conflictos declarados. |
| Qwen GPU, revisión dirigida del contraejemplo | 49,95 s; cuatro incumplimientos explicados. |
| Ambos modelos residentes en GPU | Qwen 23,80 s tras adjuntar el validador del motor; Gemma 8,24 s con contexto reutilizado. Ambos permanecieron activos. |

Estos tiempos corresponden a ensayos concretos, con salidas distintas; no son una garantía de latencia ni un benchmark aislado. Logs verifican Gemma **27/27** y Qwen **37/37** capas en Vulkan0 (Intel Graphics). Qwen completó tres solicitudes seguidas sin cierre con el perfil inicial siguiente; la optimización posterior documentada arriba amplió sus lotes en `.env`:

```dotenv
SONG_AI_QWEN_GPU_ARGS=--n-gpu-layers 999
SONG_AI_QWEN_LLAMA_ARGS=--threads 6 --flash-attn off --batch-size 256 --ubatch-size 128 --fit off
```

La configuración GPU anterior cerró `llama-server.exe` durante inferencia. Windows registró `0xc0000409` en `ucrtbase.dll` (evento 1000, 07:45:33); la API recibió WinError 10054. Microsoft documenta ese código para [terminación inmediata fast fail](https://learn.microsoft.com/en-us/cpp/intrinsics/fastfail?view=msvc-170). El evento no identifica por sí solo el subfallo ni demuestra falta de memoria. Hay [reportes relacionados de Vulkan/Intel en llama.cpp](https://github.com/ggml-org/llama.cpp/issues/22034), pero no se atribuye este cierre a ese mismo defecto. El perfil conservador funcionó con llama.cpp b9442 e Intel driver 32.0.101.8247; no se aisló cuál de sus ajustes resolvió el problema. Los logs anteriores ahora se archivan antes de cada arranque para conservar futuros diagnósticos. La decodificación sigue la [interfaz oficial de llama.cpp](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md), comprobada contra el servidor local.

El volcado específico `llama-server.exe.19484.dmp` confirma el código, módulo y parámetro de excepción 7; no se copiaron ni exportaron sus datos de memoria. En la repetición con ambos modelos residentes, la explicación de Qwen sobre Lego fue imprecisa. El handoff ahora adjunta y persiste `engine_input_validation`, y Qwen explicó el requisito Base 1.5 al repetirlo. La opinión del modelo permanece separada del chequeo determinista y de la aprobación del usuario. Durante el ensayo dual se observó memoria física libre muy reducida (aproximadamente 51 MB); las respuestas terminaron, pero eso no habilita audio ni garantiza margen para otras cargas. Los modelos del ensayo se cerraron para liberar sus recursos.

Verificación: **222 pruebas backend aprobadas, sin omisiones**, con `data/tools/ffmpeg/bin` en PATH; **11 frontend**, build, compilación Python y diff correctos. La suite completa final incluye la limpieza de encabezados y la validación del motor adjunta al handoff; terminó en 349,44 segundos. También pasó la repetición real de Gemma. Evidencia: `.playwright-mcp/two-phase/phase1-complete-20261007.json`, logs GPU, captura y reporte [para tu revisión](.playwright-mcp/two-phase/PHASE1_REVIEW_20261007.md). La aceptación poética/musical sigue siendo del usuario; completar una ficha no demuestra calidad de canto ni audio.

### Fidelidad de propuestas de letra frente a mocks (2026-10-07)

Los textos de assets con provider mock dejan de enviarse como letra de referencia a Gemma; se conservan su manifest, ID e intención con procedencia explícita `mock_example_not_confirmed_user_wish`. El steering prioriza la petición actual y el proyecto frente a ejemplos, exige señalar conflictos con requisitos confirmados y evita placeholders no pedidos. No se modifican los assets ni se aprueban propuestas automáticamente. Para peticiones con una cantidad de líneas reconocible, la presentación elimina título y numeración solo si ya hay exactamente esa cantidad de líneas; no agrega, elimina ni reescribe versos.

Prueba real aislada: Gemma respondió en 27,61 segundos con cuatro líneas sobre tarde, casa, piano y voz serena, sin temática de cuna ni placeholders. La salida real incluyó título y numeración; su limpieza de presentación se comprobó por prueba unitaria, sin afirmar que el modelo obedeció ese formato por sí solo. Diez pruebas específicas pasaron, con compilación y diff correctos. Esto verifica esa petición concreta; la calidad poética, fidelidad general y aprobación del usuario siguen requiriendo evaluación. Evidencia: `.playwright-mcp/two-phase/lyric-fidelity-20261007.json`.

### Optimización de consultas locales (2026-10-07)

Las consultas creativas simples responden con Gemma sin esperar una inferencia adicional de Qwen. Las solicitudes explícitas de revisión técnica y los cambios propuestos de configuración conservan el handoff técnico; no se omiten los gates deterministas, la confirmación de ficha ni la aprobación del sample. Las revisiones técnicas solicitadas siguen siendo síncronas. El contexto conversacional conserva especificación activa, decisiones, intenciones y bloqueos, excluyendo historial y artefactos duplicados. La evidencia completa del steering sigue registrada, pero el prompt omite expresiones internas del resolver de configuración.

El arranque acepta `-Role gemma`, `-Role qwen` o `-Role all` (predeterminado), GPU configurable por rol mediante `SONG_AI_GEMMA_GPU_ARGS`/`SONG_AI_QWEN_GPU_ARGS` y caché de prompts limitada a 256 MB (`SONG_AI_LLAMA_CPP_CACHE_RAM_MB`). Se reutiliza el prefijo de prompt y los logs permiten inspeccionar el offload real. No se afirma uso de GPU solo por tener el parámetro configurado. Los modelos no solicitados pueden mantenerse descargados durante pruebas por rol; el arranque habitual conserva ambos para compatibilidad.

La carga aislada de Gemma con logs detallados confirmó **27/27 capas en Vulkan0 (Intel Graphics)** y KV cache en ese dispositivo. La velocidad medida corresponde al conjunto de optimizaciones y no demuestra un factor de aceleración GPU por separado.

Medición real por API en la base aislada: la misma petición de letra respondió en 37,62 segundos, con 3459 tokens de entrada frente a unos 6443 anteriores. Gemma consumió 35,26 segundos de inferencia y no hubo handoff Qwen. La referencia anterior fue 111,71 segundos de Gemma más 261,53 de Qwen; cambian contexto, aceleración solicitada y modelos cargados, por lo que no es una comparación aislada CPU/GPU. La propuesta aún conserva temática de cuna del draft y **no supera aceptación creativa**. Resultado en `.playwright-mcp/two-phase/optimized-gemma-20261007.json`. Trece pruebas específicas, compilación y revisión de diff verifican estos cambios; no se generó audio.

### Correcciones de la prueba de modelos y audio (2026-10-07)

Repetición real de fase 1 con Playwright el 2026-10-07: Gemma completó inferencia en 111,7 segundos (209 tokens de salida), Qwen en 261,5 segundos (200 tokens); ambos sin timeout ni truncamiento. **Aceptación creativa fallida**: a la petición de cuatro líneas sobre una tarde tranquila en casa, Gemma respondió con tres líneas de cuna nocturna y placeholders del mock. Qwen produjo recomendaciones generales y no identificó esos incumplimientos; no compiló una nueva ficha técnica completa. El ensayo confirmó ejecución real y espera prolongada, pero no fidelidad ni calidad de la propuesta. La navegación restauró Production durante la petición iniciada en Biblioteca; la respuesta API quedó capturada, aunque no apareció en el footer, por lo que falta repetir la visualización con la fase estable. Evidencia completa: `.playwright-mcp/two-phase/phase1-retest-20261007.json`. No se ejecutó la fase de audio en este ensayo.

Implementado: Gemma recibe instrucciones para atender la propuesta solicitada y respetar el set activo; su steering conserva los gates de producción sin sustituir peticiones de letra por una guía general. Los defaults y la configuración local pasan a contexto 8192, salida Gemma 512/Qwen 768 y timeout 480 segundos para inferencia local lenta. Las respuestas que llama.cpp identifica como truncadas se rechazan; la guía de fallback expone el error y no se etiqueta como inferencia real por el solo hecho de que el servidor responda al health check. Una revisión de Qwen se registra como revisión no verificada, no como validación determinista; MIDI deja de figurar como paso obligatorio en ese handoff.

El cierre descubre los servidores del proyecto por ejecutable y modelo, incluso sin archivo PID, conserva servidores ajenos y comprueba su terminación. Si el comando falla, ResourceMonitor bloquea la generación y no declara memoria liberada. Se conserva el presupuesto de RAM: estas correcciones no garantizan que alcance la memoria ni acreditan fidelidad creativa, escucha o audio final. La repetición de las dos fases con inferencia y audio reales sigue pendiente.

Verificación: 13 pruebas unitarias dirigidas pasaron; el contrato PowerShell de cierre conservó los procesos ajenos y propagó correctamente un fallo simulado. Build, compilación Python y revisión de diff correctos. La suite general ejecutó 203 pruebas, con cinco omisiones y un error en un fixture antiguo de diagnóstico; se actualizó ese fixture y la prueba correspondiente pasó por separado. No se repitió la suite general completa después de ese ajuste.

### Prueba real en dos fases con Playwright (2026-10-06)

Prueba aislada en `http://127.0.0.1:8012`, con SQLite en `data/qa_two_phase_20261006`, sin modificar los proyectos habituales. Gemma y Qwen ejecutaron inferencia local real en CPU. Gemma devolvió una guía general en lugar de las cuatro líneas solicitadas; Qwen agotó el timeout del handoff completo. Una revisión técnica acotada sí ejecutó Qwen y señaló BPM discordantes, pero su salida quedó cortada. Esta fase **no pasó** la aceptación creativa ni valida el flujo completo.

Se redujo el contexto conversacional eliminando duplicados y acotando el historial diagnóstico, conservando inputs creativos y revisiones. El timeout del chat contempla las dos solicitudes sucesivas; el arranque local usa contexto de 8192 y un slot. Verificación: ocho pruebas unitarias, compilación y build; la calidad de las respuestas reales sigue pendiente de corrección.

Desde Production se preparó y aprobó un plan de prueba `text2music`, Turbo, API de alto nivel sin LM, ocho pasos y semilla 123. Se usó una letra de prueba escrita durante el ensayo; **no fue una letra generada por Gemma**. El job `ace_job_491d3c760373430c97b3e3863154bc00` falló antes de cargar ACE-Step: 2167 MB disponibles frente al presupuesto de 7049 MB. El cierre automático no dejó cerrados los servidores usados en el ensayo; se verificaron y cerraron sus procesos manualmente. Tras cerrar también el navegador de prueba quedaron aproximadamente 6655 MB, todavía insuficientes. **No hay generación de audio corriendo ni audio validado.** El cierre automático efectivo y la memoria disponible requieren revisión antes de repetir la fase 2. Los resultados del ensayo están en `.playwright-mcp/two-phase/phase1-results.json`; el sample y la aprobación final siguen pendientes.

### Dirección de desarrollo: especificación integral Gemma/Qwen (2026-10-03)

Primera entrega implementada el 2026-10-04: las compilaciones de especificación crean revisiones inmutables en SQLite, exponen catálogo/cobertura por API y generan `song_spec.json` y `song_spec.md` desde el mismo estado. Production muestra una ficha desplegable con idea, instrumental, voz, letra y producción, valores actuales, parámetros pendientes y explicación de cada opción. La respuesta técnica identifica la base determinista y evita presentar la validación por campos como inferencia real de Qwen. La inferencia conversacional real y las propuestas editables siguen pendientes; los gates de confirmación y sample se completaron en entregas posteriores descritas abajo.

Segunda entrega implementada el 2026-10-04: la compilación registra un handoff técnico en `tasks`, `model_runs` y eventos, y distingue `provider_review`, `mock_handoff` y fallo con fallback. El catálogo conserva procedencia por campo entre mensaje del usuario, extracción e interpretación de IA. Production permite confirmar la revisión activa con protección contra revisiones obsoletas; la confirmación crea otra revisión y un evento.

Tercera entrega implementada el 2026-10-04: una ficha completa permanece en la fase 1 y en espera del usuario. Solo la confirmación de su revisión activa mueve el proyecto a generación de letra. Backend y Production bloquean letra, plan musical, MIDI, instrumental, voz, conversión vocal, mezcla, mastering y exportación cuando la ficha no está confirmada. Los proyectos recuperados desde un set válido ya guardado quedan confirmados con origen `sqlite_import`. Gemma continúa usando extracción por reglas en esta ruta; la inferencia conversacional real y las propuestas estructuradas de Qwen siguen pendientes.

Cuarta entrega implementada el 2026-10-04: el sample se genera para un `set_id` explícito, nace pendiente, se aprueba mediante una acción separada y conserva una huella de los assets y configuraciones vigentes. Cambiar letra, instrumental, melodía, set o datos de fases lo marca como desactualizado. La canción completa, Mastering, Export y la generación final local vinculada rechazan samples ausentes, ajenos, pendientes o desactualizados. Production muestra la acción correspondiente para crear, aprobar o regenerar el checkpoint; el preset inicial también se detiene para pedir revisión.

El contrato exige además guía proactiva sobre todos los hitos y parámetros, catálogo derivado del esquema/capacidades y una interfaz con formularios, opciones, ficha completa y propuestas revisables. Gemma explica, Qwen propone/valida y el usuario elige o delega explícitamente. Los controles y la conversación comparten el mismo estado/versiones, sin depender solo del chat ni exigir conocimientos técnicos. Estas entregas SP-07 a SP-09 siguen pendientes de implementación y prueba de uso.

El [contrato de especificación de canción](docs/SONG_SPEC_GEMMA_QWEN_CONTRACT.md) define que Gemma recoge y confirma los deseos y Qwen compila el documento musical/técnico completo por etapa. Incluye procedencia, restricciones, producción, voz, sample, criterios de calidad y trazabilidad hasta el audio evaluado. La ampliación debe evolucionar `song_specs` y exportar `song_spec.json`/`song_spec.md` desde la misma revisión SQLite.

En la ruta actual `ProfessionalSongService.collect_spec`, `CreativeAgentService` y `TechnicalDirectorService` usan reglas y `ModelManagerService` simula ejecución. `approved_by_qwen` no acredita una inferencia real de Qwen, aprobación del usuario ni calidad del audio. El contrato y las tareas SP-01 a SP-09 son desarrollo pendiente; esta actualización es documental.

### Dirección de desarrollo: calidad y voz personalizada (2026-10-03)

El [contrato de audio y voz](docs/AMATEUR_AUDIO_VOICE_STEERING.md) define las mejoras pendientes del recorrido amateur, el sample representativo y aprobado del set activo, controles técnicos y evaluación por escucha de la canción completa, ajustes comprensibles y exportables verificados. El [roadmap](docs/ROADMAPP.md) ordena entregas P0/P1/P2 y sus dependencias. Son especificaciones de desarrollo: no se implementó nueva funcionalidad ni se validó audio real en esta revisión.

Todavía no existe una opción de producto para importar/grabar y copiar una voz humana en las canciones. Se planifica como voz personalizada opcional, con referencia autorizada, perfil versionado y provider que demuestre canto condicionado o conversión de voz cantada. La ruta con una voz generada debe funcionar sin esa opción. TTS hablado, mocks y archivos generados no acreditan por sí solos calidad de canto o parecido vocal.

### Revisión de experiencia para principiantes (2026-10-03)

Se revisaron `AGENTS.md`, los planes de producto y el flujo visible de la app. La [revisión de flujo amateur](docs/AMATEUR_USER_FLOW_REVIEW.md) documenta hallazgos, recorrido propuesto, prioridades y criterios de aceptación. Es planning pendiente: en particular, Production aún no presenta un sample obligatorio del proyecto activo antes de la generación final, aunque `AGENTS.md` lo exige. La implementación actual y sus límites se describen a continuación.

`AGENTS.md` §16 define ahora el perfil amateur y las reglas de acompañamiento: lenguaje común, valores musicales sugeridos revisables, tres piezas obligatorias, siguiente acción visible y sample del set activo antes de la canción completa. Ya están implementados los bloqueos centrales de ficha, set y sample; el catálogo completo, la guía conversacional real y la simplificación integral de todo el recorrido siguen en desarrollo. La experiencia completa continúa pendiente de validación con usuarios amateur.

### Correcciones del handoff de interfaz (2026-10-03)

- Biblioteca permite preparar drafts mock de instrumental, melodia y letra desde el brief actual, elegir cada asset de forma explicita y crear un set solo cuando existen los tres. Las secciones de letra editadas se conservan en `lyrics.md` del draft; la API valida los IDs y exige `manifest.json`, `intent.json` y contenido para cada asset.
- Crear proyecto bloquea el doble envio en la UI y usa `request_id` para que un reintento equivalente devuelva el mismo set. El mismo identificador con otros datos se rechaza.
- Guardar y continuar espera la persistencia y muestra el error sin navegar. Descartar restaura la ultima version cargada/guardada y sus indicadores. Atras, Adelante y Recargar tambien protegen cambios de un proyecto activo.
- El asistente libera el boton y muestra errores de red, HTTP, JSON o timeout; una respuesta tardia no aplica cambios a otra fase o proyecto.
- Sin proyecto activo, las fases de ejemplo se muestran sin confirmacion de guardado. Los avisos de CPU de Production describen una estimacion, y BPM se valida entre 48 y 240 tanto en el editor como en el backend.
- Se comprobaron con Playwright la creacion desde una biblioteca vacia, un brief de 83 BPM conservado en el draft y el editor, seleccion de la segunda terna, error de guardado simulado, descarte de BPM y una capa vocal, Atras, error de red del asistente, rechazo visible de BPM negativo y un solo POST tras doble clic. La suite Python paso con 50 pruebas (`unittest discover -s tests -q`, monitor de recursos deshabilitado). No se genero audio real en este recorrido.

La ruta principal es **local-first con Full Song / ACE-Step**:

- ACE-Step genera una cancion completa con instrumental y voz cantada integrada.
- La fase de Mastering del pipeline profesional puede usar `SONG_AI_FULL_SONG_COMMAND` con tokens dinamicos para perfiles ACE-Step Turbo/Base.
- Si Full Song esta listo, `soundtrack` y `singing_voice` separados son opcionales.
- Si el sistema cae en `procedural_vocal_guide`, la app bloquea la descarga como final.

Estado esperado local cuando ACE-Step esta importable:

```text
full_song: ready
runtime: xpu_ready | gpu_ready | cpu_extremely_slow
soundtrack: optional
singing_voice: optional
mix_and_export: ready
```

Importante: Song AI ya esta preparado para generar voz cantada real por ACE-Step, pero la calidad final depende de que ACE-Step pueda ejecutar realmente en el entorno local. Con aceleracion GPU compatible es lo recomendado; por CPU puede tardar mucho.

En Windows con Intel Core Ultra, Song AI intenta `Intel XPU` automaticamente cuando `torch.xpu.is_available()` es verdadero. Si XPU no esta disponible, queda registrado el motivo de fallback en `ace_step_diagnostics.json` y la UI muestra el dispositivo activo.

## Por Que Sin Docker

Docker Desktop no expuso la iGPU Intel ni la NPU Intel AI Boost al contenedor. En la laptop verificada, Windows detecta Intel Graphics e Intel AI Boost, pero el contenedor no ve `/dev/dri`, `/dev/dxg`, `/dev/accel` ni CUDA. Eso obliga a ACE-Step/PyTorch a correr por CPU dentro de Docker y produjo ejecuciones de mas de 4 horas sin salida final.

La ruta local evita esa capa de virtualizacion y permite probar backends nativos de Windows, Intel XPU, DirectML u OpenVINO mediante providers CLI intercambiables. Docker fue retirado de la ruta operativa del proyecto.

## Ejecucion Local

Requisitos:

- Python 3.11.
- Node.js 20 o superior.
- ffmpeg en `PATH`.
- Git si vas a instalar ACE-Step desde su repositorio.

Preparar:

```powershell
scripts\setup-local.ps1
```

Verificar prerequisitos:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\check-local-prereqs.ps1
```

Verificar Intel XPU:

```powershell
.\.venv\Scripts\python.exe tools\check_xpu_stack.py --probe-tensor
```

El entorno recomendado para Windows/Intel XPU queda fijado en `backend/requirements.txt` y en `backend/requirements-intel-xpu.txt` con `torch==2.9.1+xpu`, `torchvision==0.24.1+xpu`, `torchaudio==2.9.1+xpu` y `transformers==4.53.1`. Mantener esas librerias alineadas evita errores como `torchvision::nms` inexistente, `_torchaudio.pyd` incompatible o imports faltantes como `Dinov2WithRegistersConfig`.

Preparar o reparar dependencias Intel XPU en `.venv`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-intel-xpu-prereqs.ps1 -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-intel-xpu-prereqs.ps1
```

Instalar prerequisitos locales, incluyendo ffmpeg con `winget` y dependencias de audio:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-local-prereqs.ps1 -InstallFfmpeg
```

### Abrir Song AI con doble clic en Windows

Después de la preparación inicial (`scripts\setup-local.ps1`), haz doble clic en `Abrir Song AI.cmd` en la carpeta del proyecto. El lanzador comprueba `.venv` y la interfaz compilada, inicia la aplicación en primer plano y abre el navegador cuando `http://127.0.0.1:8000/` responde. La ventana negra muestra errores de arranque; para detener el servidor, vuelve a ella y pulsa `Ctrl+C`.

Para crear un acceso directo llamado **Song AI** en el escritorio, ejecuta una vez:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\create-desktop-shortcut.ps1
```

El acceso directo apunta a esta instalación, por lo que mover o borrar la carpeta requiere crearlo de nuevo. No es un instalador autónomo: los modelos, Python, dependencias y archivos de trabajo siguen en la carpeta del proyecto. El acceso directo no descarga modelos ni aprueba resultados musicales por sí solo.

Comando principal para ejecutar la aplicacion desde PowerShell:

```powershell
scripts\run-local.ps1 -Port 8000
```

Abrir:

```text
http://127.0.0.1:8000
```

Si ya tienes `.venv`, dependencias y frontend preparados, ese es el unico comando necesario para levantar Song AI en modo local nativo.

Modo desarrollo con Vite:

```powershell
scripts\run-local-dev.ps1
```

Prueba pequena de dos estrofas:

```powershell
.\.venv\Scripts\python.exe tools\run_small_local_song_flow.py --duration 20
```

Prueba completa rapida de todas las fases con provider local controlado:

```powershell
.\.venv\Scripts\python.exe tools\run_small_local_song_flow.py --duration 12 --run-master --fast-full-song-provider
```

Esta prueba crea un set con instrumental, melodia y letra, materializa el proyecto profesional desde SQLite, ejecuta MIDI, Instrumental, Voice, Voice Conversion, Mix, Mastering y Export, y genera `final_song.wav`, `final_song.mp3`, `final_song.flac`, `export_manifest.json` y `project_export.zip` sin invocar ACE-Step pesado.

Cuando `check-local-prereqs.ps1` diga `ready: True`, ejecutar tambien Mastering real con ACE-Step:

```powershell
.\.venv\Scripts\python.exe tools\run_small_local_song_flow.py --duration 20 --run-master
```

Diagnostico ACE-Step verificado:

- La integracion usa `tools/acestep_generate.py` como proceso CLI local que detecta ACE-Step 1.5 y usa `acestep.acestep_v15_pipeline.AceStepHandler`; no usa servicio HTTP.
- El pipeline local Full Song completa los tokens documentados del comando ACE-Step (`python_executable`, rutas de prompt/letra/salida/diagnostico, duracion, modelo, pasos, dispositivo e hilos) y limita la duracion estimada con `SONG_AI_MAX_FULL_SONG_DURATION_SECONDS`.
- Cada corrida guarda `ace_step_diagnostics.json` con prompt completo, letra completa, idioma detectado, secciones, parametros de inferencia, modelo/checkpoint, tipo de salida, recursos RAM/SWAP/CPU/VRAM y error si ocurre.
- Antes de Mastering, Production refresca `song_spec.json` y `lyrics.md` desde SQLite para no usar snapshots viejos. La voz principal de la fase Voice tiene prioridad sobre estilos heredados de drafts, y ACE-Step se bloquea si la letra final sigue siendo mock o contiene placeholders `{...}` sin resolver.
- En Windows nativo la ruta ACE-Step usa Intel XPU/PyTorch: no instala CUDA, no instala `torch==2.7.1+cu128` y no usa `nano-vllm`. `auto` prioriza XPU y evita CUDA en Windows; para validar XPU estrictamente usa `--device xpu --require-device true`.
- El wrapper imprime checks `[OK]`/`[FAIL]` para imports, seleccion de device, backend GPU, carga de pipeline, generacion y salida WAV. Tambien acepta `--check-only` para validar entorno/device sin cargar modelo ni generar audio.
- ACE-Step 1.5 usa `acestep.acestep_v15_pipeline.AceStepHandler`; el wrapper detecta esa API real y ya no depende de la API antigua `acestep.pipeline_ace_step.ACEStepPipeline`.
- La ruta XPU fija variables oficiales: `PYTORCH_DEVICE=xpu`, `SYCL_CACHE_PERSISTENT=1`, `SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1`, `TORCH_COMPILE_BACKEND=eager`, `ACESTEP_CONFIG_PATH=acestep-v15-turbo`, `ACESTEP_LM_BACKEND=pt` y `ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-0.6B`.
- El diagnostico de device imprime `sys.executable`, `torch.__version__`, ruta real de `torch`, `hasattr(torch, "xpu")`, `torch.xpu.is_available()` y `torch.xpu.device_count()` para detectar diferencias entre el entorno manual y el wrapper.
- El wrapper carga `torch`, `torchvision`, ACE-Step y dependencias desde el `.venv` local. Ya no usa `data/provider-cache/python`, porque en Windows nativo una unica fuente de librerias evita mezclar ruedas CPU/XPU. ACE-Step se instala con `--no-deps`; las dependencias puras requeridas para inferencia (`diffusers`, `vector-quantize-pytorch`, `soundfile`, etc.) quedan en requirements sin permitir que ACE-Step reemplace Torch XPU por CUDA.
- En Intel XPU, `soundfile` es dependencia valida para audio I/O cuando `torchcodec` no esta disponible.
- El wrapper imprime checks de entorno para confirmar que el `.venv` activo es el que ejecuta ACE-Step.
- En prueba controlada con `[es]`, ACE-Step conserva acentos y Unicode, pero su tokenizador puede clasificar lineas espanolas de forma mixta (`en`/`es`) y etiquetas como `zh`; revisar `docs/ACE_STEP_DIAGNOSTIC_REPORT.md` antes de ajustar prompts.
- En Docker Desktop no hubo CUDA/iGPU/NPU visible; por eso la ruta principal se movio a local sin Docker.
- Gemma ahora trata el set/proyecto activo y Production como el mismo proyecto del usuario: las fases definen la intencion y Production ejecuta tareas/exportables. Para preguntas de estado como "que sigue" o "estoy en un proyecto activo", responde desde SQLite y los checks de la UI, no desde una suposicion libre del LLM.
- La conversacion inferior usa un layout mas amplio: 60% para respuesta y 40% para escritura. Se retiro la repeticion de nombre/contexto porque esa informacion ya vive en el sidebar.
- Production se prepara automaticamente para el proyecto activo al cargarlo desde Biblioteca. Si falta el registro interno de ejecucion, muestra `Preparar Production`, pero para el usuario sigue siendo el mismo proyecto: definicion por fases primero, ejecucion/exportables despues.
- Biblioteca muestra iconos de estado por proyecto (`set`, Production, exportables, error o archivado), botones con icono para info/archivar/borrar/cargar y una ventana modal de confirmacion antes de borrar. El modal maneja errores y timeout para no quedar bloqueado en `Borrando...`. El borrado elimina el set, fases guardadas, estado UI, eventos relacionados, proyecto Production enlazado y artefactos locales de `data/sets/<set_id>` y `data/projects/<song_id>`; los drafts separados de instrumental, melodia y letra se conservan.
- Al preparar Production desde un set activo, el backend materializa `song_spec.json`, `lyrics.md` y `lyrics_approved.json` desde las fases guardadas en SQLite. Tambien repara automaticamente proyectos de Production enlazados (`user_id=set:<id>`) creados antes de este cambio, asi no vuelve a bloquear `Generar letra` o `Generar plan` con "la especificacion debe estar aprobada" cuando el proyecto ya fue definido en el editor.
- La carga desde Biblioteca rehidrata el proyecto desde SQLite: fases guardadas, formularios del editor, estado visual por fase, datos de Production, exportables, actividad y la ultima fase activa. Si no hay ultima fase, abre la primera fase incompleta.
- La aplicacion arranca en Biblioteca sin proyecto activo cuando no hay `set_id` recordado. El proyecto activo se establece solo al cargar o crear un set; desde ese momento el `set_id` queda en `localStorage` y las fases trabajan sobre ese proyecto hasta cargar o crear otro.
- Al refrescar una ruta como `/lyrics`, la UI restaura automaticamente el ultimo `set_id` activo desde `localStorage` y vuelve a cargar sus fases desde SQLite antes de editar o guardar. Si no hay proyecto recordado, la fase queda sin proyecto activo y el usuario debe cargar o crear uno desde Biblioteca.
- El `ModelOrchestrator` ahora incluye una revision tecnica interna desde snapshot SQLite antes de que Gemma responda estado del proyecto. El backend entrega proyecto, set, assets, fases, estado UI y Production al rol tecnico; la validacion devuelve faltantes/advertencias/siguiente accion y Gemma lo comunica al usuario en lenguaje natural.
- Gemma puede sugerir ajustes sobre el formulario de la fase activa mediante un handoff interno al rol tecnico. El backend devuelve un `phase_patch` con campos permitidos, el frontend lo aplica como cambio sin guardar y el usuario debe presionar Guardar para persistirlo en SQLite.
- En Lyrics, los botones `Mejorar`, `Recrear`, `Expandir`, `Acortar` y `Variantes` llaman al backend para transformar la seccion con Gemma/llama.cpp cuando esta disponible. Si los LLM no estan activos, usan fallback local y lo informan en la actividad.
- El boton `Guardar letra` de Lyrics persiste directamente la fase del proyecto activo en SQLite y no modifica drafts. `Guardar plantilla` es una accion aparte para reutilizar estructuras de letra y no cambia el proyecto activo por si sola.
- `Guardar letra` permanece disponible aunque no haya cambios pendientes; solo se bloquea mientras guarda o cuando no hay proyecto activo. El guardado de fases tiene timeout de 20 segundos para evitar que la UI quede atrapada en estado de guardado.
- El guardado de fases repara mojibake UTF-8 comun antes de persistir texto, por ejemplo `pequeÃ±os` vuelve a `pequeños`, para evitar que letras con tildes y eñes queden dañadas en SQLite o snapshots.
- Production respeta el orden de artefactos: no permite ejecutar MIDI, Instrumental, Voz, Mezcla, Mastering o Export antes de que existan los archivos previos requeridos. Si la fase Music Plan esta guardada en SQLite, el backend puede materializar `music_plan.json`; si no, la accion correcta es `Generar plan`.
- Export genera `project_export.zip` excluyendo zips/manifests exportados previamente para evitar crecimiento recursivo del ZIP y esperas largas al actualizar exportables.
- La ruta de set/sample/cancion valida que los IDs de instrumental, melodia y letra existan, correspondan a su tipo y conserven manifest, intent y contenido. El sample toma el set mas reciente desde SQLite; un sample cuyo set fue eliminado ya no puede producir una cancion completa. La prueba de disponibilidad de mezcla/export se ajusta al `ffmpeg` presente en cada entorno.
- Samples y canciones del flujo legado se registran ahora en `legacy_samples` y `legacy_songs`. SQLite decide cual es el registro vigente, los snapshots `sample.json`/`song.json` se regeneran si faltan y la migracion de archivos antiguos es idempotente.
- Las descargas desde la UI se resuelven por el `song_id` de Production o el `set_id` del proyecto local activo. La ruta global `latest` se conserva para consumidores que soliciten expresamente el ultimo export, pero ya no es el fallback de un proyecto abierto.
- El frontend separa el cliente HTTP comun en `api_client.js` y las acciones de Production en `production_actions.js`: preparacion del proyecto, ejecucion de fases, polling de generacion local y descargas mantienen la misma interfaz Vue con menor acoplamiento en `app.js`.
- Production queda mas compacto: el bloque redundante de proyecto activo se oculta, los datos resumidos duplicados bajo el orden logico se retiran visualmente y Actividad pasa a un panel plegable junto a Diagnostico de recursos e Infraestructura local.
- Production ya no restaura `exportManifest` desde el estado guardado de la fase; los exportables y el mensaje de calidad se leen del endpoint actual de Export para evitar avisos obsoletos como "falta vocals.wav" despues de generar con Full Song.
- Production ya no toma el primer proyecto profesional como fallback cuando no hay `set_id` activo; sin proyecto cargado muestra `Sin proyecto activo`, y al cargar un set solo acepta exportables del proyecto Production enlazado a `user_id=set:<id>`.
- El puente de Production es idempotente: listar proyectos ya no vuelve a crear eventos de preparacion si `song_spec.json`/spec aprobada existen. La actividad de Production tambien colapsa mensajes duplicados historicos para que se vea el estado real sin ruido.
- La fase actual de Production muestra `Listo para ejecutar` cuando el backend esta en `ready`; solo muestra `En curso` si el estado real del proyecto indica ejecucion o carga activa.
- Las acciones de Production bloquean doble click mientras ejecutan y muestran `Generando...` de inmediato. SQLite usa `busy_timeout` y WAL en repositorios activos para reducir bloqueos durante generaciones largas.
- `Generar voz` ahora registra etapas detalladas: prompt vocal preparado, provider seleccionado, si usa ACE-Step o no, recursos, inicio de comando/inferencia, progreso periodico y resultado. La tarjeta de Production muestra el ultimo mensaje tecnico de cada fase con actor y hora.
- `Masterizar` con ACE-Step marca el proyecto como `MASTERING/running`, registra inicio de proceso local, progreso periodico con tiempo/RAM/SWAP/CPU y fallo si ocurre. Production refresca eventos junto con recursos, muestra hora de inicio y tiempo transcurrido, y el diagnostico ahora muestra `swap libre / total` para detectar configuraciones de 2 GB frente a los 4 GB recomendados.
- Los timeouts de ACE-Step ahora terminan el grupo completo del proceso local para evitar que `acestep_generate.py` quede huérfano consumiendo CPU/RAM despues de fallar la fase.
- El timeout local de ACE-Step subio a 14400 segundos y la duracion maxima enviada al provider queda configurable con `SONG_AI_MAX_FULL_SONG_DURATION_SECONDS` para evitar limites ocultos en codigo.
- Production muestra antes de generar la duracion enviada a ACE-Step, el limite configurado de cancion, el timeout maximo y un estimado de tiempo de Mastering segun el runtime local. Si el estimado supera el timeout o la duracion se recorta por limite, la UI lo advierte para que el usuario pueda quitar secciones o reducir duracion.
- Production muestra provider activo, dispositivo activo, runtime y tiempo transcurrido. Los eventos de Mastering registran si ACE-Step uso XPU/CUDA/CPU o si hizo fallback.
- Si la app local se reinicia mientras una fase esta `running`, el arranque marca esa fase como interrumpida en SQLite. La UI toma el ultimo evento real de cada fase, asi no muestra `En curso` por eventos antiguos cuando ACE-Step ya no esta corriendo.
- Limpieza post-Docker: se retiraron los archivos `Dockerfile`, `docker-compose*.yml`, `.dockerignore` y el helper de contenedores LLM. El monitor de recursos usa `visible_memory_limit_mb` para describir memoria visible sin terminologia Docker y migra snapshots antiguos de SQLite de forma compatible.
- Smoke completo local: `tools/run_small_local_song_flow.py` incluye `--fast-full-song-provider` para validar todas las fases y exportables con un provider local rapido, sin instalar dependencias ni modificar `.env`.
- Steering de runtime documentado: `docs/RUNTIME_DEPLOYMENT_STRATEGY.md` define una guia reutilizable para elegir Docker, nativo o hibrido al inicio de futuros proyectos. Aplicado a Song-AI, confirma `local_hardware` y no reintroduce Docker como ruta operativa.
- Flujo de informacion por fases documentado e implementado: `docs/PHASE_INFORMATION_FLOW.md` define SQLite como fuente de verdad, archivos como artefactos derivados, estados separados de fase/ejecucion/artefacto, eventos importantes por fase, verificacion por checksum y regeneracion puntual cuando el builder/provider lo permite.
- Integracion Intel XPU para ACE-Step: `docs/ACE_STEP_INTEL_XPU_REPORT.md` documenta compatibilidad, prerequisitos, validacion y fallback. `tools/check_xpu_stack.py` verifica `torch.xpu`, `scripts/install-intel-xpu-prereqs.ps1` expresa los prerequisitos instalables, y Song-AI intenta `--device auto` sin recortar duracion/calidad.

## Arquitectura

### Roles IA

Gemma es la unica interfaz conversacional visible para el usuario. Interpreta la intencion creativa, ayuda con letra, tema, emocion, estilo y narrativa.

Qwen es interno. Actua como director tecnico: valida especificacion, revisa letra, estructura plan musical, decide fases y coordina requisitos del pipeline. El usuario no conversa directamente con Qwen.

La guia de Gemma prioriza el proyecto profesional activo. Solo menciona `sample/checkpoint` cuando no existe proyecto profesional y se esta usando el flujo legado de set.

En la charla con Gemma, la app intenta usar llama.cpp automaticamente. Si los servicios o modelos todavia no estan listos, el fallback local explica la causa real, responde con la siguiente fase profesional pendiente y evita presentar `sample/checkpoint` o `cancion completa` como requisitos del flujo principal.

Flujo conceptual:

```text
Usuario -> Gemma -> Qwen -> Gemma -> Usuario
```

Estado esperado local:

- Gemma puede correr como provider creativo en `localhost:8081`.
- Qwen puede correr como provider tecnico en `localhost:8082`.
- El endpoint de Gemma registra un handoff tecnico interno con `provider_handoff` cuando Qwen responde.
- Qwen usa respuestas cortas y `/no_think` para evitar bloqueos largos por razonamiento interno en CPU.
- Si Qwen no responde, el handoff queda persistido como fallback local y conserva la causa del error.

### Backend

- FastAPI sirve API y frontend compilado.
- SQLite es la fuente activa de trabajo.
- JSON, Markdown, MIDI y audio son snapshots o artefactos regenerables.
- Los providers son intercambiables: local, full-song, stems y futuros pro.
- Los modelos se cargan por fase; no se deben cargar todos al mismo tiempo.

### Frontend

La UI usa una experiencia tipo estudio musical:

- sidebar persistente,
- workspace central,
- footer global de Gemma,
- dark mode,
- paginas por fase creativa.

Rutas principales:

```text
/library
/intent
/lyrics
/music-plan
/midi
/instrumental
/voice
/production
```

## Flujo Profesional

Las fases actuales del pipeline son:

1. `SONG_SPEC_COLLECTION`
2. `LYRICS_GENERATION`
3. `LYRICS_TECHNICAL_REVIEW`
4. `MUSIC_PLAN_GENERATION`
5. `MIDI_GENERATION`
6. `INSTRUMENTAL_GENERATION`
7. `VOCAL_SYNTHESIS`
8. `VOICE_CONVERSION`
9. `MIXING`
10. `MASTERING`
11. `EXPORT`

La ruta recomendada para cancion final es:

```text
Intent -> Lyrics -> Music Plan -> MIDI -> Mastering con Full Song -> Export
```

Cuando `SONG_AI_FULL_SONG_COMMAND` esta configurado, Mastering usa ACE-Step y genera:

```text
final_song.wav
final_song.mp3
final_song.flac
```

La ruta por stems sigue disponible para integraciones futuras:

```text
Instrumental -> Vocals -> Voice Conversion -> Mix -> Mastering -> Export
```

Si `vocals.wav` viene de `procedural_vocal_guide`, se trata como preview tecnico y no como voz real.

## Persistencia

Directorios locales:

```text
data/                   SQLite, proyectos, letras, MIDI, audio y exports
data/models             modelos locales: llm, music, voice, stems, huggingface
data/providers          repos/adaptadores locales
```

Estructura relevante dentro de `data/`:

```text
projects/<song_id>/
  song_spec.json
  lyrics.json
  lyrics.md
  lyrics_approved.json
  music_plan.json
  song_base.mid
  midi_metadata.json
  instrumental.wav
  vocals.wav
  mix.wav
  final_song.wav
  final_song.mp3
  final_song.flac
  export_manifest.json
  project_export.zip
```

SQLite guarda:

- proyectos,
- eventos,
- artefactos,
- especificacion,
- ejecuciones/model runs,
- rutas JSON indexadas,
- datos persistidos de formularios por fase (`project_phase_data`),
- eventos historicos de fase (`project_phase_events`),
- metadata verificable de artefactos (`project_artifacts`).

## Flujo De Informacion Por Fases

Song AI funciona como un estudio persistente. El usuario puede diligenciar formularios por fases, guardar avance, cerrar la app y volver al proyecto con los controles hidratados desde SQLite.

Reglas principales:

- SQLite es la fuente de verdad del trabajo activo.
- Los archivos `json`, `md`, `mid`, `wav`, `mp3`, `flac` y `zip` son artefactos derivados.
- Guardar una fase solo persiste configuracion; no ejecuta MIDI, audio, ACE-Step ni export.
- Production concentra la ejecucion pesada y los exportables.
- Las sugerencias de IA quedan como `DRAFT` con `change_source=AI` o `MIXED`; el usuario debe presionar Guardar para pasar la fase a `COMPLETED`.
- El backend registra eventos importantes como `PHASE_SAVED`, `AI_SUGGESTED`, `ARTIFACT_GENERATED`, `ARTIFACT_MISSING` y `ARTIFACT_CORRUPTED`.
- Todo artefacto descargable se verifica contra SQLite antes de descargar.
- Si un archivo derivado falta o se corrompe, el sistema lo marca y puede regenerarlo cuando existan datos, parametros y provider suficientes.

Referencia completa: `docs/PHASE_INFORMATION_FLOW.md`.

## Aceleracion Local

Hardware verificado en la laptop de desarrollo:

- CPU: Intel Core Ultra 5 125U, 12 nucleos / 14 hilos logicos.
- iGPU: Intel Graphics integrada.
- NPU: Intel AI Boost.
- La iGPU puede usarse por PyTorch XPU si el driver Intel y las ruedas `torch` XPU estan instaladas.
- La NPU Intel AI Boost no queda cubierta por ACE-Step/PyTorch XPU; se mantiene como futura ruta OpenVINO/DirectML si aparece provider compatible.

Nota de rendimiento: ACE-Step en CPU es funcional pero extremadamente lento. En una prueba real con virtualizacion, 60 segundos con 10 pasos no completo en 3600 segundos. Por eso el comando local usa `{duration_seconds}` y pocos `--oss-steps` para validar flujo en CPU; para calidad final usa un provider acelerado y mas pasos.

Verificacion actual: el flujo completo `tools/run_small_local_song_flow.py --duration 20 --run-master` paso por SQLite y Production con `requested_device=xpu`, `active_device=xpu`, `backend_active=xpu`, CPU offload controlado, Mastering por ACE-Step y exportacion final a `final_song.wav`, `final_song.mp3`, `final_song.flac`, `export_manifest.json` y `project_export.zip`.

## Variables Principales

Archivo base:

```text
.env.example
```

Full Song local con ACE-Step:

```text
SONG_AI_MODEL_ROOT=data/models
SONG_AI_PROVIDER_ROOT=data/providers
SONG_AI_ACE_DEVICE=auto
SONG_AI_REQUIRE_ACE_DEVICE=false
PYTORCH_DEVICE=xpu
SYCL_CACHE_PERSISTENT=1
SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
TORCH_COMPILE_BACKEND=eager
ACESTEP_CONFIG_PATH=acestep-v15-turbo
ACESTEP_LM_BACKEND=pt
ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-0.6B
ACESTEP_INIT_LLM=false
SONG_AI_FULL_SONG_COMMAND={python_executable} tools/acestep_generate.py --prompt {prompt_path} --lyrics {lyrics_path} --output {output_path} --checkpoint-path {checkpoint_root} --config-path {config_path} --duration {duration_seconds} --infer-step {infer_steps} --oss-steps 16,96,172,200 --device {device} --cpu-offload true --overlapped-decode true --torch-threads {threads} --torch-interop-threads 4 --diagnostics {diagnostics_path} --output-type full_song_with_vocals
SONG_AI_INSTALL_ACE_STEP=true
SONG_AI_ALLOW_CPU_FULL_SONG=true
SONG_AI_LOCAL_COMMAND_TIMEOUT_SECONDS=14400
SONG_AI_MAX_FULL_SONG_DURATION_SECONDS=360
```

Tokens del comando full-song: `{python_executable}`, `{model_type}`, `{infer_steps}`, `{threads}`, `{device}`, `{checkpoint_root}` y `{config_path}` se resuelven por perfil ACE-Step 1.5. Turbo usa `2b-turbo`, 8 pasos, 4 hilos, `xpu` y config `acestep-v15-turbo`; Base usa `2b-base`, 32 pasos, 14 hilos, `cpu` y config `acestep-v15-base`. Ambos comparten raíz `data/models/music/acestep-1.5-2b-turbo`. Las plantillas históricas del wrapper con raíz derivada de `{model_type}` se normalizan antes de ejecutar y reciben config explícita. Una config explícita personalizada se conserva. La selección del perfil no demuestra carga ni calidad de audio.

Rutas alternativas por stems:

```text
SONG_AI_SOUNDTRACK_COMMAND=
SONG_AI_SINGING_VOICE_COMMAND=
SONG_AI_VOICE_CONVERSION_COMMAND=
```

Si Full Song funciona, esas tres pueden quedar vacias.

Servidor ACE-Step REST XPU opcional:

```powershell
scripts\start-acestep-api-xpu.bat
```

Este launcher usa `.venv`, `acestep-v15-turbo`, backend LM `pt` y LM pequeno `acestep-5Hz-lm-0.6B`. Es una ruta de prueba para aislar ACE-Step como proceso REST antes de conectar un cliente Song-AI dedicado.

## Modelos LLM Locales

Gemma y Qwen estan preparados para llama.cpp, pero no son obligatorios para que ACE-Step genere audio final. Si llama.cpp no esta activo, la app usa guia local.

Rutas persistentes:

```text
SONG_AI_GEMMA_GGUF_PATH=data/models/llm/gemma/gemma.gguf
SONG_AI_QWEN_GGUF_PATH=data/models/llm/qwen/qwen.gguf
```

URLs opcionales de descarga:

```text
SONG_AI_GEMMA_GGUF_URL=https://huggingface.co/second-state/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf
SONG_AI_QWEN_GGUF_URL=https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf
```

Endpoints por rol:

```text
SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL=http://localhost:8081
SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL=http://localhost:8082
SONG_AI_LLAMA_CPP_TIMEOUT_SECONDS=240
SONG_AI_LLAMA_CPP_INTERPRETER_N_PREDICT=160
SONG_AI_LLAMA_CPP_TECHNICAL_N_PREDICT=96
SONG_AI_LLAMA_SERVER_COMMAND=llama-server
SONG_AI_LLAMA_CPP_CTX_SIZE=4096
SONG_AI_LLAMA_CPP_GPU_ARGS=--n-gpu-layers 999
```

Song AI gestiona llama.cpp automaticamente en local:

- Al iniciar la app, `scripts/run-local.ps1` configura los comandos de arranque/parada.
- En `startup`, FastAPI ejecuta `scripts/start-local-llms.ps1`.
- Gemma arranca en `8081` y Qwen en `8082`.
- El arranque usa `--n-gpu-layers 999` por defecto para intentar offload GPU si el binario `llama-server` lo soporta.
- Antes de ACE-Step o voz pesada, `ResourceMonitor` ejecuta `scripts/stop-local-llms.ps1` para liberar RAM/VRAM compartida.
- Al terminar ACE-Step, `ResourceMonitor` vuelve a ejecutar `scripts/start-local-llms.ps1`.
- Al cerrar la app local, `scripts/run-local.ps1` detiene los LLM para no dejar procesos huerfanos.

Variables utiles:

```powershell
SONG_AI_LLM_AUTOSTART=true
SONG_AI_STOP_LLM_ON_EXIT=true
SONG_AI_START_LLM_COMMAND=powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\start-local-llms.ps1"
SONG_AI_STOP_LLM_COMMAND=powershell.exe -NoProfile -ExecutionPolicy Bypass -File "scripts\stop-local-llms.ps1"
```

Para instalar `llama-server` con aceleracion GPU en Windows/Intel iGPU, la ruta recomendada inicial es Vulkan porque los releases oficiales de llama.cpp publican binarios Windows x64 Vulkan con `llama-server.exe`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-llama-cpp-gpu.ps1 -Backend vulkan
```

Ese instalador descarga desde los releases oficiales de `ggml-org/llama.cpp`, extrae en `data/tools/llama.cpp`, configura `.env` con `SONG_AI_LLAMA_SERVER_COMMAND` y deja `SONG_AI_LLAMA_CPP_GPU_ARGS=--n-gpu-layers 999`.

SYCL/oneAPI tambien puede aprovechar GPUs Intel y es la ruta mas especifica de Intel, pero los releases Windows SYCL pueden estar deshabilitados en algunas versiones. Si quieres probarla:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\install-llama-cpp-gpu.ps1 -Backend sycl
```

Si no hay asset SYCL disponible, usa Vulkan o compila llama.cpp con oneAPI siguiendo la documentacion oficial.

La NPU Intel AI Boost no queda configurada para llama.cpp en esta ruta. A fecha actual, la ruta estable para `llama-server` local en este proyecto es iGPU por Vulkan o SYCL; NPU queda como investigacion futura mediante OpenVINO/NPU u otros runtimes especificos.

Si el `llama-server` instalado no fue compilado con backend GPU compatible, `--n-gpu-layers 999` no acelerara o puede fallar. Para Intel iGPU en Windows se recomienda un build de llama.cpp con Vulkan o SYCL/oneAPI. Si falla el arranque GPU, ajusta `SONG_AI_LLAMA_CPP_GPU_ARGS` o dejalo vacio para CPU.

No hay que activar Gemma/Qwen con una variable adicional: Song AI intenta levantarlos automaticamente. Si no responden, falta `llama-server` en PATH o faltan los `.gguf`, conserva guia local.

Si el estado indica que faltan modelos, `Preparar/reiniciar` o `Actualizar dependencias` descargan los GGUF cuando esas URLs estan configuradas. Los botones `Recrear Gemma` y `Recrear Qwen` eliminan el peso existente y lo vuelven a descargar en `data/models/llm`.

```text
POST /api/system/models/gemma/refresh
POST /api/system/models/qwen/refresh
```

Tambien puedes colocar manualmente los archivos en:

```text
data/models/llm/gemma/gemma.gguf
data/models/llm/qwen/qwen.gguf
```

## Bootstrap

El bootstrap corre localmente y prepara `data/`:

- crea directorios de modelos,
- instala dependencias Python en el `.venv` local,
- instala ACE-Step si esta activado, usando `--no-deps` para no reemplazar el stack `torch==2.9.1+xpu`,
- descarga modelos por URL si se configuran,
- clona providers si se configuran.

Variables:

```text
SONG_AI_BOOTSTRAP_ON_START=true
SONG_AI_INSTALL_LOCAL_AUDIO_DEPS=true
SONG_AI_INSTALL_ACE_STEP=true
SONG_AI_BOOTSTRAP_UPGRADE=false
SONG_AI_PROVIDER_REPOS=
```

Actualizar dependencias internas bajo demanda:

```text
POST /api/system/bootstrap/upgrade
```

La politica por defecto evita reinstalar paquetes pesados si ya son importables y hay marcador compatible en `data/.bootstrap`.

## ResourceMonitor

Song AI mide recursos del proceso local antes, durante y despues de audio pesado como ACE-Step o providers de voz cantada. Los snapshots se guardan en SQLite en `resource_snapshots` y la UI de Production muestra RAM, CPU, disco, decision y recomendaciones.

Variables:

```text
SONG_AI_RESOURCE_MONITOR_ENABLED=true
SONG_AI_RESOURCE_SAMPLE_SECONDS=2
SONG_AI_MIN_FREE_RAM_MB_FOR_AUDIO=3500
SONG_AI_MIN_FREE_DISK_MB_FOR_AUDIO=15000
SONG_AI_MAX_CPU_PERCENT_BEFORE_AUDIO=85
SONG_AI_AUDIO_START_DELAY_SECONDS=45
SONG_AI_RELEASE_LLM_BEFORE_AUDIO=true
SONG_AI_STOP_LLM_COMMAND=
SONG_AI_START_LLM_COMMAND=
```

Endpoints:

```text
GET  /api/resources/status
GET  /api/resources/history
POST /api/resources/check-audio-readiness
```

Antes de ejecutar `SONG_AI_FULL_SONG_COMMAND` o `SONG_AI_SINGING_VOICE_COMMAND`, el backend registra `before_audio`, opcionalmente ejecuta `SONG_AI_STOP_LLM_COMMAND`, espera `SONG_AI_AUDIO_START_DELAY_SECONDS`, registra `after_llm_release` y muestra RAM, CPU, swap, disco y memoria visible como diagnostico. RAM/CPU/swap son advertencias, no bloqueos preventivos. La generacion solo se detiene por errores reales: dependencia obligatoria faltante, archivo de entrada ausente, ruta/permisos invalidos o error del provider.

En local, `SONG_AI_STOP_LLM_COMMAND` y `SONG_AI_START_LLM_COMMAND` quedan vacios por defecto. Si usas servidores llama.cpp propios, puedes poner scripts locales para detenerlos antes de ACE-Step y restaurarlos al terminar.

Nota de sprint: en la ruta Intel XPU se evita `torchcodec`; ACE-Step devuelve tensores de audio y el wrapper guarda WAV con `soundfile`. La app usa el `.venv` local como fuente unica de librerias para evitar mezclar Torch CPU/XPU.

UX ResourceMonitor: Production incluye refresco manual, revision explicita de recursos, auto-actualizacion cada 10 segundos mientras la vista esta activa, timestamp de ultima lectura e historial compacto con RAM, swap y CPU.

UX Infraestructura local: Production muestra un resumen limpio con modelos de texto, audio local, almacenamiento local y preparacion. Los componentes tecnicos y acciones de recreacion quedan en modo avanzado.

UX Production: la vista principal se ordena como Proyecto activo -> Orden logico -> Exportables. Recursos e infraestructura quedan como diagnosticos colapsables para no distraer del flujo de generacion.

UX Production alcance: crear proyectos y cambiar el proyecto activo pertenece a Biblioteca. Production solo permite editar la descripcion del proyecto activo y cerrar el pipeline con generacion/exportables.

Sprint flujo por fases: Intent, Lyrics, Music Plan, MIDI, Instrumental y Voice tienen guardado explicito por fase en SQLite (`project_phase_data`). Guardar solo persiste configuracion; no ejecuta ACE-Step, MIDI, audio ni exportables. La actividad, logs y botones de ejecucion quedan concentrados en Production.

UX sidebar: la barra lateral usa `--sidebar-width: 300px` para dar mas aire a proyecto activo y fases, y el footer de Gemma se alinea con ese ancho.

UX sidebar compacto: el proyecto activo se muestra en una sola linea con prefijo `>` para reducir espacio vertical sin perder contexto.

UX procesos: las tarjetas de Production muestran estado visual por fase de ejecucion (`pendiente`, `en curso`, `generado` o `error`). El estado se calcula desde la fase actual del proyecto profesional y los artefactos exportados, para que el usuario vea que procesos ya produjeron resultados.

UX design system: se agrego `docs/DESIGN_SYSTEM.md` como referencia visual del producto. Production muestra procesos como una lista ordenada con nombre humano, resumen corto, badge de estado y accion, evitando codigos tecnicos visibles como contenido principal.

Swap recomendado en Linux: no bloquea la generacion, pero mejora estabilidad con ACE-Step. Ejemplo:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Si decides usar WSL2 para pruebas locales, la swap se define fuera del repo en `C:\Users\<usuario>\.wslconfig`:

```ini
[wsl2]
memory=8GB
swap=4GB
```

Despues de cambiarlo hay que ejecutar `wsl --shutdown` y volver a abrir la terminal.

## Como Generar Una Cancion

1. Abre `http://localhost:8000`.
2. Ve a `Library` y crea o carga un proyecto.
3. En `Intent`, define la idea musical.
4. En `Lyrics`, edita o genera letra por secciones.
5. En `Music Plan`, define BPM, tonalidad, estructura e instrumentos.
6. En `MIDI`, genera la base editable.
7. En `Production`, ejecuta Mastering/Full Song.
8. Ejecuta Export.
9. Descarga MP3/WAV/FLAC si el control de calidad lo permite.

Para cancion final real, el camino mas directo es que Production use ACE-Step en Mastering mediante `SONG_AI_FULL_SONG_COMMAND`.

## Control De Calidad Vocal

La app distingue tres casos:

```text
full_song_provider        final permitido
local_command vocals.wav  final permitido
procedural_vocal_guide    preview, final bloqueado
```

Si `vocals.wav` es procedural:

- se puede escuchar como guia,
- no se ofrece como cancion final,
- MP3/WAV/FLAC finales quedan sin descarga,
- Export devuelve un mensaje claro.

## Endpoints Utiles

Estado:

```text
GET /api/system/status
GET /api/local-pipeline/status
GET /api/studio/status
GET /api/models/status
GET /api/providers
GET /api/resources/status
GET /api/resources/history
```

Proyecto profesional:

```text
GET  /api/pro/projects
POST /api/pro/projects
POST /api/pro/projects/{song_id}/spec/messages
POST /api/pro/projects/{song_id}/lyrics
POST /api/pro/projects/{song_id}/lyrics/review
POST /api/pro/projects/{song_id}/music-plan
POST /api/pro/projects/{song_id}/midi
POST /api/pro/projects/{song_id}/instrumental
POST /api/pro/projects/{song_id}/vocals
POST /api/pro/projects/{song_id}/voice-conversion
POST /api/pro/projects/{song_id}/mix
POST /api/pro/projects/{song_id}/master
POST /api/pro/projects/{song_id}/export
GET  /api/pro/projects/{song_id}/artifacts/{artifact_type}/download
```

Bootstrap:

```text
POST /api/system/bootstrap/restart
POST /api/system/bootstrap/upgrade
```

## Scripts

```text
tools/acestep_generate.py
tools/musicgen_generate.py
tools/singing_voice_generate.py
tools/use_audio_file.py
tools/check_local_audio_stack.py
```

`tools/acestep_generate.py` es la ruta recomendada para cancion local completa.

`tools/use_audio_file.py` sirve para pruebas o para integrar archivos generados externamente.

## Verificacion

Backend:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m compileall backend tests
```

Ultima verificacion del handoff: 47 pruebas pasaron. Para ejecutar la suite sin detener o reiniciar Gemma/Qwen durante las pruebas de audio, usar temporalmente `SONG_AI_RESOURCE_MONITOR_ENABLED=false`.

Frontend:

```powershell
cd frontend
npm.cmd run build
```

Estado local:

```powershell
scripts\run-local.ps1 -Port 8000
python -c "import sys; sys.path.insert(0, 'backend'); from config.settings import Settings; from audio.local_song_pipeline import LocalSongPipeline; s=Settings.load(); print(LocalSongPipeline(s.local_models).status())"
```

## Limitaciones Actuales

- La voz real depende de que ACE-Step ejecute correctamente en el entorno local.
- Con CPU, ACE-Step puede tardar mucho.
- Con iGPU/NPU, hace falta un provider nativo compatible con Windows, Intel XPU, DirectML u OpenVINO; PyTorch/ACE-Step no usa la NPU automaticamente.
- Gemma/Qwen reales requieren modelos GGUF y servidores llama.cpp activos.
- La ruta por stems separados sigue preparada, pero la ruta final recomendada es Full Song.

## Estado Del Repositorio

Repositorio remoto:

```text
https://github.com/jporras/song-ai
```

Rama principal:

```text
main
```

## Reglas De Mantenimiento

- SQLite es la fuente activa.
- JSON y audio son artefactos/snapshots.
- No confundir maqueta tecnica con cancion final.
- No exponer Qwen como chat del usuario.
- Conservar instrumental, melodia y letra como assets separados cuando se use ruta por stems.
- Actualizar este README cuando cambie arquitectura, flujo o configuracion.

Las propuestas de continuidad y sus criterios de aceptacion estan en `docs/HANDOFF_5_5_SOL.md`.

### Auditoria de uso con Playwright MCP — 2026-10-02

Se reviso la UI con bases temporales y sin generacion real. El [handoff de Playwright](docs/HANDOFF_PLAYWRIGHT_2026-10-02.md), ampliado el 2026-10-03, conserva los diez hallazgos originales y registra sus correcciones y pruebas posteriores. La revision de experiencia para principiantes de arriba es un planning nuevo y sigue pendiente de implementacion.
# Planificación del estudio editable — 2026-10-04

Se creó [el plan AI Music Studio S00–S18](docs/AI_MUSIC_STUDIO_SPRINT_PLAN.md) a partir de los requerimientos funcionales, arquitectura ACE-Step/DSP/DAW, aprendizaje universal y copilot bidireccional. Contiene auditoría estática del código, brechas de sample y capacidades, contratos de estado/tools/propuestas, dependencias y criterios de aceptación. Prioriza un flujo completo de tempo con confirmación, audio real y undo antes de ampliar herramientas. Esta entrega es documental: no implementa los nuevos motores ni acredita capacidades instaladas, calidad audible o usabilidad.

El plan incorpora reglas explícitas de arquitectura hexagonal, SOLID y DRY: puertos por capacidad, inyección y composición, políticas/esquemas compartidos y verificaciones por sprint. Identifica las abstracciones actuales y los acoplamientos de las fachadas para evolucionarlos incrementalmente conservando API, datos y menú.

Decisión de alcance: servicios pagos y la propuesta histórica ProfessionalSongService quedan en pausa, conservando su código para una posible retomada. ProviderRegistry ya desactiva el modo pago. La clase todavía sostiene parte de Production local, ficha, generación y exportación; el plan prevé trasladar esas responsabilidades a casos de uso locales antes de desconectarla. Los nuevos desarrollos no ampliarán esa fachada histórica. Este ajuste es documental y no desactiva las operaciones locales que hoy dependen de ella.

S00 en progreso: registro de capacidades independiente y auditor reproducible mediante `python scripts/audit_studio.py --output docs/STUDIO_CAPABILITY_AUDIT.json`. Inspecciona paquetes del intérprete usado, archivos Gemma/Qwen, tareas expuestas por el wrapper, endpoints e imports/consumidores históricos sin ejecutar motores ni descargar modelos. Configuración y presencia de archivos no equivalen a capacidad verificada. Tres pruebas de contrato del registro aprobadas; faltan probes de runtime/hardware y la matriz completa control→motor para cerrar S00.

Ampliación S00: `--probe-runtime` añade detección torch aislada y health de servidores loopback sin generación. Se auditó con `.venv`: ACE-Step 1.5.0/PyTorch 2.9.1+xpu y una Intel Graphics detectada; Gemma/Qwen no respondieron en los endpoints configurados. Se añadieron inventario de bindings UI, configs/checksums de checkpoints y diagnósticos históricos sanitizados. [La matriz comentada](docs/STUDIO_CAPABILITY_AUDIT.md) distingue controles de configuración y motores audibles. Seis pruebas aprobadas; S00 sigue en progreso y no acredita inferencia ni calidad musical.

S00 añade comparación estática de firmas ACE-Step instaladas, trazas candidatas por parámetro y probe aislado de import (--probe-api-import). Los argumentos actuales coinciden con las firmas, pero el wrapper todavía no envía BPM/key/compás/idioma como parámetros estructurados. Se registraron brechas de piano roll, capas y sincronización del plan en la matriz; nueve pruebas de auditoría/registro aprobadas. Los probes distinguen importación de ejecución, y las lecturas candidatas no acreditan efecto audible.

Continuación S00: el probe con `.venv` confirmó la importación de AceStepHandler 1.5 en 29,53 segundos. Se separan timeout, error y payload inválido mediante un adaptador y un proceso acotado; once pruebas de auditoría/registro aprobadas. No se cargaron pesos ni se generó audio. La matriz registra también la discrepancia entre perfiles históricos y resolución de configuración 1.5, pendiente de corregir en S06. S00 sigue en progreso por la trazabilidad completa y el checkpoint efectivo.

S00 amplía el reporte con defaults y alternativas de configuración ACE-Step extraídos por AST, sin ejecutar el wrapper, y completa el inventario de imports directos y relativos. Trece pruebas aprobadas; configuración y checkpoint efectivos siguen pendientes de una ejecución diagnosticada.

Corrección preparatoria S01: Gemma recuerda las tres piezas y exige set válido y sample vigente escuchado/aprobado antes de la canción completa, tanto con set activo como durante la preparación. Se eliminó la instrucción contradictoria que omitía el sample y se distingue mock de producción real. Quince pruebas aprobadas en la verificación conjunta, incluidas dos regresiones de guía. La cobertura de gates en todas las rutas finales sigue pendiente; ProfessionalSongService se conserva sin ampliar.

S01 en progreso: `SampleGate` centraliza validación de set, tres assets, pertenencia, aprobación y huella vigente mediante un puerto pequeño. El builder mock reutiliza la política. La fachada histórica delega su validación y el servicio full-song directo también la exige: proyectos sin set y checkpoints mock ya no habilitan producción real. **La producción real queda bloqueada hasta implementar y verificar el sample real representativo**; no se acepta una etiqueta de provider como prueba de audio. Se conserva el recorrido mock. Falta evidencia de artefacto/checksum, revisión de spec/provider, huella semántica y validación de todas las rutas de mastering/export.

Verificación S01: siete pruebas específicas aprobadas, incluida llamada directa bloqueada antes de crear artefactos. La ejecución ampliada terminó con 57 pruebas, cinco omitidas y un fallo de texto de error; se corrigió conservando mensajes accionables por causa. La regresión afectada se volvió a ejecutar con las siete pruebas específicas: ocho aprobadas. No se presenta esa ejecución ampliada como aprobada.
Verificación posterior: suite completa de sets más política y guía, 16 pruebas aprobadas en 8,94 segundos. Compilación de módulos modificados y revisión de diferencias correctas.

Continuación S01: mastering y exportación directos verifican `SampleGate` antes de escribir archivos, registrar artefactos o avanzar fase. Descargas WAV/MP3/FLAC/ZIP finales también exigen el sample; la consulta de exportación recalcula disponibilidad desde el proyecto activo y no usa la calidad de un manifiesto antiguo como autorización. Los snapshots existentes no se modifican al consultar. Veinte pruebas de sets, política y guía aprobadas en 8,79 segundos; compilación y revisión de diferencias correctas. Sigue pendiente implementar el sample real representativo y su evidencia, la huella semántica y la revisión de spec/provider. Producción y descarga final reales permanecen bloqueadas hasta cumplir ese contrato.

S01 añade huella versión 2: toma contenido de fases sin fechas, estados ni metadatos de persistencia; excluye campos conocidos de navegación de Production, entrada transitoria de inspiración y ruta del editor de letra. Conserva parámetros musicales y campos desconocidos. Las aprobaciones calculadas con la versión anterior requieren regenerar sample y aprobarlo. Los archivos de assets todavía se verifican íntegramente; falta completar la huella semántica de assets y vincular revisión de spec/provider. No se habilita producción real con este cambio.
Verificación: 24 pruebas aprobadas en 9,26 segundos, incluida integración SQLite que conserva la huella al guardar los mismos datos o progreso y la cambia al modificar BPM; compilación Python y revisión de diferencias correctas.

Continuación S01: huella versión 3 incorpora contenido y schema de las fichas técnicas persistidas de proyectos vinculados al set. Cambiar requisitos o un provider guardado en la ficha invalida el sample; confirmar el mismo contenido no lo invalida. Fichas de otros sets no afectan su vigencia. Se incluyen conservadoramente todas las fichas vinculadas hasta definir selección explícita por render. Las aprobaciones con huellas anteriores requieren regeneración. Sigue pendiente vincular artefacto real/checksum y perfil/configuración efectivos elegidos al ejecutar; la producción real permanece bloqueada.
Verificación: 25 pruebas aprobadas en 10,57 segundos; integración SQLite cubre confirmación sin cambio, aislamiento entre sets y cambio de provider persistido. Compilación y revisión de diferencias correctas.

S01 añade registro interno de evidencia WAV para samples: carpeta aislada, PCM legible, frames completos, duración, formato, tamaño y SHA-256. SQLite conserva la evidencia; la aprobación se vincula al checksum y el gate rechaza audio reemplazado. Registrar un reemplazo revoca la aprobación y deja un evento histórico. No hay endpoint público ni generación real de sample en esta entrega; integridad técnica no acredita canto, escucha, fidelidad ni representatividad. El cierre real sigue bloqueado.
Verificación: 27 pruebas aprobadas en 11,32 segundos; dos pruebas de evidencia WAV repetidas tras añadir el evento histórico. Compilación y revisión de diferencias correctas. Audio sintético de prueba, sin ejecutar modelos.

Continuación S01: endpoint de reproducción aislado por set/sample y checksum, sin caché; aprobación de audio exige confirmación explícita de escucha y checksum vigente. Production muestra reproductor para audio registrado y confirmación vinculada a esa versión. Los checkpoints sin audio se identifican como mock; su aprobación ya no aparece como autorización de mastering/export. Registrar reemplazo limpia también la confirmación de escucha. La confirmación es una declaración del usuario; todavía falta generación real representativa y validación de escucha/calidad/usabilidad.
Verificación: 27 pruebas aprobadas; dos pruebas de evidencia repetidas tras ampliar comprobaciones de reproducción/reemplazo. Build Vite aprobado (13 módulos, 5,38 segundos), sintaxis JS y compilación Python correctas. El primer build restringido falló por permisos de lectura del entorno; el reintento autorizado pasó. No se realizó validación de usabilidad ni escucha de audio generado real.

### Alineación ACE-Step, Gemma y Qwen — 2026-10-04

Se investigaron documentación oficial 1.5 y firma instalada. [ACE_STEP_CAPABILITIES.md](docs/ACE_STEP_CAPABILITIES.md) distingue motores/APIs, capacidades documentadas, tareas conectadas y evidencia real. El wrapper solo llama text2music y aún omite BPM/key/compás/idioma estructurados. Cover/repaint y tareas Base permanecen pendientes; referencia vocal/MIDI/DSP no se presentan como funciones verificadas.

`AceStepSteering`, mediante el puerto `ModelSteering` y composición existente, lee la sección marcada y roles externos en `docs/steering/` en cada solicitud Gemma/Qwen. Añade tareas/keywords/defaults locales sin importar ACE-Step; registra revisión/hashes en resultados, handoff técnico y eventos del assistant con set activo. Qwen se alinea como director musical/técnico en vez de soporte de código. No requiere servicios reales para probar el contrato; falta evaluar comprensión/obediencia de modelos reales y compilar ACEPlan con traducción validada al motor.

Verificación: 30 pruebas aprobadas en 12,67 segundos, incluidas inyección en ambos roles, recarga documental, contrato ausente y separación soporte/verificación; compilación Python y revisión de diferencias correctas. Sin generación ni escucha de audio real en esta entrega.
Verificación ampliada: 32 pruebas de regresión aprobadas en 14,68 segundos, incluida colección de ficha existente; las cinco pruebas específicas del steering pasaron después de añadir persistencia de revisión en tasks Qwen. La descripción de roles se obtiene de los Markdown externos, sin duplicarla en los providers llama.cpp. No se realizó inferencia real para evaluar obediencia.

### Compilación de plan ACE-Step — avance S06

`AceStepPlanCompiler` prepara un plan candidato desde ficha confirmada y letra propuesta. Mapea BPM, tonalidad, compás, idioma y duración al handler; valida límites, rechaza tareas no conectadas y no trunca caption/letra. Conserva la ficha y clasifica cada campo como estructurado, condicionamiento textual o requisito pendiente de evaluación/procesador externo. Declara defaults y huella; letra, configuración efectiva y sample real siguen pendientes: no autoriza ejecución.

Previsualización de lectura: `POST /api/pro/projects/{song_id}/ace-plan/preview` con `{"lyrics":"..."}`. Lee ficha SQLite sin guardar/aprobar letra ni ejecutar modelos. El wrapper admite `--bpm`, `--key-scale`, `--time-signature`, `--vocal-language`, pasados al handler y diagnóstico. Falta conectar comandos al plan persistido/aprobado. La fachada histórica no se amplía con este compilador.

Inventario inicial: ACE-Step 1.5.0 y config Turbo 1.5 presentes; `3.5b-default` contiene cache de ACE-Step v1. La instalación posterior de Base 1.5 se registra abajo. Steering incluye inventario actualizado por solicitud sin inferir carga ni habilitar tareas Base verificadas.

Investigación de seis modos: sección 14 de [ACE_STEP_CAPABILITIES.md](docs/ACE_STEP_CAPABILITIES.md) define Base 1.5, componentes compartidos, raíz/config explícitas, recursos, LM interno, entradas de cada task y criterios para habilitar UI/compilador/adaptador. La selección Base por variable no habilita tareas que el wrapper fija a text2music. No se descargaron modelos ni se cambió configuración de ejecución.
Verificación: 36 pruebas de compilador, steering, samples y sets aprobadas en 12,85 segundos; nueve pruebas de compilador/steering repetidas tras ampliar inventario/diagnósticos. Comparación AST de `.venv` confirma firmas compatibles para initialize_service/generate_music con los argumentos nuevos. Compilación y CLI --help correctas, revisión de diferencias sin errores; no se generó audio.

Continuación de seis modos: política determinista compartida por compilador y wrapper para selección de tarea, Base explícito, audio fuente, pistas e intervalo. CLI incorpora seis modos y sus entradas, con existencia de fuentes verificada antes de cargar motores; diagnósticos conservan tarea/entradas. Preview admite seis planes candidatos desde ficha confirmada, sin aprobar ni ejecutar. Audit/steering distinguen enum enviado al handler de tareas verificadas (`verified_tasks=[]`). Sigue pendiente instalación/carga Base, verificación de artefactos/duración fuente, persistencia/aprobación/conexión del plan, UI y audio real por modo.
Verificación: 52 pruebas aprobadas en 12,74 segundos; firmas instaladas compatibles con keywords del wrapper. Compilación Python y revisión de diferencias correctas. Ningún modelo se cargó ni generó audio en estas pruebas.

### Instalación Base 1.5 — avance S06/S10

Base 1.5 instalado en la raíz compartida con Turbo, fijando revisión `e432212fec32b8965a14ffa57ae653438d6abd14`. El verificador sin carga de tensores comprobó SHA-256 del peso de 4.787.825.604 bytes y estructura safetensors; evidencia en `data/diagnostics/acestep_base_installation.json`. VAE/codificador existentes tienen pesos presentes, sin checksum completo verificado. La sección 16 de [ACE_STEP_CAPABILITIES.md](docs/ACE_STEP_CAPABILITIES.md) registra detalles y límites.

Perfiles corregidos a Base 1.5/32 pasos y Turbo 1.5/8 pasos, raíz/config explícitas y compatibilidad con plantillas históricas. La `.env` existente y el checkpoint v1 se conservan. 57 pruebas de regresión aprobadas; compileall y revisión de diff aprobados. Todavía no se cargó Base ni se generó audio con él: los seis modos requieren integración del plan/UI, ejecución y evaluación real antes de declararlos disponibles. S06/S10 siguen en progreso.

### Verificación de audio fuente — avance S06

La vista previa ACE-Step vincula `source_artifact_id` de la ficha confirmada con un artefacto del proyecto activo. Comprueba ruta aislada, WAV PCM completo, duración y SHA-256; el hash del plan incluye esta evidencia. Repaint/Lego rechazan intervalos fuera del audio real. Puerto `SourceAudioInspector` y adaptador de archivos conservan separación modular; la vista previa no persiste ni ejecuta propuestas. Sin artefacto declarado la verificación queda pendiente. 25 pruebas aprobadas y compileall correcto. Siguen pendientes aprobación/persistencia del plan, revalidación al ejecutar, UI y pruebas de audio real. Detalles en sección 17 de [ACE_STEP_CAPABILITIES.md](docs/ACE_STEP_CAPABILITIES.md).

### Alcance integrado de seis modos y fidelidad — 2026-10-04

Se revisó el adjunto del usuario sobre fidelidad a la intención frente a catálogo, especificación/revisiones, director técnico, compilador, wrapper y ejecución local actuales. [El contrato Gemma/Qwen](docs/SONG_SPEC_GEMMA_QWEN_CONTRACT.md) incorpora diagnóstico, entradas/acciones por modo, autoridad de decisiones y evaluación objetiva/estimada/por escucha. Roles externos actualizados para guiar esos insumos sin exigir MIDI/WAV guía universal ni alterar deseos aprobados. [El plan de sprints](docs/AI_MUSIC_STUDIO_SPRINT_PLAN.md) desglosa S06-A–S06-E/S10: decisiones/UI → plan aprobado → ejecución → sample/evaluación → evidencia real. Esta entrega alinea documentación y steering cargado por solicitud; no implementa todavía esos componentes pendientes ni declara disponibles los seis modos.

Avance S06-A: catálogo 1.1 incorpora acción, configuración, artefacto/ruta fuente, instrucción, pistas, intervalo y fuerza de conservación. La ficha visible explica aplicabilidad por modo y estado de plan candidato, sin presentar entradas guardadas como generación ejecutable. No completa ni confirma valores ausentes. Se corrige visualización del valor cero. Nueve pruebas de catálogo/plan/fuente aprobadas. Faltan controles editables compartidos con chat, referencia autorizada, decisiones por requisito y conexión del plan a ejecución; S06-A sigue en progreso.

### Editor y aprobación de planes — avance S06-A/B

Production permite editar las seis acciones y sus inputs, seleccionar WAV del proyecto, guardar explícitamente y revisar/confirmar una nueva ficha. La ruta fuente se obtiene del artefacto; integridad/intervalos se comprueban antes de guardar. Revisión obsoleta rechazada en transacción SQLite; otras intenciones se conservan. No genera audio al guardar.

Planes versionados en `ace_step_plans`, con snapshot `ace_plan.json` y eventos. La UI prepara un plan con letra revisable, muestra caption/metadatos/letra/requisitos y exige confirmación explícita para aprobar. La consulta recompila: cambios de ficha o checksum fuente marcan aprobación obsoleta, sin borrar su histórico. Recarga recupera estado; cambio de proyecto limpia borradores; borrar un proyecto elimina sus propios planes. La letra aprobada del plan todavía no sustituye el asset/set.

Se añadió traductor de ejecución con argumentos separados y texto en archivos, evitando interpolación creativa en shell; verifica perfil y campos traducidos. Está probado pero no conectado al runner. Siguen pendientes referencias/importación, tools de chat, vínculos al set/sample, orquestación y audio real por modo. Detalles de API/estado en sección 18 de [ACE_STEP_CAPABILITIES.md](docs/ACE_STEP_CAPABILITIES.md). Build frontend y compilación del template Vue correctos; no se realizó prueba visual ni validación con usuarios amateur.

Verificación final de este avance: 71 pruebas aprobadas (29,292 s), incluidos planes/revisiones/fuentes/aislamiento, gates y regresión de ficha/comandos anteriores. Compilación Python y revisión de diff correctas. Un primer ensayo tuvo dos errores de limpieza de SQLite en Windows; se corrigió el harness temporal y la ejecución final completa indicada pasó. No se cargó Base ni se generó audio real.

### Conexión del plan al runner local — avance S06-C

La ruta de canción completa que usa `tools/acestep_generate.py` exige ahora plan text2music aprobado/vigente y coincidencia exacta de letra con `lyrics.md`. Envía caption/letra aprobados, parámetros musicales y config mediante argumentos separados con `shell=False`, conservando preparación/restauración de recursos, diagnóstico y gate previo de sample. Artefactos finales registran plan ID/hash y revisión de especificación. Los proveedores con comandos distintos conservan su ruta intercambiable.

Esta conexión no convierte extract/lego/repaint/cover/complete en canciones finales; falta su runner de candidatos y evaluación. Tampoco habilita producción real sin sample representativo: el gate existente sigue bloqueando esa ausencia. La traducción no aplica overrides de la plantilla histórica al plan aprobado; config/pasos/dispositivo/hilos se obtienen del perfil comprobado contra el plan. Carga efectiva y audio real siguen pendientes.

Verificación de esta conexión: 18 pruebas aprobadas, incluida entrega de argumentos al proceso simulado con shell desactivado, rechazo de plan no aprobado/letra distinta y regresión de gates/comandos. Compilación Python y diff correctos. No se ejecutó ACE-Step real.

### Runner de borradores para seis tareas — avance S06-C

`POST /api/pro/projects/{song_id}/ace-candidates` requiere plan/hash aprobado vigente y `exploratory_audio_authorized=true`. Ejecuta la tarea del plan en una carpeta única de candidatos, reutilizando el runner monitorizado con argumentos separados. Revalida ficha/fuente antes del proceso y al registrar salida; verifica WAV y registra artefacto exploratorio con evidencia técnica, task, plan y revisión. No sustituye originales, sample, assets seleccionados ni final y no avanza fase del proyecto.

Un bloqueo no bloqueante compartido evita ejecución simultánea de candidatos y final dentro del proceso de aplicación. Los fallos quedan en eventos y conservan originales. La ruta es síncrona; UI de ejecución, cola/cancelación, task completa del orquestador, preflight por hardware y evaluación musical siguen pendientes. Pruebas con runner simulado no acreditan ejecución real de Base ni seis modos audibles.

### Trabajos y escucha de borradores — avance S06-C

El endpoint de candidatos ahora inicia un trabajo en segundo plano y devuelve una task persistida, reutilizando `tasks` y `model_runs` existentes. Consultas de último trabajo/estado por proyecto permiten recuperar avance tras recarga; el arranque marca trabajos pendientes/en curso como interrumpidos. Se rechaza otra solicitud mientras haya un trabajo candidato activo. Cada trabajo conserva el plan seleccionado y falla si cambia antes de ejecutar.

Production ofrece autorización explícita de borrador, inicio, consulta periódica de estado, error accionable y reproductor del candidato terminado. La reproducción verifica propiedad del trabajo, carpeta aislada e integridad/checksum contra evidencia persistida; archivo sustituido se rechaza. Escuchar no aprueba sample ni calidad final. El porcentaje registrado es un hito de estado, no estimación del tiempo restante.

21 pruebas aprobadas; build frontend y compilación Python correctos. Pruebas usan workers/procesos simulados y WAV técnico: no hubo inferencia ACE-Step, prueba visual ni escucha musical real. Pendientes: cancelación, coordinación completa con ModelOrchestrator, preflight de hardware/carga y aceptación musical/sample. El dispatcher es local de una instancia; no constituye cola distribuida ni garantiza detener procesos huérfanos tras caída del servidor.

### Cancelación de borradores — avance S06-C

Production ofrece cancelar trabajos pendientes o en curso. El endpoint POST `ace-candidates/{task_id}/cancel` comprueba proyecto y conserva estados separados: pendiente se cancela antes de cargar modelo; ejecución pasa a `cancelling` hasta que el worker detiene el proceso y restaura recursos. El runner comprueba señal antes de arrancar, durante monitoreo y antes de aceptar resultado; cancelación no se registra como fallo del provider ni habilita reproducción/final. UI continúa consultando estado mientras se detiene.

Terminación del proceso: Windows usa taskkill por PID/árbol y espera cierre; Unix termina grupo y escala si no cierra. Estado/task/model run/eventos reflejan cancelación, manteniendo originales y archivos diagnósticos aislados. 24 pruebas aprobadas con procesos simulados, build y compilación correctos. Falta validar cancelación con ACE-Step real y completar orquestación/preflight/evaluación; no se comprobó liberación física de memoria ni calidad audible.

### Preflight local y gate de recursos — avance S06-C

Antes de registrar un trabajo exploratorio se comprueban wrapper, intérprete local, config/arquitectura DiT 1.5 y archivos de pesos no vacíos de DiT/VAE/codificador. El resultado se guarda con la task y vuelve a comprobarse en el runner. Se distingue presencia de carga/integridad completa/viabilidad hardware; no descarga modelos automáticamente. Base 1.5 pasó esta comprobación local sin cargar tensores.

El runner ahora rechaza explicitamente `readiness.ready=false` despues de preparar recursos y restaura modelos de texto antes de salir. 27 pruebas aprobadas, incluida ausencia de proceso ante recursos insuficientes; compileall y diff correctos. No se ejecutó audio ni se midió inferencia. Siguen pendientes preflight medido de hardware/memoria, coordinación integral con ModelOrchestrator y evaluación por modo.

### Handoffs ACE-Step bajo el orquestador — avance S06-C

Los jobs notifican a `ModelOrchestrator` mediante el puerto `AudioHandoffLifecycle`, registrando eventos de pausa/retorno con proyecto/task/model run/plan y resultado. Estado del orquestador identifica task de audio pendiente/running/cancelling y muestra assistant suspendido; no anuncia un modelo cargado sin evidencia. Durante ese periodo se rechazan nuevos handoffs y Gemma responde guia de estado SQLite sin invocar modelo. Al terminar/fallar/cancelar, las consultas posteriores retoman desde estado persistido.

33 pruebas aprobadas, incluyendo estado/handoffs, bloqueo de revisión y respuesta Gemma sin inferencia durante audio; compileall/diff correctos. Es coordinación lógica: la liberación/carga física sigue dependiente del monitor y necesita medición real. Faltan cubrir llamadas directas a providers fuera del orquestador, recuperación de procesos huérfanos y evaluación de audio; no se cargó ACE-Step ni se probó obediencia de modelos reales.

Continuación: ProviderRegistry recibe guard de inferencia desde el orquestador. Llamadas directas Gemma/Qwen, incluidas transformaciones que usan registry, se bloquean antes de invocar provider si hay task candidata activa o exclusividad de audio tomada por candidato/final. Al cerrar audio pueden retomarse solicitudes. 29 pruebas aprobadas; compilación/diff correctos. Es un chequeo previo local, no un lease distribuido ni prueba física de memoria; solicitudes que ya estaban ejecutándose antes del audio requieren coordinación/medición adicional. No se ejecutó ACE-Step real.

### Exclusividad de planificación y audio — avance S06-C

Registry mantiene una reserva local durante toda la inferencia Gemma/Qwen y su steering; el inicio de ACE-Step comprueba atomicamente que no haya planificación en curso. La planificación tambien comprueba audio al adquirir la reserva, cerrando la carrera posterior al guard preliminar. Una segunda inferencia se rechaza con accion de esperar; no se acumulan modelos concurrentes mediante estas rutas. Reservas se liberan incluso ante excepciones.

32 pruebas aprobadas, incluida carrera simulada y liberación tras fallo; compilación/diff correctos. Coordinación limitada a la instancia y entradas del registry/runner: no detiene servidores externos ni acredita descarga física, carga o audio reales. Si la planificación estaba ejecutándose, el trabajo de audio se rechaza antes del proceso y puede solicitarse de nuevo al terminar; no hay espera/reintento automático.

### Informe inicial de fidelidad — avance S06-D

Cada candidato conserva un informe asociado a plan/revision/checksum de audio, en metadata SQLite del artefacto y resultado de task. Duracion medida desde WAV se compara con objetivo text2music; solo emite cumplimiento/incumplimiento si la ficha aprobada contiene tolerancia numerica valida. Para edicion permanece pendiente la definicion de duracion de salida por tarea. Tempo, tonalidad, letra cantada, voz, estructura, instrumentos y restricciones quedan pendientes de analisis/escucha; no se inventa porcentaje global ni aprobacion musical.

Production muestra comparacion medido/objetivo y pendientes. Catalogo incluye margen de duracion, sin asignarlo ni aprobarlo automaticamente. 12 pruebas aprobadas de informe/candidatos/jobs; no hubo analisis musical real ni escucha. Faltan controles completos de criterios, evaluadores adicionales, aceptacion del usuario y sample representativo.

Continuación S06-D: editor visible del margen aceptable de duracion (0–600 segundos), sin default. Dejar vacio elimina el criterio; guardar crea revision pendiente y requiere confirmar de nuevo. Diferencia aceptada sirve para evaluar text2music, sin prometer duracion exacta del motor. Backend rechaza booleanos, valores no finitos y fuera de rango; cero se conserva. 12 pruebas aprobadas, build/compileall/diff correctos. Faltan criterios musicales adicionales, escucha/aceptacion persistida y sample representativo.

### Revisión de escucha del candidato — continuación S06-D

El usuario puede declarar que escuchó el candidato, indicar si corresponde a su idea o necesita cambios y guardar notas. Cambios solicitados requieren descripcion. Backend verifica audio/checksum y trabajo del proyecto; la opinion se persiste como evento SQLite vinculado a task/artefacto/plan/revision y se recupera tras recarga. No cambia set, assets, sample ni aprobacion final. La decision subjetiva no reemplaza las mediciones tecnicas ni acredita voz natural/identidad.

21 pruebas específicas aprobadas y build frontend correcto; sin escucha de audio ACE-Step real ni prueba visual. La versión anterior se publicó en origin/main como `b57bc98`; este avance continúa localmente. La comprobación completa de esa versión terminó con 132 pruebas en 355,014 s y cuatro errores en fixtures antiguos que omitían el gate de set/sample. No se presenta esa suite como aprobada: los contratos downstream se ajustan con stub explícito del gate, manteniendo sus pruebas dedicadas y sin relajar producción.

Corrección de los cuatro contratos downstream: ejecución específica aprobada (4 pruebas, 128,688 s); publicada como `4338788` en origin/main. No se repitió la suite completa después del ajuste. La revisión de escucha S06-D sigue como avance local.

### Vigencia de la opinion de escucha — S06-D

La lectura y guardado de opiniones compara plan y revision con el plan vigente y sus inputs actuales. La UI identifica opiniones historicas y muestra las notas guardadas; conserva la decision original en SQLite. Ninguna opinion autoriza sample o cancion final. 22 pruebas específicas aprobadas, build frontend y compilacion Python correctos. Sin ejecucion de ACE-Step real, escucha ni validacion visual. Avance local; S06-D permanece en progreso.

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

### Propuestas de correccion desde escucha — S06-D

Verificacion integral de esta continuacion: primera suite completa, 184 pruebas en 310,688 s con 5 errores (cuatro por steering excedido y uno por fixture de export dependiente de RAM). Corregidos mediante deduplicacion del steering y aislamiento de recursos solo en esa prueba sintetica; las guardas de produccion permanecen activas. Segunda suite completa: 186 pruebas aprobadas en 312,071 s. Cuatro pruebas incorporadas despues tambien aprobadas: handoff de correccion e invalidacion SQLite ante cambio de contenido del asset elegido. Frontend: 8 pruebas Node aprobadas, build correcto; compilacion Python y diff correctos. No se ejecutaron modelos de audio ni prueba visual/amateur. Avance local sin publicar; S06 no esta terminado.

Revision tecnica opcional: POST `/api/pro/projects/{song_id}/ace-candidates/{task_id}/correction/review` entrega explicitamente la propuesta vigente al orquestador junto al set, assets, tres intenciones, ficha y notas. La UI permite solicitarla y recuperar las sugerencias guardadas, diferenciando respuesta reportada de mock/fallback y revision historica. Tasks/runs conservan trazabilidad; no se aplica output creativo. Tres pruebas específicas aprobadas para este handoff; build correcto. Sigue pendiente generar propuestas musicales estructuradas por campo y validarlas con modelos reales.

Estado actual: las propuestas abarcan los seis modos. Lego/Extract/Complete exigen pistas admitidas e instruccion coherente y proponen Base; se reutilizan politica y controles, sin generar ni guardar ajustes creativos automaticamente. Los informes incluyen conservacion de fuente/exterior, intervalo, pistas, operacion, coherencia y fugas segun modo como criterios pendientes de escucha. Gemma/Qwen reciben la correccion persistida; la guia propone revisar controles y ficha. Los planes de proyectos vinculados incluyen huella del set para invalidar cambios en sus piezas. Steering compartido deduplicado (5476 caracteres; roles 1677/2011) y excepciones de Git permiten versionar los roles. 55 pruebas backend específicas y 7 frontend aprobadas; build/compilacion correctos. Audio real bloqueado por RAM observada (~1124 MB frente a presupuesto estimado 7049 MB); no hay validacion audible/amateur. El estado por fase esta consolidado en `docs/AI_MUSIC_STUDIO_SPRINT_PLAN.md`; S06 sigue abierto.

Continuacion: GET del mismo endpoint recupera la ultima propuesta del candidato desde SQLite y deriva su vigencia sin modificar el historial. La UI muestra notas, alcance e intervalo, y permite cargarlos explicitamente en los controles existentes sin sobrescribir un borrador abierto ni guardar automaticamente. El flujo existente guarda una nueva ficha pendiente, exige confirmarla y compila/verifica el audio fuente al preparar el plan. Las notas no se convierten automaticamente en cambios musicales. Verificacion: 16 pruebas backend específicas, 7 frontend y build aprobados. Recuperacion y puente manual al compilador implementados; quedan automatizacion revisable de ajustes musicales, pistas Base, edicion real y validacion visual/amateur. Cambios locales sin publicar.

La interfaz permite registrar el alcance de una correccion desde una opinion vigente que solicita cambios: fragmento (`repaint`, inicio/final en segundos), estilo/timbre general (`cover`) u otra interpretacion (`text2music`). El endpoint POST `/api/pro/projects/{song_id}/ace-candidates/{task_id}/correction` verifica propiedad, opinion vigente y checksum del audio; los intervalos requieren duracion WAV medida. La propuesta conserva notas, criterios, revision, plan y artefacto en eventos SQLite. No modifica la ficha ni el plan aprobado ni inicia generacion. Pendientes recuperacion visible de propuestas, handoff al compilador, controles de pistas para Base y edicion real. Verificacion: 14 pruebas backend específicas y build frontend aprobados; cambios locales, sin escucha ni validacion visual/amateur.

### Comparacion A/B de candidatos — S06-D

La comparacion incluye una tabla por requisito con los objetivos de A y B, diferencias de plan/revision y duracion medida cuando existe evidencia WAV. Letra, voz e instrumentos sin analisis permanecen pendientes de escucha. Los objetivos completos pueden desplegarse; no se elige ganador ni se aprueba audio automaticamente. Continuacion verificada con 5 pruebas frontend y build correcto; cambios locales sin publicar. Pendientes prueba visual, audio real y validacion amateur.

API de candidatos devuelve historial limitado a 20 trabajos del proyecto. UI permite comparar el candidato A con una version completada anterior B; reproduce por task/checksum bajo validacion backend existente. Al iniciar un reproductor pausa el otro. B conserva contexto historico: no cambia opinions, assets, set, sample ni aprobaciones. No alinea tiempos ni normaliza volumen; comparacion subjetiva por escucha.

37 pruebas backend específicas y 2 pruebas frontend aprobadas; build/compilacion/diff correctos. No se hizo prueba visual, escucha real ni validacion amateur. Cambios locales, S06-D sigue abierto.

### Auditoria Playwright MCP — 2026-10-06

Revision de la version local con Chrome y Playwright MCP 0.0.83, servidor FastAPI en 8012 y SQLite temporal; sin ejecutar motores musicales. Navegacion de las ocho pantallas, bloqueo del proyecto sin las tres piezas, creacion de drafts/set, configuracion visible de los seis modos, guardado/confirmacion de ficha, preparacion/aprobacion del plan y persistencia comprobados. Con dos WAV sinteticos: comparacion A/B y pausa mutua, opiniones, rechazo de intervalo fuera del audio, propuesta de correccion recuperada tras recarga, revision tecnica identificada como fallback, carga explicita de controles sin guardar y creacion de sample. Cambios solicitados al sample impiden aprobarlo; mastering permanece deshabilitado y backend devuelve 400. Guardar BPM 83 persiste en SQLite y tras recarga; invalida plan/sample anteriores. Descartar restaura BPM 72. Error de conexion de Gemma conserva el texto y permite reintentar.

Corregidos y repetidos en navegador: `Export listo` requiere `quality.export_ready` del proyecto actual; actualizar el plan sin cambios ya no borra confirmaciones/autorizaciones del usuario. Regresion frontend incorporada: 9 pruebas aprobadas; build correcto. La suite backend completa anterior tiene 190 pruebas aprobadas; no se repitio por estos cambios exclusivamente frontend. Evidencia y limites en `docs/HANDOFF_PLAYWRIGHT_2026-10-02.md`. S06 sigue abierto: los fixtures no demuestran generacion ACE-Step, calidad musical/vocal, ejecucion real de los seis modos ni usabilidad amateur. Cambios locales sin publicar.

### Alcance de sprints corregido — 2026-10-06

El plan operativo `docs/AI_MUSIC_STUDIO_SPRINT_PLAN.md` y `docs/ROADMAPP.md` priorizan ahora únicamente preparación de entradas compatibles, coordinación y evaluación de ACE-Step: S00–S06/S10. MIDI/piano roll, DAW/timeline, mixer, DSP general y automatización son ampliaciones diferidas, no requisitos de cierre. Las tres piezas siguen siendo instrumental, melodía vocal y letra; no se obliga a crear MIDI ni una guía WAV para text2music. Importación de audio, fuentes/pistas e intervalos se implementan solo como insumos requeridos por los modos. Se conservan funciones/rutas existentes y backlog histórico; esta corrección documental no elimina código, implementa capacidades ni cierra sprints. Voz personalizada es opcional y requiere evidencia propia.

### Entradas ACE-Step adicionales — S06-F, 2026-10-06

Editor ofrece referencia musical WAV ya registrada, semilla, pasos, guidance y shift opcionales. Guardar crea revisión pendiente; confirmación y plan conservan parámetros. Referencia se valida por propietario/ruta/integridad y su evidencia cambia el hash; adaptador envía argumentos explícitos. Pasos de runtime se comparan con override aprobado. Wrapper limita batch a 1 y aplica shift delegado Turbo 3/Base 1. Caption incorpora groove/rango/balance. El plan identifica ruta directa sin reescritura LM; no ofrece controles de API alto nivel desconectados. Sigue pendiente importación nueva, candidato instrumental comprobado, exclusiones/prioridades revisables, inferencia real y evaluación musical/amateur. Sprints abiertos, cambios locales sin publicar.

Verificación de esta entrega: 27 pruebas backend específicas (configuración 5, compilador 6, argumentos 4, opciones/referencia 3, correspondencia runtime 3 y revisión de plan 6), 9 pruebas frontend; build y compilación correctos. No se repitió suite backend completa ni Playwright después de estos nuevos controles.

### Evaluación API ACE-Step alto nivel — 2026-10-06

Evaluados documentación oficial y código instalado: LM 5 Hz añade códigos de condicionamiento musical, potencialmente útil para text2music; no hay comparación audible local. Cover/Repaint/Extract omiten LM. Recomendada prueba opcional con deseos confirmados y reescritura desactivada, seeds en GenerationConfig, evidencia efectiva y presupuesto conjunto. Dos comprobaciones del helper preservan campos completos y rellenan faltantes; AST detecta que instrumental no se consume en generate_music instalado. RAM libre 4297,12 MB frente a pesos LM 1.7B de 3536,72 MB adicionales al pipeline: no se cargó ni generó audio. Informe en docs/ACE_STEP_CAPABILITIES.md y evidencia JSON. IN-07 propuesto dentro del sprint, implementación pendiente; evaluación no activa API/LM ni certifica mejora sonora.

### API ACE-Step opcional conectada — IN-07, 2026-10-06

Production permite elegir directa (default), alto nivel sin LM o alto nivel con LM musical experimental para crear desde texto. Ficha/plan mantienen aprobación y hash; parámetros se traducen al wrapper. LM local seleccionable 1.7B/0.6B, pesos/tokenizer y presupuesto adicional exigidos antes del proceso; backend pt/CPU con unload al finalizar. No se modifican caption/letra/idioma aprobados; seed explícita y batch 1. Fallo de inicialización/inferencia o ausencia de códigos no produce éxito/fallback silencioso. Evidencia runtime se conserva en candidato/sample y compara API/uso LM solicitados. Orquestación y cancelación existentes siguen activas. 38 pruebas backend específicas y 9 frontend aprobadas, build/compilación/diff correctos; compatibilidad AST de dataclasses comprobada. Sin inferencia real ni revisión Playwright de nuevos controles, calidad/amateur pendientes. Conexión local lista para ensayo con recursos suficientes; no se publica ni se cierra sprint.

### Continuación S06-01 — controles numéricos (2026-10-09)

Quince controles de composición, instrumental, voz y herramientas MIDI conservadas tienen entrada numérica sincronizada con el deslizador y etiquetas individuales. Se validan rangos en UI y backend antes de guardar, sin recortar decisiones del usuario. Las descripciones distinguen intención creativa de controles DSP independientes no conectados a ACE-Step. Ver `docs/NUMERIC_DIRECTION_CONTROLS_20261009.md`. Avance D/V: 90,5%; S06-01 continúa con verificación parcial.

### Verificación agrupada de controles numéricos — 2026-10-09

Playwright MCP verificó 24 instancias de controles en cuatro pantallas: sincronización, guardado HTTP 200 y recuperación tras recargar. UI y backend rechazaron vibrato 101 conservando valor y revisión persistidos. Se corrigieron etiquetas vacías de BPM/emoción. Evidencia: `docs/NUMERIC_DIRECTION_CONTROLS_20261009.md`. Lote cerrado; S06-01 sigue parcial por la cobertura global de accesibilidad pendiente, sin sumar puntos por una comprobación local.

### Accesibilidad de selección y composición — 2026-10-09

Estados aria-pressed y selección textual para instrumentos/inspiraciones, botones comprensibles para reordenar composición y foco en errores de guardado. Build y Playwright teclado/guardado/reflow aprobados; evidencia `docs/SELECTION_KEYBOARD_QA_20261009.md`. S06-01 sigue parcial; global D/V90,5%.

### Contraste de campos del Builder — 2026-10-09

Playwright verificó141 evaluaciones de campos/bordes/placeholders en nueve superficies, incluida configuración musical y ACE-Step abierta, sin fallos. Harness reproducible y límites en `docs/BUILDER_CONTROL_CONTRAST_20261009.md`. S06-01 conserva verificación parcial con pendientes acotados a controles nativos, diálogos compuestos y estados active/disabled; global90,5%.

### Cierre D/V S06-01 — 2026-10-09

Controles accesibles con estilos explícitos, fallback forced-colors y corrección de contraste en diálogo de eliminación (4,30→7,02:1). Build y Playwright Chromium aprobaron controles por teclado, tres diálogos y estados CTA. Matriz acumulada en `docs/BUILDER_ACCESSIBILITY_CLOSURE_20261009.md`; S06-01 V0,5→1, aceptación0. Global D/V90,5→90,8%; alcance de ingeniería cerrado, sin certificación WCAG integral ni aceptación amateur. Próximo bloque: handoffs/jobs pendientes sin audio antes de generación real final.

### Jobs y recuperación de dispatch — 2026-10-09

Corregida retención del token de cancelación cuando no arranca el dispatcher.15 pruebas agrupadas jobs/limpieza de hijos reales aprobadas; reintento conserva identidad y requiere nueva acción para nuevo intento. Evidencia `docs/JOB_DISPATCH_RECOVERY_QA_20261009.md`. Global90,8%; cancelar ACE-Step con pesos y medir memoria/handoff siguen para lote final de audio.

### Preflight final de audio — 2026-10-09

Contrato instalado compatible; handoff administrado Gemma/Qwen liberó RAM994→8450MB. Pesos Base/Turbo y dependencias presentes en ruta del perfil real; LM1.7B presente,0.6B ausente. PyTorch2.9.1+xpu detecta IntelGraphics. Modelos de texto detenidos para siguiente lote, perfiles Vulkan conservados. No empezó nueva generación. Matriz y límites: `docs/FINAL_AUDIO_PREFLIGHT_20261009.md`; global90,8%.

### Ensayo real de cancelación iniciado — 2026-10-09

`scripts/verify_real_audio_cancellation.py` ejecuta el runner real con copia de inputs de Isabella, SQLite QA aislado, diagnóstico y cancelación al observar pipeline_loaded. Proceso iniciado (worker14108; intento1791602127219395700). XPU seleccionado; aún cargando al último control, sin resultado final acreditado ni cambios de métrica90,8%. La restauración administrada de Gemma/Qwen está en finally del servicio. Resultado futuro en `data/qa_real_cancel_20261009/1791602127219395700/result.json`.

### Cancelación con pesos y recuperación reales — 2026-10-09

Turbo/XPU cargó pesos; el runner canceló y terminó worker14108 sin WAV. Restauración Gemma/Qwen confirmada con health200 e inferencia real breve en ambos; probes no acreditan fidelidad. Espera de warmup incorporada al harness. S04-02 yS04-03 V0,5→1; global90,8→92,0%. Evidencia `docs/REAL_CANCELLATION_HANDOFF_20261009.md`. RAM310MB tras restaurar: siguiente audio requiere liberar otra vez modelos; no sumar memoria compartida.

### APIalto nivel sinLM: ensayo real iniciado — 2026-10-09

`scripts/verify_real_high_level_audio.py` copia SQLite/proyecto QA y ejecuta compilador, aprobación QA explícita, jobs, monitor y runner reales con Turbo/15s/8pasos, sinLM. Job ace_job_d866bef6871a3e21cf6f4997b7b8876d7e156c2e33c56811b94fe86d436bea68 y plan ace_plan_2cb5913a56a24c0e8218c960d564178c; revisión spec_rev_64926a5cb6b2. El primer harness omitió deterministic_valid; compilador lo rechazó sin cargar pesos. Reintento conserva validación del proyecto QA y pasó guards. Sin resultado de audio acreditado aún; global92,0%. Puntero `data/runtime/high_level_active_20261009.json`.

### Casos reales siguientes preparados — 2026-10-09

Harness reutilizable por modo/API, fuente e instrucción con prepare-only. Cover/Repaint compilados y aprobados en QA con recortePCM real15s de Isabella, checksums y transformación documentados; Repaint5–10s máscara explicit. Sin dispatch de esos modos ni solapamiento; APIalto nivel actual sigue decodificando. `docs/REAL_AUDIO_NEXT_CASES_20261009.md`; global92,0%.

### APIalto nivel sinLM verificada — 2026-10-09

Job real completó WAV15s/48kHz/estéreo/PCM16; TurboXPU8pasos, LMfalse/rewritesfalse.18campos reportados por motor coinciden con plan, sin discrepancias. S06-07 V0,5→1; global92,0→92,4%. No aceptación/escucha acreditada ni cierre de rutaLM/otros modos. Evidencia `docs/REAL_HIGH_LEVEL_AUDIO_20261009.md`.

### Cover iniciado y Repaint secuenciado — 2026-10-09

Cover/direct real: QA1791602787119137000, plan ace_plan_c344f17b8035459e9e346917697996dc, revisión spec_rev_4c96dd7a9e2d; fuentePCM15s verificada, Turbo8pasos. `continue_real_audio_batch.py` espera resultado y solo inicia Repaint si Cover completó, sin solapar motores. Lego/guitar, Extract/vocals y Complete/drums preparados con instrucciones TASK_INSTRUCTIONS instaladas, Base32pasos; no ejecutados. Preparación no suma puntos: global92,4%.

### Comparación de señal para edición real — 2026-10-09

Adapter `pcm_edit_comparison` mide identidad/diferenciaRMS por regiones antes/seleccionada/después sobre PCM16 alineado, verifica checksums antes/después y rechaza formatos/longitudes no comparables. No infiere calidad ni fidelidad perceptual. Prueba de cambio localizado aprobada; Cover sigue en ejecución y Repaint secuenciado, sin cambios de porcentaje92,4%.

### Cover real completado; Repaint iniciado — 2026-10-09

Cover produjo WAV15s/48kHz/estéreo/PCM16, traza wrapper coincidente, señal no silenciosa/sin muestras a escala máxima. ComparaciónPCM documentada sin atribuir fidelidad perceptual. S10-02 V0→0,5; global92,4→92,6%. Repaint iniciado secuencialmente5–10s/máscaraexplicit, QA1791603039769048600; no resultado aún. `docs/REAL_COVER_AUDIO_20261009.md`.

### Repaint completado y medición reproducible — 2026-10-09

Repaint generó audio real de 15s: región5–10s modificada, aproximadamente99,5% de muestras externas idénticas. Integridad/checksum/señal verificados; escucha de transiciones pendiente. S10-03 V0→0,5; evidencia `docs/REAL_REPAINT_AUDIO_20261009.md`. El script `scripts/measure_real_audio_result.py` reproduce mediciones de jobs completados, contrasta checksum persistido y no registra aprobación ni carga modelos; ejecutado sobre Cover y Repaint. Continúa Lego/Base de forma aislada y secuencial.

### Corrección de pistas objetivo para los modos Base — 2026-10-09

La primera ejecución real Lego falló antes de cargar pesos: faltaba `--tracks` en la traducción del plan al proceso. Corregido en `AceStepExecutionArguments`: las pistas del plan aprobado llegan al wrapper mediante unión por coma, con validación y trazabilidad en `wrapper_task_constraints`; no se presentan como parámetro nativo del handler. Nueve pruebas de traducción/aceptación USER y ejecución aprobadas, incluyendo Lego, Extract y Complete. Reintento real en proyecto QA separado; global92,9% sin acreditar un modo que todavía no terminó.

### Lote Base secuencial — 2026-10-09

Reintento Lego QA1791603499514019000 confirmó `--tracks guitar` y superó la validación inicial; perfil Base/CPU32pasos. `continue_real_audio_batch.py --remaining-base` espera su resultado y secuencia Extract/vocals y Complete/drums, midiendo integridad/checksum/señal entre jobs y deteniéndose ante fallo o silencio digital. Verificado bloqueo con el resultado fallido anterior: no despacha otro audio. Informes por QA, sin modificar proyectos originales ni atribuir aprobación por generación. Global92,9% mientras no exista evidencia de cierre adicional.

### Conservación externa Repaint y difusión Base — 2026-10-09

Repaint: las regiones0–4,95s y10,05–15s son100% idénticas a la fuente PCM; diferencias externas limitadas a los márgenes de50ms usados en la medición. Evidencia `repaint_boundary_comparison.json`, sin inferir aceptación audible. Lego cargó Base e inició difusiónCPU32pasos; no hay resultado final todavía. Global92,9%, sin repetir suites ni aumentar el porcentaje por comprobaciones parciales adicionales.

### Lego completado; Extract iniciado — 2026-10-09

Lego/BaseCPU32pasos produjo WAV15s con checksum e integridad verificados, señal no silenciosa y sin muestras a escala máxima; runtime/configuración y traza wrapper coincidentes. Falta escuchar guitarra/coherencia/transiciones. S10-04 V0→0,5; global92,9→93,2%. Evidencia `docs/REAL_LEGO_AUDIO_20261009.md`. Extract/vocals inició automáticamente tras la medición; Complete/drums queda secuenciado. RunnerLego388,5s con picoRAM100%, sin ampliar concurrencia ni modificar canciones originales.

### Descarga HTTP de candidato real — 2026-10-09

`scripts/verify_real_candidate_download.py` verificó la descarga ASGI del WAV real Lego: HTTP200,2880044bytes,checksumidéntico,attachmentaudio/wav y rechazoHTTP400conchecksumincorrecto. Sin cargar modelos ni iniciar servidor; informe `download_postflight.json` enQA1791603499514019000. No sustituye navegación/descarga real de navegador ni cierre integrado; S01-04 permaneceV0,5 y global93,2%. Extract sigue en ejecución y Complete espera.

### Contrato ACE-Step actualizado con evidencia real — 2026-10-09

`docs/ACE_STEP_CAPABILITIES.md` incorpora una tabla vigente que sustituye notas históricas incompatibles: distingue ejecuciones/integridad de text2music,alto nivel sinLM,Cover,Repaint yLego de escucha pendiente y modos aún en curso. Aclara `--tracks` como validación de wrapper, sin inventar parámetros del motor. Extract continúa en difusión; descarga de navegador se reserva para liberar memoria al terminar lote. Global93,2%, sin sumar documentación como nuevo cierre.

### Procedencia explícita del escenario QA — 2026-10-09

El harness de audio clona profundamente la ficha y marca los campos modificados como `explicit_technical_qa_scenario/technical_qa_only`; evita conservar procedencia del fixture para seed,pasos,tarea,fuente y demás valores fijados por la prueba. No son decisiones creativas USER ni aceptación. Casos anteriores se conservan sin reescribir; su metadata de procedencia heredada no acredita confirmación de esos valores, aunque el escenario técnico se aprobó como QA. Extract sigue activo; el siguiente Complete utilizará esta corrección. Global93,2%.

### Extract completado; Complete en difusión — 2026-10-09

Extract/BaseCPU32pasos produjo WAV15s válido y checksum/traza wrapper/configuración coincidentes. Señal no silenciosa con RMS−40,6dBFS: escuchar voz/fugas/nivel antes de acreditar separación útil. S10-05 V0→0,5; global93,2→93,5%. Evidencia `docs/REAL_EXTRACT_AUDIO_20261009.md`. Complete/drums iniciado automáticamente tras validación técnica, QA1791604384966484400; sin resultado final todavía. Originales y aceptación intactos; no suites repetidas ni normalización automática.

### Pendiente de configuración acotado a LM opcional — 2026-10-09

S00-04 actualiza sus pendientes con la evidencia ya obtenida de Base/direct y alto nivel sinLM. Conserva V0,5: aún falta observar carga y uso efectivo del LM opcional, no acreditados por esas rutas. Complete sigue activo; no se duplica una prueba ni se incrementa el porcentaje por actualizar el registro. Global93,5%.

### Regresión de selección múltiple Complete — 2026-10-09

Prueba específica aprobada: MusicSpecUSER batería+bajo llega intacto al wrapper como `drums,bass`, con instrucción conservada, transformación trazada y ficha sin mutación. Cubre selección múltiple del fallo de pistas corregido, sin repetir suites ni generar audio adicional. Complete real sigue en difusión; esta prueba no demuestra ejecución musical de dos pistas. Global93,5%.

### Servidor para revisión UI de audio real — 2026-10-09

`scripts/serve_real_audio_qa.py` abre la aplicación existente sobre una QA completada, con autostart/bootstrap/modelos desactivados y acceso solo localhost. Rechaza directorios fuera de data/qa_* y resultados no completados. `--check-only` comprobado sobre Lego; servidor/navegador aún no iniciados mientras Complete utiliza recursos. Preparación de verificación, sin aumentar global93,5% ni acreditar interfaz todavía.

### Complete completado; lote real de seis modos — 2026-10-09

Complete/BaseCPU32pasos terminó con WAV15s íntegro/checksum/configuración/traza wrapper coincidentes, señal no silenciosa y sin muestras a escala máxima. S10-06 V0→0,5; global93,5→93,8%. Evidencia `docs/REAL_COMPLETE_AUDIO_20261009.md`. Seis modos con generación real documentada; escucha/fidelidad de edición y separación siguen pendientes. Lote terminó exit0. Servidor QA iniciado enlocalhost8025 sobre resultadoComplete, modelos desactivados para siguiente revisión de interfaz; no acredita navegador todavía ni modifica originales.

### Studio y descarga real por Playwright — 2026-10-09

Navegación Biblioteca→proyecto→Production→Studio recuperó Complete real; reproducción15s sin error y descargaWAV con checksumidéntico verificadas. Corregida copia del plan que anunciaba ejecución pendiente pese a candidato terminado del mismo plan; buildVite aprobado y revisión posterior de navegador. Evidencia `docs/REAL_COMPLETE_UI_DOWNLOAD_20261009.md`. No acredita escucha completa,A/B ni exportaciones finales; global93,8% sin cerrar entregables más amplios por este subbloque.

### A/B con Lego y Complete reales — 2026-10-09

Importación QA de Lego preservó origen/checksum sin nueva inferencia. Playwright seleccionó Complete comoB; ambos15s reproducen sin error y alternar pausa el otro candidato. Evidencia `docs/REAL_AB_PLAYBACK_20261009.md`. No registra aceptación ni sustituye escucha musical; S04-04 conservaV0,5/global93,8%. Modelos de texto gestionados cerrados para liberar RAM; originales intactos.
