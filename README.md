# Song AI

Song AI es un estudio musical local asistido por IA para crear canciones completas desde una idea creativa hasta exportables finales. La aplicacion corre localmente sin Docker, guarda el trabajo en SQLite dentro de `data/` y mantiene separados los artefactos de letra, plan musical, MIDI, audio y exportacion.

El objetivo actual es generar canciones locales con herramientas gratuitas. El modo pro/pago esta pausado.

## Estado Actual

La ruta principal es **local-first con Full Song / ACE-Step**:

- ACE-Step genera una cancion completa con instrumental y voz cantada integrada.
- La fase de Mastering del pipeline profesional puede usar `SONG_AI_FULL_SONG_COMMAND`.
- Si Full Song esta listo, `soundtrack` y `singing_voice` separados son opcionales.
- Si el sistema cae en `procedural_vocal_guide`, la app bloquea la descarga como final.

Estado esperado local cuando ACE-Step esta importable:

```text
full_song: ready
runtime: gpu_ready | cpu_extremely_slow
soundtrack: optional
singing_voice: optional
mix_and_export: ready
```

Importante: Song AI ya esta preparado para generar voz cantada real por ACE-Step, pero la calidad final depende de que ACE-Step pueda ejecutar realmente en el entorno local. Con aceleracion GPU compatible es lo recomendado; por CPU puede tardar mucho.

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

