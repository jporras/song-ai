# Song AI Generator

Sistema modular en Python para generar canciones personalizadas completas mediante assets reutilizables:

- instrumental base,
- melodia vocal adaptable,
- letra dinamica.

La aplicacion esta pensada para funcionar primero con mocks y providers locales, y despues permitir providers profesionales sin acoplar el core. El caso guia actual es una cancion de cuna o cancion infantil/emocional completa, no un Short ni una letra simple repetitiva.

## Estado Actual

Sprint actual: Sprint 14 en ejecucion: alcance real de cancion completa de cuna/infantil emocional y preparacion del pipeline local/hibrido.

Ultimo ajuste:
- Se corrigio el alcance del producto: el objetivo es generar una cancion completa con buena letra, estructura musical, soundtrack, voz cantada, mezcla final y exportacion de audio.
- La referencia visual o de YouTube queda solo como inspiracion de sensibilidad/ternura; el video es opcional y no define el formato.
- La prioridad del sistema queda fija: buena letra, buena intencion emocional, buena estructura musical, soundtrack coherente, voz cantada y mezcla final.
- Se agregaron defaults de cancion de cuna para Isabella en la UI y en los mocks creativos.
- Se configuro el stack local/hibrido recomendado: Gemma 4 E4B IT GGUF para interpreter/lyrics, Qwen3 4B GGUF para soporte tecnico, MusicGen para soundtrack, RVC/ACE-Step para voz cantada, Demucs para stems y ffmpeg para mezcla/export.
- El sistema explicita que no debe priorizar canciones de 20 segundos, formato Short, repeticion excesiva, letras genericas ni TTS hablado como si fuera canto.
- El proyecto fue inicializado como repositorio Git en `main` y subido a `https://github.com/jporras/song-ai`.
- `docs/` queda como planeamiento inicial local y no se versiona en Git; el repositorio contiene solo el proyecto ejecutable, configuracion y documentacion operativa.
- Se agrego estado de estudio IA en `GET /api/studio/status`: providers activos por rol, politica de SQLite como fuente activa, JSON como snapshots y handoffs via estado.
- La UI de Biblioteca muestra providers activos, estado de modelos locales y contrato del estudio IA.
- Estructura alineada con arquitectura backend/frontend: el codigo Python vive en `backend/`.
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
- Produccion ahora muestra explicitamente el paso `Generar WAV/MP3`; en modo mock crea `exports/final_mix.wav` como audio valido de prueba y genera `final_mix.mp3` si `ffmpeg` esta disponible.
- Produccion incluye `Crear MP3 predefinido`, que arma la cancion de cuna para Isabella con los defaults actuales, crea set/sample/cancion/mezcla y exporta WAV/MP3 en un solo flujo.
- Produccion incluye `Gemma transversal`, asistente de proyecto activo via llama.cpp cuando `SONG_AI_LLAMA_CPP_ENABLED=true`; si llama.cpp no responde, conserva guia local y deja la app ejecutable.
- Produccion incluye `Qwen tecnico`, rol separado para ajustes tecnicos, debugging, arquitectura, workers, SQLite, ffmpeg y pipeline. Qwen no reemplaza a Gemma en creatividad musical.

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
- Sprint 13: estado de estudio IA, providers activos y contrato multi-modelo en UI/API.

Pendiente siguiente:
- Levantar/instalar los binarios y modelos GGUF reales de llama.cpp para Gemma 4 E4B IT y Qwen3 4B; la app ya tiene cliente HTTP, providers y fallback local.
- Conectar MusicGen small como primer generador real de soundtrack.
- Definir worker de voz cantada con RVC/ACE-Step.
- Conectar Demucs y ffmpeg para stems, mezcla y export WAV/MP3.
- Implementar carga por demanda y liberacion de memoria entre modelos.

## Alcance De Cancion

El sistema debe crear una cancion completa de cuna, infantil/emocional o familiar personalizada. Puede usar nombre propio, narrativa suave, tono poetico y estructura musical completa.

Estructuras soportadas:
- intro,
- verso 1,
- pre-coro opcional,
- coro,
- verso 2,
- puente opcional,
- coro final,
- outro.

