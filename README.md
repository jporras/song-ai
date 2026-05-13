# Song AI Generator

Sistema modular en Python para generar canciones personalizadas mediante assets reutilizables:

- instrumental base,
- melodia vocal adaptable,
- letra dinamica.

La aplicacion esta pensada para funcionar primero con mocks y providers locales, y despues permitir providers profesionales sin acoplar el core.

## Estado Actual

Sprint actual: Sprint 13 en ejecucion: migracion web con backend hexagonal, Vue, Docker, SQLite y preparacion para modelos locales.

Ultimo ajuste:
- Se agrego `docs/MULTI_MODEL_MASTER_SPEC.md` como especificacion maestra del sistema multi-modelo.
- Estructura alineada con `docs/TECHNICAL_SPEC.md`: el codigo Python vive en `backend/`.
- Entorno virtual local creado en `.venv` con Python 3.11.0.
- Las opciones de estado/verificacion/listado de carpetas salieron del menu principal y ahora viven como diagnostico de test.
- El menu principal ahora guia al usuario por procesos creativos: instrumental, melodia, letra, set, sample y cancion completa.
- Las preguntas creativas muestran catalogos numerados y permiten opcion personalizada cuando aplica.
- Cada pregunta creativa incluye una explicacion breve y una opcion `L` para describir libremente; la app interpreta ese texto de forma local/mock y asigna un valor cercano.
- Sprints 8 a 12 completados en modo mock/local: providers, mezcla, exportaciones y plantillas reutilizables.
- Transformacion web iniciada: backend FastAPI con arquitectura hexagonal, frontend Vue/Vite y SQLite en un solo contenedor Docker.
- Los sets ahora representan proyectos musicales: guardan nombre de proyecto, fecha, descripcion, IDs de assets y ruta del `set.json` en SQLite.
- La vista de produccion incluye asistencia IA para recordar que un set/proyecto necesita completar los puntos 1, 2 y 3: instrumental, melodia y letra.
- `AGENTS.md` define como regla del rol IA que la asistencia debe recordar, validar y bloquear avance cuando falte instrumental, melodia o letra.
- Los sets persistidos en SQLite se pueden exportar/regenerar como JSON; si el `set.json` ya existe, se sobrescribe desde la version vigente en base de datos.
- La UI incluye un footer de asistencia IA con sugerencias dinamicas para reforzar el procedimiento correcto: completar instrumental, melodia y letra, crear set, generar sample y luego cancion completa.
- `AGENTS.md` tambien define que la IA debe ayudar a completar una cancion acorde al proyecto activo usando nombre, descripcion, intents, assets y set como contexto.
- Se inicio `ModelOrchestrator` en modo mock: registra handoffs, tasks y model runs en SQLite sin cargar modelos reales todavia.
- Cada proyecto conserva un historico de pasos (`project_events`) con fecha, fase, actor/modelo, estado y mensaje para reconstruir el camino de creacion de la cancion.

Completado:
- Sprint 1: estructura modular, menu principal, carpetas de datos y storage basico.
- Sprint 2: modelos JSON iniciales, `AssetDraft`, `SongSet`, `manifest.json` e `intent.json`.
- Sprint 3: exploradores mock para instrumentales, melodias y letras.
- Sprint 4: curaduria basica con favoritos.
- Sprint 5: set builder mock con validacion de assets disponibles.
- Sprint 6: sample builder mock desde el ultimo set valido.
- Sprint 7: full song builder mock desde el ultimo sample valido.

- Sprint 8: providers locales mock intercambiables.
- Sprint 9: providers pro placeholder sin APIs reales.
- Sprint 10: mezcla mock con verificacion de `ffmpeg` y contrato de stems.
- Sprint 11: exportaciones completas planeadas por formato.
- Sprint 12: plantillas reutilizables desde sets.

Pendiente siguiente:
- Reemplazar mocks por providers reales sin cambiar el flujo.
- Conectar `ModelOrchestrator` a providers reales y workers bajo demanda.

## Especificacion Maestra

La vision multi-modelo vive en:

- `docs/MULTI_MODEL_MASTER_SPEC.md`

