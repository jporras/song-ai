# Song AI Generator

Sistema modular en Python para generar canciones personalizadas completas mediante assets reutilizables:

- instrumental base,
- melodia vocal adaptable,
- letra dinamica.

La aplicacion se enfoca ahora en generar una cancion terminada con herramientas locales. El modo pro queda pausado hasta que el pipeline local produzca sin errores una cancion decente con instrumental, melodia, voz cantada y mezcla. El caso guia actual es una cancion de cuna o cancion infantil/emocional completa, no un Short ni una letra simple repetitiva.

## Estado Actual

Sprint actual: Sprint 15 en ejecucion: cierre del modo local real y pausa explicita del modo pro.

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
- Produccion incluye `Cancion local final`, que solo genera final si existen comandos locales reales para soundtrack, voz cantada y ffmpeg. Si falta algo, no entrega un MP3 final falso.
- El pipeline local valida disponibilidad real de ACE-Step antes de marcarlo como listo; si el comando falla, la API devuelve error JSON legible en vez de tumbar la UI.
- El modo pro queda en pausa: no se registran providers pagos/remotos en el pipeline activo.
- Produccion incluye `Estado local del sistema`: lista componentes, servicios/volumenes, comandos locales y bootstrap con indicador visual, boton para consultar estado y boton para preparar/reiniciar bootstrap en segundo plano.
- Produccion incluye `Fases del proyecto/set`: muestra si ya estan completos instrumental, melodia, letra, set, sample, cancion, mezcla, exports y final local MP3.
- La API de fases usa una ruta estatica prioritaria (`/api/projects/phases`) y la UI tolera respuestas fallidas para no dejar la pantalla en blanco.
- El bootstrap de Docker arranca en segundo plano junto con FastAPI para que reparaciones largas de modelos/dependencias no dejen la UI sin responder.
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
- Sprint 9: modo pro pausado; no se registran providers pagos/remotos en el pipeline activo.
- Sprint 10: mezcla mock con verificacion de `ffmpeg` y contrato de stems.
- Sprint 11: exportaciones completas planeadas por formato.
- Sprint 12: plantillas reutilizables desde sets.
- Sprint 13: estado de estudio IA, providers activos y contrato multi-modelo en UI/API.

Pendiente siguiente:
- Levantar/instalar los binarios y modelos GGUF reales de llama.cpp para Gemma 4 E4B IT y Qwen3 4B; la app ya tiene cliente HTTP, providers y fallback local.
- Configurar `SONG_AI_SOUNDTRACK_COMMAND` para generar `stems/instrumental.wav` localmente con MusicGen u otra herramienta gratuita.
- Configurar `SONG_AI_SINGING_VOICE_COMMAND` para generar `stems/vocals.wav` localmente con RVC/ACE-Step u otra herramienta gratuita de voz cantada.
- Usar ffmpeg local/Docker para mezclar y exportar `exports/final_mix.wav` y `exports/final_mix.mp3`.
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

El contenedor se construye en dos etapas:
- `frontend-builder`: usa Node.js solo para compilar Vue/Vite.
- `runtime`: usa `python:3.11-slim-bookworm` para ejecutar FastAPI, audio y bootstrap.

Node.js no queda en el runtime final porque la app sirve `frontend/dist` ya compilado. Python queda fijado en 3.11 por compatibilidad con modelos y librerias de audio. Las dependencias base del backend (`fastapi`, `uvicorn`) van en la imagen Docker; las dependencias pesadas/variables de audio se instalan en volumen Docker mediante bootstrap.

Volumenes Docker persistentes:
- `song_ai_data`: proyectos, SQLite, sets, samples, canciones y exports.
- `song_ai_models`: modelos locales descargados (`llm/`, `music/`, `voice/`, `stems/`, `huggingface/`).
- `song_ai_providers`: repositorios/adaptadores locales clonados para providers gratuitos.
- `song_ai_provider_cache`: cache pip y paquetes Python instalados en runtime para audio local.

