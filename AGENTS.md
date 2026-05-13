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
