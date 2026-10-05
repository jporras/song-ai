# AGENTS.md

## Objetivo

Este proyecto implementa un sistema modular de generación de canciones personalizadas mediante IA.

---

# Reglas IMPORTANTES

## 1. Mantener arquitectura modular

Nunca acoplar:
- providers,
- explorers,
- builders.

---

## 2. Nunca perder intención musical

Toda generación debe preservar:
- instrumental intent,
- vocal intent,
- lyrical intent.

Guardar siempre:
- manifest.json
- intent.json

---

## 3. Providers intercambiables

El sistema debe soportar:
- local providers,
- pro providers.

Nunca asumir un provider único.

---

## 4. Mantener assets separados

Separar:
- instrumental,
- melodía,
- letra.

Nunca fusionarlos prematuramente.

---

## 5. El sample es obligatorio

Antes de generar canción completa:
- debe existir sample,
- debe existir set válido.

---

## 6. El set/proyecto debe completar puntos 1, 2 y 3

Todo set representa un proyecto musical y debe estar compuesto por:
- 1. instrumental,
- 2. melodía,
- 3. letra.

La IA de asistencia debe:
- recordar al usuario que esos tres puntos son obligatorios,
- validar que exista al menos un draft de cada tipo antes de crear el set,
- indicar qué parte falta si el proyecto todavía no puede avanzar,
- no permitir sample ni canción completa sin set válido.

---

## 7. La IA debe asistir la cancion segun el proyecto activo

La IA de asistencia debe ayudar al usuario a completar una cancion acorde al proyecto/set en el que se esta trabajando.

Siempre debe tomar como contexto:
- project_name,
- description,
- instrumental intent,
- vocal intent,
- lyrical intent,
- assets seleccionados,
- set.json,
- manifest.json,
- intent.json.

La IA debe sugerir:
- ajustes de genero, mood, BPM, tonalidad e instrumentos,
- mejoras de melodia vocal, rango, energia y estructura,
- mejoras de letra, idioma, tono, tema y placeholders,
- siguientes pasos para pasar de drafts a set, sample y cancion completa.

La IA no debe sugerir cambios que rompan:
- la intencion instrumental,
- la intencion vocal,
- la intencion lirica,
- la descripcion del proyecto activo.

Si falta informacion para completar una cancion coherente, la IA debe pedir o sugerir solo los datos necesarios para continuar.

---

## 8. El sistema debe funcionar sin APIs reales

Durante primeras fases:
- usar mocks,
- evitar dependencias externas.

---

## 9. Modelos especializados y handoffs

El sistema debe evolucionar como un estudio musical IA multi-modelo.

Roles esperados:
- assistant conversacional,
- extractor de intencion,
- music providers,
- voice providers,
- lyrics providers,
- audio pipeline.

Los modelos no deben comunicarse directamente entre si mediante prompts encadenados.

Deben comunicarse mediante:
- base de datos,
- tasks,
- estados,
- intent.json,
- manifest.json,
- set.json.

Debe existir un `ModelOrchestrator` para:
- activar/desactivar modelos,
- manejar handoffs,
- controlar memoria,
- registrar progreso,
- suspender y reactivar el assistant.

---

## 10. La DB es la fuente activa

SQLite es la fuente activa de trabajo.

Los JSON son snapshots/exportaciones regenerables:
- si se exportan desde DB, se sobrescriben,
- no deben reemplazar la version activa persistida,
- el audio nunca debe ser la fuente de verdad.

Cada proyecto/cancion debe conservar un historico de pasos:
- fase,
- actor o modelo activo,
- estado,
- mensaje,
- fecha,
- task/model run relacionado cuando aplique.

Ese historico permite reconstruir como se creo la cancion desde la conversacion inicial hasta la exportacion.

---

## 11. Toda funcionalidad debe dejar el proyecto ejecutable

Cada sprint debe:
- compilar,
- ejecutar,
- mantener menú funcional.

---

## 12. No generar código monolítico

