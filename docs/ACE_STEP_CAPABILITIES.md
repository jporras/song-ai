# ACE-Step 1.5 — Contrato de capacidades para Song-AI

Estado: guía de integración basada en documentación oficial consultada el 2026-10-04. **Verificar contra la versión y los modelos instalados antes de ejecutar.**

## 0. Propósito y autoridad

Este documento describe **lo que ACE-Step acepta**, no una promesa de que el audio generado sea idéntico a la intención. Gemma y Qwen deben producir un `ACEPlan` válido a partir de la especificación aprobada por el usuario (`MusicSpec`), sin cambiarla silenciosamente.

Orden de autoridad para las decisiones: (1) preferencias explícitas del usuario y especificación aprobada; (2) capacidades reales del backend instalado; (3) propuestas técnicas registradas bajo el orquestador; (4) defaults declarados. Si (1) y (2) entran en conflicto, conservar el requisito y registrar el bloqueo: solicitar cambio o indicar limitación. El MIDI y el WAV guía son representaciones de la especificación; si discrepan, detener y reconciliar. MusicSpec designa conceptualmente `song_specs`; no crea una segunda fuente activa.

**Separar planificación de generación**: Gemma y Qwen acuerdan `MusicSpec` y `ACEPlan`; ACE-Step genera; un validador contrasta el resultado con `MusicSpec`. El LM interno de ACE-Step puede modificar/estimar metadatos y no equivale a ejecutar las instrucciones de Gemma/Qwen de forma determinista.

## 1. Catálogo de tareas admitidas

| `task_type` | Entrada obligatoria | Operación | Restricción |
|---|---|---|---|
| `text2music` | `caption` o `lyrics` | Generar desde texto | No ejecuta MIDI como partitura |
| `cover` | `src_audio`, `caption` | Transformar estilo/timbre preservando parte de la estructura | Fidelidad aproximada |
| `repaint` | `src_audio`, `caption`, intervalo | Regenerar un segmento | Intervalo en segundos; preferir máscara explícita |
| `lego` | `src_audio`, `instruction`, `caption` | Crear una pista en contexto | Solo modelo Base |
| `extract` | `src_audio`, `instruction` | Extraer pista | Solo modelo Base |
| `complete` | `src_audio`, `instruction`, `caption` | Completar arreglo | Solo modelo Base |

Para `lego` y `extract`, tipos de pista documentados: `vocals`, `backing_vocals`, `drums`, `bass`, `guitar`, `keyboard`, `percussion`, `strings`, `synth`, `fx`, `brass`, `woodwinds`. Para `complete`, declarar explícitamente las pistas a completar. No asumir que se soportan otras etiquetas.

## 2. Parámetros documentados (`GenerationParams`, interfaz Python)

| Campo | Tipo / rango | Reglas |
|---|---|---|
| `task_type` | enumeración de sección 1 | Nunca inventar modos |
| `instruction` | texto | Instrucción específica de edición/pista; usar forma requerida por la tarea |
| `caption` | cadena, máximo 512 caracteres | Descripción musical concreta: estilo, instrumentación, voz, textura, dinámica; no volcar MusicSpec entero |
| `lyrics` | cadena, máximo 4096 caracteres | Texto cantado con etiquetas de secciones; `[Instrumental]` para ausencia de letra |
| `instrumental` | booleano | `true` impide voz cantada aunque exista letra |
| `vocal_language` | código ISO 639-1, `unknown` | Para español `es` |
| `bpm` | entero 30–300 o nulo | Tempo objetivo, no exactitud garantizada |
| `keyscale` | texto, p. ej. `C Major`, `Am` | Tonalidad objetivo; cadena vacía para autodetección |
| `timesignature` | `2`, `3`, `4`, `6` como texto | Equivalen a 2/4, 3/4, 4/4 y 6/8 |
| `duration` | segundos 10–600; `-1` automático | Objetivo, comprobar duración real |
| `reference_audio` | ruta de audio o nulo | Referencia musical; no es partitura MIDI |
| `src_audio` | ruta de audio o nulo | Audio fuente de tareas de edición |
| `audio_codes` | cadena de códigos semánticos 5 Hz | Solo uso avanzado; **no** convertir WAV/MIDI directamente a esta cadena sin el codificador compatible |
| `audio_cover_strength` | flotante 0–1 | 1 fuerte influencia de fuente; 0.5 equilibrada; 0.1 interpretación libre; evaluar por oído/métricas |
| `repainting_start` | segundos, >=0 | Inicio de intervalo |
| `repainting_end` | segundos, `-1` hasta final | Final posterior a inicio |
| `chunk_mask_mode` | `auto` o `explicit` | Para repaint localizado, usar `explicit` |
| `thinking` | booleano | Activa LM 5 Hz en tareas compatibles; se omite en `cover`, `repaint`, `extract` |
| `use_cot_metas` | booleano | LM puede estimar metadatos |
| `use_cot_caption` | booleano | LM puede reescribir caption |
| `use_cot_language` | booleano | LM puede detectar idioma |
| `use_cot_lyrics` | booleano | Reservado; no depender de él |
| `lm_temperature` | 0–2 | Creatividad LM, solo si se usa |
| `lm_cfg_scale` | flotante | Condicionamiento LM |
| `lm_top_k` | entero | Muestreo LM |
| `lm_top_p` | 0–1 | Muestreo LM |
| `lm_negative_prompt` | texto | Condicionamiento negativo LM |
| `inference_steps` | Turbo 1–20 (8 recomendado); Base 1–200 (32–64 recomendado) | Depende del modelo |
| `guidance_scale` | 1–15 | En Turbo se ajusta internamente a 1; no prometer CFG en Turbo |
| `shift` | flotante | Para Turbo, documentación recomienda 3.0; no se autocorrige |
| `seed` | entero, `-1` aleatorio | Fijar para repetibilidad bajo mismas condiciones, sin prometer identidad entre hardware/versiones |
| `use_adg` | booleano | Solo Base |
| `cfg_interval_start/end` | flotantes | Control avanzado de CFG |
| `infer_method` | `ode`/`sde` | Método de difusión |
| `timesteps` | lista opcional | Avanzado; prevalece sobre pasos y shift |

