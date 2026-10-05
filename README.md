# Song AI

Song AI es un estudio musical local asistido por IA para crear canciones completas desde una idea creativa hasta exportables finales. La aplicacion corre localmente sin Docker, guarda el trabajo en SQLite dentro de `data/` y mantiene separados los artefactos de letra, plan musical, MIDI, audio y exportacion.

El objetivo actual es generar canciones locales con herramientas gratuitas. El modo pro/pago esta pausado.

La [guía de documentación](docs/README.md) indica qué especificación usar para cada cambio y separa planes vigentes de reportes históricos.

## Estado Actual

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

Comando principal para ejecutar la aplicacion:

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
