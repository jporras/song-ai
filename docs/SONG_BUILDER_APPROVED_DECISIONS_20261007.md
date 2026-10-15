# Decisiones de alcance del Song Builder — 2026-10-07

Decisiones explícitas del usuario. Sustituyen reglas anteriores incompatibles; no constituyen aprobación de implementación de todo el rediseño ni prueba de capacidades.

| Decisión | Definición vigente | Consecuencia |
| --- | --- | --- |
| Sample previo | Opcional, no obligatorio | No bloquear generación completa por ausencia, antigüedad o falta de aprobación de sample. Mantener revisión de spec/request y set válido. Si existe sample, preservar evaluación/vigencia y no usar evidencia antigua para afirmar calidad. |
| Instrumental | Intención soportada; ejecución condicionada a validación | Permitir conservar «sin canto» en MusicSpec, sin prometer cero voz hasta demostrar integración y audio. No sustituir el deseo por voz predeterminada. |
| Dirección por sección | Parte de MusicSpec aunque ACE-Step no la ejecute toda directamente | Persistir dirección, prioridad y procedencia; mapear lo transmisible y explicar lo aproximado/no conectado. No eliminar la intención ni inventar parámetros. |
| Referencia audio | Opcional y avanzada | No requisito de creación ni clonación de voz; mostrar cuando capacidad/ruta aplicables y verificar artefacto. Fuente de edición requerida por algunos modos es un concepto distinto. |
| Perfil ACE-Step | Automático por defecto; edición manual disponible para cualquiera | Resolver desde capacidades observadas, hardware y política versionada; registrar valores efectivos/procedencia SYSTEM. No cargar esa decisión al amateur; no reemplazar ajustes USER explícitos ni hacer fallback creativo oculto. |

## Recorrido y aceptación actualizados

### Interfaz común asistida — decisión reafirmada

Todos usan los mismos controles y MusicSpec. Se retira la clasificación por experiencia del diseño: no hay selector principiante/profesional ni formularios distintos por conocimiento musical. Los controles musicales aplicables se muestran en su etapa; ajustes adicionales pueden desplegarse por tarea y relevancia, siempre disponibles para cualquiera. El perfil ACE-Step sigue automático por defecto y permite ajuste manual con ayuda.

Cada control ofrece nombre claro, unidad/rango cuando corresponda y ayuda con **significado, efecto y ejemplo**. Tooltip accesible por hover y foco; botón «Ayuda» permite abrir la misma explicación por toque/teclado. Información imprescindible, errores y límites de capacidad permanecen visibles, no exclusivamente dentro de tooltip. Gemma explica y recomienda; no sustituye ni guarda decisiones USER sin revisión explícita.

Criterios S06A–S06B/S10:

- Dos personas con diferente experiencia acceden a los mismos campos/capacidades, sin elegir un nivel.
- BPM, tonalidad, compás, duración y controles de ejecución aplicables tienen ayuda accesible; una explicación diferencia valor objetivo de garantía acústica.
- Mostrar ayuda o ajustes adicionales no modifica valores ni revisión. Propuestas IA siguen siendo propuestas hasta aplicación/guardado explícitos.
- Ayuda funciona con teclado y móvil, admite cierre y no bloquea edición. No depende exclusivamente de hover.
- Mantener preguntas contextualizadas y una CTA principal; mostrar controles por etapa no exige presentar todo el catálogo simultáneamente.

Esta decisión modifica contratos de interacción, no habilita capacidades ausentes. Implementación del Builder/ayudas sigue pendiente según las fases del diseño; la corrección documental no acredita validación amateur.

Idea → sonido/composición/estructura/letra → tres assets y set válido → MusicSpec/request confirmados → **generar canción candidata completa**, o elegir **prueba opcional** → Studio/escucha/ajustes → aceptación y descarga verificada. Generar un archivo no acredita calidad ni aceptación final.

Pruebas necesarias para migrar la política:

- Con set y revisión/request válidos, la generación completa puede comenzar sin sample.
- Un sample ausente, antiguo, mock o no aprobado no constituye por sí solo bloqueo de generación completa; tampoco acredita calidad del resultado.
- Inputs inválidos, revisión no confirmada, set incompleto o falta de capacidades/recursos siguen bloqueando según contrato.
- Si el usuario elige sample, persisten sus vínculos/evaluaciones y cambios invalidan su evidencia, sin convertirlo en gate obligatorio.
- Perfil automático queda registrado antes de ejecución; USER con ayuda contextual se conserva y se valida conforme a AC-ACE-USER-01. Una selección incompatible se explica, no se corrige silenciosamente.

## Brecha de implementación

El árbol actual conserva SampleGate y rutas/consejos que exigen sample. **La nueva política todavía requiere implementación y regresión en UI/backend/builders/assistant.** S06C/S06D incorporan retirar ese requisito de todas las rutas completas; mantener verificaciones de set, request, integridad y evidencia del audio. No borrar registros de samples ni módulos históricos.

Esta decisión elimina la obligatoriedad del sample previo; no elimina escucha/aceptación del resultado ni autoriza afirmar fidelidad acústica por una task terminada. AC-ACE-USER-01 permanece vigente.