`GenerationConfig` incluye `batch_size` (1–8), `allow_lm_batch`, `use_random_seed`, `seeds`, `lm_batch_chunk_size`, `audio_format` (`flac`, `mp3`, `opus`, `aac`, `wav`, `wav32`). Para el portátil con memoria limitada, **configurar por defecto `batch_size=1`**, evitando ejecuciones simultáneas de otros modelos, sujeto a medición.

### Diferencia importante entre APIs

La API HTTP puede denominar `key_scale`, `time_signature`, `audio_duration`, `reference_audio_path`, `src_audio_path` y `audio_code_string`, mientras que la interfaz Python utiliza `keyscale`, `timesignature`, `duration`, `reference_audio`, `src_audio` y `audio_codes`. **No pasar nombres Python directamente a HTTP sin un adaptador comprobado.** El significado de `thinking`/códigos semánticos debe verificarse contra el endpoint concreto.

## 3. Gramática de la letra

Usar etiquetas estructurales claras como `[Intro]`, `[Verse]`, `[Chorus]`, `[Bridge]`, `[Outro]`, `[Instrumental]`. Son **indicaciones** al modelo, no marcadores de tiempo exactos. No inventar etiquetas que se supongan órdenes rígidas ni confiar en que una sección tenga un número exacto de compases. Guardar la segmentación temporal real en `MusicSpec`, no únicamente en la letra.

Ejemplo:

```text
[Intro]
[Instrumental]
[Verse]
Primera línea de la estrofa
Segunda línea de la estrofa
[Chorus]
Primera línea del estribillo
[Outro]
[Instrumental]
```

## 4. Selección del modo: reglas para Gemma y Qwen

1. **No existe audio** y el usuario acepta interpretación creativa: `text2music`.
2. **Existe WAV guía** y se busca conservar composición cambiando timbre/estilo: probar `cover`, con `src_audio` y fuerza alta como punto de partida; comprobar conservación real.
3. **Hay un defecto localizado** y el resto está aprobado: `repaint` con intervalo explícito; no regenerar toda la canción.
4. **Falta una pista instrumental** y hay modelo Base: `lego`.
5. **Hay que aislar una pista** y hay modelo Base: `extract`.
6. **Hay pistas parciales que necesitan arreglo** y hay modelo Base: `complete`.
7. **Solo existe MIDI**: renderizar a WAV guía mediante un sintetizador/instrumentos definidos; ACE-Step no garantiza MIDI-to-audio exacto.
8. **Se exige identidad nota por nota**: no prometerla con ACE-Step; ofrecer síntesis MIDI determinista o un flujo híbrido donde ACE-Step aporta capas expresivas y la composición fija se conserva fuera de él.

## 5. Contrato `ACEPlan` que deben producir Gemma y Qwen

Este JSON es **un contrato propio de Song-AI**, NO el payload nativo de ACE-Step. Un adaptador traduce los campos a la API instalada.

```json
{
  "schema_version": "1.0",
  "music_spec_id": "song-001",
  "user_approved": true,
  "model_family": "turbo",
  "task_type": "cover",
  "goal": "Mantener melodía y armonía de la guía; cambiar la producción a balada acústica",
  "source": {
    "src_audio": "guides/song-001.wav",
    "reference_audio": null,
    "midi": "guides/song-001.mid"
  },
  "inputs": {
    "caption": "Intimate acoustic pop ballad, warm piano, fingerpicked guitar, expressive female lead, soft bass and delicate drums",
    "lyrics": "[Verse]\n...\n[Chorus]\n...",
    "instrumental": false,
    "vocal_language": "es",
    "bpm": 76,
    "keyscale": "C Major",
    "timesignature": "4",
    "duration": 180
  },
  "controls": {
    "audio_cover_strength": 0.9,
    "thinking": false,
    "inference_steps": 8,
    "shift": 3.0,
    "seed": 12345,
    "batch_size": 1
  },
  "hard_constraints": ["lyrics", "section_order", "target_melody"],
  "soft_constraints": ["voice_timbre", "acoustic_texture"],
  "known_limitations": ["ACE-Step cannot guarantee exact MIDI note reproduction"],
  "requires_user_decision": [],
  "validation": ["lyrics_alignment", "duration", "bpm", "key", "melody_similarity", "section_order"]
}
```

Los campos `hard_constraints` son **criterios de aceptación Song-AI**, no garantías del generador. Si la salida incumple un criterio duro, debe rechazarse o solicitar aprobación del usuario para cambiar la especificación.

## 6. Protocolo de negociación Gemma ↔ Qwen

**Gemma (intención)**: extrae preferencias, ambigüedades, letra y objetivos perceptivos. **Qwen (viabilidad)**: comprueba modos, tipos, rangos, longitud, archivos, memoria y compatibilidad; propone el plan. **Gemma (explicación)**: presenta diferencias y decisiones al usuario. **Qwen (compilación)**: propone `ACEPlan` estructurado; un adaptador validado traduce al payload instalado. Son roles objetivo; el compilador ACEPlan sigue pendiente. Los handoffs pasan por tasks y SQLite bajo ModelOrchestrator, nunca por conversación directa ni votación entre modelos.

**Preguntas que sí requieren aclaración:** ¿se debe conservar exactamente la melodía o basta con similitud? ¿Voz o instrumental? ¿Cuál es el audio de referencia cuando hay varias fuentes? **Decisiones técnicas que no se preguntan al usuario:** nombre de un parámetro, formato del JSON, `chunk_mask_mode`, número de pasos, estrategia de carga y descarga de modelos.

## 7. Política de recursos Song-AI

