# Revisión del flujo para una persona sin experiencia musical

Fecha: 2026-10-03. Alcance: revisión documental y del código visible; no se hizo una prueba de usabilidad con personas ni se generó audio real. Las propuestas de esta página están **pendientes de implementación**.

El contrato complementario de [calidad de audio y voz personalizada](AMATEUR_AUDIO_VOICE_STEERING.md) define controles técnicos, revisión por escucha, sample representativo y alcance futuro para usar una voz de referencia. No existe todavía una opción de copiar una voz humana en el producto. Las prioridades de ambos contratos se integran en [ROADMAPP.md](ROADMAPP.md).

## Conclusión

La arquitectura de tres assets y el acompañamiento de Gemma son una base útil, pero el recorrido actual exige entender conceptos de producción antes de escuchar un primer resultado. La revisión identifica obstáculos para completar el flujo sin ayuda externa. Se recomienda una guía progresiva sobre el proyecto activo, manteniendo las fases técnicas disponibles para quien las necesite. Es una hipótesis de diseño que debe validarse con usuarios amateur antes de afirmar que es la mejor experiencia.

## Usuario y decisiones del recorrido

`AGENTS.md` §16 define al usuario principal como una persona que puede describir una idea, emoción u ocasión sin conocer composición ni producción musical. La app debe ayudarle a elegir un resultado coherente con esa idea. Las tres piezas siguen siendo obligatorias, pero pueden prepararse con asistencia de IA y valores sugeridos; conocer teoría musical o componer manualmente no es requisito para avanzar.

| Momento | Decisión del usuario | Asistencia de la app |
| --- | --- | --- |
| Idea | Qué quiere transmitir, idioma y preferencias que le importan. | Preguntar solo lo necesario y proponer estilo, tempo, tonalidad e instrumentos con una explicación breve. Destinatario y ocasión son opcionales cuando no aplican. |
| Tres piezas | Elegir o ajustar una base musical, una melodía de voz y una letra. | Preparar opciones separadas, resumir sus diferencias y mostrar cuál falta. Si son mocks, indicar qué se puede revisar y qué todavía no se puede escuchar. |
| Set | Confirmar que las tres selecciones representan su idea. | Validar existencia, tipo y compatibilidad, conservar las tres intenciones y crear el set después de la confirmación. |
| Sample | Revisar el fragmento y decidir si le gusta o qué cambiar. | Explicar qué representa el sample, su relación con el set y los ajustes que requieren regenerarlo. |
| Canción y descarga | Iniciar la producción completa y elegir el archivo de salida. | Explicar tiempo estimado y disponibilidad, mostrar ejecución real y ofrecer descargas verificadas. |

Los cinco hitos expresan progreso, no obligan a crear cinco pantallas nuevas ni un asistente rígido. El usuario puede volver a editar; las dependencias indican qué debe actualizar. La conversación complementa acciones visibles: completar el flujo no debe depender de adivinar qué pregunta escribirle a Gemma. La preparación previa al set debe conservarse como preparación de idea/drafts, sin crear un proyecto musical incompleto ni heredar silenciosamente datos de otro proyecto.

## Contratos que debe conservar la experiencia

La asistencia debe producir progresivamente la [especificación completa Gemma/Qwen](SONG_SPEC_GEMMA_QWEN_CONTRACT.md): deseos y decisiones trazables, detalles técnicos propuestos, viabilidad y criterios de calidad. El usuario confirma un resumen creativo y puede consultar el documento completo sin tener que redactarlo ni dominar sus parámetros.

