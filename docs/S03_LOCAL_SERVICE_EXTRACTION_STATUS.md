# S03-04 — asistencia local e inventario de compatibilidad (2026-10-08)



## Cierre de desarrollo y verificación de la extracción

Los siete comandos restantes se trasladaron a clases pequeñas: GenerateLocalMusicPlan/GenerateLocalMidi, GenerateLocalInstrumental/GenerateLocalVocals/ConvertLocalVoice, MixLocalSong y MasterLocalSong. LocalProductionCommands compone solo el comando elegido y sus dependencias. LocalProductionContext comparte ficha confirmada, consultas derivadas, sample y progreso.

SongService tiene **cero delegaciones directas a ProfessionalSongService**. Ya no inicializa ese servicio ni ModelManagerService al arrancar: la propiedad professional_songs construye y conserva compatibilidad solo mediante acceso explícito. El servicio antiguo delega sus siete comandos a las mismas clases con un adaptador histórico de preparación; no hay dos implementaciones de los comandos.

La ruta local no reconstruye MusicSpec desde fases antiguas ni marca aprobación automática. Master consulta letra activa SQLite, rechaza mock/placeholders y regenera snapshots desde la misma ficha confirmada. Los comandos locales no simulan carga/descarga de Qwen con ModelManager. Plan/MIDI deterministas se registran como compatibility planning, no inferencia Qwen. El pipeline de compatibilidad conserva sus comprobaciones de aprobación/artefactos; no se declara parte necesaria del camino ACE-Step. La política de sample vigente no se modifica aquí.

El provider full-song local existente conserva su nombre ProfessionalFullSongService y comparte LocalAudioProcessService; es una implementación separada de generación local, no el monolito ProfessionalSongService extraído.

### Verificación agrupada

- **33 pruebas backend aprobadas** en 12,235 s: comandos, consultas, dispatcher, exportación, revisiones, preparación/concurrencia, intención, letra y compatibilidad de recopilación anterior.
- Los siete comandos pasan por providers inyectados de prueba; se conserva MusicSpec. Sin inicialización histórica ni ModelManager en SongService activo.
- Bloqueo por ficha no confirmada, fallo de voz con estado failed y letra activa con placeholders cubiertos.
- Servicio histórico diferido y cacheado, accesible explícitamente.
- compileall y diff check de archivos editados correctos.
- Smoke ASGI en SQLite temporal: /lyrics, /api/pro/phases y /api/pro/projects responden 200; dos proyectos, histórico sin inicializar. Autostart LLM/audio y monitor desactivados; ningún dato productivo modificado.

No suite backend completa, nuevo Playwright, inferencia ni audio reales. Los dobles/fixtures no acreditan canto o fidelidad audible.

**S03-04: D 0.5→1, V 0.5→1, A=0. Global 65,7%→66,9%.** Cierre técnico de extracción; aceptación de arquitectura pendiente. Inferencia y audio real permanecen en sus entregables S00/S06/S10.

## Bloque anterior: consultas, regeneración y exportación locales

Extracción de este bloque reduce las delegaciones directas de SongService a ProfessionalSongService de 16 a 7:

- LocalProductionArtifactQueries comparte siete lecturas (plan, MIDI, instrumental, voz, voz convertida, mezcla y master); conserva claves de respuesta, exige proyecto SQLite y archivos dentro de su carpeta. No instancia servicios de generación/monitor de recursos. Los siete servicios antiguos delegan sus get al mismo lector, sin duplicar implementación.
- Las lecturas de plan/MIDI siguen siendo consultas de artefactos derivados de compatibilidad: no modifican ni reemplazan MusicSpec, no verifican calidad de audio por existir un archivo.
- ArtifactRegeneration despacha tipos a handlers inyectados. SongService usa propuesta de letra y revisión local actuales; no crea una aprobación simulada al regenerar lyrics_approved_json. El servicio histórico conserva su propio comportamiento a través del mismo dispatcher y handlers históricos.
- ExportLocalProject usa consulta SQLite, require_confirmed_music_spec compartido, SampleGate vigente, master disponible y LocalProjectExportService. Conserva eventos y comprobación de artefactos/calidad/checksums. No reconstruye ficha desde snapshots. La política de sample no cambia en esta entrega.

