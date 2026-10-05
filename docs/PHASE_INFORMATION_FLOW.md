# Phase Information Flow

Este documento define como viaja la informacion de Song-AI entre frontend, FastAPI, SQLite y artefactos derivados.

## Principio Central

SQLite es la fuente de verdad para el estado de trabajo del proyecto.

Los archivos JSON, Markdown, MIDI, WAV, MP3, FLAC y ZIP son artefactos derivados. No deben ser la fuente principal para hidratar formularios ni para determinar el estado funcional de una fase.

## Fases Principales

- Intent
- Lyrics
- Music Plan
- MIDI
- Instrumental
- Voice
- Voice Conversion
- Mix
- Mastering
- Export

Cada fase debe tener:

- formulario o configuracion persistible,
- estado funcional de fase,
- origen de datos,
- eventos historicos,
- artefactos generados si aplica,
- hidratacion al cargar proyecto,
- validacion antes de ejecucion,
- regeneracion de artefactos cuando sea posible.

## Estados De Fase

`phase_status`:

- `NOT_CREATED`: no existe registro de la fase en SQLite.
- `INITIALIZED`: existe registro creado con valores por default.
- `DRAFT`: existen valores modificados o sugeridos, pero el usuario todavia no los confirmo con Guardar.
- `COMPLETED`: el usuario presiono Guardar y la fase queda confirmada.

`USER_MODIFIED` y `AI_SUGGESTED` no son estados finales de fase. Son eventos y deben reflejarse en `change_source`.

## Origen De Datos

`change_source`:

- `DEFAULT`: valores iniciales del sistema.
- `USER`: valores modificados por el usuario.
- `AI`: valores propuestos por Gemma/Qwen.
- `MIXED`: combinacion de valores del usuario e IA.

Las sugerencias de IA no completan una fase automaticamente. Solo el usuario puede completar una fase presionando Guardar.

## Estados De Ejecucion

`execution_status`:

- `NOT_RUN`
- `RUNNING`
- `SUCCESS`
- `FAILED`
- `CANCELLED`

El estado de fase y el estado de ejecucion son conceptos distintos.

Ejemplo:

```text
Music Plan:
phase_status = COMPLETED

MIDI:
execution_status = FAILED
```

Esto significa que el usuario diligencio correctamente Music Plan, pero el proceso de generacion MIDI fallo.

## Estados De Artefacto

`artifact_status`:

- `NOT_GENERATED`
- `GENERATING`
- `GENERATED`
- `MISSING`
- `CORRUPTED`
- `FAILED`
- `REGENERATED`

Si un endpoint genera archivo, no basta con que el archivo exista. Debe quedar registrado en SQLite con estado, ruta, tamano, checksum, parametros y fecha.

## Modelo De Datos

### project_phase_data

Guarda el estado funcional e hidratable de cada formulario/fase.

Campos:

- `id`
- `project_id`
- `phase_name`
- `phase_status`
- `change_source`
- `data_json`
- `validation_status`
- `created_at`
- `updated_at`
- `completed_at`

En Song-AI esta tabla mantiene compatibilidad con columnas historicas `set_id`, `phase` y `status`, pero los campos canonicos nuevos son `project_id`, `phase_name`, `phase_status` y `change_source`.

### project_phase_events

Registra eventos importantes, no cada tecla escrita.

Eventos minimos:

- `PHASE_INITIALIZED`
- `USER_MODIFIED`
- `AI_SUGGESTED`
- `PHASE_SAVED`
- `PHASE_REOPENED`
- `PHASE_RESET`
- `EXECUTION_STARTED`
- `EXECUTION_COMPLETED`
- `EXECUTION_FAILED`
- `EXECUTION_CANCELLED`
- `ARTIFACT_GENERATED`
- `ARTIFACT_MISSING`
- `ARTIFACT_CORRUPTED`
- `ARTIFACT_REGENERATED`

Campos:

- `id`
- `project_id`
- `phase_name`
- `event_type`
- `source`
- `before_json`
- `after_json`
- `message`
- `error_code`
- `error_message`
- `created_at`

### project_artifacts

Registra archivos generados y su verificabilidad.

Campos:

- `id`
- `project_id`
- `phase_name`
- `artifact_type`
- `status`
- `file_path`
- `file_size`
- `checksum`
- `generation_params_json`
- `source_phase_snapshot_json`
- `provider_name`
- `provider_version`
- `seed`
- `error_code`
- `error_message`
- `created_at`
- `updated_at`
- `last_verified_at`

Song-AI conserva `song_artifacts` para compatibilidad de endpoints existentes y sincroniza metadata esencial hacia `project_artifacts`.

### legacy_samples y legacy_songs

Persisten el flujo compatible `set -> sample -> song` cuando se usan los builders legados. Guardan la relacion con el set, estado, provider, fecha, ruta del snapshot y el payload activo. `sample.json` y `song.json` son exportaciones regenerables desde estas tablas.

Al iniciar, Song-AI migra snapshots legados con relaciones validas mediante inserciones idempotentes. Un JSON antiguo no sobrescribe una fila ya existente en SQLite. Al borrar el set, se eliminan sus registros y carpetas dependientes de sample/cancion.

Las descargas del proyecto abierto deben incluir `song_id` para Production o `set_id` para el flujo local. No se debe resolver una descarga contextual recorriendo exports de otros proyectos.

## Flujo De Guardado De Formulario

1. Usuario abre fase.
2. Frontend solicita datos actuales del proyecto.
3. Backend consulta `project_phase_data`.
4. Si la fase no existe, puede crearla con valores default o devolver `NOT_CREATED`.
5. Frontend hidrata el formulario con `data_json`.
6. Usuario modifica valores.
7. Frontend marca estado local como dirty.
8. Al presionar Guardar:
   - frontend envia `data_json` al endpoint de la fase,
   - backend valida datos,
   - backend guarda `project_phase_data`,
   - `phase_status` pasa a `COMPLETED`,
   - `change_source` se actualiza a `USER`, `AI` o `MIXED`,
   - se registra `PHASE_SAVED` en `project_phase_events`,
   - se actualiza `updated_at` y `completed_at`.

Guardar solo persiste configuracion. Guardar no ejecuta ACE-Step, MIDI, audio ni export.

## Flujo De Sugerencia IA

Para compilar una canción completa, aplicar [SONG_SPEC_GEMMA_QWEN_CONTRACT.md](SONG_SPEC_GEMMA_QWEN_CONTRACT.md). Un `phase_patch` aislado no sustituye la especificación integral. Evolucionar `song_specs` con revisiones, procedencia, validaciones y decisiones por etapa; exportar `song_spec.json` y `song_spec.md` desde esa revisión. Los handoffs usan tasks y referencias al contexto persistido; separar reglas locales de una revisión real del modelo. La generación final requiere además sample aprobado y evaluación de resultado según su etapa.

1. Usuario solicita ayuda a Gemma.
2. Gemma interpreta la intencion creativa.
3. Qwen puede revisar tecnicamente la fase.
4. Backend recibe propuesta IA.
5. Se guarda en `project_phase_data` como `DRAFT`.
6. `change_source = AI` o `MIXED`.
7. Se registra `AI_SUGGESTED` en `project_phase_events`.
8. El usuario debe confirmar con Guardar para pasar a `COMPLETED`.

## Flujo De Edicion Conversacional De Fase

Ampliación pendiente SP-07 a SP-09: catálogo, avance de guía, delegaciones y controles de configuración comparten campo/revisión con la especificación activa. Diferenciar valor guardado y borrador visible en el contexto del assistant. Una propuesta se compara contra su revisión de origen; si hubo edición local posterior, no aplicar automáticamente el parche: devolver un conflicto revisable. Aceptar propuesta modifica borrador; Guardar valida/persiste; Generar crea una task independiente.

Estado inicial 2026-10-04: `song_specs` conserva la vista activa compatible y `song_spec_revisions` registra revisiones inmutables con versión de esquema, completitud, validación determinista, modo de revisión técnica y confirmación de usuario. La consulta de especificación devuelve historial y catálogo/cobertura; `song_spec.json` y `song_spec.md` se generan juntos. La confirmación sigue en `not_requested` y el modo actual es `rule_validation` hasta implementar el handoff real.