- Un proyecto/set solo se crea con un draft seleccionado de instrumental, melodía y letra. El asistente debe decir cuál falta.
- El usuario confirma las sugerencias de IA antes de guardarlas; Guardar no genera audio. SQLite conserva el estado activo; `intent.json`, `manifest.json` y `set.json` son snapshots regenerables.
- Los tres assets permanecen separados. Los providers local/pro son intercambiables y el sistema puede operar con mocks.
- Según `AGENTS.md` §§5-6, la secuencia obligatoria es set válido → sample → canción completa. La interfaz y todos los endpoints de generación final deben respetar el mismo requisito.
- Gemma usa el contexto del proyecto activo y propone solo cambios compatibles con sus tres intenciones y descripción. Los handoffs internos se registran mediante estados, tasks y persistencia, no mediante prompts encadenados.
- La selección de voz forma parte de la intención vocal; un perfil personalizado es opcional y no sustituye ninguna de las tres piezas. La aprobación del sample se vincula a sus inputs y a la versión escuchada.
- Un sample mock permite evaluar el recorrido mock. La aprobación para producción real requiere una muestra representativa de la voz, provider y configuración relevantes del final; la canción completa también se evalúa por escucha y controles técnicos.

## Interfaz que acompaña la guía de IA

La aplicación debe ofrecer controles visibles para recibir las decisiones del usuario y enseñar las opciones. Gemma explica y acompaña; Qwen propone parámetros y valida coherencia; la UI permite elegir, corregir, comparar y guardar. Conversación y formularios usan la misma especificación versionada. Catálogo completo y sincronización: [SONG_SPEC_GEMMA_QWEN_CONTRACT.md](SONG_SPEC_GEMMA_QWEN_CONTRACT.md), SP-07 a SP-09.

| Hito | Configuración y acciones visibles necesarias |
| --- | --- |
| Idea | Texto de idea, idioma, emoción, estilo/preferencias y duración propuesta; ocasión/destinatario opcionales. Explicaciones, selección libre/asistida y propuesta de IA revisable. |
| Tres piezas | Instrumental: instrumentos, energía y ritmo. Melodía de voz: carácter/timbre, tipo de voz y fraseo. Letra: editor por secciones, tema/tono, nombres y placeholders. Selectores explícitos de variantes, resúmenes y comparación; detalle de parámetros técnicos relacionados. |
| Set | Resumen de los tres assets y configuración conjunta, conflictos/faltantes, valores propuestos/delegados y confirmación. Volver a una pieza sin perder las demás. |
| Sample | Fragmento/duración propuestos, configuración/voz representada, vigencia, reproductor para audio o etiqueta mock. Revisar, aprobar y capturar ajustes con explicación de regeneración. |
| Canción y descarga | Resumen de producción/disponibilidad, ejecución, reproductor completo, evaluación/aceptación, ajustes y versiones. Formatos/archivos realmente soportados, verificación y descarga por proyecto. |

Mantener visible el mapa del recorrido con progreso, bloqueos y siguiente acción. Ofrecer «Ver todas las opciones» y ficha por familias con búsqueda/detalle. «Ajustes avanzados» expone controles técnicos del catálogo sin exigir abrirlos para crear. Los parámetros automáticos o no soportados son consultables con su explicación; no mostrar habilitado un control que no cambia el resultado.

Cada control tiene etiqueta humana, explicación breve, valor guardado/borrador, recomendación IA identificada y error junto al campo. Usar texto/editor para idea/letra; opciones para idioma/formato; selección múltiple para instrumentos; número con unidad/rango para parámetros precisos; lista de secciones cuando se soporte; reproductor para comparar audio. Permitir lenguaje común y propuesta técnica equivalente, cuyo valor puede consultarse en la ficha.

Para cada propuesta mostrar cambio y motivo, con aceptar/editar/descartar. Aceptar deja un borrador; Guardar persiste; Generar ejecuta. Confirmación agrupada y «Que la IA lo proponga» registran alcance y valores, sin exigir cada número ni aceptar por silencio. Datos desconocidos dicen «Por decidir»; ejemplos/defaults no figuran como guardados.

Controles con etiquetas accesibles, teclado, errores/estados que no dependan solo del color y layout usable en pantallas pequeñas. Guardar valida en UI y servidor, conserva edición al fallar y protege navegación. Recarga/cambio de proyecto hidrata SQLite y avance de guía propio. Respuestas IA tardías no sobrescriben ediciones locales posteriores.