Politica de actualizacion:
- Docker no actualiza Python ni paquetes base a ciegas; eso cambia solo cuando se reconstruye la imagen con cambios del proyecto.
- El bootstrap no reinstala dependencias pesadas si ya existen marcadores compatibles en el volumen y los modulos Python requeridos son importables.
- Si el volumen ya tiene paquetes Python instalados de una version anterior pero no tiene marcador, el bootstrap detecta modulos importables, crea el marcador y evita repetir `pip install`.
- Si ACE-Step existe pero sus dependencias internas fallan, por ejemplo `diffusers` requiere una version mas nueva de `huggingface_hub`, el bootstrap considera el volumen incompleto y repara dependencias con `--upgrade`.
- Si cambian `requirements-local-audio.txt`, `SONG_AI_ACE_STEP_PACKAGE`, URLs de modelos o repos configurados, el bootstrap descarga/instala lo necesario.
- No hay cron automatico porque actualizar modelos/librerias sin control puede romper compatibilidad con Python 3.11 o con los pesos descargados. La actualizacion interna existe como tarea de UI/API bajo demanda.

El contenedor puede preparar dependencias/modelos al arrancar si se activa el bootstrap:

```text
SONG_AI_BOOTSTRAP_ON_START=true
SONG_AI_INSTALL_LOCAL_AUDIO_DEPS=true
SONG_AI_INSTALL_ACE_STEP=true
SONG_AI_BOOTSTRAP_UPGRADE=false
SONG_AI_DOWNLOAD_MUSICGEN=true
SONG_AI_MUSICGEN_MODEL_ID=facebook/musicgen-small
```

Tambien puede descargar modelos por URL o clonar providers:

```text
SONG_AI_GEMMA_GGUF_URL=https://...
SONG_AI_QWEN_GGUF_URL=https://...
SONG_AI_VOICE_MODEL_URL=https://...
SONG_AI_PROVIDER_REPOS=acestep=https://github.com/.../ACE-Step.git;rvc=https://github.com/.../RVC.git
```

El bootstrap es idempotente: crea carpetas y solo descarga/clona/instala cuando falta contenido. Si los procesos son largos, se puede levantar el Docker y dejar que el contenedor termine de instalar en ejecucion. Los modelos y librerias quedan en volumenes Docker, no en carpetas temporales del contenedor.

Si necesitas reemplazar o actualizar librerias ya instaladas en `song_ai_provider_cache`, activa:

```text
SONG_AI_BOOTSTRAP_UPGRADE=true
```

Con ese flag, pip usa `--upgrade --upgrade-strategy eager`. Sin ese flag, el bootstrap usa marcadores en el volumen y deteccion de modulos ya instalados para evitar reinstalar y evitar warnings de carpetas ya existentes. Si hay marcador pero los modulos no importan correctamente, se considera instalacion incompleta y se reinstala. El runtime tambien desactiva el aviso de nueva version de pip para que los logs se concentren en el estado real del pipeline.

La ruta final local por defecto en Docker usa ACE-Step como generador completo de cancion:

```text
SONG_AI_FULL_SONG_COMMAND=python tools/acestep_generate.py --prompt {prompt_path} --lyrics {lyrics_path} --output {output_path} --checkpoint-path /app/models/music/ace-step --duration 60 --cpu-offload true --overlapped-decode true
```

ACE-Step se instala en `/app/provider-cache/python` cuando `SONG_AI_INSTALL_ACE_STEP=true`. Sus checkpoints se guardan en `/app/models/music/ace-step`, dentro del volumen `song_ai_models`. El primer arranque puede tardar bastante porque instala librerias y descarga pesos; los siguientes arranques reutilizan el volumen.

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

El flujo tiene dos salidas diferenciadas:
- **Maqueta tecnica**: valida archivos, stems, manifest y descarga, pero no es la cancion final.
- **Cancion local final**: exige herramientas locales configuradas para generar instrumental real, voz cantada real y mezcla final. Si falta una herramienta, la app no crea un falso final.

El modo pro queda fuera de esta etapa. Solo se retomara cuando el modo local genere una cancion decente sin errores.

Para conectar herramientas locales reales, configura comandos por variables de entorno. La app reemplaza estos placeholders:
- `{prompt_path}`: archivo con prompt musical e intents.
- `{lyrics_path}`: letra final exportada.
- `{instrumental_path}`: instrumental WAV generado.
- `{output_path}`: salida esperada del comando.
- `{work_dir}`: carpeta de trabajo del pipeline.

Ejemplo de contrato:

```text
SONG_AI_SOUNDTRACK_COMMAND=python tools/musicgen_generate.py --prompt {prompt_path} --output {output_path}
SONG_AI_SINGING_VOICE_COMMAND=python tools/singing_voice_generate.py --lyrics {lyrics_path} --prompt {prompt_path} --instrumental {instrumental_path} --output {output_path}
```

Scripts locales incluidos:
- `tools/check_local_audio_stack.py`: revisa ffmpeg, comandos configurados y dependencias Python.
- `tools/acestep_generate.py`: genera una cancion completa local con ACE-Step usando prompt y letra; es la ruta final recomendada en Docker.
- `tools/musicgen_generate.py`: genera instrumental con MusicGen via `transformers` cuando `torch`, `transformers` y `scipy` estan instalados y el modelo esta disponible/cacheado.
- `tools/singing_voice_generate.py`: adaptador para un backend local real de voz cantada. No simula voz por si mismo; exige un comando backend que produzca `vocals.wav`.
- `tools/use_audio_file.py`: usa un archivo local ya generado y lo copia/convierte a WAV para que Song AI lo mezcle. Es util para integrar herramientas locales externas mientras se completa el worker automatico.

Ejemplo mas completo:

```text
SONG_AI_FULL_SONG_COMMAND=python tools/acestep_generate.py --prompt {prompt_path} --lyrics {lyrics_path} --output {output_path} --checkpoint-path /app/models/music/ace-step --duration 60
SONG_AI_SOUNDTRACK_COMMAND=python tools/musicgen_generate.py --prompt {prompt_path} --output {output_path} --model facebook/musicgen-small --seconds 45
SONG_AI_SINGING_VOICE_COMMAND=python tools/singing_voice_generate.py --lyrics {lyrics_path} --prompt {prompt_path} --instrumental {instrumental_path} --output {output_path} --backend-command "python tools/mi_backend_voz_cantada.py --lyrics {lyrics_path} --prompt {prompt_path} --instrumental {instrumental_path} --output {output_path}"
```

Ejemplo usando archivos locales ya generados:

```text
SONG_AI_SOUNDTRACK_COMMAND=python tools/use_audio_file.py --input C:\audio\instrumental.wav --output {output_path}
SONG_AI_SINGING_VOICE_COMMAND=python tools/use_audio_file.py --input C:\audio\voz_cantada.wav --output {output_path}
```

Antes de generar final local:

```text
python tools/check_local_audio_stack.py
```

El endpoint de estado local es:

```text
GET /api/local-pipeline/status
GET /api/system/status
GET /api/projects/phases
```

La generacion final local se ejecuta con:

```text
POST /api/local-final-song
POST /api/system/bootstrap/restart
POST /api/system/bootstrap/upgrade
```

`/api/system/bootstrap/upgrade` permite actualizar/reemplazar dependencias internas del contenedor desde la UI, sin entrar al Docker. Ejecuta el bootstrap con `pip --upgrade --upgrade-strategy eager` y conserva los volumenes.

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

En la fase actual mock se genera una maqueta audible de cancion en `exports/final_mix.wav`: instrumental sintetico suave, guia melodica y una guia vocal sintetica de vocales, ademas de una copia de la letra real del set en `exports/lyrics.md`. Esta guia vocal ayuda a validar melodia, estructura y mezcla, pero no pronuncia la letra ni reemplaza una voz cantada real. Tambien se crean stems mock separados en `stems/instrumental.wav`, `stems/melody_guide.wav` y `stems/vocals.wav` para conservar instrumental, melodia y voz por separado. En Docker tambien se genera `exports/final_mix.mp3` con `ffmpeg`; si se ejecuta fuera de Docker y `ffmpeg` no esta disponible, queda `exports/final_mix.mp3.pending.txt`. El archivo `exports/final_mix.mock.txt` sigue marcando donde se reemplazara el contenido por la mezcla real cuando se conecten providers de audio.

La UI incluye la accion **Guardar MP3 en mi equipo**, que descarga el ultimo `final_mix.mp3` desde Docker hacia una ruta elegida por el usuario en el navegador. La API equivalente es:

```text
GET /api/audio-exports/latest/download?format=mp3
```

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

Al iniciar, la app sincroniza de forma conservadora sets antiguos desde `data/sets/<set_id>/set.json` hacia SQLite cuando todavia no existen en la tabla activa. Esto corrige proyectos creados antes del indice SQLite sin convertir los JSON en fuente de verdad permanente.

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
