# S10-08 — Protocolo de piloto con usuarios amateur

Estado: preparación técnica entregada; piloto sin ejecutar. Desde la reclasificación del 2026-10-15, S10-08 mide preparación en desarrollo/verificación y realización del piloto en aceptación. Este protocolo no acredita usabilidad ni aceptación. Las reglas del Builder y los criterios de sprint vigentes prevalecen sobre recomendaciones metodológicas de este documento.

## Preparación

- Usar una copia QA con SQLite y archivos propios; conservar Isabella y Alma de producción intactas. Registrar commit o diff/build, fecha, URL y configuración observada.
- Proponer inicialmente tres participantes sin experiencia de producción musical. Registrar si han usado otras apps musicales; ampliar si aparecen problemas distintos. No presentar tres personas como validación universal.
- Mantener la misma interfaz para todos, sin selector principiante/profesional. Tooltips y controles adicionales deben estar disponibles.
- Explicar: las propuestas IA se revisan antes de guardar; los mocks son ejemplos; la generación de audio puede tardar. No enseñar dónde está cada control antes de que la persona intente encontrarlo.
- Preparar recursos para generación exclusiva de ACE-Step. Comprobar disponibilidad al inicio; un fallo de entorno se registra por separado de un defecto de experiencia.
- Una persona observa y anota; ayuda solo si hay un bloqueo. Registrar qué explicación necesitó el participante. No enviar invitaciones ni datos de participantes automáticamente.

## Guion para el participante

1. **Tu idea:** «Crea una canción para una persona o una ocasión que elijas. Explica qué quieres que se sienta al escucharla». Puede elegir voz generada o intención instrumental según capacidades verificadas; no prometer ausencia absoluta de voz sin comprobar el resultado.
2. **Define el sonido:** «Revisa lo que propone la aplicación. Encuentra una opción que no conozcas y usa su ayuda. Cambia una decisión musical que te interese». No exigir términos técnicos ni una cifra concreta. Anotar si comprende el efecto y la diferencia entre sugerencia y guardado.
3. **Prepara las piezas:** «Revisa instrumental, melodía vocal y letra. Conserva algo que te guste y pide cambiar otra parte». Verificar que reconoce las tres piezas y que las propuestas no sustituyen silenciosamente sus decisiones.
4. **Revisión:** «Confirma lo que quieres generar. Decide si quieres escuchar un fragmento primero o crear la canción completa». Ofrecer ambas opciones; no dirigirlo a sample obligatorio.
5. **Generación y resultado:** «Inicia la generación. Mientras esperas, explica qué está ocurriendo y qué podrías hacer. Cuando termine, escucha el resultado, registra tu opinión y encuentra los archivos disponibles». Si no existen exportables verificados, registrar el bloqueo; el observador no simula una descarga final ni aceptación.
6. **Persistencia:** «Recarga la aplicación y vuelve a tu proyecto. Encuentra tu configuración y la opinión que guardaste». Comprobar revisión, decisiones y artefacto correspondiente en SQLite.

El resultado debe evaluarse por escucha completa del participante; distinguir su aceptación de las verificaciones objetivas. Si detecta un defecto y decide aceptar con mejoras posteriores, registrar esa decisión y el pendiente, como ocurrió con Isabella.

## Escenarios complementarios

Después del recorrido principal, usar un proyecto QA separado para comprobar: descartar una propuesta, cambiar de proyecto con cambios pendientes, una revisión antigua en otra pestaña y cancelación de generación. No ejecutar simultáneamente dos modelos o trabajos de audio para provocar un error. Registrar qué escenario se ejecutó realmente; no atribuir los restantes al participante.

## Registro de observación

Usar identificadores anónimos; guardar la referencia del proyecto QA sin recopilar nombres u otros datos personales innecesarios. Las decisiones musicales y aprobaciones siguen en SQLite; esta ficha registra investigación de experiencia.

| Campo | Valor a registrar |
| --- | --- |
| Sesión/participante | Identificador anónimo y experiencia previa |
| Entorno | Fecha, build/diff, URL QA, hardware/modelos utilizados |
| Paso | Número del guion y pantalla |
| Acción e intención | Qué intentó hacer, con sus palabras |
| Resultado observado | Completado sin ayuda / con ayuda / bloqueado / no ejecutado |
| Tiempo | Inicio/fin; separar espera de inferencia de interacción |
| Ayuda necesaria | Tooltip, chat, observador; explicación concreta |
| Confusión/error | Texto o control y efecto visible |
| Evidencia | Captura autorizada, evento/task/revisión/checksum; evitar datos personales |
| Aceptación | Decisión explícita y observaciones, sin interpretar el silencio |
| Hallazgo | Problema reproducible, impacto, tarea de sprint y estado |

## Cierre del piloto

- Consolidar por paso qué funcionó, qué necesitó ayuda y qué bloqueó; publicar también casos no ejecutados. No dar porcentajes generales sin denominador.
- Priorizar pérdida de intención/datos, aprobación no autorizada, bloqueo de generación por sample y artefactos incorrectos como problemas de cierre. Separar problemas de comprensión de defectos de audio o recursos.
- Corregir hallazgos y repetir solo los pasos afectados, conservando evidencia anterior y nueva.
- El usuario responsable revisa los resultados y decide si el recorrido cumple la experiencia prevista. El estado técnico verificado de preparación S10-08 no significa piloto realizado; su aceptación permanece abierta hasta esa decisión.