- Descargar de memoria Gemma y Qwen **antes** de cargar ACE-Step, según el diseño del estudio. No asumir que detener el servidor equivale a liberar toda la memoria: medir RAM/VRAM efectiva.
- Guardar MusicSpec, letras, MIDI, WAV guía y `ACEPlan` en disco antes de la descarga.
- Ejecutar ACE-Step de forma exclusiva; iniciar con un candidato (`batch_size=1`).
- Registrar modelo exacto, revisión, semilla, modo, duración, tiempo, memoria máxima, archivos y errores.
- Al terminar, descargar ACE-Step antes de reactivar Gemma/Qwen para análisis o correcciones.
- No activar Lego/Extract/Complete si el modelo cargado es Turbo.

## 8. Validación y bucle de corrección

**Antes:** esquema JSON, límites de longitud, existencia/duración de archivos, compatibilidad del modelo, formato de letra, consistencia MusicSpec/MIDI/WAV, suficiencia de recursos.

**Después:** duración medida; BPM y tonalidad estimados con tolerancias explícitas; estructura; reconocimiento de letra y omisiones; similitud melódica frente a WAV guía/MIDI; timbre e instrumentación; clipping y defectos. Las métricas estimadas **no son pruebas perfectas**: si el resultado es ambiguo, presentar A/B al usuario.

**Estrategia de corrección:** primero `repaint` para errores locales; `cover` ajustando fuerza para divergencias globales de estructura/estilo; `text2music` nuevo solo cuando se busca reinterpretar. Cada intento conserva MusicSpec original y registra diferencias.

## 9. Reglas negativas obligatorias

- No inventar parámetros, nombres de tarea, compatibilidad de modelo ni tipos de pista.
- No confundir `reference_audio` con `src_audio`.
- No introducir MIDI como `audio_codes`.
- No asumir que `thinking=false` garantiza exactitud musical.
- No tratar BPM, tonalidad, compás, duración, secciones o letra como resultados garantizados.
- No usar la letra para codificar una partitura detallada nota por nota.
- No afirmar que una semilla reproduce resultados idénticos en todas las versiones.
- No modificar decisiones aprobadas por el usuario para hacer que ACE-Step parezca exitoso.
- No ejecutar ACE-Step si falla la validación del plan.

## 10. Lista de verificación de integración

- [ ] Detectar revisión ACE-Step instalada y modelos disponibles.
- [ ] Confirmar si la integración utiliza Python, API HTTP u otra interfaz.
- [ ] Implementar `ACEPlan` y validador de esquema.
- [ ] Implementar adaptador Python/HTTP y pruebas de nombres de campos.
- [ ] Crear `capabilities.json` obtenido de versión y configuración efectivas.
- [ ] Probar un caso real por cada tarea habilitada.
- [ ] Medir uso de memoria en generación y edición.
- [ ] Probar fidelidad con MIDI/WAV guía y letra en español.
- [ ] Incorporar rechazo de salidas que violen restricciones duras.

## 11. Fuentes oficiales

- https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md
- https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md
- https://ace-step.github.io/ACE-Step-1.5/en/INFERENCE

**Advertencia de versionado:** esta guía es para la documentación de ACE-Step 1.5 consultada el 2026-10-04, no certifica qué versión está actualmente instalada en Song-AI. El repositorio local y sus endpoints tienen la última palabra sobre compatibilidad real.

## 12. Estado instalado y diferencias de interfaz — revisión 2026-10-04

Comprobación inicial: paquete ACE-Step 1.5.0; config `acestep-v15-turbo` presente. La carpeta `acestep-1.5-3.5b-default` contiene cache histórico `ACE-Step-v1-3.5B`, con transformer/dcae/vocoder de esa arquitectura; no equivale a Base 1.5. Base 1.5 se instaló posteriormente como registra la sección 16. El steering inventaría configs Base/Turbo 1.5 por solicitud, sin confirmar carga ni generación.

Avance del compilador: wrapper con flags `--bpm`, `--key-scale`, `--time-signature`, `--vocal-language`, pasados al handler y diagnósticos. Las plantillas de comandos históricas todavía no se conectan al plan nuevo. La previsualización desde ficha confirmada conserva requisitos y devuelve mapeo candidato; no autoriza ejecución ni acredita fidelidad.