Ese documento define:
- filosofia del sistema como estudio musical IA,
- roles de assistant, intent extractor, music providers, voice providers y audio pipeline,
- handoffs entre modelos,
- persistencia con SQLite como fuente activa,
- JSON exportables como snapshots,
- fases completas desde conversacion inicial hasta exportacion y plantillas.

## Estructura

```text
backend/
  adapters/
  application/
  audio/
  builders/
  config/
  core/
  explorers/
  models/
  providers/
  utils/
  main.py
  server.py
  requirements.txt
data/
  drafts/
  sets/
  samples/
  songs/
  templates/
docs/
frontend/
  src/
```

## Ejecucion

### Docker

Levantar backend y frontend:

```powershell
docker compose up --build
```

Servicio:
- Aplicacion web Vue + backend API: `http://localhost:8000`

El contenedor `song-ai-app` incluye Node.js para construir Vue/Vite y Python/FastAPI para ejecutar el backend. Los datos se guardan en el volumen Docker `song_ai_data`.

SQLite guarda el indice de rutas de configuraciones JSON en `data/song_ai.sqlite`.

No se usa Nginx en esta etapa porque FastAPI sirve la API y el frontend compilado por Vite desde el mismo contenedor. Si mas adelante se separan frontend/backend o se requiere reverse proxy/cache TLS, se agregara una carpeta `nginx/` con su configuracion Docker.

### Backend Web Local

Si no usas Docker, primero construye el frontend con Node/Vite:

```powershell
cd frontend
npm install
npm run build
cd ..
```

