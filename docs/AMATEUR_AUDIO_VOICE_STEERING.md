# Dirección de producto: creación amateur, calidad y voz personalizada

Fecha: 2026-10-03. Estado: **contrato de desarrollo pendiente**. Esta definición no acredita audio real, clonación de voz implementada ni una experiencia validada con usuarios. Complementa [AMATEUR_USER_FLOW_REVIEW.md](AMATEUR_USER_FLOW_REVIEW.md): ese documento gobierna el recorrido; este gobierna calidad, voz y aceptación del resultado. El orden de entrega está en [ROADMAPP.md](ROADMAPP.md).

## Resultado que debe ofrecer el producto

La compilación de los deseos y su traducción a un documento ejecutable se rige por [SONG_SPEC_GEMMA_QWEN_CONTRACT.md](SONG_SPEC_GEMMA_QWEN_CONTRACT.md). Gemma confirma la intención; Qwen completa la especificación musical/técnica por etapa y sus criterios de fidelidad. La generación y las evaluaciones de esta página usan la revisión aprobada, sin reducir el rol técnico a comprobar que hay campos llenos.

Una persona sin experiencia musical puede convertir una idea en una canción, preparar con IA las tres piezas obligatorias, elegir cómo debe sonar la voz, revisar una muestra representativa y descargar un resultado evaluado tanto técnicamente como por escucha. La app debe explicar qué está listo, qué falta, qué acción sigue y qué resultado produce cada acción.

«Excelente calidad» es un objetivo a demostrar con audio real y evaluación de escucha. No se deduce del formato WAV, del dispositivo utilizado, del nombre del modelo, de un archivo existente ni de una task completada. «Voz natural generada», «voz personalizada a partir de una referencia» y «grabación de una persona» son opciones diferentes y deben nombrarse con precisión.

## Alcance actual y dependencias

- El árbol actual permite preparar drafts mock, seleccionar tres assets y trabajar por fases. El contrato guiado y el sample obligatorio del set activo siguen pendientes en la ruta principal.
- No existe una opción de producto para cargar o grabar una voz y copiar su identidad vocal en las canciones. Los providers actuales y sus placeholders no acreditan esa capacidad.
- La generación Full Song está preparada para un comando local; no hay evidencia en esta revisión de una canción real que cumpla los criterios de este documento.
- La voz personalizada será opcional. Se debe poder crear una canción con una voz generada disponible sin cargar una grabación propia. La falta de clonación no bloquea esa ruta.
- El modo local y los mocks mantienen el desarrollo ejecutable. Providers pro permanecen como capacidad futura; no introducir una dependencia obligatoria de APIs pagadas.

## Mejoras del recorrido

| ID | Prioridad | Mejora | Aceptación |
| --- | --- | --- | --- |
| UX-01 | P0 | Preparación inicial guardada separada del set: idea, idioma, emoción y preferencias; destinatario y ocasión opcionales. | Recargar recupera la preparación sin crear un set incompleto, tomar datos de otro proyecto o anunciar canción generada. |
| UX-02 | P0 | IA propone instrumental, melodía vocal y letra en lenguaje común, con explicación y confirmación antes de guardar. | El usuario puede aceptar, editar o descartar cada propuesta; las tres piezas conservan intent y manifest; seleccionar una pieza no selecciona silenciosamente las otras. |
| UX-03 | P0 | Mostrar tres piezas, selección explícita, compatibilidad y un resumen previo al set. | Faltantes y conflictos se explican con una acción; backend rechaza assets ausentes, cruzados o incompletos; UI y Gemma coinciden. |
| UX-04 | P0 | Sample del set activo, revisable y con versión de inputs. | Todos los endpoints finales rechazan sample ausente, ajeno, fallido, desactualizado o sin aprobación; aprobar un mock solo permite continuidad mock. |
| UX-05 | P1 | Ruta de cinco hitos y una acción siguiente; ajustes técnicos opcionales. | Una persona nueva llega al sample sin abrir BPM, MIDI, stems, IDs o configuración de providers; puede volver a editar y comprende qué pierde vigencia. |
| UX-06 | P1 | Elección y escucha de voz con términos como cálida, suave o enérgica y rango sugerido. | Cambiar voz actualiza la intención vocal con confirmación; nunca se anuncia una identidad vocal que el provider no puede mantener. |
| UX-07 | P1 | Antes de generar: resumen de resultado, disponibilidad, estimación de tiempo y acciones de detener/reintentar cuando el backend las soporte. | Sin medición disponible se dice que el tiempo es desconocido; disponibilidad no aparece como ejecución. Fallar conserva configuración y no habilita un final incompleto. |
| UX-08 | P1 | Revisar canción completa, solicitar cambios concretos y descargar. | Acciones comprensibles: «Se entiende poco la letra», «Quiero otra interpretación», «La voz está muy baja». Se muestra el alcance del cambio antes de gastar otra generación; solo se ofrecen como finales exportables aprobados y verificados. |