Aceptación SP-09: con DB vacía, completar el camino mediante controles visibles con ayuda opcional de Gemma; editar el mismo parámetro desde UI/propuesta conversacional y comprobar documento/backend tras guardar/recargar. Revisar cobertura de campos, delegación, opciones no soportadas, errores, conflictos, accesibilidad y dos proyectos. Probar que una persona amateur comprende las opciones y pide ayuda sin conocer nombres técnicos.

## Hallazgos de la revisión inicial y acciones propuestas

| Prioridad | Hallazgo comprobable | Riesgo para un principiante | Cambio propuesto | Criterio de aceptación |
| --- | --- | --- | --- | --- |
| P0 | `frontend/index.html` crea el proyecto desde Biblioteca después de preparar tres “drafts” y elegir IDs; `frontend/src/app.js` arranca con un ejemplo de canción de cuna. | Puede confundir el ejemplo con datos propios y crear assets sin comprender qué representa cada uno. | Mostrar primero una bienvenida breve: “¿Para quién es la canción y qué quieres transmitir?”. Etiquetar el ejemplo como ejemplo editable. Presentar las tres piezas en lenguaje común, con explicación de una línea y progreso 0/3 a 3/3. Mantener elección explícita de cada draft. | Con DB vacía, una persona puede explicar qué falta y crear un proyecto sin API ni saber qué es un draft; ningún valor de ejemplo se presenta como guardado. |
| P0 | El flujo principal de Production muestra Mastering/Full Song y “Generar final local”; la UI no ofrece crear/revisar un sample del proyecto activo. El sample existe en la ruta legada (`/api/samples`). | Se salta una revisión corta antes de una generación larga y se contradice `AGENTS.md` §§5-6. | Definir un sample del **set activo** como paso obligatorio y visible: crear, escuchar o leer si es mock, ajustar, aprobar. Unificar el bloqueo en backend para la ruta local y Production, con evento en SQLite y snapshot derivado. No seleccionar el “último set” global cuando haya un proyecto activo. | Con set sin sample, las acciones finales muestran “Primero crea y revisa un sample” y la API rechaza generación; con sample de otro set también rechaza; con sample válido del set activo permite avanzar. |
| P1 | La barra lateral expone Intent, Lyrics, Music Plan, MIDI, Instrumental, Voice y Production desde el inicio. README “Cómo generar una canción” omite la revisión del sample y da un recorrido distinto del planning original. | No queda claro qué pasos son obligatorios, cuáles son ajustes opcionales ni cuál es el próximo clic. | Mostrar una ruta principal de cinco hitos: Idea → Tres piezas → Proyecto listo → Sample → Canción y descarga. En cada hito, una acción siguiente y el motivo de cualquier bloqueo. Agrupar MIDI, stems, proveedores y diagnóstico bajo “Ajustes avanzados” sin retirar las fases. Actualizar README cuando exista el flujo implementado. | En DB vacía y en proyecto a medio hacer, la pantalla y Gemma indican el mismo siguiente paso; un usuario puede avanzar sin abrir un ajuste avanzado. |
| P1 | Los selectores muestran `asset_id`, `summary` y fecha; Biblioteca dice “proyecto / set”, “drafts” y “lyrics”. | Elegir entre variaciones es difícil sin información musical comprensible. | Mostrar nombre corto, estilo, ánimo, idioma o voz según tipo y un resumen de la intención; dejar ID y fecha como detalle. Usar “base musical”, “melodía de voz” y “letra” en la ruta guiada. | Con dos variaciones de cada tipo, el usuario identifica cuál eligió y puede volver a cambiarla antes de crear el set. |
| P1 | Production muestra tiempos, dispositivo, runtime, procesos y varias acciones de salida. | Puede pulsar una tarea cara o lenta sin saber el resultado esperado ni el costo temporal. | Antes de ejecutar, resumir qué se producirá, duración estimada, tipo de resultado (mock/preview/final), requisitos y posibilidad de cancelar. Mostrar progreso en lenguaje común; dejar datos de hardware en detalle técnico. | Ningún estado de “listo” se confunde con “generado”; los errores ofrecen una acción de recuperación y no borran la configuración guardada. |
| P2 | Gemma tiene una pregunta inicial “¿Qué sigue para terminar esta canción?”, pero el primer paso todavía depende de navegar y preparar drafts manualmente. | La ayuda puede ser reactiva cuando se necesita orientación desde el arranque. | Ofrecer tres preguntas sugeridas según estado: “Ayúdame a describir la canción”, “¿Qué pieza falta?” y “¿Qué reviso en el sample?”. Toda sugerencia de formulario queda como borrador revisable, con explicación breve y botón Guardar. | Las recomendaciones coinciden con SQLite y los assets seleccionados; sin proyecto activo, Gemma dirige a crear las tres piezas sin inventar progreso. |