Ampliación del mismo día: cada compilación registra handoff técnico como task/model run/evento y guarda si hubo provider real, mock o fallback. Revisiones completas quedan `pending` en `SONG_SPEC_COLLECTION` hasta que el usuario confirma su ID activo; la confirmación genera una nueva revisión `confirmed`, rechaza IDs anteriores y avanza a `LYRICS_GENERATION`. Backend y UI exigen esa confirmación para las fases profesionales siguientes. El sample guarda la huella del set, assets y fases; requiere aprobación explícita y pierde vigencia al cambiar esos inputs. La canción completa y los cierres vinculados al set verifican esa aprobación. Aún falta invalidar granularmente artefactos profesionales dependientes y recibir propuestas estructuradas del modelo.

Cuando el usuario le pide a Gemma ajustar la fase visible, Gemma no modifica formularios directamente. El flujo canonico es:

1. Usuario pide un cambio en lenguaje natural desde el footer de Gemma.
2. Frontend envia `active_phase`, proyecto activo, pregunta y estado visual de fases.
3. Gemma interpreta la intencion creativa y mantiene la conversacion.
4. Backend envia un handoff interno al rol tecnico Qwen/director tecnico.
5. Qwen/director tecnico traduce la intencion a un `phase_patch` estructurado:
   - `phase`: debe coincidir con la fase activa.
   - `changes`: solo campos permitidos para esa fase.
   - `reason`: resumen del ajuste.
   - `requires_user_save`: siempre `true`.
6. Backend valida que el parche no toque campos desconocidos ni otra fase.
7. Frontend aplica el parche al formulario visible.
8. Frontend marca la fase como `dirty`.
9. Usuario revisa los valores y presiona Guardar si los acepta.

El parche conversacional es estado local revisable. No sustituye a SQLite como fuente de verdad hasta que el usuario guarda la fase. Si Qwen no esta disponible, el backend puede generar un parche conservador con reglas locales y dejar persistido el handoff/fallback para auditoria.

## Flujo De Carga De Proyecto

Al abrir un proyecto desde Library:

1. Frontend llama al endpoint de detalle del proyecto.
2. Backend devuelve:
   - datos del proyecto,
   - `phase_status` de cada fase,
   - `change_source` de cada fase,
   - `data_json` de cada fase,
   - `artifact_status` de cada artefacto,
   - `current_phase` recomendada.
3. Frontend hidrata todos los formularios con `data_json`.
4. Frontend marca visualmente fases no iniciadas, inicializadas, borrador, completadas, con error o con artefacto generado/faltante.
5. Frontend ubica al usuario en la fase donde iba.

Respuesta esperada:

```json
{
  "project_id": "abc123",
  "name": "Cancion de cuna Sofia",
  "current_phase": "music_plan",
  "phases": {
    "intent": {
      "phase_status": "COMPLETED",
      "change_source": "USER",
      "data": {}
    },
    "lyrics": {
      "phase_status": "COMPLETED",
      "change_source": "MIXED",
      "data": {}
    },
    "music_plan": {
      "phase_status": "DRAFT",
      "change_source": "AI",
      "data": {}
    }
  },
  "artifacts": {
    "midi": {
      "status": "GENERATED",
      "file_path": "projects/abc123/song_base.mid"
    },
    "final_song": {
      "status": "MISSING",
      "file_path": "projects/abc123/final_song.wav"
    }
  }
}
```

## Flujo De Generacion De Artefactos

1. Usuario ejecuta una accion en Production o una fase ejecutable.
2. Backend valida que las fases requeridas esten `COMPLETED`.
3. Backend registra `EXECUTION_STARTED`.
4. Backend ejecuta builder/provider correspondiente.
5. Si genera archivo:
   - guarda archivo fisico,
   - calcula checksum,
   - calcula tamano,
   - registra `project_artifacts`,
   - `status = GENERATED`,
   - registra `ARTIFACT_GENERATED`,
   - registra `EXECUTION_COMPLETED`.
6. Si falla:
   - `status = FAILED`,
   - guarda `error_code` y `error_message`,
   - registra `EXECUTION_FAILED`.

## Validacion De Artefactos

Al cargar un proyecto, consultar artefactos o descargar:

1. Backend revisa artefactos registrados.
2. Verifica si el archivo existe.
3. Verifica checksum si aplica.
4. Si no existe:
   - `artifact_status = MISSING`,
   - registra `ARTIFACT_MISSING`.
5. Si existe pero checksum no coincide:
   - `artifact_status = CORRUPTED`,
   - registra `ARTIFACT_CORRUPTED`.
