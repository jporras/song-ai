# Migración de intención histórica a MusicSpec

## Resultado aplicado — 2026-10-07

La migración de datos de Isabella y Alma está terminada en la DB real. Son los dos proyectos activos y conservan sus IDs; no se crean duplicados ni una biblioteca histórica alternativa. Tres assets independientes por proyecto reemplazan la selección compartida. El fixture de smoke test y drafts sustituidos quedan fuera del listado normal sin borrar registros/archivos. Su recuperación sigue posible por ID y respaldo.

`ProjectConsolidation` recibe la resolución creativa investigada; `scripts/consolidate_song_projects.py --apply` crea primero respaldo consistente SQLite y copia de archivos, valida traducción ACE-Step sin persistir confirmación, aplica y registra task/eventos/revisión. Una segunda ejecución completa no escribe otra revisión. La fuente íntegra (ficha, fases, assets) y conflictos/resoluciones quedan en SQLite dentro de las tasks de los proyectos. Inferencia Codex autorizada por el usuario; no simula ejecución Gemma/Qwen. Todos los campos del catálogo quedan recuperados/propuestos o identificados como opcionales/delegados. No se convierten sliders DSP ni MIDI en parámetros ACE-Step.

Reglas semánticas aplicadas:

- Nombre y letra editada de Alma prevalecen sobre el destinatario Isabella heredado.
- Texto de `lyricsEditor.content` se conserva literalmente, incluidas tildes; los datos no estaban corruptos.
- Estructura: Isabella intro/verso/coro; Alma verso/coro/verso/coro/verso. No inventar puente ni eliminar repetición intencional de coro.
- Instrumentos: Isabella piano/caja de música/pad/cuerdas cinematográficas; Alma piano/caja de música/pad/cello/violín. BPM 72 y C major prevalecen sobre el mock compartido de BPM 96.
- Una voz principal según opciones guardadas; se resuelven armonías/call-response contradictorios de plantilla. Los detalles expresivos se conservan en MusicSpec con limitación de ejecución explícita.
- Tiempos individuales de secciones delegados, no inventados ni deducidos del archivo final; objetivo histórico de 120 segundos conservado.
- Production regenera sus documentos de letra desde SQLite. `lyrics_approved.json` queda pendiente, sin aprobación Qwen ficticia.

Los seis archivos finales originales permanecen intactos por SHA-256; ambos WAV miden 120 segundos. La evidencia de existencia/integridad no demuestra qué nombre cantan ni calidad/fidelidad a la ficha consolidada. Revisión creativa y escucha siguen pendientes. La revisión nueva queda `pending`; no se atribuye aceptación por migrar.

Informe y respaldo: `data/rescue_20261007/consolidation_report.json`, `data/rescue_20261007/before_consolidation/`. Ensayo previo y Playwright en copia QA; comprobación posterior de la DB real verifica dos proyectos, seis assets, identidad de letras y checksums. No hay nueva generación ni carga LLM.

La migración de estos datos está cerrada. Retirar todos los consumidores/formularios antiguos del producto sigue siendo trabajo de S02/S03/S05: la migración de información no equivale a completar el rediseño del Song Builder.

## Entrega inicial de la herramienta genérica (contexto de desarrollo)

Primera entrega 2026-10-07, alcance S02/S03/S05. No borra fases, assets ni revisiones. La inferencia actual es determinista y explícitamente identificada; no constituye ejecución Gemma/Qwen.

`POST /api/pro/projects/{song_id}/spec/legacy-migration` prepara una propuesta desde el set vinculado y fases SQLite. Incluye contexto completo de fases y detalle de los tres assets seleccionados (sus archivos originales/exports de intención y contenido cuando existen); fuentes ausentes se identifican. No usa defaults actuales del frontend ni otro proyecto.

El primer mapper traduce campos conocidos de Intent/Music Plan/Lyrics/Voice. Un valor faltante con fuentes coincidentes es candidato; discrepancias entre fuentes y valores actuales son conflictos. Datos no mapeados permanecen en contexto y en fuentes originales; no se presentan como controles ejecutables. Los datos de assets se conservan para revisión/inferencia posterior, no se sintetizan semánticamente en esta primera entrega. Origen histórico no comprobado: guardar un default no lo convierte en deseo USER.

`POST .../spec/legacy-migration/apply` aplica exclusivamente campos faltantes seleccionados de la propuesta vigente. Verifica revisión y hash de fuentes, no acepta valores arbitrarios ni sobrescrituras. Crea una revisión pending, con procedencia histórica inferida, fuentes/fechas disponibles y regla. Task SQLite conserva propuesta, contexto y revisión resultante; JSON continúa siendo exportación. La revisión técnica/creativa posterior sigue requerida, sin aprobar por migración.

UI: Revisar datos históricos → leer añadidos/conflictos → Migrar datos faltantes o descartar. Este paso no pide permiso técnico para investigar, pero mantiene revisión explícita de deseos antes de guardarlos. Datos históricos aún no migrados pueden continuar consultándose.

Evidencia: 20 pruebas backend dirigidas, 15 frontend y build aprobados. Playwright MCP en copia QA obtuvo HTTP 200, tres añadidos (brief, compás, arco dinámico) y tres conflictos (tipo, BPM, voz); conservó dos fases y tres assets. Aplicación comprobada en SQLite temporal mediante tests; no aplicación masiva sobre proyectos reales, inferencia LLM ni audio.

Pendiente para retirar circuitos históricos: ampliar cobertura de intención con Gemma/Qwen desde tasks/contexto; resolver contradicciones mediante propuestas; integrar todo el catálogo creativo y convertir formularios antiguos en consumidores de MusicSpec. Solo retirar código cuando sus datos/consumidores tengan reemplazo verificado. No borrar servicios pagos pausados ni hacer limpieza destructiva.