- La integracion usa `tools/acestep_generate.py` como proceso CLI local que importa `acestep.pipeline_ace_step.ACEStepPipeline`; no usa servicio HTTP.
- Cada corrida guarda `ace_step_diagnostics.json` con prompt completo, letra completa, idioma detectado, secciones, parametros de inferencia, modelo/checkpoint, tipo de salida, recursos RAM/SWAP/CPU/VRAM y error si ocurre.
- El wrapper agrega `data/provider-cache/python` al `sys.path` para que funcione desde el backend y manualmente.
- En prueba controlada con `[es]`, ACE-Step conserva acentos y Unicode, pero su tokenizador puede clasificar lineas espanolas de forma mixta (`en`/`es`) y etiquetas como `zh`; revisar `docs/ACE_STEP_DIAGNOSTIC_REPORT.md` antes de ajustar prompts.
- En Docker Desktop no hubo CUDA/iGPU/NPU visible; por eso la ruta principal se movio a local sin Docker.
- Gemma ahora trata el set/proyecto activo y Production como el mismo proyecto del usuario: las fases definen la intencion y Production ejecuta tareas/exportables. Para preguntas de estado como "que sigue" o "estoy en un proyecto activo", responde desde SQLite y los checks de la UI, no desde una suposicion libre del LLM.
- La conversacion inferior usa un layout mas amplio: 60% para respuesta y 40% para escritura. Se retiro la repeticion de nombre/contexto porque esa informacion ya vive en el sidebar.
- Production se prepara automaticamente para el proyecto activo al cargarlo desde Biblioteca. Si falta el registro interno de ejecucion, muestra `Preparar Production`, pero para el usuario sigue siendo el mismo proyecto: definicion por fases primero, ejecucion/exportables despues.
- Al preparar Production desde un set activo, el backend materializa `song_spec.json`, `lyrics.md` y `lyrics_approved.json` desde las fases guardadas en SQLite. Tambien repara automaticamente proyectos de Production enlazados (`user_id=set:<id>`) creados antes de este cambio, asi no vuelve a bloquear `Generar letra` o `Generar plan` con "la especificacion debe estar aprobada" cuando el proyecto ya fue definido en el editor.
- La carga desde Biblioteca rehidrata el proyecto desde SQLite: fases guardadas, formularios del editor, estado visual por fase, datos de Production, exportables, actividad y la ultima fase activa. Si no hay ultima fase, abre la primera fase incompleta.
- El `ModelOrchestrator` ahora incluye una revision tecnica interna desde snapshot SQLite antes de que Gemma responda estado del proyecto. El backend entrega proyecto, set, assets, fases, estado UI y Production al rol tecnico; la validacion devuelve faltantes/advertencias/siguiente accion y Gemma lo comunica al usuario en lenguaje natural.
- Production respeta el orden de artefactos: no permite ejecutar MIDI, Instrumental, Voz, Mezcla, Mastering o Export antes de que existan los archivos previos requeridos. Si la fase Music Plan esta guardada en SQLite, el backend puede materializar `music_plan.json`; si no, la accion correcta es `Generar plan`.
- El puente de Production es idempotente: listar proyectos ya no vuelve a crear eventos de preparacion si `song_spec.json`/spec aprobada existen. La actividad de Production tambien colapsa mensajes duplicados historicos para que se vea el estado real sin ruido.
- La fase actual de Production muestra `Listo para ejecutar` cuando el backend esta en `ready`; solo muestra `En curso` si el estado real del proyecto indica ejecucion o carga activa.
- Las acciones de Production bloquean doble click mientras ejecutan y muestran `Generando...` de inmediato. SQLite usa `busy_timeout` y WAL en repositorios activos para reducir bloqueos durante generaciones largas.
- `Generar voz` ahora registra etapas detalladas: prompt vocal preparado, provider seleccionado, si usa ACE-Step o no, recursos, inicio de comando/inferencia, progreso periodico y resultado. La tarjeta de Production muestra el ultimo mensaje tecnico de cada fase con actor y hora.
- `Masterizar` con ACE-Step marca el proyecto como `MASTERING/running`, registra inicio de proceso local, progreso periodico con tiempo/RAM/SWAP/CPU y fallo si ocurre. Production refresca eventos junto con recursos, muestra hora de inicio y tiempo transcurrido, y el diagnostico ahora muestra `swap libre / total` para detectar configuraciones de 2 GB frente a los 4 GB recomendados.
- Los timeouts de ACE-Step ahora terminan el grupo completo del proceso local para evitar que `acestep_generate.py` quede huérfano consumiendo CPU/RAM despues de fallar la fase.
- El timeout local de ACE-Step subio a 14400 segundos y la duracion maxima enviada al provider queda configurable con `SONG_AI_MAX_FULL_SONG_DURATION_SECONDS` para evitar limites ocultos en codigo.
- Production muestra antes de generar la duracion enviada a ACE-Step, el limite configurado de cancion, el timeout maximo y un estimado de tiempo de Mastering segun el runtime local. Si el estimado supera el timeout o la duracion se recorta por limite, la UI lo advierte para que el usuario pueda quitar secciones o reducir duracion.
- Si la app local se reinicia mientras una fase esta `running`, el arranque marca esa fase como interrumpida en SQLite. La UI toma el ultimo evento real de cada fase, asi no muestra `En curso` por eventos antiguos cuando ACE-Step ya no esta corriendo.
- Limpieza post-Docker: se retiraron los archivos `Dockerfile`, `docker-compose*.yml`, `.dockerignore` y el helper de contenedores LLM. El monitor de recursos usa `visible_memory_limit_mb` para describir memoria visible sin terminologia Docker y migra snapshots antiguos de SQLite de forma compatible.
- Smoke completo local: `tools/run_small_local_song_flow.py` incluye `--fast-full-song-provider` para validar todas las fases y exportables con un provider local rapido, sin instalar dependencias ni modificar `.env`.
- Steering de runtime documentado: `docs/RUNTIME_DEPLOYMENT_STRATEGY.md` define una guia reutilizable para elegir Docker, nativo o hibrido al inicio de futuros proyectos. Aplicado a Song-AI, confirma `local_hardware` y no reintroduce Docker como ruta operativa.
- Flujo de informacion por fases documentado e implementado: `docs/PHASE_INFORMATION_FLOW.md` define SQLite como fuente de verdad, archivos como artefactos derivados, estados separados de fase/ejecucion/artefacto, eventos importantes por fase, verificacion por checksum y regeneracion puntual cuando el builder/provider lo permite.

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
data/provider-cache     paquetes Python pesados instalados por bootstrap local
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
- La iGPU y la NPU existen en Windows, pero ACE-Step/PyTorch no las usa automaticamente.
- Para aprovechar iGPU/NPU hace falta un provider local especifico, por ejemplo DirectML, OpenVINO, Intel Extension for PyTorch/XPU o un wrapper CLI compatible. La arquitectura de providers permite agregarlo sin acoplar ACE-Step al resto del pipeline.

