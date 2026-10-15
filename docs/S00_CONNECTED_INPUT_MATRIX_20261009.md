# S00-03: matriz consolidada de inputs conectados — 2026-10-09

## Alcance verificado

Verificacion del contrato de entrada por capas: controles visibles → SQLite/revision → compilador → archivos/argv/contexto del wrapper. Cada capa usa fixtures y casos propios; no se afirma que todas las combinaciones hayan recorrido todos los controles en una unica sesion. Se verifica preservacion y transformacion, no ejecucion de pesos, obediencia del modelo, audio ni usabilidad con personas. La aceptacion final queda fuera del porcentaje D/V.

## Matriz de 21 inputs

| Input | Origen/control y comprobacion |
| --- | --- |
| captions | Nueve campos UI de estilo/emocion/instrumentos/voz/expresion/energia/groove/rango/mezcla; composicion literal y traza por campo. |
| lyrics | Editor Unicode/proteccion/recarga/confirmacion; compilador rechaza discrepancia; wrapper preserva markdown. |
| bpm | UI97 y chat97; guardar/confirmar; extremos30/300; request sin redondeo. |
| key_scale | UI D Major; proyeccion del campo key y validacion de valores invalidos. |
| time_signature | UI6/8→6 con alias trazado. |
| vocal_language | UI Spanish→es con alias trazado. |
| audio_duration | UI123s; extremos10/600. |
| task_type | Seleccion de seis modos; traduccion/condiciones de fuente/Base y LM. |
| generation_api | UI ruta LM y bloqueo Cover+LM; traduccion direct/high_level/high_level_lm por pruebas de contrato. |
| lm_model_path | Selector UI cambiado a0.6B, persistencia y traza USER; no carga. |
| seed | UI24680; limites0/4294967295 y argv. |
| inference_steps | UI32; extremos Base1/200 y Turbo1/20. |
| guidance_scale | UI5 Base; extremos1/15 Base, Turbo fijo1 y rechazo de otro valor. |
| shift | UI1.5; extremos0.1/10. |
| reference_audio | UI seleccion ID; resolucion SYSTEM de ruta, checksum verificado. |
| src_audio | Importacion autorizada, seleccion ID fuente; misma ruta/checksum y rechazo ajeno/alterado. |
| instruction | Boton de preparacion explicita de instrucciones por pistas; guitar y bass,guitar. |
| repainting_start | UI0.5, validacion numerica/intervalo segun archivo. |
| repainting_end | UI1.5, validacion final y -1 en contrato. |
| audio_cover_strength | UI0.75 guardado/confirmado; snapshot historico compila igual. |
| chunk_mask_mode | Campo SYSTEM explicit para repaint/lego; no se atribuye control USER inexistente. |

Inputs nuevos sin mapping fallan. El perfil/modelo es contexto de ejecucion, no otro input del payload; inventario y carga observada se siguen en S00-04. Requisitos no ejecutables se conservan declarando limitaciones; no se convierten en versos/comandos del motor.

## Chat y autoria

QA song_e763821404ae/set qa-chat-set: pregunta Estado del proyecto activo, quiero ajustar BPM a97. envia song/set/revision. sqlite_guidance y deterministic_question_parser declarados; no Gemma/Qwen reales. Respuesta no cambia ficha; aplicar cambia formulario (dirty), DB permanece BPM72. Solo guardar y confirmar cambia DB/request a97. Registra reviewed_assistant_proposals, producer, revision, accepted/explicit_user_save y transformaciones. Nueve campos caption introducidos via UI forman exactamente balada; tierna; piano, cello; voz suave; intima; gran coro final; pulso lento; registro medio; voz clara, con nueve fuentes.

Chat no es editor universal de todos los parametros: lo no conectado al parser se configura por controles. No se acredita inferencia de modelos ni comandos automaticos; registry model_can_execute=false, autorizacion/revision obligatorias comprobadas. Propuestas sobre revision/proyecto/draft distinto se rechazan en contratos frontend/backend.

## Evidencias y condiciones

- S00_USER_CONTROLS_PLAYWRIGHT_20261009.md
- S00_EXECUTION_CONTROLS_PLAYWRIGHT_20261009.md
- S00_SOURCE_CONTROLS_PLAYWRIGHT_20261009.md
- S00_LM_LYRICS_VERIFICATION_20261009.md
- S00_LYRICS_EDITOR_PLAYWRIGHT_20261009.md
- S00_FULL_INPUT_RUNTIME_CONTRACT_20261009.md
- test_ace_step_user_input_acceptance:20 rutas compatibles Base/Turbo × modo/API y dos extremos por ruta (40 escenarios); trece rutas Base previas; payload/caption/lyrics/argv.
- test_music_spec_phases: letra protegida, revision, confirmacion real y wrapper.
- test_user_input_persistence_request:20 controles via router/SQLite/reapertura/confirmacion/wrapper.
- test_acestep_runtime_inputs:21 entradas, sustitucion, CLI real falla antes de pesos.
- test_ace_step_configuration/test_ace_step_capability_profile/test_ace_step_plan_review: campos desconocidos, fuentes, valores, restricciones Turbo/LM, intervalos, aprobacion/hash/vigencia.
- Lote final39 pruebas backend aprobado. Lotes anteriores de editor33 y frontend57/build documentados, no sumados ni reejecutados sin cambios.

S00-03 verificacion0.5→1 para esta matriz de contratos. No cierre de ejecucion real: S00-04/S06-04/S06-05/S05/S10 conservan pendientes de carga efectiva, obediencia, modos/audio y recorrido real. No hay nueva generacion ni modificacion de Isabella/Alma. Servidor QA y navegador cerrados.
