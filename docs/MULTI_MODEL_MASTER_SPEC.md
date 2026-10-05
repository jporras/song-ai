# Multi-Model Song AI System - Master Spec

> **Arquitectura objetivo.** Los roles y handoffs orientan el desarrollo, pero los ejemplos de modelos, providers y fases no son una lista de capacidades ya disponibles. Consultar [el mapa de documentación](README.md), `AGENTS.md` y el README de la raíz para reglas y estado actual.

## Objetivo General

Construir un sistema modular de generacion de canciones personalizadas mediante IA, con backend Python, interfaz web Vue y soporte futuro para consola, capaz de:

- conversar con el usuario,
- interpretar intencion musical,
- generar assets reutilizables,
- crear previews,
- producir canciones completas,
- soportar modelos locales y providers pro,
- orquestar multiples modelos especializados,
- persistir toda la intencion creativa en base de datos y JSON exportables.

El sistema no debe pensar en "generar una cancion" como un unico proceso. Debe pensar en:

- generacion de assets musicales reutilizables,
- persistencia de intencion,
- orquestacion de modelos,
- pipeline modular de produccion.

---

## Filosofia Del Sistema

El sistema debe funcionar como un estudio musical IA compuesto por agentes, providers y modelos especializados. Cada modelo tiene un rol especifico.

Ejemplo de roles:

- Gemma: conversacion natural y guia del usuario.
- Qwen: extraccion estructurada, validacion tecnica y metadata musical.
- Modelos musicales: instrumental, soundtrack, variaciones y stems.
- Modelos de voz: voz guia, melodia vocal y voz final.
- Audio pipeline: mezcla, mastering y exportacion.

Los modelos no deben comunicarse directamente entre si mediante prompts encadenados. Deben comunicarse mediante:

- base de datos,
- tareas,
- estados,
- `intent.json`,
- `manifest.json`,
- `set.json`,
- proyectos/sets.

Toda intencion creativa importante debe persistirse.

---

## Principio Central

La intencion del usuario siempre debe sobrevivir aunque:

- cambie el modelo,
- cambie el provider,
- cambie local/pro,
- cambie la calidad,
- se regenere audio.

Por eso el sistema debe almacenar:

- `intent.json`,
- `manifest.json`,
- `set.json`,
- `profile.json`,
- prompts generados,
- metadata estructurada,
- registros en SQLite.

El audio no es la fuente de verdad. La fuente de verdad es la intencion estructurada persistida en base de datos.

Los JSON son snapshots/exportaciones regenerables desde la base de datos.

---

## Arquitectura General

```text
Usuario
  |
  v
Gemma Assistant / UI Assistant
  |
  v
Qwen Intent Extractor
  |
  v
Asset Explorers
  |
  v
Set Builder
  |
  v
Sample Builder
  |
  v
Approval Phase
  |
  v
Production Layer
  |-- Local Production
  |-- Pro Production
  |
  v
Mixing / Mastering
  |
  v
Export
```

En la fase actual, la UI Vue y el backend FastAPI implementan el flujo en modo mock/local. La arquitectura debe mantener compatibilidad con consola, API REST, workers y colas.

---

## Roles De Modelos

Contrato operativo pendiente: [especificación completa con Gemma y Qwen](SONG_SPEC_GEMMA_QWEN_CONTRACT.md). El assistant recoge y confirma deseos; el director técnico compila una especificación por etapas con trazabilidad, validación de capacidades y criterios de calidad. `song_spec.json` y `song_spec.md` son exportaciones de una misma revisión persistida en SQLite. Los nombres de modelos no acreditan una inferencia ejecutada ni aprobación del usuario.

### 1. Assistant Model

Modelo sugerido:

- Gemma, Qwen ligero o cualquier LLM conversacional local/pro compatible con el `AssistantProvider`.

Responsabilidades:

- conversar naturalmente,
- interpretar deseos ambiguos,
- mantener personalidad y coherencia emocional,
- guiar el flujo,
- pedir confirmaciones,
- traducir respuestas tecnicas a lenguaje humano,
- sugerir el siguiente paso correcto,
- suspenderse cuando otro modelo toma control,
- retomar conversacion cuando termina otro modelo.
- explicar proactivamente todos los hitos y familias de parámetros, con propuestas, ejemplos y decisiones delegables, apoyándose en controles visibles de la interfaz.

Reglas:

- Es el unico rol que habla directamente con el usuario.
- No debe generar JSON estructurado complejo si hay un extractor especializado disponible.
- No debe hacer validacion tecnica profunda si hay un extractor/validator activo.

---

### 2. Intent Extractor

Modelo sugerido:

- Qwen local/pro por su fortaleza en instrucciones, estructura y razonamiento.

Responsabilidades:

- convertir conversacion en estructura,
- generar o actualizar `intent.json`,
- validar campos faltantes,
- generar prompts estructurados,
- construir metadata musical,
- preparar prompts para modelos musicales,
- detectar inconsistencias,
- pedir aclaraciones mediante el assistant.
- compilar la especificación integral de canción, su procedencia, restricciones y criterios de aceptación mediante el rol de director técnico,
- distinguir detalles propuestos de decisiones confirmadas y señalar requisitos que el provider no soporta,
- vincular cada requisito con el plan de generación y la evidencia posterior de fidelidad.
- mantener el catálogo completo del esquema/capacidades para que guía y formularios cubran todos los parámetros sin prometer controles no soportados.

Reglas:

- No habla directamente con el usuario.
- Responde mediante outputs estructurados:
  - tasks,
  - `missing_fields`,
  - `validation_results`,
  - metadata,
  - prompts.

---

### 3. Music Providers

Responsables de:

- instrumental,
- soundtrack,
- stems,
- variaciones,
- renders finales.

Implementaciones requeridas:

- `LocalMusicProvider`,
- `ProMusicProvider`.

Ejemplos locales:

- MusicGen,
- Stable Audio Open.

Ejemplos pro:

- Stable Audio 2.5,
- futuros providers.

---

### 4. Voice Providers

Contrato pendiente de capacidades, referencias y aceptación: [AMATEUR_AUDIO_VOICE_STEERING.md](AMATEUR_AUDIO_VOICE_STEERING.md). Los ejemplos de motores de esta sección no acreditan canto ni clonación compatible. Cada adaptador debe declarar y demostrar si produce voz hablada, canto, voz condicionada por referencia o conversión de canto; UI y orquestador se basan en esas capacidades.

Perfiles vocales opcionales, referencias y versiones se gestionan mediante servicios y SQLite, separados de providers y builders. La evaluación técnica/perceptual y la aprobación del usuario también son responsabilidades separadas. El resultado del provider es un artefacto candidato, no una canción automáticamente aprobada. No suponer que el provider Full Song acepta identidad vocal personalizada.

Responsables de:

- voz guia,
- melodia vocal,
- voz final,
- voces emocionales.

Implementaciones requeridas:

- `LocalVoiceProvider`,
- `ProVoiceProvider`.

Ejemplos locales:

- Kokoro,
- XTTS,
- Parler-TTS.

Ejemplos pro:

- ElevenLabs,
- OpenAI TTS,
- futuros providers.

---

### 5. Lyrics Providers

Responsables de:

- letras dinamicas,
- placeholders,
- variaciones,
- adaptacion de tono,
- coherencia lirica con el proyecto activo.

Implementaciones requeridas:

- `LocalLyricsProvider`,
- `ProLyricsProvider`.

En fases iniciales puede reutilizar el Assistant Model o el Intent Extractor, siempre que no se rompa la separacion de responsabilidades.

---

### 6. Audio Pipeline

Responsable de:

- mezcla,
- mastering,
- stems,
- exportacion,
- compresion,
- render final.