Quedan siete comandos históricos: generate_music_plan, generate_midi, generate_instrumental, generate_vocals, convert_voice, mix_song y master_song; además de inicializar ProfessionalSongService. Requieren separar orquestación y dependencias conservando sus validaciones, sin agregar MIDI al camino activo ACE-Step. Servicio histórico conservado.

Verificación: 16 pruebas backend agrupadas aprobadas (5,873 s), incluyendo siete contratos de consulta/SQLite intacta, archivos obligatorios/rutas, dispatcher, exportación bloqueada antes de efectos, orquestación local con dobles, revisiones y propuestas. compileall correcto. Los bytes de fixtures y dobles de sample/export no acreditan generación ni calidad real. No nueva prueba Playwright ni modificación UI en este bloque.

S03-04 sigue D=0.5/V=0.5/A=0, global 65,7%; reducción de dependencias 16→7 documentada sin cambiar el denominador ni cerrar un entregable incompleto.

## Entregado en el bloque anterior

CollectLocalIntent reemplaza collect_professional_spec en SongService. Consulta usa MusicSpec y revisión SQLite, nombre del proyecto y set seleccionado cuando existe. Gemma responde mediante registry/steering y tarea collect_song_intent del orquestador. No invoca ModelManager simulado, CreativeAgentService, TechnicalDirectorService ni ProfessionalSongService. No guarda sugerencias ni exporta ficha; no atribuye aprobación Qwen. Qwen se solicita por separado con compile_song_spec sobre decisiones guardadas.

Mensaje inválido o revisión obsoleta se rechazan antes de tarea/inferencia. Mock, respuesta vacía o error dejan tarea failed. Un proyecto sin ficha recibe orientación de preparación y permanece sin ficha. Task conserva consulta/respuesta/steering y origen; la aprobación creativa requiere guardado explícito en controles. La acción UI envía revisión, bloquea cambios sin guardar y no muestra una respuesta en otro proyecto/revisión. Nombres de acciones distinguen consultar, revisar propuesta y comprobar reglas de aprobación.

## Inventario anterior a esta extracción

Lectura/creación local, revisión/confirmación/restauración/exportación de MusicSpec, acceso/revisión/propuesta de letra, descarga/verificación de artefactos y runner de candidatos tienen servicios locales independientes. El catálogo de fases ahora usa LocalProjectQueries.

SongService conserva 16 delegaciones históricas, además de inicializar ProfessionalSongService para ellas:

| Familia | Métodos restantes | Trabajo pendiente |
| --- | --- | --- |
| Plan musical | generate_music_plan/get_music_plan | Separar consulta/proyección del pipeline histórico |
| MIDI | generate_midi/get_midi | Encapsular compatibilidad; no introducir MIDI como requisito de ACE-Step |
| Instrumental | generate_instrumental/get_instrumental | Separar ruta histórica de creación ACE-Step |
| Voz sintetizada | generate_vocals/get_vocals | Encapsular ruta; no confundir TTS con canto |
| Conversión vocal | convert_voice/get_converted_voice | Mantener opcional, sin prometer identidad |
| Mezcla | mix_song/get_mix | Separar orquestación histórica de render local |
| Master/export | master_song/get_master/export_song | Preservar gates, artefactos y verificación al trasladar |
| Regeneración | regenerate_artifact | Reutilizar servicios extraídos sin dispatcher monolítico |

Servicio histórico conservado. Ninguna ruta de compatibilidad borrada o declarada migrada por esta entrega. S03-04 sigue D=0.5/V=0.5/A=0; global 65,7%.

## Evidencia

- 15 pruebas backend agrupadas aprobadas (3,322 s): asistencia local, propuesta completa de letra y propuesta Qwen.
- 2 pruebas Node aprobadas: acción conserva revisión, no modifica ficha, bloquea cambios y descarta respuesta de otro proyecto.
- Test de recopilación histórica conservado explícitamente contra ProfessionalSongService: 1 aprobado (1,510 s). Fixtures antiguas de test_audio_export preparan sus datos con collect_spec histórico, sin exigir autopersistencia al API activo. Primer intento detectó expectativa de generación antigua contra API nuevo; corregido para el test histórico, sin cambiar el contrato activo.
- Build Vite y compileall correctos. No ejecución real de Gemma/Qwen, audio, prueba completa de suite ni nuevo audit Playwright.
