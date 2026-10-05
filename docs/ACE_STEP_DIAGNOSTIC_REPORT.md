# Informe tecnico ACE-Step

Fecha de revision: 2026-05-23/24, entorno Docker local `song-ai-app`.

## Resumen

ACE-Step esta integrado como proceso CLI local. La app ejecuta `tools/acestep_generate.py`, y en ACE-Step 1.5 ese wrapper detecta la libreria Python real `acestep.acestep_v15_pipeline.AceStepHandler`. No hay servicio HTTP/API de ACE-Step.

La ruta principal no genera `vocals.wav` separado: genera `final_song.wav` con instrumental y voz integrada durante `MASTERING`, usando `SONG_AI_FULL_SONG_COMMAND`. La ruta `VOCAL_SYNTHESIS` sigue existiendo para providers por stems, pero `SONG_AI_SINGING_VOICE_COMMAND` esta vacio por defecto.

## Flujo actual

1. Usuario avanza el proyecto profesional hasta `MASTERING`.
2. `ProfessionalSongService.master_song()` detecta `full_song_service.configured()`.
3. `ProfessionalFullSongService.generate()` valida proyecto y `lyrics.md`.
4. Escribe `full_song_prompt.txt`.
5. Ejecuta `SONG_AI_FULL_SONG_COMMAND` con placeholders:
   - `{prompt_path}`
   - `{lyrics_path}`
   - `{output_path}`
   - `{duration_seconds}`
   - `{diagnostics_path}`
6. `tools/acestep_generate.py` lee prompt y letra como UTF-8.
7. El wrapper inicializa `AceStepHandler`.
8. Llama `generate_music(..., task_type="text2music", lyrics=<lyrics>)` y guarda el tensor resultante como WAV.
9. Si existe WAV, la app exporta MP3/FLAC y registra artefactos.

## Evidencia de entrada

Prueba controlada ejecutada dentro del contenedor:

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

Archivos generados:

- `/app/data/diagnostics/ace_step_controlled/prompt.txt`
- `/app/data/diagnostics/ace_step_controlled/lyrics_es.md`
- `/app/data/diagnostics/ace_step_controlled/spanish_lullaby_run.log`
- `/app/data/diagnostics/ace_step_controlled/spanish_lullaby_diagnostics.json`

Resultado:

- `detected_language`: `Spanish`
- `has_spanish_language_tag`: `true`
- `contains_unicode`: `true`
- `contains_accents`: `true`
- secciones detectadas: `[es]`, `[verse]`, `[chorus]`
- `instrumental_mode`: `false`
- `music_only_mode`: `false`
- `lyric_free_generation`: `false`
- `sung_vocal_requested`: `true`
- salida WAV: no generada antes del timeout.

## Espanol y tokenizacion

La integracion no elimina acentos ni convierte la letra a ASCII. Los archivos se leen y escriben con `encoding="utf-8"` y el diagnostico conserva `Aquí` y `sueño`.

El log interno de ACE-Step si muestra clasificacion mixta por linea:

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

Conclusion: el problema no es que Song-AI pierda Unicode; ACE-Step hace deteccion/tokenizacion por linea y puede clasificar texto corto de forma inconsistente incluso en ingles. Mantener `[es]` ayuda a dejar intencion explicita, pero no garantiza clasificacion uniforme de todas las lineas.

## Recursos

Estado inicial observado con LLMs arriba:

```text
RAM total: 7596.68 MB
RAM libre: ~2292.62 MB
RAM usada: 69.8%
SWAP usada: ~1446.87 MB
VRAM: no detectada
CUDA disponible: false
```

Despues de detener Gemma/Qwen:

```text
RAM libre: ~6725.25 MB
RAM usada: 11.5%
SWAP usada: ~224.42 MB
```

ACE-Step cargo el modelo desde cache en 16-18 segundos, pero una inferencia minima de 8 segundos con `infer_step=1` no produjo WAV antes del timeout. En espanol, el unico paso de difusion tardo ~128 segundos y el proceso siguio sin terminar la decodificacion/exportacion antes del corte.

## Hallazgos

1. Integracion: correcta como libreria Python invocada por proceso CLI. No es API.
2. Nota historica: el wrapper CLI usaba antes `/app/provider-cache/python` para librerias pesadas. En Windows nativo se retiro ese cache y ahora el `.venv` es la fuente unica de dependencias Python.
3. Entrada: Song-AI preserva prompt, letra, Unicode, acentos y etiquetas.
4. Estructura: se aceptan etiquetas bracket `[verse]`, `[chorus]`, `[bridge]`, `[outro]`; la app tambien puede producir Markdown `## Verse`, que ahora queda registrado para diagnostico.
5. Modo: la llamada usa `task_type="text2music"` con lyrics no vacias; no activa modo instrumental, music-only ni lyric-free.
6. Memoria: Gemma/Qwen consumen suficiente RAM como para dejar ACE-Step en zona critica si permanecen cargados.
7. GPU: no hay CUDA/VRAM disponible en este entorno, por lo que ACE-Step corre por CPU.
8. Resultado vocal: no se pudo confirmar calidad de voz cantada porque no se genero WAV completo en CPU dentro de los timeouts reproducibles.

## Cambios aplicados

- `tools/acestep_generate.py`
  - diagnostico JSON persistente;
  - registro de prompt/letra/idioma/secciones/parametros;
  - registro RAM/SWAP/CPU/VRAM;
  - `task_type="text2music"` explicito;
  - `debug=True` para logs de tokenizacion ACE-Step;
  - diagnostico autonomo desde el `.venv` local.
- `backend/application/professional_full_song_service.py`
  - log de prompt completo, letra completa, modelo, duracion, tipo de salida y ruta diagnostica;
  - placeholder `{diagnostics_path}`;
  - resumen de recursos con SWAP usada y VRAM.
- `backend/audio/resource_monitor.py`
  - captura SWAP usada y VRAM por `nvidia-smi` si existe.
- `backend/adapters/sqlite/song_workflow_repository.py`
  - columnas `swap_used_mb` y `vram_json` en `resource_snapshots`.
- `backend/core/storage.py`
  - persistencia de `swap_used_mb` y `vram`.
- `backend/application/vocal_synthesis_service.py`
  - logs de recursos ampliados para providers de voz por stems.
- `docker-compose.yml`, `.env`, `.env.example`
  - comando ACE-Step actualizado con `--diagnostics {diagnostics_path}` y `--output-type full_song_with_vocals`.
- `tests/test_audio_export.py`
  - prueba de preservacion de letra espanola, acentos, secciones y modo no instrumental.

## Recomendaciones concretas

1. Ejecutar ACE-Step con GPU NVIDIA expuesta a Docker. CPU no es viable para iteracion normal.
2. Mantener `SONG_AI_RELEASE_LLM_BEFORE_AUDIO=true`.
3. Antes de ACE-Step, detener Gemma/Qwen, esperar 30-45 segundos y validar que RAM libre suba realmente.
4. Mantener `[es]` al inicio de letras en espanol y usar secciones bracket simples.
5. Para pruebas de calidad, usar duraciones cortas y lyrics mas largas que una frase por seccion; los textos muy cortos parecen aumentar clasificaciones ambiguas del tokenizador.
6. No usar `SONG_AI_SINGING_VOICE_COMMAND` para ACE-Step si se espera una cancion completa; ACE-Step esta configurado como Full Song provider.
7. Si se necesita `vocals.wav` aislado, conectar un provider vocal por stems distinto o un wrapper ACE-Step especifico de separacion/stems, manteniendo assets separados.