Antes del set, persistir una preparación identificada propia, independiente de `sets`; su esquema se definirá en el sprint UX-01. Después del set, usar su identidad y la relación explícita con el proyecto de Production. Evitar seleccionar el último proyecto/sample global para resolver el contexto activo.

## Contrato del sample y de las revisiones

El sample debe contener voz cantada y un fragmento musical suficiente para juzgar idioma, pronunciación, identidad vocal, balance y estilo. Elegir un fragmento representativo de la letra y la melodía, incluyendo una transición o una parte exigente cuando exista. La duración se configura según provider y contenido; no fijar un número universal sin probarlo.

Debe usar la voz, el perfil de referencia si aplica, el provider y la configuración musical relevantes de la producción final. Si una muestra usa otro motor o una guía procedural, etiquetarla como guía no representativa; no sirve para aprobar la calidad de una canción real. Los mocks sirven para comprobar flujo y contratos.

Registrar una huella de inputs: set y versiones de las tres piezas, letra resuelta, intención musical, selección y versión de voz, provider/modelo y parámetros relevantes de generación y mezcla. Separar los parámetros propios de longitud del sample de los inputs creativos compartidos. Guardar la aprobación junto con esa huella y la versión del artefacto escuchado. No producir desde el audio del sample como fuente de verdad: producir desde los inputs persistidos que se aprobaron.

Cambios de letra cantada, melodía, tempo, tonalidad, instrumental, voz, referencia, modelo o configuración que afecte el sonido invalidan el sample aprobado. Un cambio de nombre o descripción administrativa que no altera la intención no debe invalidarlo. Una edición de descripción con efecto creativo requiere confirmar y actualizar la intención, y entonces sí invalida dependencias. Esta clasificación debe aplicarse en backend.

Antes de registrar un resultado de una task, comparar sus inputs con la revisión activa. Un resultado tardío conserva su histórico, pero no reemplaza el artefacto vigente de una revisión posterior. Aprobaciones y regeneraciones se vinculan a artefactos concretos, no a un booleano global del proyecto.

## Calidad técnica y calidad percibida

Crear un servicio de evaluación independiente de los providers. Evalúa el sample, el render completo y cada exportable final. Guardar el informe activo en SQLite; un JSON exportado es su snapshot. Conservar resultados por artefacto y versión del perfil de calidad.

| ID | Evaluación | Resultado requerido |
| --- | --- | --- |
| QA-01 | Decodificación real, formato, duración, canales, frecuencia de muestreo y valores de señal. | Archivo completo y decodificable, sin valores no finitos ni duración fuera de la tolerancia del trabajo. Validar el contenido, no solo extensión/tamaño. |
| QA-02 | Silencio inesperado, cortes, saturación, true peak, sonoridad y rango dinámico. | Registrar métricas y advertencias por tramo. Pausas y silencios artísticos se comparan con el plan; evitar rechazarlos por una regla global. Fallos confirmados bloquean la etiqueta final. |
| QA-03 | Letra e interpretación vocal. | Revisar idioma, palabras omitidas/inventadas, pronunciación, inteligibilidad, afinación, ritmo, expresión, respiraciones y artefactos audibles. Transcripción/alineación automáticas son señales auxiliares, con sus límites; no equivalen a juicio musical. |
| QA-04 | Coherencia y mezcla. | Voz comprensible frente al instrumental, identidad vocal estable cuando se pidió un solista, entradas y finales limpios, estructura y emoción acordes a las tres intenciones. Evaluar canción completa además del sample. |
| QA-05 | Voz de referencia, si fue elegida. | Evaluar parecido de timbre, continuidad de identidad y conservación de la interpretación. Una métrica de similitud no acredita por sí sola buen canto ni autorización del titular. |
| QA-06 | Exportación. | Exportar desde el render aprobado; registrar checksum y parámetros; decodificar el archivo exportado y comprobar su pertenencia al proyecto y revisión solicitados. Convertir o remuestrear no demuestra una mejora de calidad. |

