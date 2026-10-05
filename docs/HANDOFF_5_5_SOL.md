# Propuestas para 5.5 Sol

## Estado de ejecucion (2026-10-02)

- P1 completada: Production descarga por `song_id`; el flujo local descarga por `set_id`; la UI ya no usa `latest` como fallback contextual. Se agrego `AudioDownloadService` y una prueba con dos proyectos que impide devolver el export equivocado.
- P2 completada: `legacy_samples` y `legacy_songs` son la fuente activa para el flujo legado. Los JSON se migran sin sobrescribir filas existentes, se regeneran desde DB y se eliminan con el set.
- P3 completada para el alcance propuesto: la resolucion de descargas salio de `SongService`, el cliente HTTP comun salio de `app.js` y las acciones de carga, preparacion, ejecucion, polling y descarga de Production viven en `frontend/src/production_actions.js`. `app.js` conserva la composicion de estado y los contratos de la plantilla.

Verificacion de esta ejecucion: la suite completa paso con 47 pruebas en 281 segundos usando `SONG_AI_RESOURCE_MONITOR_ENABLED=false` para aislar procesos locales. Tambien pasaron la compilacion Python, el build Vite y `git diff --check`.

## Encargo

Continuar Song AI con cambios pequenos y verificables. Este documento es una propuesta de trabajo, no una descripcion de funciones ya implementadas. Revisar el estado real del arbol antes de editar: hay cambios locales sin confirmar en backend, frontend, README y documentacion. Conservarlos y no restaurar archivos para empezar de cero.

El flujo principal actual es local y por fases: el usuario define el proyecto/set con instrumental, melodia y letra; Production genera los artefactos. SQLite debe seguir siendo la fuente activa y los JSON deben ser snapshots regenerables. Mantener separados providers, explorers y builders, y conservar la intencion instrumental, vocal y lirica.

## Estado comprobado al redactar este documento

- `StorageManager.save_song_set()` valida que los tres drafts existan, sean del tipo correcto y tengan `manifest.json`, `intent.json` y contenido. `SampleBuilder` lee el set mas reciente desde SQLite y `FullSongBuilder` comprueba que el set del sample siga en SQLite.
- `tests/test_set_validation.py`: 2 pruebas pasan. La prueba `test_audio_export_contains_song_mock_context_and_local_pipeline_status` pasa tras ajustar la expectativa a la presencia real de `ffmpeg`.
- `python -m compileall -q backend tests` y `npm run build` pasaron. La suite Python completa se inicio, pero se interrumpio durante una prueba local lenta; no se puede afirmar que pase entera.
- `backend/core/storage.py` aun enumera samples y canciones legadas leyendo `data/samples/*/sample.json` y `data/songs/*/song.json` mediante `list_samples()`, `get_latest_sample()`, `list_songs()` y `get_latest_song()`.
- `SongService.latest_audio_export_file()` intenta primero un export profesional obtenido al recorrer todos los proyectos en `_latest_professional_audio_export_file()`. El endpoint `/api/audio-exports/latest/download` no recibe `set_id` ni `song_id`; el fallback de descarga del frontend lo usa sin identificador de proyecto.

## P1. Asociar cada descarga al proyecto solicitado

**Problema:** con varios proyectos, la descarga global puede elegir el primer export profesional disponible aunque el usuario tenga otro proyecto activo. Eso puede entregar una cancion ajena al contexto visual.

**Archivos de partida:** `backend/application/song_service.py`, `backend/adapters/http/fastapi_app.py`, `frontend/src/app.js`, `tests/test_audio_export.py`.

**Trabajo propuesto:**

1. Para Production, usar la ruta existente `/api/pro/projects/{song_id}/artifacts/{artifact_type}/download` y enviar el `song_id` del proyecto activo.
2. Si se conserva una descarga del flujo legado, darle una ruta identificada por `set_id` o `song_id`, resolver el artefacto solo dentro de ese proyecto y rechazar IDs desconocidos. Evitar buscar un export en todos los proyectos como fallback de una descarga activa.
3. Definir explicitamente que hace la ruta `latest`: mantenerla solo para usos que pidan de verdad el ultimo export global, o retirarla cuando sus consumidores migren. No cambiar su contrato silenciosamente.