## Recorrido objetivo

1. **Idea:** describir ocasión, destinatario, idioma, emoción y preferencias esenciales. BPM y tonalidad tienen valores sugeridos editables. La persona sabe que aún no creó una canción.
2. **Tres piezas:** preparar y comparar base musical, melodía de voz y letra por separado. Indicar “1 de 3”, “2 de 3”, “3 de 3”; permitir corregir cada pieza y conservar su intención.
3. **Proyecto listo:** seleccionar una variación de cada tipo, revisar un resumen conjunto y confirmar el set. Mostrar incompatibilidades concretas antes de confirmar.
4. **Sample:** generar un fragmento corto del set activo; etiquetar claramente si es audio, guía o mock. Revisarlo y aprobarlo o volver a las piezas. Cambios posteriores que afecten el resultado marcan el sample como desactualizado y requieren regeneración antes del final.
5. **Canción y descarga:** explicar tiempo y provider disponible; generar desde el sample aprobado, mostrar progreso y resultado, y ofrecer solo exportables verificados del proyecto activo.

La ruta avanzada conserva edición por fases, Music Plan, MIDI, Instrumental, Voice, diagnósticos y control de providers. La ruta guiada y la avanzada deben compartir el mismo estado SQLite y las mismas validaciones.

## Orden de implementación

1. **Resolver la contradicción del sample (P0):** contrato de estado por `set_id`, invalidación al cambiar inputs, bloqueo en todos los endpoints finales y acción visible de revisión. Esta es la condición previa para presentar el recorrido como listo para producción.
2. **Guiar el primer proyecto (P0):** bienvenida, ejemplo explícito, lenguaje común, contador de las tres piezas y mensajes de faltantes. Reutilizar las acciones actuales de preparación y selección sin autoelegir variaciones ajenas.
3. **Una sola acción siguiente (P1):** navegación guiada y mensajes de Gemma derivados del mismo estado. Conservar acceso avanzado para quien lo busque.
4. **Comparar y generar con confianza (P1/P2):** resúmenes de assets, revisión previa a procesos largos, progreso, errores recuperables y preguntas sugeridas.

Las entregas UX-01 a UX-08, QA-01 a QA-06 y VO-01 a VO-06 tienen aceptación detallada en el contrato complementario. El roadmap reúne su orden sin duplicar criterios ni dar por implementadas propuestas.

## Verificación del futuro cambio

Probar al menos estos recorridos con SQLite temporal: primera visita sin proyecto; dos variantes de cada asset; set con una pieza faltante; sample ausente, ajeno y desactualizado; sugerencia IA no confirmada; fallo de provider; recarga a mitad de proceso; dos proyectos con exportables distintos. Medir si una persona nueva puede crear y revisar un sample sin asistencia externa, cuánto tarda y dónde se detiene. Mantener pruebas de validación en backend para las reglas de set/sample/final y una prueba de interfaz del camino principal.