El perfil de calidad debe ser versionado e incluir tolerancias de duración, detección de silencio y saturación, límites de pico, objetivo y tolerancia de sonoridad, formatos de entrega y condiciones de escucha. Antes de liberar una ruta de audio real, elegir y justificar esos valores con un corpus de prueba y fijarlos en configuración. Un perfil sin umbrales calibrados tiene evaluación incompleta y no acredita calidad verificada. No escribir límites distintos en UI y backend.

La aprobación tiene tres dimensiones independientes: integridad técnica, evaluación perceptual y conformidad del usuario con la canción. Estados de evaluación: pendiente, aprobada, rechazada o incompleta. Solo un render técnicamente aprobado, con revisión perceptual completada y aceptación del usuario puede anunciarse como final aprobado. Si falta una evaluación, explicar cuál falta; permitir escuchar el borrador. La descarga de borradores, si se ofrece, debe etiquetarse expresamente y no pasar por la acción de descarga final.

El reintento nunca sustituye un resultado aprobado silenciosamente. Mostrar antes qué se regenerará y conservar el resultado anterior y la nueva versión. Corregir mezcla o exportación reutiliza los artefactos válidos cuando sea posible; si el provider solo produce una canción integrada, explicar que el cambio puede requerir regenerarla completa. No prometer stems aislados que no fueron producidos o verificados.

## Voz personalizada: alcance futuro

La opción visible será «Usar mi voz o una voz autorizada». Debe poder omitirse. No presentar «voz humana» como sinónimo de clonación: una grabación real puede incorporarse sin entrenar un modelo, y una voz generada natural puede utilizarse sin copiar a una persona.

| ID | Prioridad | Entrega | Aceptación |
| --- | --- | --- | --- |
| VO-01 | P1 | Contrato de capacidades de voz, independiente del proveedor. | Declarar canto, voz hablada, referencia vocal, conversión de canto, idiomas, rango, ejecución local/pro y salida integrada/separada. UI solo ofrece acciones realmente soportadas. |
| VO-02 | P2 | Importar archivo o grabar desde navegador, escuchar y confirmar la referencia. | Guía simple de grabación y límites según provider; alternativa de subir archivo si no hay micrófono. Backend valida formato decodificado, tamaño/duración, ruido, señal utilizable y número de hablantes según capacidades. Si falta evaluación fiable, pedir una revisión explícita y marcarla pendiente. |
| VO-03 | P2 | Crear perfil vocal reutilizable y asociarlo a la selección de voz del proyecto. | Persistir ID, versión, propietario/autorización declarada, idioma, referencias con checksum, provider y estado de preparación. Un error no deja el perfil listo; cambiar referencia crea versión e invalida samples dependientes. |
| VO-04 | P2 | Adaptador real de canto condicionado por referencia o conversión de voz cantada. | Prueba local real con letra en español y melodía del proyecto, perfil elegido y resultado cantado. Un motor de TTS hablado no cumple esta entrega. Integración Full Song solo se admite si el motor demuestra soporte de referencia vocal; no suponer que ACE-Step lo tiene. |
| VO-05 | P2 | Comparar referencia y muestra cantada, ajustar y aprobar. | Usuario escucha ambas, confirma parecido y naturalidad; si la voz no se conserva, explicar y ofrecer reintento, otra voz o volver a la ruta generada. Cambiar de provider nunca elimina la selección sin confirmación. |
| VO-06 | P2 | Gestionar referencias, perfiles y dependencia de proyectos. | Mostrar ubicación y uso; poder desvincular y eliminar. Antes de borrar, explicar proyectos afectados; revocar uso impide nuevas generaciones de esa voz e invalida aprobaciones para nueva producción. Conservar histórico coherente sin referencias activas rotas. |

Antes de procesar una voz personalizada, solicitar una declaración clara de que es propia o de que se cuenta con permiso para ese uso. Registrar esa decisión y su alcance con el perfil. No prometer verificación de identidad si no se implementa. La app explica si el procesamiento es local; cualquier envío a un provider externo requiere una elección explícita que identifique el destino y los datos enviados. No hacer cargas externas silenciosas.

La grabación original es un archivo de entrada que debe conservarse mientras el perfil la necesite; no se puede regenerar desde SQLite. SQLite guarda su registro, relación, ubicación, checksum y autorización, y sigue siendo la fuente activa de selección y estado del proyecto. El archivo de voz no reemplaza `intent.json`, `manifest.json`, los tres assets ni el set. Un perfil de voz es una selección auxiliar de la intención vocal, no una cuarta pieza musical obligatoria.