Nota de rendimiento: ACE-Step en CPU es funcional pero extremadamente lento. En una prueba real con virtualizacion, 60 segundos con 10 pasos no completo en 3600 segundos. Por eso el comando local usa `{duration_seconds}` y pocos `--oss-steps` para validar flujo en CPU; para calidad final usa un provider acelerado y mas pasos.

Verificacion adicional: una prueba de 5 segundos con 4 `oss_steps` cargo el modelo en 810 segundos y siguio siendo demasiado lenta para uso interactivo por CPU. La app ahora reporta `runtime=cpu_extremely_slow` y escribe `full_song_generation.log` en vivo mientras ACE-Step corre.

## Variables Principales

Archivo base:

```text
.env.example
```

Full Song local con ACE-Step:

```text
SONG_AI_MODEL_ROOT=data/models
SONG_AI_PROVIDER_ROOT=data/providers
SONG_AI_PROVIDER_CACHE=data/provider-cache
SONG_AI_FULL_SONG_COMMAND=python tools/acestep_generate.py --prompt {prompt_path} --lyrics {lyrics_path} --output {output_path} --checkpoint-path data/models/music/ace-step --duration {duration_seconds} --infer-step 4 --oss-steps 16,96,172,200 --cpu-offload true --overlapped-decode true --torch-threads 14 --torch-interop-threads 4 --diagnostics {diagnostics_path} --output-type full_song_with_vocals
SONG_AI_INSTALL_ACE_STEP=true
SONG_AI_ALLOW_CPU_FULL_SONG=true
SONG_AI_LOCAL_COMMAND_TIMEOUT_SECONDS=14400
SONG_AI_MAX_FULL_SONG_DURATION_SECONDS=360
SONG_AI_IGPU_EXPERIMENTAL=false
LIBVA_DRIVER_NAME=iHD
```

Rutas alternativas por stems:

```text
SONG_AI_SOUNDTRACK_COMMAND=
SONG_AI_SINGING_VOICE_COMMAND=
SONG_AI_VOICE_CONVERSION_COMMAND=
```

Si Full Song funciona, esas tres pueden quedar vacias.

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
```

Ejemplo para levantar llama.cpp con los GGUF ya descargados:

```powershell
llama-server -m data\models\llm\gemma\gemma.gguf --port 8081 --ctx-size 4096
llama-server -m data\models\llm\qwen\qwen.gguf --port 8082 --ctx-size 4096
```

No hay que activar Gemma/Qwen con una variable adicional: Song AI intenta usarlos automaticamente cuando los servidores llama.cpp estan disponibles. Si no responden o faltan los `.gguf`, conserva guia local.

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
- instala dependencias pesadas en `data/provider-cache/python`,
- instala ACE-Step si esta activado,
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

La politica por defecto evita reinstalar paquetes pesados si ya son importables y hay marcador compatible en `data/provider-cache`.

## ResourceMonitor

Song AI mide recursos del proceso local antes, durante y despues de audio pesado como ACE-Step o providers de voz cantada. Los snapshots se guardan en SQLite en `resource_snapshots` y la UI de Production muestra RAM, CPU, disco, decision y recomendaciones.

Variables:

```text
SONG_AI_RESOURCE_MONITOR_ENABLED=true
SONG_AI_RESOURCE_SAMPLE_SECONDS=2
SONG_AI_MIN_FREE_RAM_MB_FOR_AUDIO=6000
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

Nota de sprint: ACE-Step local necesita `torchcodec` para guardar WAV con versiones recientes de `torchaudio`. En Windows, `torchcodec` necesita ffmpeg full/shared en PATH para cargar sus DLL; el paquete `Gyan.FFmpeg` estatico no basta, usa `Gyan.FFmpeg.Shared`. La app prioriza `data/provider-cache/python`, donde ACE-Step, Torch y TorchCodec deben quedar instalados como stack compatible.

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