El sistema debe poder producir:
- letra original de buena calidad,
- estructura musical completa,
- soundtrack/instrumental,
- voz cantada,
- mezcla final,
- exportacion de audio,
- video opcional solo como fase futura.

No se considera objetivo principal:
- canciones de 20 segundos,
- formato Short,
- repeticion excesiva,
- letras genericas,
- TTS hablado como si fuera canto.

## Stack Local/Hibrido

LLM via llama.cpp:
- `interpreter`: Gemma 4 E4B IT GGUF para entender intencion, pedir/inferir datos faltantes, decidir estilo, tono y estructura, y coordinar servicios.
- `lyrics`: Gemma 4 E4B IT GGUF para crear letra completa, mejorar metrica/rima, adaptar tono, estructurar secciones y generar prompts musicales.
- `technical`: Qwen3 4B GGUF para soporte tecnico, codigo, debugging y arquitectura.

Audio:
- `soundtrack`: MusicGen small inicialmente; MusicGen medium si el hardware lo permite.
- `singing_voice`: RVC / ACE-Step; so-vits-svc opcional.
- `stems`: Demucs.
- `mixer`: ffmpeg.

Variables para conectar llama.cpp:

```powershell
$env:SONG_AI_LLAMA_CPP_ENABLED="true"
$env:SONG_AI_LLAMA_CPP_BASE_URL="http://localhost:8080"
$env:SONG_AI_INTERPRETER_MODEL="Gemma 4 E4B IT GGUF"
$env:SONG_AI_LYRICS_MODEL="Gemma 4 E4B IT GGUF"
$env:SONG_AI_TECHNICAL_MODEL="Qwen3 4B GGUF"
```

En Docker, si llama.cpp corre en el host, usa:

```powershell
$env:SONG_AI_LLAMA_CPP_ENABLED="true"
$env:SONG_AI_LLAMA_CPP_BASE_URL="http://host.docker.internal:8080"
docker compose up --build
```

El endpoint esperado es el servidor HTTP de llama.cpp compatible con `POST /completion`. La app mantiene fallback local si el servidor no esta disponible.

Restricciones de ejecucion:
- proyecto local/hibrido para portatil de 16 GB RAM,
- no cargar todos los modelos al mismo tiempo,
- cargar por demanda y liberar memoria,
- persistir progreso en SQLite,
- emitir eventos de progreso al usuario.

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

El contenedor `song-ai-app` incluye Node.js para construir Vue/Vite, Python/FastAPI para ejecutar el backend y `ffmpeg` para generar MP3 desde el WAV de mezcla. Los datos se guardan en el volumen Docker `song_ai_data`.

SQLite guarda el indice de rutas de configuraciones JSON en `data/song_ai.sqlite`.

No se usa Nginx en esta etapa porque FastAPI sirve la API y el frontend compilado por Vite desde el mismo contenedor. Si mas adelante se separan frontend/backend o se requiere reverse proxy/cache TLS, se agregara una carpeta `nginx/` con su configuracion Docker.

### Uso Desde La UI

1. Abre `http://localhost:8000`.
2. En `Instrumental`, usa o ajusta los valores por defecto de cancion de cuna: genero `lullaby`, mood `tender`, BPM `72`, piano, music box, soft pad y strings.
3. Guarda el instrumental.
4. En `Melodia`, usa una guia de voz cantada suave, rango medio y estructura completa.
5. Guarda la melodia.
6. En `Letra`, usa el tema `lullaby for {name}` y placeholders como `name=Isabella`.
7. Guarda la letra.
8. En `Editor de letra`, selecciona un draft de letra, modifica el Markdown y guarda cambios. Esto actualiza `lyrics.md` sin tocar instrumental ni melodia.
9. En `Produccion`, crea el set/proyecto. El set solo se habilita si existen instrumental, melodia y letra.
10. Crea el sample/checkpoint.
11. Crea la cancion completa mock.
12. Si quieres validar rapido el flujo por defecto, usa `Crear MP3 predefinido` para generar la cancion de cuna de Isabella con set, sample, cancion, mezcla y WAV/MP3.
13. Para el flujo manual: prepara mezcla.
14. Prepara exports.
15. Genera WAV/MP3. En fase mock se crea `final_mix.wav` y, dentro del contenedor Docker, `final_mix.mp3` usando `ffmpeg`.
16. Usa `Gemma transversal` para pedir sugerencias sobre el proyecto activo. Si llama.cpp esta activo, Gemma responde desde `POST /completion`; si no, usa guia local y registra handoffs en SQLite.
17. Usa `Qwen tecnico` para ajustes de codigo/pipeline, errores, workers, ffmpeg, SQLite y arquitectura.
18. En `Biblioteca`, revisa providers activos, estado del estudio IA, tasks, model runs, historico del proyecto y rutas JSON indexadas.

