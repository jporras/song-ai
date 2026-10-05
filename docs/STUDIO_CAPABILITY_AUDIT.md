# S00 — Auditoría de capacidades y controles
Fecha: 2026-10-04. En progreso. Reporte reproducible: STUDIO_CAPABILITY_AUDIT.json.
Se ejecutó con .venv/Scripts/python.exe; el Python global del reporte inicial no describía el entorno del servidor. La CLI ahora registra explícitamente intérprete y versión.

## Entorno observado
- ACE-Step 1.5.0, PyTorch 2.9.1+xpu, Transformers 4.53.1, SoundFile 0.13.1 y FastAPI 0.115.6.
- PyTorch detecta una Intel Graphics por XPU; CUDA no disponible. No se asignaron tensores ni se cargaron pesos: no acredita inferencia en ese dispositivo.
- Gemma/Qwen: archivos configurados existen, health de endpoints configurados no disponible en esta comprobación. No se inició llama-server ni se pidió inferencia.
- Checkpoints encontrados bajo data/models/music; sus config.json se inventarían con checksum. Directorio/config no acredita peso completo, compatibilidad ni modelo cargado.
- Diagnósticos antiguos se resumen sin prompts/letras: fecha, estado, modelo/dispositivo observados. Nunca se promueven a evidencia de ejecución vigente.

## Matriz trazada de controles y motores
El JSON enumera controles de plantilla con bindings y línea. Sus audit_id son localizadores de auditoría, no IDs estables de dominio; S03 define estos últimos. Una entrada se marca PARTIAL hasta trazar handler y motor. No se infiere soporte por tener v-model o un botón.

| Control/familia | Estado | Ruta / motor | Efecto demostrado y siguiente acción |
| --- | --- | --- | --- |
| Guardar fases | IMPLEMENTED | app.js/savePhaseData → API proyectos/fases → SongService → SQLite | Guarda configuración; no cambia audio por guardar |
| BPM/tonalidad/compás | PARTIAL | intent/musicPlan → configuración persistida → especificación/plan | No hay time-stretch audible conectado al control; S04/S05 |
| Letra y secciones | PARTIAL | lyricSections → guardado; servicios lyrics/plan | Edición textual existente; reordenar no edita clips de audio; S07 |
| Notas piano roll | PARTIAL | addMidiNote/removeMidiNote → midiPlan.notes | Configuración visual; falta acreditar render sincronizado de esas notas; S12 |
| Humanización/velocity/swing | PARTIAL | midiPlan → fase guardada | No equivale a secuenciador audible; trazar consumo y render S12 |
| Instrumental nivel/Mute/Solo | PARTIAL | stem.level, toggleStemMute/toggleStemSolo → markDirty | Cambia estado del formulario; MixingService usa dos entradas y ganancias prefijadas; S09 |
| Voz/capas/vibrato | PARTIAL | voice → guardado → dirección de generación | No acredita procesamiento vocal exacto ni capas de audio independientes; S13 |
| Waveform | EXPERIMENTAL | waveformBars en app.js | Barras calculadas con seno, sin lectura del audio; reemplazar por peaks reales S07 |
| Crear/aprobar sample | PARTIAL | production_actions → API samples → builder/storage | Checkpoint mock; no acredita escucha ni habilitación válida de producción real; S01 |
| Confirmar ficha | IMPLEMENTED | API spec/confirm → revisión SQLite | Confirma revisión y rechaza obsoleta; no verifica audio |
| Generar/masterizar | PARTIAL | runProductionStep → rutas históricas → ACE-Step text2music o master local | Hay integración; falta evidencia vigente de calidad y gate real completo |
| Repaint/Cover/Extract/Lego/Complete | MISSING | No expuestos en wrapper | S10 según compatibilidad efectiva |
| Descargas | PARTIAL | rutas por proyecto/artefacto → export/download services | Reutilizar aislamiento; aprobación por render todavía incompleta |
| Copilot | PARTIAL | askGemmaAssistant → API assistant → contexto/provider/fallback | Puede proponer formularios; falta tool ejecutable, confirmación y undo S03–S05 |
| Play/Seek/Loop de sesión | MISSING | Sin transporte multipista localizado | S04/S07 |
| DSP EQ/pan/compresión por canal | MISSING | Sin tools/mixer conectado a estos parámetros | S09/S11 |

## Decisiones de integración
- Conservar ACE-Step local como generación; wrapper text2music es la única task expuesta. No habilitar variantes de edición desde documentación externa.
- Mantener ProfessionalSongService congelado para nuevas funciones. Extraer responsabilidades locales en S02/S03; no desconectar consumidores actuales.
- Evaluar FFmpeg para stretch/render y separación por provider en S04/S08; una herramienta presente no acredita paridad ni calidad.
- FFmpeg existe en data/tools/ffmpeg/bin/ffmpeg.exe; el launcher añade esa carpeta a PATH. El auditor distingue presencia local y resolución por PATH; no acredita ejecución por presencia.
- La auditoría es lectura; no inicia servicios, instala dependencias ni altera proyectos musicales.
- Probes con opt-in --probe-runtime: torch en subproceso de 30 segundos; health solo loopback con timeout de 2 segundos, sin proxies ni redirecciones.
- Registro de capacidades conservador: no habilita generación por package/config/hardware. Evidencia de ejecución y escucha requieren pruebas posteriores.