La investigación volvió a contrastar [INFERENCE.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md), [API.md](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md), [matriz de modelos](https://github.com/ace-step/ACE-Step-1.5#models) y el código instalado, sin descargar pesos ni ejecutar generación.

| Evidencia | Estado Song AI | Consecuencia |
| --- | --- | --- |
| Paquete en `.venv` | ACE-Step 1.5.0; import de AceStepHandler confirmado en el audit | No demuestra checkpoint cargado ni calidad |
| Interfaz conectada | `AceStepHandler.generate_music`, API Python de bajo nivel | No es `acestep.inference.generate_music(GenerationParams, GenerationConfig)` ni HTTP |
| Task del wrapper | Enum de seis tareas con validaciones compartidas | Sin selección pública en UI ni ejecución real verificada por modo |
| Campos enviados | `captions`, `lyrics`, `audio_duration`, pasos, seed y controles del wrapper | El loader extrae la lista exacta por AST en cada solicitud |
| Campos musicales estructurados | Flags y keywords al handler disponibles; integración completa desde ficha pendiente | Idioma por defecto `en` si el comando omite el flag; no prometer que escribir español en caption resuelve el mapeo |
| Referencias/fuentes | Flags fuente/referencia pasados al handler; archivo existente requerido | Falta selección de artefacto/checksum/duración; no ofrecer clonación como función verificada |
| Modelo efectivo | Sin confirmar; perfiles históricos y config por defecto pueden discrepar | No inferir Base/Turbo del nombre de la carpeta; registrar config/checkpoint efectivos |
| Sample | Checkpoint mock; registro técnico WAV y revisión disponibles | Generación real representativa aún pendiente; cierre real bloqueado |

La firma instalada usa `captions`, `key_scale`, `time_signature`, `audio_duration`; la interfaz de alto nivel usa `caption`, `keyscale`, `timesignature`, `duration`. El cuadro de la sección 2 describe **alto nivel**, no el método que llama el wrapper. Se requieren adaptadores por interfaz y pruebas de mapeo.

La documentación de inferencia recomienda `shift=3.0` para Turbo y dice que CFG se ajusta a 1; API.md describe shift como exclusivo de Base. Es una discrepancia documental. El método instalado acepta shift, pero el wrapper no lo envía. No resolverla eligiendo un valor por intuición: comprobar código/config del modelo efectivo y un caso de ejecución antes de habilitarlo.

`create_sample` del LM de ACE-Step produce caption, letra y metadatos para generación posterior; **no es** el fragmento de audio escuchado/aprobado exigido por Song AI. El LM 5 Hz interno, aunque use una familia Qwen, es un componente distinto de nuestro director técnico Qwen3.

La referencia de timbre es condicionamiento, no prueba de identidad de una persona. Voz sintética cantada, perfil personalizado y grabación humana son rutas distintas. La personalización/clonación sigue pendiente de un contrato, provider, referencia autorizada y evaluación. ACE-Step tampoco sustituye un DAW determinista, EQ/compresión por canal ni un sintetizador que ejecute cada nota MIDI.

## 13. Steering inyectado en inferencia

El backend lee la sección marcada siguiente y el rol en `docs/steering/` en cada solicitud del registry a Gemma/Qwen. Añade versión de paquete, tasks y keywords observados del wrapper y defaults/config candidatos. Registra hashes y revisión en el resultado; el handoff Qwen conserva esa metadata. No importa motores, no accede a Internet y no promueve documentación o un audit previo a ejecución verificada. Un contrato ausente o inválido produce un error; no se corta silenciosamente para acomodar contexto.

En llama.cpp las solicitudes incluyen el contexto: cargar los pesos o enlazar un Markdown no incorpora conocimiento persistente al modelo. Reenviar steering por solicitud cubre recargas y cambios del contrato. Los providers reciben el mismo snapshot por rol; mocks pueden ignorar instrucciones y se siguen identificando como mocks. La inyección se verifica con dobles; comprensión/obediencia de modelos reales requiere una evaluación posterior.

<!-- MODEL_STEERING_START -->
### Contrato ACE-Step para Gemma y Qwen — 1.0

ACE-Step genera audio condicionado; Gemma recoge/explica intención y Qwen compila/revisa viabilidad. El usuario aprueba creatividad; SQLite conserva especificación, decisiones, tasks e histórico. Las tres piezas instrumental, melodía vocal y letra permanecen separadas en el proyecto, aunque text2music produzca una mezcla conjunta. No declarar stems independientes por recibir un WAV mezclado.

Capacidades documentadas 1.5: text2music genera desde descripción/letra; cover transforma audio fuente; repaint regenera intervalo; lego añade pista en contexto, extract aísla pista y complete completa arreglo, estas últimas solo Base. La lista local adjunta indica qué llama realmente el wrapper; si un modo no aparece allí, describirlo como pendiente. Una firma/import/archivo presente no verifica audio.

Qwen debe convertir deseos en: requisitos obligatorios/preferidos, caption musical breve, letra segmentada, idioma vocal, BPM, tonalidad, compás, duración objetivo, instrumentos/voz/estructura, task, seed/perfil/config, entradas y criterios de evaluación. Identificar el origen usuario/IA/default y confirmación. El plan del motor es una proyección de la ficha completa, no su reemplazo. Datos requeridos por la ficha que el motor no consume quedan como restricciones o tareas externas, sin omitirlos.

Límites documentados de alto nivel: caption 512 caracteres, letra 4096, BPM 30–300, duración objetivo 10–600 segundos (automático -1); compás 2/3/4/6 representa 2/4, 3/4, 4/4, 6/8; idioma español es es. Son referencias documentadas, no validaciones ya implementadas en nuestro wrapper. Caption expresa género, ánimo, instrumentos, timbre/energía vocal, textura y dinámica; no copiar toda la ficha dentro. No truncar letra ni eliminar un requisito obligatorio para caber: proponer solución y pedir decisión.

Hay tres APIs distintas: alto nivel GenerationParams usa caption/keyscale/timesignature/duration; handler instalado usa captions/key_scale/time_signature/audio_duration; HTTP tiene su propio esquema. Solo el adaptador decide nombres y parámetros soportados. Revisar keywords locales adjuntos: un campo omitido no pasa al motor por estar guardado. No inventar thinking, instrumental, reference_audio o controles de DSP como argumentos conectados.

Etiquetas Verse/Chorus/Bridge/Intro/Outro orientan letra/estructura; no fijan tiempos o notas exactas. BPM, tonalidad, duración, letra y voz son objetivos condicionados, no resultados garantizados. Midi no es audio_codes ni partitura ejecutable por ACE-Step. Para fidelidad exacta de notas o cambios deterministas, declarar motor/síntesis/DSP externos pendientes. source audio y reference audio tienen funciones distintas; referencia no garantiza clonar una voz.

Turbo y Base tienen distintas tareas/pasos/CFG. No inferir modelo efectivo por defaults. La documentación presenta diferencias sobre shift entre interfaces: no recomendarlo como control ejecutable sin validación local. LM 5 Hz interno y Qwen director son distintos; create_sample del LM produce texto/metadatos, no el sample de audio obligatorio de Song AI.

Antes de final: set válido, ficha confirmada y sample vigente representativo del provider/voz/config, escuchado y aprobado con checksum. Mock o WAV técnicamente íntegro no acredita calidad ni habilita cierre real. Después: integridad, duración, escucha, fidelidad frente a requisitos y aprobación del usuario. No declarar calidad profesional ni voz humana grabada por finalizar una task. Cambios relevantes exigen nueva revisión; conservar conflictos y presentar un siguiente paso concreto en la UI y conversación.
<!-- MODEL_STEERING_END -->

## 14. Configuración objetivo para los seis modos — investigación 2026-10-04

Fuentes: [matriz oficial de modelos](https://github.com/ace-step/ACE-Step-1.5#models), [instalación y descarga](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md), [contratos de tareas](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md). Contraste local: `model_downloader.py`, `init_service_orchestrator.py` y firma `GenerateMusicMixin.generate_music` de la instalación 1.5.0.

### Modelo y archivos

Elegir **`acestep-v15-base`** para habilitar text2music, cover, repaint, lego, extract y complete. Base XL también admite seis tareas; no hace falta XL para obtenerlas. Turbo y SFT admiten las tres primeras. La carpeta histórica 3.5B de Song AI no equivale a este Base 1.5.

Usar una raíz común, por ejemplo `data/models/music/acestep-v15` (ubicación propuesta, no creada por esta investigación):

```text
acestep-v15/
  acestep-v15-base/       # DiT Base 1.5, config, código y pesos completos
  vae/                   # codificación y decodificación de audio
  Qwen3-Embedding-0.6B/   # codificador de texto
  acestep-v15-turbo/      # opcional para alternar tareas rápidas
  acestep-5Hz-lm-*/       # LM interno, opcional según ruta/recursos
```

La distribución principal ofrece componentes compartidos, Turbo y LM 1.7B; Base se descarga por separado. El downloader instalado registra `ACE-Step/acestep-v15-base` y admite `--model`/`--dir`. También puede reutilizarse la raíz existente que contiene VAE/codificador válidos, añadiendo Base en su subdirectorio; no duplicar pesos por el nombre de la carpeta. Conservar el cache histórico.

Comando preparado para una instalación posterior, verificado contra argumentos del downloader local (no ejecutado):

```powershell
.\.venv\Scripts\python.exe -m acestep.model_downloader --model acestep-v15-base --dir data/models/music/acestep-v15
```

El downloader instalado descarga primero la distribución principal si sus componentes no existen; por tanto, puede descargar también Turbo/LM compartidos. Revisar espacio y raíz reutilizable antes de instalar.

### Selección explícita y recursos

```powershell
$env:ACESTEP_CHECKPOINTS_DIR = "C:\Users\jorge\Personal\Programas\Codigo\song-ai\data\models\music\acestep-v15"
$env:ACESTEP_CONFIG_PATH = "acestep-v15-base"
```

Son valores objetivo, **no configuración aplicada**. En Song AI el wrapper sobrescribe CHECKPOINTS_DIR desde `--checkpoint-path`; ese argumento debe apuntar a la misma raíz. Pasar además `--config-path acestep-v15-base` al wrapper: su default Turbo puede prevalecer sobre el perfil elegido. Corregir perfiles/repositorios v1 en el adaptador antes de declarar selección Base operativa; MODEL_REPO no sustituye CONFIG_PATH.

Como punto inicial de evaluación Base: 32–64 pasos, batch 1 y CFG dentro de los límites documentados; fijar seed para comparaciones. Son propuestas técnicas, no garantía de calidad. Empezar con clips cortos representativos y medir RAM/memoria XPU, duración y offload. La documentación admite CPU/XPU, con CPU considerablemente más lenta. El equipo detectado no tiene validación de inferencia Base. No extrapolar requisitos generales de VRAM al rendimiento de una iGPU. XL exige al menos 12 GB VRAM con offload/quantización según documentación; queda fuera de la elección inicial hasta medir recursos.

### Entradas que debe exponer Song AI

| Modo | Entrada y operación que debe recibir el adaptador |
| --- | --- |
| text2music | Descripción y/o letra, metadatos musicales; no requiere fuente |
| cover | Audio fuente y descripción objetivo; fuerza de conservación; referencia opcional diferenciada |
| repaint | Audio fuente, descripción, inicio/final en segundos y máscara/estrategia de edición |
| lego | Audio de contexto, tipo de pista, instrucción de generación y descripción |
| extract | Mezcla fuente, pista objetivo e instrucción de extracción |
| complete | Audio parcial, pistas a añadir, instrucción y descripción de arreglo |

Validar duración/intervalos, origen/checksum de fuentes, pista admitida y permisos de referencia. El audio fuente es condición generativa; no significa edición DSP determinista ni stems originales garantizados.

### LM interno y API

La API de alto nivel coordina `AceStepHandler`, `LLMHandler`, `GenerationParams` y `GenerationConfig`. El LM interno se omite en cover/repaint/extract y puede usarse en text2music/lego/complete; es distinto del Qwen director técnico. Para usarlo, inicializar realmente `LLMHandler` y coordinar recursos. En Song AI las variables LM actuales se registran, pero la llamada directa al handler no demuestra ejecución del LM. DiT-only es una ruta posible, sin atribuirle planificación LM.

Mantener un adaptador de dominio por motor; decidir si coordinar alto nivel o implementar explícitamente todas las entradas del handler. No mezclar nombres de esas APIs ni asumir que habilitar una API HTTP es obligatorio: puede mantenerse ejecución local por proceso.

### Condiciones para declarar disponibles los seis modos

1. Archivos completos y modelo efectivo Base 1.5 comprobados en carga; registrar revisión/checksum/dispositivo.
2. Wrapper/adaptador con selección de tarea y entradas específicas; enum CLI implementado, conexión pública al plan/UI pendiente.
3. Compilador, esquema y políticas por task; preview de seis candidatos implementado, ejecución/aprobación pendientes.
4. UI para fuentes/pistas/intervalos, explicaciones y propuestas; Gemma/Qwen reciben el estado habilitado vigente.
5. Un caso real validado por modo, artefactos íntegros, escucha y requisitos de fidelidad registrados. Configuración/presencia no equivale a verificación.
6. Set/sample/spec vigentes y aprobaciones por revisión para cierre; mantener mocks en las pruebas de contratos.

Esta entrega define configuración e integración necesarias; no descargó pesos, cambió `.env`, cargó modelos ni habilitó los seis modos.

## 15. Avance de contratos de seis tareas — 2026-10-04

El wrapper incorpora `--task-type` con seis valores, audio fuente/referencia, instrucción, pistas, fuerza de conservación y máscara/intervalo. Una política compartida valida fuente requerida, selección explícita Base 1.5 para Lego/Extract/Complete, pistas admitidas y concordancia con instrucción, intervalo finito y ordenado. Comprueba existencia de archivos antes de cargar motores. Si falta instrucción en text2music se conserva el default nativo; no se duplica un prompt de motor en código.

El compilador admite previsualización de seis planes desde ficha confirmada con campos específicos: `task_type`, `ace_step_config`, `src_audio`, `instruction`, `target_tracks`, `repainting_start/end`, `audio_cover_strength`. Mantiene la ficha completa; fuentes propuestas requieren verificación de artefacto y el plan no autoriza ejecución. Para Extract la letra candidata puede estar vacía. El audit detecta el enum solo si el wrapper lo pasa al handler; el steering mantiene `verified_tasks=[]` y selección pública de generación deshabilitada.

Estos avances sustituyen el estado de task fija descrito en secciones anteriores. Base instalado y checksum comprobado se registran en la sección 16. Pendientes: carga Base, adaptador de artefactos y duración real de fuentes, límites efectivos del intervalo, plan persistido/aprobado, conexión a comandos y UI, LM cuando proceda y ejecución real por modo. La existencia de flags no acredita disponibilidad completa del estudio.

## 16. Instalación Base 1.5 y perfiles corregidos — 2026-10-04

Se descargó `ACE-Step/acestep-v15-base` fijando revisión `e432212fec32b8965a14ffa57ae653438d6abd14`, en `data/models/music/acestep-1.5-2b-turbo/acestep-v15-base`. La raíz conserva Turbo y reutiliza VAE/codificador existentes; su nombre no define el modelo seleccionado. El checkpoint histórico v1 se conserva.

`scripts/verify_acestep_installation.py` comprobó archivos requeridos, SHA-256 del peso contra el identificador oficial de descarga y offsets de 677 tensores safetensors sin cargarlos. Evidencia local regenerable: `data/diagnostics/acestep_base_installation.json`.

- Peso Base: 4.787.825.604 bytes.
- SHA-256: `4177f600501a6d4bd81cadaa0abac557ffd15c54e5c8cb52053cdb24a0844d6b`.
- Arquitectura declarada: `AceStepConditionGenerationModel`.
- VAE/codificador: pesos presentes; checksum completo pendiente.
- Carga de modelo, generación, calidad y seis modos de audio: sin verificar.

Perfiles corregidos: Base selecciona `acestep-v15-base`, 32 pasos y CPU; Turbo selecciona `acestep-v15-turbo`, 8 pasos y XPU. Ambos proporcionan raíz y config explícitas al wrapper. El adaptador normaliza la plantilla histórica que derivaba raíz de `{model_type}` y añade config cuando falta, sin modificar la `.env` existente ni comandos ajenos. La selección evita la discrepancia histórica de rutas/defaults; el modelo efectivo sigue requiriendo evidencia de carga.

Verificación del cambio: 57 pruebas de regresión aprobadas, compilación Python y revisión de diff. S06/S10 continúan en progreso: siguen pendientes conexión del plan aprobado a ejecución/UI, muestras reales y evaluación independiente de cada tarea.

## 17. Audio fuente vinculado al proyecto — avance S06

La vista previa acepta `source_artifact_id` en la especificación confirmada junto con `src_audio`. Cuando está declarado para una tarea con fuente, el puerto `SourceAudioInspector` exige un artefacto registrado del mismo proyecto y una ruta coincidente dentro de su carpeta. El adaptador verifica WAV PCM completo, duración y SHA-256 reutilizando la inspección de integridad existente. Archivos externos, artefactos ajenos y archivos truncados se rechazan.

Para Repaint/Lego el inicio debe ser menor que la duración real y el final no puede excederla; `-1` conserva el significado de final del audio. La evidencia forma parte del hash del plan: reemplazar el archivo cambia la identidad del candidato. Sin `source_artifact_id` se conserva el pendiente de verificación; no se interpreta una ruta como fuente aprobada. La vista previa no escribe en DB ni ejecuta motores.

25 pruebas aprobadas y compilación Python correcta. Se admite inicialmente WAV PCM; otros formatos requieren un adaptador explícito. Pendientes: persistir/aprobar planes, volver a verificar checksum inmediatamente antes de ejecución, controles UI para elegir artefacto, generación real y calidad musical. Este avance no declara los seis modos disponibles.

## 18. Controles y revisión persistida del plan — S06-A/B en progreso

La ficha ofrece un editor de las seis acciones, modelo Base/Turbo, artefacto WAV fuente, pistas, instrucción avanzada, intervalo y fuerza de conservación. Los valores iniciales se muestran como propuesta; guardar es explícito. La ruta fuente se obtiene del artefacto SQLite y no admite edición arbitraria. Integridad y duración se verifican antes de guardar una operación con fuente. La lista de fuentes procede del proyecto completo, no del listado resumido de proyectos. Sin WAV registrado se explica el bloqueo; la importación de fuentes sigue pendiente.

`PUT /api/pro/projects/{song_id}/ace-configuration` recibe `revision_id` y `values` con controles admitidos. Conserva el resto de la ficha y sus intenciones, registra procedencia del control y crea revisión pendiente de confirmar. El chequeo de revisión también se aplica dentro de una transacción SQLite con bloqueo de escritura. No se atribuye esta edición a inferencia Qwen; `technical_review_mode` identifica validación determinista de inputs. La revisión cambia la huella de generación y no conserva aprobaciones finales anteriores.

Se reutiliza el exportador existente de `song_spec.json`/`song_spec.md`; la DB conserva estado activo. El servicio histórico permanece sin ampliación: el caso de uso nuevo de edición vive en `EditAceStepConfiguration` y reutiliza contratos/validaciones.

### Planes, letra y aprobación

- `POST /api/pro/projects/{song_id}/ace-plan`: compila y guarda un candidato con la letra proporcionada, usando ficha confirmada y fuente verificada cuando está declarada.
- `GET /api/pro/projects/{song_id}/ace-plan`: devuelve el último plan con estado efectivo vigente u obsoleto, recomputando el candidato contra inputs actuales. Conserva la aprobación histórica sin presentarla como vigente cuando cambian datos.
- `POST /api/pro/projects/{song_id}/ace-plan/{plan_id}/approve`: exige `plan_sha256` y `lyrics_confirmed=true`, recompila y vuelve a comprobar checksum fuente/revisión. No admite fuentes pendientes de verificar. Aprobación repetida conserva su fecha.

La tabla `ace_step_plans` contiene identidad de proyecto, revisión de ficha, hash, contenido, estado y fechas. `ace_plan.json` es un snapshot regenerable; events registran preparación/aprobación. El borrado del proyecto elimina solo sus planes. La UI permite revisar caption, metadatos, letra exacta, requisitos retenidos y datos técnicos, aprobar explícitamente y recuperar el estado tras recarga. Una letra propuesta en el plan todavía no sustituye automáticamente el asset lírico del set.

`AceStepExecutionArguments` traduce el plan aprobado/vigente a una lista de argumentos y archivos de caption/letra; exige coincidencia de perfil/config y rechaza payload sin traducción. No ejecuta procesos y todavía no está conectado al runner. La futura llamada usará `shell=False`; no interpolar texto creativo en una consola. El adaptador no sustituye preflight de recursos, sample ni gates finales.

Pendientes: edición por decisión completa y herramientas de chat compartidas, referencias autorizadas, importación de fuentes, vincular letra aprobada al asset/set, integración runner/orquestador, revalidación inmediata en ejecución y audio real por tarea. `ready_for_execution` permanece falso, incluso para un plan aprobado. La aprobación del plan no demuestra recepción del motor, ejecución, calidad ni aceptación de audio.

Verificación: 71 pruebas aprobadas, build frontend, compilación de template Vue/Python y revisión de diff. Sin validación visual, inferencia Base ni escucha de audio real en esta entrega.

## 19. Conexión inicial al runner — S06-C

`ProfessionalFullSongService` conecta text2music desde plan aprobado/vigente cuando la plantilla identifica el wrapper local. Exige coincidencia exacta entre letra persistida del proyecto y la del plan, perfil/config coincidentes y gate real de sample antes de preparar el proceso. El traductor escribe caption/letra aprobados y el runner usa la lista de argumentos con `shell=False`; añade diagnóstico y conserva control/restauración de recursos. Registra plan ID/hash y revisión de ficha en artefactos finales.

Los parámetros efectivos provienen del plan y perfil; las opciones arbitrarias de la plantilla histórica no se interpolan en esta ruta. Otros providers conservan su contrato de comandos. Las cinco operaciones restantes requieren runner de candidatos con semántica propia y no se autorizan como canción completa por esta conexión. La vigencia se comprueba antes de preparar argumentos; faltan revalidación inmediatamente tras preparación de recursos/al registrar salida, orquestación integral, sample representativo y evidencia real. No declarar seis modos ejecutables ni calidad por pruebas con proceso simulado.

## 20. Runner exploratorio conectado para las seis tareas

Endpoint `POST /api/pro/projects/{song_id}/ace-candidates`, con `plan_sha256` y `exploratory_audio_authorized=true`: exige plan aprobado/vigente y usa la tarea aprobada, config/perfil coherentes y argumentos sin shell. Reutiliza preparación/proceso/restauración del runner local. Revalida después de preparar recursos y antes de registrar salida; cada ejecución escribe en carpeta única `projects/{song_id}/candidates/{run_id}`. Verifica WAV íntegro y registra artefacto `ace_step_candidate_wav` con task, revisión, plan/hash y evidencia, siempre sin aprobación de sample/calidad musical.

Un lock compartido protege candidatos/final dentro de una instancia de la app; no es un bloqueo distribuido entre workers. No cambia fase, set ni assets seleccionados. Fallos o inputs modificados no registran el archivo como resultado vigente y conservan originales/diagnóstico. La llamada HTTP actual es síncrona; no habilitarla como botón de producción final. Pendientes: jobs/UI/cancelación, task/handoffs completos del orquestador, preflight hardware, sample representativo y ejecución/escucha real por modo. La ruta backend admite las seis tareas; su disponibilidad audible sigue sin verificar.

## 21. Trabajos en segundo plano y reproducción

La sección anterior queda actualizada: POST de candidatos inicia una `task` existente de tipo `ace_step_exploratory_candidate` mediante dispatcher local y retorna sin esperar inferencia. `GET /api/pro/projects/{song_id}/ace-candidates` devuelve último trabajo; GET con `/{task_id}` consulta estado con propiedad de proyecto. Un `model_run` registra ejecución/error; el payload guarda plan seleccionado, hash y autorización explícita. Cambio de identidad del plan también invalida el trabajo. Arranque marca tasks/model runs interrumpidos; no se reinicia generación automáticamente.

UI permite autorizar, iniciar, consultar estado y escuchar. GET `/{task_id}/audio?audio_sha256=...` requiere trabajo completado, artefacto propio del proyecto, carpeta de candidato y evidencia WAV idéntica al registro; responde sin cache. No aprueba sample/final ni mide fidelidad por reproducción. El usuario puede recuperar estado después de recarga.

21 pruebas aprobadas, build y compilación Python correctos. Sin ejecución ACE-Step real ni prueba visual. Pendientes: cancelación, handoffs completos bajo ModelOrchestrator, preflight/carga por hardware y audio real evaluado por modo. Jobs de una instancia con un candidato activo a la vez; no prometer exclusividad distribuida ni recuperación de procesos huérfanos con este dispatcher.

## 22. Cancelación explícita

POST `ace-candidates/{task_id}/cancel` valida propiedad del proyecto. Pendiente → cancelled sin inferencia; running → cancelling → cancelled tras detener proceso/restaurar recursos. Mientras cancela no acepta otro candidato. Una solicitud sobre trabajo ya terminado conserva su resultado/estado. Reinicio también identifica `cancelling` como interrumpido.

El token de cancelación es local al worker y no se serializa como input musical. Se comprueba antes del proceso, durante monitoreo y antes de registrar resultado; task/model run y eventos distinguen cancelación de error. Audio cancelado no se sirve como candidato terminado. Puede conservarse archivo aislado de diagnóstico si la cancelación llegó al terminar la generación; no se convierte en sample/final.

Windows termina árbol por PID y espera salida; Unix termina grupo y puede escalar a SIGKILL. Se conserva restauración de modelos y bloqueo de ejecución hasta cerrar el worker. 24 pruebas aprobadas, build y compilación correctos; terminación/restauración verificadas con mocks, sin proceso ACE-Step real ni medición de memoria liberada. Pendientes: integración completa ModelOrchestrator, preflight y pruebas de ejecución/escucha/cancelación reales.

## 23. Preflight de archivos y recursos

`AceStepPreflight` comprueba archivos locales antes de crear la task y al preparar el runner: wrapper/intérprete, config DiT con arquitectura 1.5, pesos no vacíos y componentes VAE/codificador. Reporta config/dispositivo del perfil y presencia; `model_loaded_verified`, `hardware_inference_verified` y `weights_checksum_verified` permanecen falsos. No revalida el checksum completo por petición ni descarga archivos ausentes. El reporte se conserva en payload de task. Una comprobación local confirmó presencia de requisitos Base 1.5 sin importar el motor.

El runner aplica `readiness.ready=false` como bloqueo antes de Popen y restaura modelos de texto en su salida. No transforma monitor omitido ni disponibilidad de archivos en validación de memoria suficiente para Base; todavía requiere medir memoria efectiva/carga en este hardware. 27 pruebas aprobadas, compilación y diff correctos. Pendientes: carga real, evidencia de liberación, coordinación integral ModelOrchestrator y audio evaluado por tarea.

## 24. Coordinación lógica de audio bajo ModelOrchestrator

`AudioHandoffLifecycle` conecta jobs con el orquestador, sin prompts entre modelos. Inicio/retorno registran eventos SQLite relacionados con proyecto/task/run/plan; el cierre indica completed/failed/cancelled. `status` deriva task activa de la DB y suspende assistant ante pending/running/cancelling. `active_model` sigue sin afirmar carga física. Gemma devuelve orientación desde SQLite sin invocar LLM durante esa suspensión, y nuevos handoffs se rechazan hasta cierre. La reanudación lógica permite consultas posteriores; no acredita que el modelo ya haya sido recargado.

33 pruebas aprobadas con workers/proveedores simulados, compilación/diff correctos. Pendientes: exclusividad de llamadas directas a providers fuera del orquestador, medición efectiva de RAM/modelos liberados/cargados, recuperación de procesos huérfanos y audio real. No declarar gestión física de memoria validada por los eventos de pausa/retorno.

### Guard del registry para planificación directa

La composición inyecta `require_planning_available` en ProviderRegistry. Interpretación Gemma y revisión Qwen comprueban task candidata activa y lock de ejecución de audio antes de llamar al provider, también sin pasar por run_handoff. Esto cubre nuevas solicitudes durante candidatos y generación final local. Al cerrar/cancelar vuelven a estar disponibles. 29 pruebas aprobadas. El chequeo no detiene inferencias que ya estaban en curso ni aporta exclusividad distribuida; medir/coordinar carga efectiva sigue pendiente. No acredita RAM liberada ni obediencia real.

### Reserva durante la inferencia

Registry adquiere `exclusive_planning` durante toda llamada al provider/steering. Audio y planificación comprueban atomicamente su exclusión: ACE-Step no arranca si una inferencia ya estaba en curso y el registry no inicia si el audio adquirió exclusividad después del guard inicial. También se evita una segunda inferencia concurrente por registry. Ante conflicto se rechaza la solicitud con indicación de esperar/reintentar; sin espera automática. Excepciones liberan reserva. 32 pruebas aprobadas, compilación/diff correctos. Exclusividad de una instancia; no administra servidores externos ni demuestra liberación de pesos/memoria o calidad audible.

## 25. Evaluación inicial de candidatos

`CandidateFidelityReport` conserva revision de ficha, plan/hash y checksum del audio. Duracion WAV es medida objetiva; comparar contra objetivo text2music exige `duration_tolerance_seconds` valida de la ficha aprobada. Sin tolerancia muestra pendiente; operaciones de edicion no reutilizan automaticamente la duracion de cancion como criterio de salida. Catálogo incluye el campo sin default creativo.

Tempo, tonalidad, letra cantada, voz, estructura, instrumentos, frases obligatorias y exclusiones mantienen esperado pero observado desconocido, pendientes de analisis/escucha. UI muestra informe, persistido en artefacto/task SQLite. No hay porcentaje global, aceptacion musical ni aprobacion del sample. 12 pruebas aprobadas; pendientes controles completos de criterios/evaluadores y evidencia musical real.

El editor incorpora `duration_tolerance_seconds` con guardado explicito en ficha versionada, rango 0–600 y opcion vacia (`null` elimina el criterio). No se asigna valor por silencio. El backend exige numero finito y rechaza booleanos; guardar vuelve a dejar pendiente confirmacion e invalida planes previos por revision. No es parametro de generacion ni garantia de duracion exacta. 12 pruebas y build aprobados; sin medicion de musica real ni prueba visual.
