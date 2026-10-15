# Chat → formulario → MusicSpec: verificación

Fecha: 2026-10-08. S03/S05; evidencia parcial, no cierre de sprint.

Playwright MCP sobre `http://127.0.0.1:8015`, servidor con SQLite de prueba `data/qa_consolidation_final_20261007`. Modelos desactivados, sin generación de audio. No se editaron decisiones de los proyectos originales.

| Caso | Resultado observado |
| --- | --- |
| Enviar «Cambia el BPM a 109» desde Intent de Alma | HTTP 200, propuesta 109, revisión/hash de origen, parser determinista, sin persistir |
| Usar propuesta en formulario | Control BPM muestra 109 |
| Cambiar manualmente a 111 y guardar | HTTP 200, nueva revisión con BPM 111 |
| Leer evidencia SQLite por API | `proposed_value=109`, `saved_value=111`, `review_result=user_modified`; confirmación general pendiente |
| Recargar página | Proyecto Alma y control BPM 111 recuperados |
| Enviar traza alterada con propuesta 222 | HTTP 400 con acción de consultar de nuevo; revisión vigente sin cambios |

El recorrido de una propuesta determinista y un valor modificado está verificado en navegador. No demuestra inferencia/obediencia de Gemma/Qwen, fidelidad del audio ni usabilidad con personas amateur. Pruebas backend complementan aceptación sin modificación, vigencia y ausencia de mutaciones.

Segunda comprobación: propuestas 113 BPM y 115 BPM aplicadas consecutivamente, edición manual a 117 y guardado HTTP 200. SQLite conservó ambas en orden: primera sustituida por aplicación 2, segunda modificada por el usuario; BPM final 117 y confirmación pendiente. Este caso se realizó en la misma copia QA con modelos desactivados.

Próximos criterios: propuestas originadas por modelos con evidencia de ejecución, cobertura/ayudas completas y recorrido de generación real. Servidor y navegador QA cerrados al terminar.
