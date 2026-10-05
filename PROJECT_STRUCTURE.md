# Project Structure

Este archivo mantiene un mapa practico del repositorio. Actualizarlo cuando se cree o borre un archivo o carpeta del proyecto.

## Raiz

- `AGENTS.md`: reglas de trabajo del proyecto para asistentes y arquitectura.
- `README.md`: estado funcional, ejecucion local, sprints y capacidades actuales.
- `requirements.txt`: entrada general de dependencias Python.
- `PROJECT_STRUCTURE.md`: mapa vivo de archivos y carpetas del repositorio.
- `ACE_STEP_DIAGNOSTIC_REPORT.md`: reporte diagnostico de ACE-Step.

## Backend

- `backend/main.py`: entrada CLI/aplicacion.
- `backend/server.py`: entrada del servidor local.
- `backend/requirements*.txt`: dependencias Python por perfil local/audio/XPU.
- `backend/adapters/http/fastapi_app.py`: API FastAPI y frontend estatico.
- `backend/adapters/sqlite/`: repositorios SQLite para sets, samples/canciones legadas, workflows, orquestacion y configs JSON. `legacy_song_repository.py` persiste el flujo `set -> sample -> song`.
- `backend/application/`: servicios de casos de uso, pipeline profesional, letras, MIDI, mezcla, mastering, exportacion y orquestacion de modelos. `audio_download_service.py` resuelve descargas globales o por proyecto.
- `backend/audio/`: renderizado local, mezcla, formatos, perfiles ACE-Step, deteccion de aceleracion y monitoreo de recursos.
- `backend/bootstrap/`: preparacion local de providers/modelos.
- `backend/builders/`: construccion de sets, samples, full song, exports y templates.
- `backend/config/`: settings, recursos, modelos y variables de entorno.
- `backend/core/`: storage, menu, opciones creativas y app base.
- `backend/explorers/`: exploradores/mock explorers.
- `backend/models/`: entidades de dominio como assets, intent, manifest, set y workflow. `music_validation.py` define el rango BPM aceptado para datos persistidos.
- `backend/providers/`: providers intercambiables locales, pro, Hugging Face y llama.cpp.
- `backend/utils/`: utilidades compartidas.

## Frontend

- `frontend/index.html`: plantilla principal de la UI Vue.
- `frontend/src/app.js`: estado, computed properties, flujos de UI y llamadas API.
- `frontend/src/api_client.js`: construccion de URLs y lectura uniforme de respuestas HTTP.
- `frontend/src/production_actions.js`: preparacion, ejecucion, polling, export y descargas de Production para la UI Vue.
- `frontend/src/styles.css`: sistema visual y layout.
- `frontend/package.json`: scripts Vite (`dev`, `build`, `preview`).
- `frontend/vite.config.js`: configuracion Vite.
- `frontend/dist/`: build generado por Vite; no editar a mano.
- `frontend/node_modules/`: dependencias instaladas; no editar a mano.

## Scripts

- `scripts/setup-local.ps1`: prepara entorno local.
- `scripts/run-local.ps1`: levanta Song AI local.
- `scripts/run-local-dev.ps1`: modo desarrollo con Vite.
- `scripts/install-llama-cpp-gpu.ps1`: descarga/configura `llama-server` Windows x64 con backend GPU Vulkan o SYCL.
- `scripts/start-local-llms.ps1`: arranca Gemma/Qwen con `llama-server`, puertos por rol y offload GPU configurable.
- `scripts/stop-local-llms.ps1`: detiene los procesos locales Gemma/Qwen registrados por PID.
- `scripts/check-local-prereqs.ps1`: verifica prerequisitos locales.
- `scripts/install-local-prereqs.ps1`: instala prerequisitos locales.
- `scripts/install-intel-xpu-prereqs.ps1`: instala/repara stack Intel XPU.
- `scripts/check_acestep_xpu.py`: comprobacion ACE-Step/XPU.
- `scripts/start-acestep-api-xpu.bat`: arranque alternativo API ACE-Step XPU.

## Tools

- `tools/acestep_generate.py`: wrapper diagnostico/generacion ACE-Step 1.5 con XPU.
- `tools/check_xpu_stack.py`: diagnostico Torch XPU.
- `tools/check_local_audio_stack.py`: diagnostico audio local.
- `tools/run_small_local_song_flow.py`: smoke test del flujo local.
- `tools/musicgen_generate.py`: generacion MusicGen.
- `tools/singing_voice_generate.py`: generacion de voz cantada.
- `tools/use_audio_file.py`: provider para reutilizar audio local.

## Tests

- `tests/test_audio_export.py`: pruebas de exportacion/audio.
- `tests/test_set_validation.py`: validacion de assets, seleccion e idempotencia de sets, rango BPM, persistencia/migracion legada y aislamiento de descargas.
- `tests/diagnostics.py`: helpers diagnosticos para tests.

## Docs

- `docs/ACE_STEP_INTEL_XPU_REPORT.md`: integracion ACE-Step Intel XPU.
- `docs/PHASE_INFORMATION_FLOW.md`: flujo de informacion por fases.
- `docs/HANDOFF_5_5_SOL.md`: propuestas priorizadas y criterios de aceptacion para la siguiente implementacion.
- `docs/HANDOFF_PLAYWRIGHT_2026-10-02.md`: auditoria de uso con Playwright MCP; diez hallazgos reproducidos y plan de correccion para 5.5 Sol.
- `docs/RUNTIME_DEPLOYMENT_STRATEGY.md`: estrategia runtime local/Docker/hibrida.

## Data Local

- `data/`: fuente activa local y artefactos generados. Contiene SQLite, sets, drafts, samples, songs, projects, modelos y diagnosticos.
- `data/song_ai.sqlite`: base activa de trabajo.
- `data/sets/`: snapshots de sets.
- `data/projects/`: artefactos de proyectos Production.
- `data/drafts/`: drafts separados de instrumental, melodia y letra.

## Registro De Cambios Estructurales

- 2026-05-31: creado `PROJECT_STRUCTURE.md`.
- 2026-05-31: agregados `scripts/start-local-llms.ps1` y `scripts/stop-local-llms.ps1` para gestionar Gemma/Qwen locales.
- 2026-05-31: agregado `scripts/install-llama-cpp-gpu.ps1` para instalar/configurar llama.cpp GPU.
- 2026-10-02: agregados persistencia SQLite para samples/canciones legadas y servicio de descarga asociado al proyecto activo.
- 2026-10-03: agregado `backend/models/music_validation.py` para validar BPM antes de persistir fases o crear drafts.