Herramientas previstas:

- ffmpeg,
- pydub,
- Demucs.

---

## Sistema De Orquestacion

Debe existir un `ModelOrchestrator`.

Responsabilidades:

- activar/desactivar modelos,
- controlar memoria RAM,
- manejar handoffs,
- manejar tareas,
- manejar progreso,
- suspender el assistant,
- reactivar el assistant,
- registrar ejecuciones en base de datos.

El orquestador no debe acoplarse a modelos especificos. Debe trabajar contra providers y contratos internos.

Estado de implementacion inicial:

- `ModelOrchestrator` existe en modo mock.
- Registra `tasks` y `model_runs` en SQLite.
- Simula handoffs para validar UI, persistencia y contratos.
- No carga modelos reales todavia.

---

## Restriccion De Memoria

El sistema debe asumir escenarios de 16 GB RAM.

Reglas:

- Solo un modelo pesado activo a la vez.
- El assistant puede mantenerse activo si es ligero.
- Modelos tecnicos, musicales o de voz se cargan bajo demanda.
- Los modelos se pueden descargar de memoria al terminar.
- El estado se conserva en DB/JSON, no en memoria del modelo.

---

## Handoff Entre Modelos

Flujo esperado:

```text
Assistant activo
  |
  v
Assistant detecta necesidad tecnica
  |
  v
Assistant pide confirmacion al usuario
  |
  v
Assistant entra en suspension
  |
  v
Se carga Intent Extractor
  |
  v
Intent Extractor procesa
  |
  v
Se guarda resultado en DB/JSON
  |
  v
Intent Extractor se descarga
  |
  v
Assistant retoma conversacion
```

Este patron debe funcionar para todos los modelos especializados.

---

## Feedback Al Usuario

Siempre se debe mostrar:

- modelo activo,
- tarea actual,
- porcentaje o estado,
- progreso,
- posibilidad de cancelar,
- si el assistant esta suspendido temporalmente.

Ejemplo:

```text
[##########----------] 50%

Modelo activo:
Qwen3-4B-Instruct

Tarea:
Extrayendo intencion musical

Assistant suspendido temporalmente.
```

---

## Fases Del Sistema

### Fase 0 - Configuracion

Configurar:

- idioma,
- providers,
- formato,
- rutas,
- cache de modelos,
- preferencias local/pro.

### Fase 1 - Conversacion Inicial

El assistant conversa con el usuario y ayuda a definir el proyecto musical.

### Fase 2 - Extraccion Estructurada

El Intent Extractor:

- crea o actualiza `intent.json`,
- detecta faltantes,
- valida intencion,
- genera metadata musical.

### Fase 3 - Exploracion De Assets

Explorar:

1. Instrumental base.
2. Melodia vocal adaptable.
3. Letra dinamica.

Cada asset puede generarse:

- aleatorio,
- prompt IA,
- perfil base,
- configuracion guiada.

### Fase 4 - Curaduria

El usuario:

- escucha,
- compara,
- marca favoritos,
- elimina drafts,
- pide variaciones.

### Fase 5 - Ensamble De Set

Combinar:

- instrumental,
- melodia,
- letra.

Generar o actualizar:

- `set.json`,
- registro SQLite del set/proyecto.

### Fase 6 - Sample / Preview

Generar preview corto:

- coro,
- intro + coro,
- 20 segundos,
- preview textual/mock durante fases iniciales.

Objetivo:

- validar creatividad,
- evitar costo alto,
- detectar ajustes antes de produccion completa.

### Fase 7 - Ajustes

Modificar:

- BPM,
- key,
- letra,
- voz,
- instrumentos,
- emocion,
- estructura.

### Fase 8 - Preproduccion Final

Validar:

- compatibilidad,
- duracion,
- providers,
- exportaciones,
- formato final,
- requisitos de hardware.

### Fase 9 - Aprobacion Del Usuario