## Arquitectura y persistencia pendientes

Mantener servicios pequeños para preparación, selección de voz, referencias, evaluación y aprobación. Explorers preparan drafts; builders ensamblan set/sample/canción; providers producen audio o voz; el pipeline mezcla/exporta; la evaluación juzga el resultado. Ningún provider decide por sí mismo que una canción está aprobada.

El `ModelOrchestrator` agenda preparación del perfil, generación y evaluación pesada según recursos. Handoffs mediante tasks, estados y DB; el assistant retoma desde el contexto persistido. Guardar un formulario o seleccionar una voz no carga ni entrena un modelo pesado. Cancelación y reintento tienen alcance explícito; reintentos equivalentes usan identidad de solicitud para evitar duplicados.

Extender SQLite con registros versionados para preparación inicial, perfiles y referencias vocales, revisiones de inputs, evaluaciones y aprobaciones; definir migraciones antes de escribir endpoints. Registrar fase, actor/provider, estado, mensaje, fecha, task/model run y versión del artefacto cuando aplique. `set.json`, `intent.json`, `manifest.json` y los informes exportados se regeneran desde DB sin sobrescribir estado activo.

Los contratos HTTP futuros deben cubrir preparar/reanudar idea, seleccionar voz, importar/preparar perfil, generar/revisar sample por set, consultar evaluación, aprobar versión, generar final y descargar artefacto por proyecto. Son operaciones propuestas, **no endpoints existentes**. Precisar payloads, errores, idempotencia y relaciones `set_id`/`song_id` en el sprint correspondiente. Validaciones obligatorias se aplican en servidor y UI, incluyendo llamadas directas.

## Verificación y criterios de entrega

| Entrega | Evidencia necesaria |
| --- | --- |
| Flujo y estado | SQLite temporal: DB vacía, recarga de preparación, tres piezas, selección de variantes, dos proyectos, fallos de guardado/provider, cancelación, reintento y resultados tardíos. |
| Sample obligatorio | Rechazo desde cada ruta final de sample ausente, de otro set, desactualizado, no aprobado y mock para producción real; aceptación de una versión vigente. Cambios creativos invalidan, cambios administrativos no. |
| Calidad automática | Archivos de prueba válidos y dañados, señal no finita, silencio inesperado, saturación y export equivocado. Informe con perfil versionado; evaluación incompleta impide afirmar calidad verificada. |
| Voz personalizada | Mocks para contratos y prueba real separada de canto: referencia autorizada, fallo de preparación, voz no soportada, cambio de perfil, borrado y recarga. Prueba hablada no acredita canto. |
| Calidad de escucha | Corpus versionado con distintos estilos, voces y letras en español. Escucha de muestras y canciones completas por personas amateur y revisores de audio; registrar inteligibilidad, naturalidad, identidad, mezcla y fallos por tramo. |
| Usabilidad | Piloto propuesto de al menos cinco personas sin experiencia musical: crear desde una idea, elegir piezas/voz, escuchar sample, pedir ajuste y descargar. Registrar asistencia, tiempo, errores y dónde se detienen. |

Como objetivo inicial del piloto, al menos cuatro de cinco participantes deben completar el recorrido sin intervención del facilitador y comprender la diferencia entre muestra, borrador y final. Para escucha, usar una escala de 1 a 5 con ejemplos de referencia y exigir mediana de al menos 4 en inteligibilidad, naturalidad vocal y balance, sin defectos graves pendientes. Son metas de producto propuestas, no resultados obtenidos ni una garantía estadística; revisarlas con evidencia y documentar desacuerdos. El parecido de voz se evalúa separadamente cuando aplica.

Una entrega debe registrar qué se verificó con mocks, qué se escuchó con audio real, qué runtime se probó y qué quedó pendiente. No anunciar «excelente calidad» ni voz personalizada disponible hasta completar su evidencia específica. Mantener actualizados README, roadmap y el contrato afectado; conservar los diagnósticos históricos.
# Avance S01 — 2026-10-04

`SampleGate` se aplica a cierre histórico, servicio full-song directo, mastering, creación de exportación y descargas finales. El recorrido mock conserva sus comprobaciones de set/aprobación/vigencia. La consulta de exportación recalcula disponibilidad actual; un manifiesto antiguo no acredita autorización vigente. La producción real permanece bloqueada porque todavía falta implementar la evidencia del sample real representativo. Veinte pruebas de política, guía y sets aprobadas; estas pruebas no acreditan calidad audible ni aceptación de usuarios.