Preferir:
- clases pequeñas,
- providers,
- builders,
- managers.

---

## 13. Mantener compatibilidad futura

Diseñar pensando en:
- API REST,
- workers,
- UI web,
- colas,
- generación distribuida.

---

## 14. Nunca hardcodear prompts

Todos los prompts deben construirse desde:
- intent.json,
- profile.json,
- lyrics.md.

---

## 15. Registrar cada avance en README.md

Cada avance funcional, cambio de arquitectura o sprint completado debe quedar registrado en README.md.

README.md debe reflejar siempre:
- que tiene actualmente la aplicacion,
- como se ejecuta,
- que sprints estan completos o en progreso,
- que funcionalidades existen,
- que falta por construir.

---

## 16. Diseñar el flujo para usuarios amateur en música

El usuario principal puede describir una idea, una emoción o una ocasión, pero no tiene por qué conocer composición, BPM, tonalidad, MIDI, stems, mezcla ni mastering.

La experiencia debe:

- partir de la idea del usuario en lenguaje natural,
- pedir solo los datos creativos necesarios para continuar,
- permitir que la IA proponga valores musicales coherentes, explicarlos y dejar que el usuario los revise antes de guardar,
- presentar instrumental, melodía vocal y letra como tres piezas obligatorias, sin exigir que el usuario las componga manualmente,
- mostrar qué está preparado, qué falta y una acción principal para el siguiente paso,
- ofrecer los controles técnicos mediante ajustes avanzados,
- mostrar controles visibles para recibir decisiones y revisar propuestas, sincronizados con la conversación y el documento técnico,
- explicar progresivamente todas las familias y parámetros de la especificación, con valores sugeridos, ficha completa y delegación explícita; no exigir conocimiento previo ni confirmar por silencio,
- usar nombres comprensibles en la interfaz y reservar IDs, providers y códigos de estado para detalles técnicos,
- distinguir propuesta, configuración guardada, generación en curso, sample y canción final,
- explicar bloqueos y errores con una acción concreta para continuar.

El recorrido guiado debe seguir:

1. Definir la idea.
2. Preparar y elegir instrumental, melodía vocal y letra.
3. Confirmar un set válido.
4. Generar y revisar un sample de ese set.
5. Generar la canción completa y descargar los archivos verificados.

La preparación inicial de la idea y los drafts no debe crear un set incompleto. El sample debe corresponder al set activo y a sus datos vigentes; los cambios que afecten su resultado requieren revisarlo o regenerarlo antes de producir la canción completa. Estas validaciones deben aplicarse tanto a la ruta guiada como a la avanzada, en UI y backend.

Gemma acompaña el recorrido desde el contexto persistido del proyecto activo. Antes de que exista un set, debe identificar claramente la preparación inicial y las piezas pendientes. Las propuestas de ejemplo o mock deben identificarse como tales y nunca presentarse como una canción final generada.

El contrato detallado del recorrido, las prioridades y los criterios de aceptación se mantienen en `docs/AMATEUR_USER_FLOW_REVIEW.md`. Una propuesta de experiencia solo se considera validada cuando se prueba con personas sin experiencia musical; la revisión de código y documentación no sustituye esa comprobación.

---

## 17. Calidad de audio, canto y voz personalizada

El contrato de desarrollo y aceptación se mantiene en `docs/AMATEUR_AUDIO_VOICE_STEERING.md`; el orden de entrega está en `docs/ROADMAPP.md`.

