# AC-ACE-USER-01 — Fidelidad de decisiones USER al request

Estado: criterio incorporado por el usuario el 2026-10-07. Pruebas/resultados pendientes; añadir este contrato no acredita cobertura aprobada.

> Para cada input ACE-Step conectado, demostrar mediante test que una decisión USER introducida desde MusicSpec llega sin modificación no autorizada al AceStepRequest; y que cualquier transformación necesaria queda trazable.

## Alcance

Avance 2026-10-07: `tests/test_ace_step_user_input_acceptance.py` comprueba mapping y captura del wrapper en 13 combinaciones compatibles, con cobertura de los 21 nombres de inputs actualmente emitidos. Planes nuevos incluyen `input_trace` y la incorporan al hash. 23 pruebas backend dirigidas aprobadas incluyendo regresión de compilador, ejecución, opciones y revisión. Alcance parcial: no cubre aún UI/chat/persistencia, locks, autorizaciones creativas, verificación de archivos ni gates completos. La traza de lyrics identifica correctamente argumento de preview no confirmado, sin inventar aprobación USER; la identidad del texto sí se comprueba.

Derivar casos del perfil de capacidades conectadas y del mapping MusicSpec → request, no de todas las firmas nativas. Cubrir argumentos directos, caption/lyrics compuestos, referencias y opciones condicionales de task/model/API. Detectar entradas conectadas nuevas sin caso de aceptación; distinguir valores SYSTEM de decisiones USER.

Cada caso identifica input/ruta, proyecto/revisión, valor USER original, requisitos/locks, resultado esperado independiente del mapper probado y request obtenido. Capturar también argumentos/archivos del wrapper sin cargar pesos. No construir expectativas con la misma función bajo prueba.

## Reglas

1. Preservación directa: valor y significado llegan al destino; IA, inferencias y defaults no sobrescriben USER. MusicSpec de entrada permanece intacta.
2. Transformación mecánica declarada: guardar campo origen/destino, antes/después, regla/versionado, motivo y revisión/request. Español → es, 4/4 → 4 o unidades → segundos requieren trazabilidad, sin otra confirmación creativa si preservan significado.
3. Transformación creativa: cambiar, resumir, traducir, redondear o eliminar contenido no queda autorizado por necesidad técnica. Presentar diff y obtener aprobación cuando cambie contenido/significado; registrar autorización y revisión. Caption compuesto debe enlazar cada requisito a su fragmento o limitación, no solo ser texto no vacío.
4. Conflicto/imposibilidad: bloquear request ejecutable ante requisito obligatorio no transmisible; conservar deseo. No corregir valores inválidos ni truncar texto silenciosamente.
5. Referencias: USER selecciona artefacto; SYSTEM verifica proyecto/checksum y resuelve ruta. Traza ID/checksum → argumento; no sustituir archivo ni atribuir ruta derivada al usuario.
6. Vigencia: request identifica revisión/hash y perfil/reglas. Cambios USER requieren nueva compilación/confirmación pertinente e invalidación del plan/sample afectados.

## Casos mínimos

| Caso | Resultado esperado |
| --- | --- |
| USER BPM 97, IA propone 72, default diferente | Request BPM 97 y spec intacta. |
| Español y 4/4 | es y 4 con antes/después/regla trazados. |
| Frase literal con acentos y línea protegida | Lyrics conserva texto; direcciones no se convierten en versos. |
| Instrumentos, expresión y clímax del coro | Requisitos transmisibles trazados al caption; lo no conectado identificado, no omitido silenciosamente. |
| Caption/lyrics supera límite | Error; no truncamiento ni request ejecutable. |
| BPM decimal o guidance incompatible con Turbo | Rechazo; no redondeo/reemplazo. |
| Fuente/referencia seleccionada | ID/checksum/archivo coinciden; rechazar ajeno o alterado. |
| Cambio USER después de plan aprobado | Request anterior no figura vigente; revisión y gates actualizados. |
| Handler/alto nivel/LM opcional | Captura verifica traducción por ruta; cambios no autorizados bloqueados. |
| Input conectado nuevo | Matriz detecta caso ausente; aceptación no puede declararse completa. |

## Sprints y evidencia

S00: inventario/perfil/cobertura; S03–S05: persistencia/procedencia; S06A–S06B: controles/chat → MusicSpec; S06C: compilación y wrapper por rutas/modos; S06D: vigencia tras feedback. Cerrar una capacidad conectada exige su caso aprobado con evidencia.

README registra inputs/rutas cubiertos y casos pasados/fallidos/omitidos, transformaciones y pendientes. Mocks/capturas prueban fidelidad del pedido; no obediencia del audio, identidad vocal, calidad acústica ni usabilidad, que requieren evidencias separadas.

## Avance 2026-10-09: frontera de ejecución

Contexto de ejecución contiene payload aprobado completo, revisión/hash y checksums de audio verificado. `runtime_input_trace` coteja los 21 campos conectados con valores y archivos realmente leídos por el CLI antes de pesos o reemplazo de output. Pruebas verifican igualdad, cambios no autorizados por cada campo, sustitución de archivo y rechazo en CLI real; las trece combinaciones existentes comprueban el payload completo conservado en el contexto. Lote de 41 pruebas aprobado. No declara completa la cobertura de UI/chat/persistencia ni la obediencia del audio. Ver `S00_FULL_INPUT_RUNTIME_CONTRACT_20261009.md`.

## Avance 2026-10-09: persistencia y confirmacion reales

`tests/test_user_input_persistence_request.py` recorre router autorizado → SQLite → reapertura → confirmacion persistida → compilador → contexto/argv. Cubre 20 controles, transformaciones Spanish→es y 6/8→6, proyecto aislado y rechazo de revision antigua. Guardar explicitamente un valor sin cambiarlo registra USER y conserva lock; la procedencia anterior queda indicada. Letra sigue argumento de preview no confirmado por editor. Lote 27 pruebas aprobado; matriz completa UI/chat, audio seleccionado y locks de letra sigue pendiente. Mensaje de set corregido para no prescribir MIDI/mastering como insumos obligatorios.
