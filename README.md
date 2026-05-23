# Song AI

Song AI es un estudio musical local asistido por IA para crear canciones completas desde una idea creativa hasta exportables finales. La aplicacion corre en Docker, guarda el trabajo en SQLite y volumenes persistentes, y mantiene separados los artefactos de letra, plan musical, MIDI, audio y exportacion.

El objetivo actual es generar canciones locales con herramientas gratuitas. El modo pro/pago esta pausado.

## Estado Actual

La ruta local principal es **Full Song con ACE-Step**:

- ACE-Step genera una cancion completa con instrumental y voz cantada integrada.
- La fase de Mastering del pipeline profesional puede usar `SONG_AI_FULL_SONG_COMMAND`.
- Si Full Song esta listo, `soundtrack` y `singing_voice` separados son opcionales.
- Si el sistema cae en `procedural_vocal_guide`, la app bloquea la descarga como final.

Estado esperado en Docker cuando ACE-Step esta importable:

```text
full_song: ready
runtime: gpu_ready | cpu_extremely_slow
soundtrack: optional
singing_voice: optional
mix_and_export: ready
```

Importante: Song AI ya esta preparado para generar voz cantada real por ACE-Step, pero la calidad final depende de que ACE-Step pueda ejecutar realmente en el contenedor. Con GPU es lo recomendado; por CPU puede tardar mucho.

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

Estado verificado en Docker:

- Gemma corre como provider creativo en `llama-gemma:8080`.
- Qwen corre como provider tecnico en `llama-qwen:8080`.
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

Volumenes Docker:

```text
song_ai_data            SQLite, proyectos, letras, MIDI, audio y exports
song_ai_models          modelos locales: llm, music, voice, stems, huggingface
song_ai_providers       repos/adaptadores locales
song_ai_provider_cache  paquetes Python pesados instalados en runtime
```

Estructura relevante dentro de `/app/data`:

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
- rutas JSON indexadas.

## Docker

Levantar la app:

```powershell
docker compose up -d --build
```

Abrir:

```text
http://localhost:8000
```

Ver logs:

```powershell
docker logs -f song-ai-app
```

Reiniciar sin perder modelos ni datos:

```powershell
docker compose restart app
```

Reconstruir conservando volumenes:

```powershell
docker compose up -d --build
```

No uses `docker compose down -v` salvo que quieras borrar modelos, cache y datos.

## Aceleracion GPU / iGPU

La aceleracion recomendada para ACE-Step es NVIDIA CUDA. Para intentarlo, usa el override GPU:

```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Validar dentro del contenedor:

```powershell
docker compose exec -T app sh -lc "nvidia-smi || true; ls -la /dev/nvidia* 2>/dev/null || true"
```

Tambien existe un override experimental para iGPU en hosts Linux que exponen `/dev/dri`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.igpu.yml up -d --build
```

Validar:

```powershell
docker compose exec -T app sh -lc "ls -la /dev/dri 2>/dev/null || true"
```

Importante: en Docker Desktop sobre Windows, una Intel iGPU puede existir en el sistema, pero normalmente no queda disponible para PyTorch/ACE-Step dentro del contenedor Linux. Si dentro del contenedor no aparecen `/dev/dri`, `/dev/dxg` ni `/dev/nvidia*`, la generacion real solo puede correr por CPU o con una GPU NVIDIA correctamente expuesta.

Nota de rendimiento: ACE-Step en CPU es funcional pero extremadamente lento. En una prueba real dentro de Docker, el modelo cargo correctamente y descargo checkpoints a `/app/models/music/ace-step`, pero 60 segundos con 10 pasos no completo en 3600 segundos. Por eso el comando local usa `{duration_seconds}` y pocos `--oss-steps` para validar flujo en CPU; para calidad final usa GPU y mas pasos.

Verificacion adicional: una prueba de 5 segundos con 4 `oss_steps` cargo el modelo en 810 segundos y siguio siendo demasiado lenta para uso interactivo por CPU. La app ahora reporta `runtime=cpu_extremely_slow` y escribe `full_song_generation.log` en vivo mientras ACE-Step corre.

## Variables Principales

Archivo base:

```text
.env.example
```

Full Song local con ACE-Step:

```text
SONG_AI_FULL_SONG_COMMAND=python tools/acestep_generate.py --prompt {prompt_path} --lyrics {lyrics_path} --output {output_path} --checkpoint-path /app/models/music/ace-step --duration {duration_seconds} --infer-step 4 --oss-steps 16,96,172,200 --cpu-offload true --overlapped-decode true
SONG_AI_INSTALL_ACE_STEP=true
SONG_AI_ALLOW_CPU_FULL_SONG=true
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
SONG_AI_GEMMA_GGUF_PATH=/app/models/llm/gemma/gemma.gguf
SONG_AI_QWEN_GGUF_PATH=/app/models/llm/qwen/qwen.gguf
```

URLs opcionales de descarga:

```text
SONG_AI_GEMMA_GGUF_URL=https://huggingface.co/second-state/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf
SONG_AI_QWEN_GGUF_URL=https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf
```

Endpoints por rol:

```text
SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL=http://llama-gemma:8080
SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL=http://llama-qwen:8080
SONG_AI_LLAMA_CPP_TIMEOUT_SECONDS=240
SONG_AI_LLAMA_CPP_INTERPRETER_N_PREDICT=160
SONG_AI_LLAMA_CPP_TECHNICAL_N_PREDICT=96
```

Levantar llama.cpp con los GGUF ya descargados:

```powershell
docker compose -f docker-compose.yml -f docker-compose.llm.yml up -d --build
```

No hay que activar Gemma/Qwen con una variable adicional: Song AI intenta usarlos automaticamente cuando los servidores llama.cpp estan disponibles. Si no responden o faltan los `.gguf`, conserva guia local.

