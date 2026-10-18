# Recorrido visual de Generar — 2026-10-17

## Recorrido visible para una canción con ficha confirmada

1. En **6. Generar**, la pantalla indica **2 de 3: prepara el plan, revisa la letra y apruébalo**. «Ir al plan» lleva al control de preparación.
2. **Preparar el plan de esta canción** abre la letra actual y pone el foco en el editor. El aviso superior cambia a «Crear plan para revisar» y lleva al formulario. **Crear plan para revisar** guarda una propuesta de plan, sin generar audio.
3. La pantalla muestra lo que recibirá ACE-Step, incluida la letra exacta. «Ir a aprobar el plan» lleva al control de aprobación. El usuario confirma expresamente la letra y pulsa **Aprobar este plan y letra**.
4. La pantalla muestra **3 de 3: plan aprobado** y **Generar canción completa** al inicio del panel. El plan aprobado queda consultable en un desplegable. El sample previo sigue siendo opcional.
5. Tras solicitar la generación, la actividad y Studio sirven para seguir el proceso, escuchar el resultado y revisar los archivos. Un archivo generado no constituye aprobación del audio.

Si faltan la ficha confirmada, un plan vigente o los recursos necesarios, la acción final permanece bloqueada con un siguiente paso visible.

## Verificación Playwright en datos aislados

Se copió `data/qa_chat_controls_20261009` a `data/qa_visual_plan_20261017` y se sirvió solo en `127.0.0.1:8028`, con autostart de LLM, bootstrap y monitor de recursos desactivados. La sesión habitual en el puerto 8000 y Alma original no se modificaron.

Playwright con Chrome a 1440 × 900 recorrió Biblioteca → cargar Alma QA → Generar → preparar plan → revisar propuesta → confirmar y aprobar plan. El backend QA respondió a la creación y aprobación reales del plan; el estado pasó de ausencia de plan a `candidate` y después a `approved`. El botón final quedó visible y habilitado. Playwright comprobó que pulsarlo envía `POST /api/pro/projects/{song_id}/master`. Esa solicitud final se interceptó y respondió con un error QA controlado para evitar ejecutar ACE-Step. No se generó audio ni se evaluó la calidad musical.

El recorrido detectó dos defectos de interfaz: la aprobación y el botón final quedaban debajo de una ficha extensa; además, al terminar la carga del proyecto podía restaurarse un paso guardado por encima de una navegación más reciente. El plan ahora presenta los parámetros en una cuadrícula compacta, la aprobación sigue al resumen y el botón final aparece al inicio tras aprobar. La carga conserva la ruta elegida durante sus llamadas de red.

Verificación adicional: 64 pruebas Node aprobadas, build Vite de 41 módulos y `git diff --check` sin errores. La aceptación con una persona sin experiencia musical, la ejecución ACE-Step real y la escucha de la canción permanecen como comprobaciones separadas.

## Continuación verificada: exportación y descargas

La prueba inicial terminaba antes de exportar. Se continuó con una copia independiente de `data/qa_high_level_1791602467245496700`, que ya contenía una canción completa generada en una prueba real anterior, un plan aprobado y los tres formatos finales. Se sirvió solo en `127.0.0.1:8029`; las rutas de artefactos de la copia se actualizaron a su directorio QA. Se retiraron del registro SQLite copiado las entradas del ZIP y del manifiesto para comprobar que la exportación los creaba de nuevo. No se modificó la fuente ni el proyecto habitual.

Playwright cargó Alma QA, pasó de Generar a Studio y encontró **Preparar archivos para descargar** visible y habilitado. El `POST /api/pro/projects/{song_id}/export` respondió 200: el servicio creó ZIP y manifiesto en la copia QA. Studio actualizó la lista a WAV, MP3, FLAC, ZIP y Metadata JSON, todos con enlace de descarga. Las cinco rutas devolvieron 200 y contenido no vacío; el botón **Descargar** del ZIP produjo una descarga completa en Chrome. El ZIP descargado pasó `ZipFile.testzip()` y contiene siete entradas: candidato, WAV, MP3, FLAC, `song_spec.json`, `ace_plan.json` y `lyrics.md`. Los checksums de los cinco artefactos exportados coincidieron con SQLite.

Esta verificación detectó que **Preparar export** estaba oculto en un desplegable y ligado a un objeto sin `canRun`, por lo que quedaba deshabilitado. Se añadió la acción visible en Studio y se aclaró que **Actualizar lista de archivos** solo consulta. El botón de exportación cambia a **Volver a preparar archivos** cuando ya existe ZIP. Se oculta el estado heredado de «Generar final local» cuando la canción ACE-Step vigente está disponible.

La generación ACE-Step y la exportación se verificaron en ensayos distintos: la primera solicitud se interceptó en el recorrido visual anterior; esta continuación usó audio real preexistente y ejecutó la exportación y descargas sin regenerarlo. No se afirma una ejecución continua nueva de ACE-Step ni aceptación audible. Los archivos disponibles dependen de los artefactos del proyecto; esta copia produjo cinco descargas, no una promesa de MIDI o stems universales.