El usuario aprueba el set/sample.

Sin aprobacion no se puede generar produccion final.

### Fase 10 - Produccion Completa Local

Generar cancion completa usando modelos locales.

Objetivo:

- preview avanzado,
- pruebas,
- iteracion barata,
- validacion antes de providers pro.

### Fase 11 - Produccion Completa Pro

Generar version premium usando providers pro.

Regla importante:

No rehacer creatividad desde cero. Debe reutilizar:

- `intent.json`,
- `set.json`,
- prompts,
- estructura musical,
- assets aprobados,
- metadata del proyecto.

La produccion pro es un render premium del mismo concepto.

### Fase 12 - Mezcla Y Mastering

Generar:

- mezcla final,
- stems,
- mastering,
- balance,
- normalizacion.

### Fase 13 - Exportacion

Exportar:

- MP3,
- M4A,
- OGG,
- WAV,
- FLAC,
- AIFF,
- stems,
- instrumental,
- voz,
- `lyrics.md`,
- manifests.

### Fase 14 - Plantilla Reutilizable

Guardar:

- set,
- prompts,
- intencion,
- perfiles,
- configuracion musical.

Permitir reutilizacion futura.

---

## Base De Datos

Inicialmente usar SQLite.

Tablas recomendadas:

- `projects`,
- `assets`,
- `sets`,
- `tasks`,
- `model_runs`,
- `project_events`,
- `prompts`,
- `exports`,
- `templates`.

La base de datos es la fuente activa de trabajo.

`project_events` debe funcionar como historico del proyecto/cancion:

- registra cada cambio de fase,
- guarda fecha,
- guarda actor o modelo activo,
- guarda estado,
- enlaza task/model run cuando aplique,
- permite reconstruir el camino desde conversacion inicial hasta exportacion.

---

## Persistencia

Toda informacion importante debe persistirse.

Reglas:

- La DB es la fuente activa.
- Los JSON exportables son snapshots/exportaciones.
- Cuando se exporta desde DB, los JSON se regeneran.
- Si un JSON exportado ya existe, se sobrescribe desde la DB.
- Los manifests y exports se sincronizan desde la version persistida.
- El audio no reemplaza a la intencion estructurada.

---

## JSON Importantes

### intent.json

Fuente principal de intencion musical.

Debe contener:

- BPM,
- mood,
- key,
- instruments,
- lyrics context,
- voice style,
- structure,
- placeholders,
- energy,
- texture,
- metadata emocional.

### set.json

Combinacion seleccionada de assets para un proyecto musical.

Debe contener:

- project name,
- description,
- created_at,
- instrumental_id,
- melody_id,
- lyrics_id,
- compatibility_data.

### manifest.json

Metadata de cualquier asset generado.

### profile.json

Identidad musical reutilizable.

---

## Reglas Importantes

Nunca:

- hardcodear providers,
- perder intencion,
- acoplar modelos,
- mezclar logica conversacional con logica tecnica,
- depender de un solo modelo,
- fusionar assets prematuramente,
- generar produccion final sin set, sample y aprobacion.

---

## El Sistema Debe Ser

- modular,
- extensible,
- orientado a providers,
- orientado a tasks,
- orientado a estados,
- orientado a assets reutilizables,
- compatible con local/pro,
- preparado para workers y colas.

---

## MVP Inicial

El MVP debe funcionar completamente con mocks antes de integrar APIs reales.

Primero:

- flujo,
- arquitectura,
- persistencia,
- handoffs,
- tasks,
- estados,
- menu/API/UI.

Despues:

- IA real,
- audio real,
- mezcla real,
- providers pro.

---

## Objetivo Final

Crear un motor de generacion musical IA multi-modelo capaz de:

- mantener intencion creativa,
- reutilizar assets,
- producir canciones personalizadas,
- alternar entre local/pro,
- escalar a multiples providers,
- funcionar como pipeline musical inteligente.