Luego ejecuta API FastAPI y frontend estatico desde Python:

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe backend\server.py
```

URL local:

```text
http://localhost:8000
```

### Local con venv

Activar entorno virtual en PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verificar version:

```powershell
python --version
```

Ejecutar aplicacion:

```powershell
$env:PYTHONPATH="backend"
.\.venv\Scripts\python.exe backend\main.py
```

El menu guia el flujo creativo:
- explorar instrumental con modo rapido, guiado o desde perfil/base,
- explorar melodia vocal con modo rapido, guiado o basada en perfil,
- crear letra con plantilla rapida, modo guiado o variacion IA mock,
- listar drafts,
- marcar favoritos,
- listar favoritos,
- crear un set valido con los primeros drafts disponibles,
- crear un sample mock desde el ultimo set,
- crear una cancion completa mock desde el ultimo sample.
- listar providers disponibles,
- preparar mezcla mock,
- preparar exportaciones,
- guardar plantilla reutilizable.

Flujo sugerido:

```text
1. Explorar instrumental
2. Explorar melodia vocal
3. Crear letra
4. Listar drafts
7. Crear set valido
8. Crear sample mock
9. Crear cancion completa mock
```

Para crear una cancion completa primero debe existir un set/proyecto valido. Ese set esta compuesto por los puntos 1, 2 y 3:
- instrumental,
- melodia,
- letra.

La asistencia IA del frontend revisa los drafts disponibles y recuerda que partes faltan antes de crear el set, sample o cancion completa.

Los puntos 1, 2 y 3 preguntan por intencion creativa y guardan esa informacion en `intent.json`.

Las preguntas creativas muestran opciones posibles antes de pedir respuesta. Por ejemplo:
- estilos o generos,
- atmosfera emocional,
- BPM,
- tonalidad,
- instrumentos,
- estilo vocal,
- rango vocal,
- estructura,
- idioma,
- tema lirico,
- placeholders.

Cuando una opcion no cubre la idea del usuario, el flujo permite escribir una alternativa personalizada.

Tambien existe la opcion `L. Describir libremente para interpretar`. En esta fase la interpretacion es local/mock por palabras clave; mas adelante podra conectarse a un provider IA sin cambiar el flujo.

En instrumentos, la app muestra un catalogo base por familias como teclas, guitarras, bajos, percusion, cuerdas, metales, sintetizadores, sonidos regionales y efectos. No pretende ser una lista total de todos los instrumentos posibles; para eso estan las opciones `L` y `C`.

Ejecutar diagnostico de test:

```powershell
python tests\diagnostics.py
```

El diagnostico valida:
- estado basico del proyecto,
- existencia o creacion de carpetas de datos,
- listado de carpetas de datos.

## Persistencia

Cada draft guarda:
- `manifest.json`,
- `intent.json`,
- `metadata.json`,
- archivo mock del asset (`instrumental.txt`, `melody.txt` o `lyrics.md`).

Los sets se guardan en `data/sets/<set_id>/set.json`.
Cada set es un proyecto musical y contiene:
- `project_name`: nombre visible del proyecto/cancion.
- `created_at`: fecha de creacion.
- `description`: descripcion breve del objetivo musical.
- IDs de instrumental, melodia y letra.
- `compatibility_data`: estado de compatibilidad entre assets.

Los samples mock se guardan en `data/samples/<sample_id>/sample.json` y `preview.txt`.

Las canciones completas se guardan en `data/songs/<song_id>/`.

Dentro de cada cancion:
- `song.json`: metadata de la cancion y rutas planeadas.
- `exports/`: aqui quedaran mezclas finales y metadata.
- `stems/`: aqui quedaran stems como instrumental y voces.

Formatos comunes planeados para `exports/`:
- `final_mix.mp3`: comprimido, muy compatible para compartir y reproducir.
- `final_mix.m4a`: AAC comprimido, comun en moviles y buena calidad por tamano.
- `final_mix.ogg`: formato abierto util para web/apps.
- `final_mix.wav`: sin compresion, recomendado para master y procesamiento.
- `final_mix.flac`: lossless comprimido, alta calidad con menor peso.
- `final_mix.aiff`: sin compresion, comun en produccion musical.
- `lyrics.md`: letra editable.
- `manifest.json`: metadata del export.

Formatos comunes planeados para `stems/`:
- `instrumental.wav`
- `vocals.wav`
- `melody_guide.wav`
- `drums.wav`
- `bass.wav`
- `music.wav`
- versiones `.flac` cuando se quiera compresion lossless.

En la fase actual mock todavia no se genera audio real. Se crea `exports/final_mix.mock.txt` para marcar donde quedara el archivo final cuando se implemente el pipeline de audio con providers/ffmpeg.

Las plantillas reutilizables se guardan en `data/templates/<template_id>/template.json`.

SQLite indexa las rutas de los JSON generados:
- `manifest.json`
- `intent.json`
- `metadata.json`
- `set.json`
- `sample.json`
- `song.json`
- `exports/manifest.json`
- `template.json`

SQLite tambien guarda orquestacion multi-modelo:
- `tasks`: tareas del pipeline y progreso.
- `model_runs`: ejecuciones de modelos/providers.
- `project_events`: historico de pasos por proyecto/cancion.

En esta fase los handoffs son mock y sirven para validar contratos, progreso, persistencia y UI antes de cargar modelos reales.

La API expone este indice en:

```text
GET /api/json-configs
```

Los sets tambien se guardan en SQLite para que la interfaz pueda listarlos, mostrarlos como proyectos y enseñar su configuracion cuando el usuario lo pida:

```text
GET /api/sets
GET /api/sets/{set_id}
POST /api/sets
POST /api/sets/export
GET /api/orchestration/status
GET /api/tasks
GET /api/model-runs
GET /api/project-events
POST /api/orchestration/handoff
```

`POST /api/sets` recibe opcionalmente:

```json
{
  "project_name": "Mi nueva cancion",
  "description": "Balada pop calida para una dedicatoria familiar"
}
```

Cada set expone nombre de proyecto, fecha, descripcion, IDs de instrumental, melodia y letra, compatibilidad, ruta del `set.json` y un bloque `ai_management` preparado para que el interpreter provider gestione sugerencias y recuerde los requisitos creativos del proyecto.

`POST /api/sets/export` exporta todos los sets persistidos en SQLite hacia sus archivos `set.json`. La base de datos conserva la version de trabajo; el JSON es una copia exportada y se sobrescribe cuando ya existe un archivo previo con el mismo nombre.

## Reglas De Documentacion

Cada avance funcional, cambio de arquitectura o sprint completado debe quedar registrado en este README.