Si el estado indica que faltan modelos, `Preparar/reiniciar` o `Actualizar dependencias` descargan los GGUF cuando esas URLs estan configuradas. Los botones `Recrear Gemma` y `Recrear Qwen` eliminan el peso existente y lo vuelven a descargar en el volumen Docker.

```text
POST /api/system/models/gemma/refresh
POST /api/system/models/qwen/refresh
```

Tambien puedes colocar manualmente los archivos en el volumen Docker:

```text
/app/models/llm/gemma/gemma.gguf
/app/models/llm/qwen/qwen.gguf
```

## Bootstrap

El bootstrap corre dentro del contenedor y prepara volumenes:

- crea directorios de modelos,
- instala dependencias pesadas en `/app/provider-cache/python`,
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

La politica por defecto evita reinstalar paquetes pesados si ya son importables y hay marcador compatible en el volumen.

## ResourceMonitor

Song AI mide recursos dentro del contenedor antes, durante y despues de audio pesado como ACE-Step o providers de voz cantada. Los snapshots se guardan en SQLite en `resource_snapshots` y la UI de Production muestra RAM, CPU, disco, decision y recomendaciones.

Variables:

```text
SONG_AI_RESOURCE_MONITOR_ENABLED=true
SONG_AI_RESOURCE_SAMPLE_SECONDS=2
SONG_AI_MIN_FREE_RAM_MB_FOR_AUDIO=6000
SONG_AI_MIN_FREE_DISK_MB_FOR_AUDIO=15000
SONG_AI_MAX_CPU_PERCENT_BEFORE_AUDIO=85
SONG_AI_AUDIO_START_DELAY_SECONDS=45
SONG_AI_RELEASE_LLM_BEFORE_AUDIO=true
SONG_AI_STOP_LLM_COMMAND=python tools/manage_llm_containers.py stop
SONG_AI_START_LLM_COMMAND=python tools/manage_llm_containers.py start
```

Endpoints:

```text
GET  /api/resources/status
GET  /api/resources/history
POST /api/resources/check-audio-readiness
```

Antes de ejecutar `SONG_AI_FULL_SONG_COMMAND` o `SONG_AI_SINGING_VOICE_COMMAND`, el backend registra `before_audio`, opcionalmente ejecuta `SONG_AI_STOP_LLM_COMMAND`, espera `SONG_AI_AUDIO_START_DELAY_SECONDS`, registra `after_llm_release` y muestra RAM, CPU, swap, disco y limite de memoria Docker como diagnostico. RAM/CPU/swap son advertencias, no bloqueos preventivos. La generacion solo se detiene por errores reales: dependencia obligatoria faltante, archivo de entrada ausente, ruta/permisos invalidos o error del provider.

En Docker Compose, la app monta `/var/run/docker.sock` y usa `tools/manage_llm_containers.py` para detener temporalmente `song-ai-llama-gemma` y `song-ai-llama-qwen` antes de ACE-Step. Al terminar, ejecuta `SONG_AI_START_LLM_COMMAND` para dejarlos disponibles de nuevo. Si el socket Docker no esta disponible, el helper lo reporta y la generacion continua.

Nota de sprint: ACE-Step dentro de Docker necesita `torchcodec`/`pytorchcodec` para guardar WAV con versiones recientes de `torchaudio`. `backend/requirements-local-audio.txt` lo declara y el bootstrap lo valida como dependencia persistente en `/app/provider-cache/python`. Si falta, la app muestra: `Falta pytorchcodec. Instala la dependencia antes de generar con ACE-Step.`

UX ResourceMonitor: Production incluye refresco manual, revision explicita de recursos, auto-actualizacion cada 10 segundos mientras la vista esta activa, timestamp de ultima lectura e historial compacto con RAM, swap y CPU.

UX Infraestructura local: Production muestra un resumen limpio con modelos de texto, audio local, almacenamiento Docker y preparacion. Los componentes tecnicos y acciones de recreacion quedan en modo avanzado.

UX Production: la vista principal se ordena como Proyecto activo -> Orden logico -> Exportables. Recursos e infraestructura quedan como diagnosticos colapsables para no distraer del flujo de generacion.

UX Production alcance: crear proyectos y cambiar el proyecto activo pertenece a Biblioteca. Production solo permite editar la descripcion del proyecto activo y cerrar el pipeline con generacion/exportables.

Sprint flujo por fases: Intent, Lyrics, Music Plan, MIDI, Instrumental y Voice tienen guardado explicito por fase en SQLite (`project_phase_data`). Guardar solo persiste configuracion; no ejecuta ACE-Step, MIDI, audio ni exportables. La actividad, logs y botones de ejecucion quedan concentrados en Production.

UX sidebar: la barra lateral usa `--sidebar-width: 300px` para dar mas aire a proyecto activo y fases, y el footer de Gemma se alinea con ese ancho.

UX sidebar compacto: el proyecto activo se muestra en una sola linea con prefijo `>` para reducir espacio vertical sin perder contexto.

Swap recomendado en Linux: no bloquea la generacion, pero mejora estabilidad con ACE-Step. Ejemplo:

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

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

Docker:

```powershell
docker compose up -d --build
docker compose exec -T app python -c "import sys; sys.path.insert(0, '/app/backend'); from config.settings import Settings; from audio.local_song_pipeline import LocalSongPipeline; s=Settings.load(); print(LocalSongPipeline(s.local_models).status())"
```

## Limitaciones Actuales

- La voz real depende de que ACE-Step ejecute correctamente en Docker.
- Con CPU, ACE-Step puede tardar mucho.
- Con GPU, usa un compose GPU cuando el entorno Docker/WSL la exponga correctamente.
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