**Aceptacion:** crear dos proyectos A y B con exports distintos; al descargar desde A se obtienen los bytes y nombre de A, nunca los de B. Si A no tiene export, responder un error claro aunque B si lo tenga. Comprobar tambien el caso de un unico proyecto y que la UI sigue descargando MP3.

## P2. Llevar samples y canciones legadas a SQLite

**Problema:** el set ya tiene indice en SQLite, pero el sample y la cancion del flujo legado se descubren por archivos. Si se borra un snapshot, el estado funcional desaparece; si queda un archivo huerfano, puede parecer un proyecto vigente.

**Archivos de partida:** `backend/core/storage.py`, `backend/builders/sample_builder.py`, `backend/builders/full_song_builder.py`, `backend/adapters/sqlite/`, `backend/models/`, `tests/test_set_validation.py` y `tests/test_audio_export.py`.

**Trabajo propuesto:**

1. Agregar un repositorio SQLite pequeno para samples y canciones legadas, con IDs, `set_id`, estado, fecha y rutas de artefactos. Mantener `sample.json` y `song.json` como exports derivados.
2. Registrar cada creacion en SQLite y consultar SQLite para listar y seleccionar samples/canciones. Definir una politica explicita cuando un set se elimina: borrar registros dependientes o marcarlos invalidados, sin dejar un sample elegible.
3. Migrar una vez los JSON legados que tengan relaciones validas. Hacer la migracion idempotente; no dejar que un snapshot antiguo sobrescriba una fila ya editada en DB.
4. Conservar la secuencia obligatoria: set valido, sample existente, cancion. Registrar eventos de avance cuando aplique.

**Aceptacion:** reiniciar la aplicacion y recuperar sample/cancion desde SQLite; borrar un JSON y regenerarlo desde DB sin perder el estado; repetir la migracion sin duplicados; impedir una cancion con sample sin set valido. Verificar que `manifest.json` e `intent.json` de los drafts siguen presentes y que el audio nunca se usa como fuente de verdad.

## P3. Reducir el tamano de los controladores sin cambiar el flujo

**Problema:** `backend/application/song_service.py` tiene unas 1.578 lineas y `frontend/src/app.js` unas 2.188. Mezclan casos de uso distintos y aumentan el riesgo de regresiones al tocar Production o el editor.

**Trabajo propuesto:** extraer un caso de uso por vez, empezando por descarga/export y estado del proyecto. En backend, dejar `SongService` como fachada fina sobre servicios pequenos; en frontend, separar llamadas API y estado/acciones de Production de las acciones del editor. Mantener los contratos HTTP, el menu y la hidratacion del proyecto activo.

**Aceptacion:** sin cambios visibles para el usuario, el build de Vite pasa, los tests de descarga y persistencia pasan y `scripts/run-local.ps1 -Port 8000` sigue levantando la aplicacion. Evitar una reescritura completa de `app.js` en un solo paso.

## Orden y verificacion

Resolver P1 antes de P2 porque puede devolver el archivo de otro proyecto. P2 puede hacerse en una segunda entrega con migracion y pruebas. P3 debe ser incremental mientras se tocan esas rutas.

Comandos de verificacion disponibles:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_set_validation -v
.\.venv\Scripts\python.exe -m unittest tests.test_audio_export -v
.\.venv\Scripts\python.exe -m compileall -q backend tests
cd frontend
npm run build
```

La suite de audio puede tardar bastante o invocar procesos locales; informar exactamente que pruebas corrieron y cuales quedaron pendientes. Al completar cada avance funcional, actualizar `README.md` y este mapa de archivos si cambia la estructura: `PROJECT_STRUCTURE.md`.