## Verificación de esta entrega
### Ampliación: contrato instalado y trazabilidad
- El auditor compara por AST las firmas instaladas con las llamadas del wrapper, sin ejecutar el paquete. En el entorno auditado los keywords de initialize_service y generate_music coinciden; esto no prueba resolución de mixins, imports ni ejecución del checkpoint.
- --probe-api-import añade una comprobación aislada de import de la API: watchdog de 55 segundos y límite externo de 60 segundos. Distingue timeout, error de importación, fallo de lanzamiento y respuesta inválida; registra la etapa sin publicar logs ni datos de proyectos.
- La ejecución con `.venv` confirmó la importación de `acestep.acestep_v15_pipeline.AceStepHandler` en 29,53 segundos. No instanció el handler ni cargó pesos; generación y calidad siguen sin verificar. El límite anterior de 45 segundos había producido un resultado inconcluso.
- Inventario de esta plantilla: 160 controles con bindings y 68 expresiones v-model trazadas como candidatos; son elementos de plantilla, no conteo de instancias dinámicas ni capacidades completas.
- parameter_trace_candidates enumera cada v-model simple y lecturas candidatas de claves en servicios. No confunde coincidencia de nombre con flujo de datos ni con efecto audible; expresiones dinámicas se identifican aparte.

| Parámetro / ruta | Evidencia de consumo | Brecha y tarea |
| --- | --- | --- |
| musicPlan.bpm / intent.bpm | _spec_from_set_data prioriza plan, después idea; _build_prompt incluye BPM; MIDI lo consume | Wrapper no envía bpm estructurado a ACE-Step; S06 debe compilarlo explícitamente |
| musicPlan.key | spec/plan y prompt; MIDI armonía | Wrapper no envía key_scale estructurado; S06 |
| musicPlan.timeSignature | Import del plan escribe time_signature | Generación de plan nueva fija 4/4; wrapper no envía time_signature; S06/S12 |
| Idioma de letra | spec y prompt textual, lyrics.md | Wrapper no envía vocal_language; la firma instalada tiene default en; resolver normalización S06 |
| Secciones y duración | _write_music_plan_from_set toma seconds y _duration_seconds toma duración total | _build_prompt no incluye timeline detallada; plan ya existente no se actualiza por este import; S01/S06 |
| midiPlan.notes y sus parámetros | phasePayload guarda notas; MidiGenerationService crea melodía desde timeline/tonalidad | No consume las notas editadas del piano roll; S12 |
| instrumental.stems.level/muted/solo | Persistencia en phasePayload | MixingService usa ganancias fijas y dos entradas; S09 |
| voice.breaths/humanization/vibrato/layerBlend | Persistencia en fase | _spec_from_set_data toma principalmente mainVoice/style, no convierte esos controles en DSP; S13 |
| Instrumentos/estilo/voz | _spec_from_set_data → spec → _build_prompt | Condición textual, no garantía de stems o mezcla por instrumento; S06/S08 |

Estos hallazgos se registran antes de modificar generación: el módulo histórico queda congelado; las correcciones irán a compiladores/casos de uso locales con puertos.

Once pruebas aprobadas de registro y auditoría: incluyen firmas, trazas candidatas, restricción de probes a loopback y clasificación de resultados de importación. Un import exitoso conserva `generation_verified=false` y `weights_loaded=false`.
S00 aún requiere trazar consumo de cada parámetro guardado y comprobar el checkpoint efectivo de ACE-Step. La prueba real de generación/sample corresponde a S01/S06.

### Resolución del perfil pendiente de corregir
El reporte incorpora `ace_step_configuration`: expresiones de defaults para configuración, checkpoint y dispositivo, y alternativas de retorno del resolver extraídas por AST. No ejecuta el wrapper. Los campos efectivos quedan sin confirmar hasta contar con diagnóstico de una ejecución. El grafo de dependencias incluye ahora `import`, `from` y referencias relativas.
`backend/audio/ace_step_profiles.py` define perfiles con repositorios históricos v1 y modifica `ACESTEP_MODEL_REPO`. El wrapper 1.5 resuelve además `ACESTEP_CONFIG_PATH`; su argumento por defecto es `acestep-v15-turbo` y tiene prioridad sobre la inferencia por nombre del checkpoint. Elegir un perfil base o encontrar su directorio no demuestra que se cargue la configuración base. S06 debe unificar esta resolución en el adaptador local y registrar configuración/checkpoint efectivos por ejecución.

Verificación de esta ampliación: 13 pruebas aprobadas de configuración, auditoría y registro; compilación Python correcta. Las pruebas comprueban que inspeccionar defaults no ejecuta el wrapper ni acredita un modelo cargado.

Corrección derivada de auditoría: SongService dejó de indicar a Gemma que omita el sample en la ruta sin set. Ambas rutas del prompt exigen las tres piezas, set válido y sample vigente escuchado/aprobado; identifican que un mock no acredita producción real. Dos pruebas de regresión aprobadas. La guía conversacional no reemplaza el gate del backend, todavía pendiente de completar en S01.