6. Frontend muestra advertencia y opcion de regenerar si es posible.

## Regeneracion De Artefactos

Si el proceso esta guardado en base de datos pero el archivo fue borrado o danado, debe poder regenerarse cuando sea posible.

Regenerar no significa repetir todo el flujo completo. Significa ejecutar solo el builder/provider necesario usando:

- `project_phase_data`,
- `generation_params_json`,
- `source_phase_snapshot_json`,
- `provider_name`,
- `provider_version`,
- `seed` si existe.

Ejemplos:

- `lyrics.md` se regenera desde lyrics `data_json`.
- `music_plan.json` se regenera desde music_plan `data_json`.
- `song_base.mid` se regenera desde Music Plan si el generador es deterministico.
- `final_song.wav` puede regenerarse desde Lyrics + Music Plan + parametros, pero puede no ser identico sin seed/version/parametros exactos.

No prometer regeneracion identica si no existe seed, version de provider y parametros exactos.

## Endpoints

Endpoints generales recomendados:

- `GET /api/pro/projects`
- `POST /api/pro/projects`
- `GET /api/pro/projects/{project_id}`
- `GET /api/projects/{project_id}/phases`
- `GET /api/projects/{project_id}/phases/{phase_name}`
- `POST /api/projects/{project_id}/phases/{phase_name}/initialize`
- `PUT /api/projects/{project_id}/phases/{phase_name}`
- `POST /api/projects/{project_id}/phases/{phase_name}/save`
- `POST /api/projects/{project_id}/phases/{phase_name}/reset`
- `POST /api/projects/{project_id}/phases/{phase_name}/ai-suggest`
- `GET /api/pro/projects/{project_id}/events`
- `GET /api/pro/projects/{project_id}/artifacts`
- `POST /api/pro/projects/{project_id}/artifacts/{artifact_type}/verify`
- `POST /api/pro/projects/{project_id}/artifacts/{artifact_type}/regenerate`
- `GET /api/pro/projects/{project_id}/artifacts/{artifact_type}/download`

Endpoints especificos existentes se conservan:

- `POST /api/pro/projects/{song_id}/lyrics`
- `POST /api/pro/projects/{song_id}/music-plan`
- `POST /api/pro/projects/{song_id}/midi`
- `POST /api/pro/projects/{song_id}/master`
- `POST /api/pro/projects/{song_id}/export`

Si se mantienen endpoints especificos por fase, deben internamente usar el mismo modelo de datos: `project_phase_data`, `project_phase_events` y `project_artifacts`.

## Reglas De UI

1. Cada fase debe tener boton Guardar.
2. Guardar solo persiste configuracion.
3. Guardar no ejecuta ACE-Step, MIDI, audio ni export.
4. Production concentra ejecucion pesada y exportables.
5. Las fases deben mostrar estado visual: No creada, Inicializada, Borrador, Completada, Error de ejecucion, Artefacto generado, Artefacto faltante o danado.
6. Al cargar proyecto, los controles deben rellenarse desde SQLite.
7. Ningun formulario debe depender de leer archivos derivados.
8. Si hay datos guardados, deben aparecer automaticamente.
9. Si hay artefactos faltantes, mostrar opcion de verificar/regenerar.

## Reglas De Consistencia

Ampliación pendiente: [AMATEUR_AUDIO_VOICE_STEERING.md](AMATEUR_AUDIO_VOICE_STEERING.md) define preparación anterior al set, referencias/perfiles vocales, huella de inputs, evaluación y aprobación por versión. Estas entidades aún requieren migraciones y contratos HTTP; no asumir que el esquema descrito aquí ya las implementa. Mantener estado de evaluación y aprobación separado del estado de ejecución y del estado de artefacto.

1. SQLite es fuente de verdad.
2. Archivos son derivados.
3. Estados de fase, ejecucion y artefactos no deben mezclarse.
4. IA puede sugerir, pero usuario confirma.
5. Todo proceso importante genera evento.
6. Todo artefacto generado se registra.
7. Todo archivo descargable debe validarse antes de descargar.
8. La regeneracion debe usar datos persistidos.
9. El frontend debe poder reconstruir el estado completo del proyecto con una sola carga inicial.
10. No registrar cada tecla, solo eventos importantes.
