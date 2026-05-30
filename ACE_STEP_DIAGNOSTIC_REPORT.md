# Informe tecnico ACE-Step

Fecha de revision: 2026-05-23/24, entorno Docker local `song-ai-app`.

ACE-Step esta integrado como proceso CLI local: `ProfessionalFullSongService` ejecuta `SONG_AI_FULL_SONG_COMMAND`, que llama a `tools/acestep_generate.py`; ese wrapper importa `acestep.pipeline_ace_step.ACEStepPipeline`. No hay servicio HTTP/API de ACE-Step.

La ruta principal genera `final_song.wav` con instrumental y voz integrada durante `MASTERING`. No genera `vocals.wav` separado salvo que se configure un provider por stems en `SONG_AI_SINGING_VOICE_COMMAND`.

## Flujo

1. El usuario llega a `MASTERING` en el proyecto profesional.
2. `ProfessionalSongService.master_song()` usa `ProfessionalFullSongService` si `SONG_AI_FULL_SONG_COMMAND` esta configurado.
3. Se escriben `full_song_prompt.txt` y se reutiliza `lyrics.md`.
4. El comando local recibe `{prompt_path}`, `{lyrics_path}`, `{output_path}`, `{duration_seconds}` y `{diagnostics_path}`.
5. `tools/acestep_generate.py` lee prompt/letra en UTF-8, carga `ACEStepPipeline` y llama `pipeline(..., task="text2music", lyrics=<lyrics>, save_path=<final_song.wav>)`.
6. Si el WAV existe, la app exporta MP3/FLAC y registra artefactos.

## Prueba controlada

Prompt:

```text
tender Spanish lullaby, soft female vocal, acoustic guitar
```

Lyrics:

```text
[es]
[verse]
Duerme mi cielo
cierra los ojos

[chorus]
Aquí estoy contigo
guardando tu sueño
```

Artefactos en el contenedor:

- `/app/data/diagnostics/ace_step_controlled/spanish_lullaby_run.log`
- `/app/data/diagnostics/ace_step_controlled/spanish_lullaby_diagnostics.json`
- `/app/data/diagnostics/ace_step_controlled/english_lullaby_run.log`
- `/app/data/diagnostics/ace_step_controlled/english_lullaby_diagnostics.json`

Resultado espanol:

- `detected_language`: `Spanish`
- `[es]`, `[verse]`, `[chorus]` preservados
- Unicode y acentos preservados (`Aquí`, `sueño`)
- `instrumental_mode=false`
- `music_only_mode=false`
- `lyric_free_generation=false`
- `sung_vocal_requested=true`
- WAV no generado antes del timeout.

Log ACE-Step relevante:

```text
[es] --> zh --> ['[en]', '[es]']
[verse] --> zh --> ['[en]', '[verse]']
Duerme mi cielo --> en --> [...]
cierra los ojos --> es --> [...]
Aquí estoy contigo --> en --> [...]
guardando tu sueño --> es --> [...]
```

Comparacion inglesa:

```text
[en] --> zh --> ['[en]', '[en]']
[verse] --> zh --> ['[en]', '[verse]']
Sleep my sky --> en --> [...]
close your eyes --> en --> [...]
guarding your dream --> de --> [...]
```

Conclusion: Song-AI no elimina acentos ni altera Unicode; ACE-Step clasifica/tokeniza lineas cortas de forma mixta incluso en ingles. `[es]` ayuda a declarar intencion, pero no fuerza que todas las lineas se tokenicen como espanol.

## Recursos

Entorno observado:

- CUDA disponible: `false`
- VRAM detectada: ninguna
- RAM total contenedor/WSL: `7596.68 MB`
- Con Gemma/Qwen arriba: `~2292.62 MB` libres, swap usada `~1446.87 MB`
- Tras detener Gemma/Qwen: `~6725.25 MB` libres, swap usada `~224.42 MB`

ACE-Step cargo el modelo en 16-18 segundos desde cache, pero una prueba minima de 8 segundos con `infer_step=1` no produjo WAV antes del timeout. En la prueba espanola, el unico paso de difusion tardo alrededor de 128 segundos y el proceso no alcanzo a terminar decodificacion/exportacion.

## Diagnostico

- Integracion: correcta como libreria Python invocada por CLI.
- Configuracion: habia un bug en el wrapper cuando se ejecutaba manualmente; no agregaba `/app/provider-cache/python` a `sys.path`. Corregido.
- Espanol: la entrada se preserva, pero ACE-Step tokeniza espanol corto de forma inconsistente.
- Memoria: con LLMs cargados, ACE-Step entra con muy poca RAM libre y mucho swap usado.
- GPU: no hay aceleracion disponible; CPU es el bloqueo principal.
- Voz cantada: no se pudo confirmar calidad final porque no se obtuvo WAV completo en CPU dentro del timeout.

## Cambios aplicados

- `tools/acestep_generate.py`: diagnostico JSON, recursos, parametros, idioma, secciones, `task="text2music"` explicito y carga autonoma del provider cache.
- `backend/application/professional_full_song_service.py`: log de prompt/letra/modelo/duracion/tipo de salida y placeholder `{diagnostics_path}`.
- `backend/audio/resource_monitor.py`: SWAP usada y VRAM.
- `backend/adapters/sqlite/song_workflow_repository.py`: columnas `swap_used_mb` y `vram_json`.
- `backend/core/storage.py`: persistencia de SWAP/VRAM.
- `backend/application/vocal_synthesis_service.py`: logs ampliados para providers vocales por stems.
- `.env.example`: comando ACE-Step local con diagnostico.
- `README.md`: avance registrado.
- `tests/test_audio_export.py`: prueba de preservacion de espanol y modo no instrumental.

## Recomendaciones

1. Ejecutar ACE-Step con un provider local acelerado cuando este disponible.
2. Mantener `SONG_AI_RELEASE_LLM_BEFORE_AUDIO=true`.
3. Detener Gemma/Qwen, esperar 30-45 segundos y verificar memoria antes de ACE-Step.
4. Mantener `[es]` y secciones bracket simples para letras en espanol.
5. Usar letras menos fragmentarias para pruebas de calidad; textos muy cortos parecen empeorar la deteccion por linea.
6. Usar ACE-Step como Full Song provider. Si se necesita `vocals.wav` aislado, conectar un provider vocal por stems distinto.