El flujo actual crea artefactos mock, pero respeta el contrato final: cancion completa con letra original, estructura musical, soundtrack, voz cantada, mezcla y exportacion de audio. No apunta a Shorts ni a TTS hablado.

### Proyectos Activos

La aplicacion trabaja sobre proyectos de canciones. Un proyecto activo corresponde a un set y debe cargar transversalmente:
- nombre y descripcion del proyecto,
- instrumental seleccionado,
- melodia seleccionada,
- letra seleccionada y su `lyrics.md` editable,
- set activo,
- samples asociados,
- canciones asociadas,
- eventos de progreso del proyecto.

Desde `Biblioteca`, usa `Cargar proyecto` sobre un set guardado. Al cargarlo, la app actualiza el formulario de proyecto, la configuracion visible, el editor de letra y el contexto usado por la asistencia IA.

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
- crear un sample/checkpoint mock desde el ultimo set,
- crear una cancion completa mock desde el ultimo sample.
- listar providers disponibles,
- preparar mezcla mock,
- preparar exportaciones,
- generar WAV/MP3 desde la cancion mas reciente,
- crear MP3 predefinido de la cancion de cuna base,
- consultar el asistente Gemma transversal sobre el proyecto activo,
- consultar Qwen tecnico para ajustes de implementacion y pipeline,
- guardar plantilla reutilizable.

Flujo sugerido:

```text
1. Explorar instrumental
2. Explorar melodia vocal
3. Crear letra
4. Listar drafts
7. Crear set valido
8. Crear sample/checkpoint mock
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

Los samples mock se guardan en `data/samples/<sample_id>/sample.json` y `preview.txt`. En el alcance actual el sample es un checkpoint de calidad antes de la cancion completa, no el formato final ni un Short.

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

En la fase actual mock se puede generar `exports/final_mix.wav` como audio valido de prueba para verificar el flujo de exportacion. En Docker tambien se genera `exports/final_mix.mp3` con `ffmpeg`; si se ejecuta fuera de Docker y `ffmpeg` no esta disponible, queda `exports/final_mix.mp3.pending.txt`. El archivo `exports/final_mix.mock.txt` sigue marcando donde se reemplazara el contenido por la mezcla real cuando se conecten providers de audio.

La cancion final real debe pasar por:
- letra completa y prompt musical con Gemma,
- soundtrack/instrumental con MusicGen,
- voz cantada con RVC/ACE-Step,
- stems opcionales con Demucs,
- mezcla y normalizacion con ffmpeg,
- export WAV/MP3.

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

El estado activo del estudio IA se expone en:

```text
GET /api/studio/status
GET /api/models/status
GET /api/providers
```

`GET /api/studio/status` indica:
- providers activos por rol (`interpreter`, `music`, `voice`, `lyrics`),
- que SQLite es la fuente activa,
- que los JSON son snapshots regenerables,
- que los handoffs entre modelos deben pasar por SQLite, tasks, `intent.json`, `manifest.json` o `set.json`,
- que no hay prompts encadenados directamente entre modelos.

Los sets tambien se guardan en SQLite para que la interfaz pueda listarlos, mostrarlos como proyectos y enseñar su configuracion cuando el usuario lo pida:

```text
GET /api/sets
GET /api/sets/{set_id}
GET /api/projects/{set_id}
POST /api/sets
POST /api/presets/lullaby/mp3
POST /api/sets/export
GET /api/lyrics/{asset_id}
PUT /api/lyrics/{asset_id}
POST /api/mix
POST /api/exports
POST /api/audio-exports
POST /api/assistant/gemma
POST /api/assistant/qwen
GET /api/orchestration/status
GET /api/tasks
GET /api/model-runs
GET /api/project-events
POST /api/orchestration/handoff
GET /api/studio/status
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