- No anunciar calidad final por completar una task o generar un archivo: verificar integridad técnica, revisar el audio completo por escucha y registrar la aceptación del usuario.
- Vincular aprobación del sample a set, revisión de inputs y artefacto escuchado. Cambios creativos invalidan esa aprobación; todas las rutas finales verifican vigencia en backend.
- Para producción real, el sample debe representar voz, provider y configuración relevantes del final. Una guía o mock no acredita esa calidad.
- Una voz generada natural, una voz personalizada por referencia y una grabación humana son opciones distintas. Declarar capacidades reales de los providers; TTS hablado no demuestra canto.
- La voz personalizada es opcional y pendiente de implementación; no bloquear la ruta de voz generada por su ausencia. Registrar referencia autorizada, perfil/versiones y dependencias antes de integrarla.
- Mantener las tres piezas musicales obligatorias y separadas; un perfil vocal no crea una cuarta pieza ni reemplaza la intención vocal.
- Guardar estado, evaluaciones y aprobaciones en SQLite; conservar los archivos originales de referencia necesarios y sus registros/checksums. Los JSON siguen siendo exportaciones regenerables.
- Mantener mocks para contratos y exigir evidencia separada de audio real, escucha y usabilidad antes de afirmar que una entrega cumple calidad o experiencia.

---

## 18. Especificación completa con Gemma y Qwen

El contrato de roles, documento técnico y trazabilidad se mantiene en `docs/SONG_SPEC_GEMMA_QWEN_CONTRACT.md`.

- Gemma recoge y confirma los deseos del usuario; Qwen compila la especificación musical/técnica, propone detalles y comprueba coherencia y viabilidad. La aprobación creativa sigue siendo del usuario.
- El documento debe cubrir las tres intenciones, requisitos obligatorios/preferidos, decisiones y procedencia, estructura, selección de voz, producción, sample, calidad, exportación y criterios verificables de fidelidad.
- Evolucionar `song_specs` y `song_spec.json` existentes; SQLite es la fuente activa. Exportar también `song_spec.md` desde la misma revisión, sin crear otra fuente de verdad.
- Separar completitud por etapa, validación determinista, revisión del modelo, confirmación del usuario y aprobación del audio. Un booleano de campos completos no acredita inferencia Qwen ni aceptación del usuario.
- Mantener versiones y trazabilidad deseo → requisito → assets/plan → parámetros del provider → evidencia del audio. No omitir restricciones obligatorias ni tratar propuestas IA como deseos confirmados.
- Handoffs mediante tasks y contexto persistido bajo el orquestador; identificar ejecución real, fallback o mock. Providers/modelos son intercambiables sin perder los roles.
- Compilar generación desde la revisión aprobada y validar sus capacidades. La especificación dirige la calidad; audio real, escucha y aceptación aportan la evidencia del resultado.
- Derivar un catálogo completo del esquema y capacidades. Qwen mantiene cobertura/recomendaciones; Gemma explica el camino y las decisiones con lenguaje común.
- La UI ofrece controles para campos editables y acceso a delegados/informativos; formularios, guía y chat comparten revisión, procedencia y validaciones. No depender exclusivamente de la conversación para configurar una canción.

---

## 19. Alinear modelos con ACE-Step

- Leer `docs/ACE_STEP_CAPABILITIES.md` antes de modificar generación, planes de provider o consejos sobre audio. El steering de roles está en `docs/steering/`.
- Gemma y Qwen reciben la sección marcada del contrato y el estado local observado en cada solicitud del registry; un enlace al archivo o cargar pesos no transmite ese conocimiento.
- Separar tareas documentadas, tareas llamadas por el wrapper y ejecución/calidad verificadas. No habilitar por una firma, versión, default o nombre de carpeta.
- Mantener distinción entre API de alto nivel, handler y HTTP. Probar traducción de cada campo; parámetros omitidos del wrapper no se consideran controles ejecutables.
- Qwen compila/revisa especificación musical y viabilidad, Gemma recoge/explica deseos, usuario aprueba y ACE-Step genera. Tasks/SQLite coordinan los handoffs; no encadenar modelos directamente.
- Preservar revisión/hashes del steering en resultados y eventos; evaluar obediencia real por separado de pruebas de inyección.
- `create_sample` del LM interno no sustituye el sample de audio obligatorio. Referencia de timbre no acredita identidad vocal; notas MIDI ni comandos DSP se ejecutan por incluirlos en un caption.
