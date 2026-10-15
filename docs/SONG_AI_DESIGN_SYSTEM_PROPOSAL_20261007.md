# Song-AI: Design System y arquitectura visual

## Implementación incremental autorizada — 2026-10-08

El usuario autorizó continuar el bloque conjunto visual/Builder. Aplicados tokens oscuros semánticos y aliases en `frontend/src/design_system.css`, estilos de controles/estados/foco y shell de recorrido. El resto del diseño conserva estado pendiente de implementación/validación; no interpretar la etiqueta histórica de propuesta como bloqueo para esta implementación autorizada. Build/28 pruebas frontend aprobados; Playwright visual/contraste computado pendientes. No tema claro ni reescritura de pantallas completa.

## Decisiones vigentes del usuario — 2026-10-07

[Contrato de decisiones](SONG_BUILDER_APPROVED_DECISIONS_20261007.md): **sample previo opcional, sin bloqueo de generación completa**; instrumental como intención soportada con ejecución condicionada a validación; dirección por sección en MusicSpec aunque su traducción tenga límites; referencia audio opcional/avanzada, sin clonación; perfil ACE-Step automático por defecto y manual disponible para cualquiera. Esta decisión sustituye requisitos anteriores incompatibles en este documento. Las descripciones de pruebas/gates del árbol anterior son históricas; retirar el bloqueo de sample sigue pendiente de implementación y regresión. Mantener set válido, request confirmado y evaluación/aceptación de audio separadas.

Fecha: 2026-10-07. **Propuesta pendiente de revisión y aprobación; no implementada.** Complementa [UX/UI del Song Builder](SONG_BUILDER_UX_ARCHITECTURE_20261007.md). El [Design System vigente](DESIGN_SYSTEM.md) sigue describiendo la interfaz actual; esta propuesta sustituirá reglas concretas solo después de aprobación y migración. No reescribe frontend, instala dependencias ni cambia Vue, providers o Vulkan.

## A. Frontend Visual Audit

Inspección estática de `frontend/package.json`, `index.html`, `src/styles.css`, `src/app.js` y contratos. No es nueva auditoría de navegador, lector de pantalla ni prueba amateur. Inventario reproducible: [visual_audit.py](design-system/visual_audit.py); [resultado JSON](design-system/frontend_visual_inventory_20261007.json).

| Área | Estado observado | Conservar / corregir |
| --- | --- | --- |
| Stack | Vue 3.5, Vite 6, plugin Vue; HTML con templates y `app.js` | Mantener Vue/Vite. No React ni librería UI adicional por este diseño. |
| CSS | CSS global de 1758 líneas, 17 propiedades en `:root`, clases de panel, button, badge, grids y formularios | Evolucionar tokens y componentes en capas; preservar comportamiento. |
| Librerías UI/iconos | No declaradas en package.json; símbolos Unicode y entidades HTML en controles | Unificar SVG al migrar, sin emojis como iconografía final. |
| Tipografía | Stack Inter/system/Segoe UI; sin `@font-face` ni carga de fuente en HTML inspeccionado | Inter declarada no garantiza que esté instalada. Usar fuentes de sistema inicialmente. |
| Tema | Oscuro único; sin selector/light theme ni media query de tema en CSS inspeccionado | Dark prioritario; Light preparado en tokens, activación posterior. |
| Colores | 158 ocurrencias literales, 105 expresiones distintas, incluyendo rgba | Inventario por regex, no 105 colores perceptualmente distintos. Migrar a semántica, revisar composiciones con alpha. |
| Geometry/spacing | Radios 8/10/12/14/16/pill; gaps/paddings 5/6/7/10/14/18/22 entre otros | No toda diferencia es defecto; elegir escala y retirar valores accidentales. |
| Duplicación | Selectores repetidos como `.pipeline-step`, `.gemma-footer`, `#app`; varios son ajustes responsive | No borrar overrides legítimos. Consolidar tras revisar cascada y breakpoint. |
| Layout | Sidebar 300px, workspace, footer Gemma persistente; blur/sombras y algunos gradientes | Mantener contexto y asistencia Gemma; reducir tratamiento decorativo y espacio fijo excesivo en móvil. |
| Responsive | Media queries max-width 900px y 920px; columnas a una; footer con altura mínima 228px y padding inferior workspace 300px | Unificar breakpoints y verificar teclado móvil/zoom. No afirmar fallo visual sin renderizar. |
| Accesibilidad | `lang=es`, controles HTML, labels, algunos role alert/status y aria-live | Base reutilizable. Title/símbolos no sustituyen nombre accesible claro. |
| Focus/motion | Focus de inputs; sin regla `:focus-visible` ni `prefers-reduced-motion` en CSS inspeccionado; animación processingPulse | Definir foco uniforme y reducción de movimiento. La ausencia CSS no prueba ausencia de foco nativo. |
| Contraste actual | CTA #F8FAFC sobre #7C8CFF: **2,85:1** calculado | No pasa 4,5:1 de texto normal. Corregir pares completos, no solo tono de fondo. |

Reutilizables: labels y formularios nativos, side cards, modales de cambios, secciones de letra, badges/estados, reproductores/candidate comparison, alertas, jobs y guardas de respuestas tardías. La reutilización es de patrón/markup/comportamiento; actualmente no son todos componentes Vue aislados. No declarar un sistema de componentes ya terminado.

## B. Visual Direction

Un estudio musical oscuro, calmado y preciso: base grafito/navy, texto claro, violeta reservado a identidad/acción primaria y propuestas IA, cian controlado para generación/reproducción. Música mediante estructura, letra y waveform real; carácter cinematográfico mediante composición, aire y jerarquía, sin efectos permanentes.

Builder espacioso, una decisión por bloque y una CTA dominante; Studio algo más denso por reproducción/versión/selección. Superficies sólidas, bordes discretos, pocos niveles; sin gradientes de fondo global, blur generalizado ni sombras en cada tarjeta. Ilustraciones y texturas no son necesarias para explicar el flujo.

La IA acompaña dentro de la experiencia, no convierte cada pantalla en chat. Gemma conserva un compositor global acoplado abajo, plegable; tarjetas de sugerencias junto al campo expresan decisiones, no duplican la conversación. Esto preserva el contrato actual de asistencia en footer y evita dos entradas de chat competidoras. En móvil se abre como sheet accesible.

## C. Color System

Paleta propuesta, colores sólidos excepto overlay. Fuente documental completa: [tokens.proposal.json](design-system/tokens.proposal.json). **No se importa en frontend.** `secondary` y `accent` son aliases del mismo acento frío, no dos colores nuevos.

| Token semántico | Dark HEX | Light HEX, reserva | Uso |
| --- | --- | --- | --- |
| background | #10131B | #F4F6FB | Fondo; no negro puro. |
| surface | #181D28 | #FFFFFF | Cards/inputs base. |
| surface-secondary | #202735 | #EAF0F8 | Agrupación y sidebar. |
| surface-elevated | #293243 | #FFFFFF | Menú/dialog/popover. |
| primary | #9D83F7 | #6645B5 | CTA y selección principal. |
| primary-hover | #B29BFF | #56379F | Hover CTA. |
| primary-active | #8B6CE6 | #482B8A | Presionado CTA. |
| secondary / accent | #82D3E8 | #17647B | Generación, reproducción, acento escaso. |
| text-primary | #F1F4FA | #172131 | Contenido esencial. |
| text-secondary | #B6C0D2 | #46566D | Descripción y apoyo. |
| text-muted | #A0ACC1 | #53647B | Metadata legible, no bajar opacity. |
| text-on-primary | #10131B | #FFFFFF | Texto sobre primary/hover/active. |
| text-on-secondary | #10131B | #FFFFFF | Texto sobre botón frío sólido. |
| border | #343D4F | #CFD7E4 | Separador decorativo, no única delimitación de control. |
| border-strong | #7D8AA3 | #718197 | Límites operativos de inputs/sliders. |
| success | #79D9A0 | #216B40 | Estado positivo con icono/texto. |
| warning | #F4C66A | #775200 | Pendiente/advertencia con explicación. |
| error | #FF909C | #B5273E | Error recuperable y acción. |
| info | #90C6FF | #205EA1 | Información neutral, diferente de generación. |
| ai | #B79FFF | #6544AA | Label/icono de propuesta. |
| ai-surface | #251F36 | #F1EBFC | Área de sugerencia, uso localizado. |
| ai-border | #9980CF | #8066B2 | Diferenciación del bloque IA. |
| focus | #CEBEFF | #5D37A5 | Anillo teclado uniforme. |
| disabled-surface | #252C3A | #E5EAF2 | Control inactivo. |
| disabled-text | #A0ACC1 | #53647B | Texto inactivo legible. |
| disabled-border | #4B576D | #A3AFC0 | Límite de inactivo. |
| selected-surface | #2D2542 | #EEE7FC | Chips/timeline seleccionados. |
| generation-surface | #172E38 | #E7F3F7 | Progreso/reproducción. |
| overlay | #10131BCC | #17213199 | Scrim de modal; contraste depende del contenido compuesto. |

Semántica: USER neutral con «Tu decisión» cuando relevante; AI violeta + icono + «Sugerencia de Song-AI» o «Interpretación por revisar»; ACE generación frío + estado textual; success verde, warning ámbar, error rojo. AI no implica decisión aprobada. Una CTA violeta lleva verbo y no se interpreta como propuesta IA por su color.

### Contraste calculado

[Reporte de 66 pares](design-system/contrast_20261007.md): todos pasan el umbral asignado. Incluye texto primario/secundario/muted en cuatro superficies de cada tema; textos sobre CTA en default/hover/active; colores de estado, bordes operativos, foco, sugerencias, selección y generación. Comparación sin redondear; ratios mostrados con dos decimales. No es certificación global WCAG ni contraste de cada composición real.

Objetivo AA: texto normal ≥4,5:1; texto grande ≥3:1; límites/indicadores operativos evaluados ≥3:1. Separadores decorativos y controles deshabilitados tienen tratamiento distinto; no usar el borde decorativo como única señal de input. [WCAG texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [contraste no textual](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

No aplicar opacity al componente completo para disabled. Focus con anillo 2px y separación 2px evita apoyarlo directamente sobre fondo de botón violeta; validar capas, recortes y contraste adyacente renderizado. No combinar textos/colores arbitrarios por pertenecer a la paleta.

## D. Typography

Primera entrega: `"Segoe UI", system-ui, -apple-system, BlinkMacSystemFont, sans-serif`, adecuada al entorno Windows y sin petición externa. Inter solo si posteriormente se decide empaquetarla localmente y se verifican licencia/peso/carga. No añadir fuentes de red como dependencia del modo local.

| Token | Tamaño desktop / móvil | Weight | Line-height | Letter-spacing |
| --- | --- | --- | --- | --- |
| Display | 40 / 32px | 650, fallback 600 | 1,15 | -0,02em |
| H1 | 32 / 28px | 600 | 1,2 | -0,015em |
| H2 | 24 / 22px | 600 | 1,3 | -0,01em |
| H3 | 20 / 20px | 600 | 1,35 | 0 |
| Body | 16 / 16px | 400 | 1,6 | 0 |
| Body Small | 14 / 14px | 400 | 1,5 | 0 |
| Label | 14 / 14px | 600 | 1,4 | 0 |
| Caption | 13 / 13px | 400 | 1,5 | 0 |

Lyrics: 18px/1,75, ancho 60–68 caracteres, separación de secciones 24px; permitir zoom y tamaño de edición. Input móvil ≥16px. Navegación 14–16px semibold, Studio información esencial ≥14px. Reservar 13px a metadata secundaria, nunca letras ni estado de bloqueo esencial.

BPM/key/duración: números tabulares `font-variant-numeric: tabular-nums`, 20–24px para valor, unidad 14px. Monospace sistema `ui-monospace, Consolas, monospace` solo timestamps/diagnóstico, no toda la UI ni letra. No mayúsculas extendidas en párrafos; títulos de bloque con capitalización normal. Tokens en rem al implementar para respetar ajustes de usuario.

## E. Spacing + Geometry

Escala: 4, 8, 12, 16, 24, 32, 48, 64px. Aliases: xs=4, sm=8, md=16, lg=24, xl=32, 2xl=48, 3xl=64; 12 es intermedio para grupos compactos. Unidades CSS rem en la implementación.

| Contexto | Regla |
| --- | --- |
| Label/ayuda/control | 8px label→control; 8px control→ayuda; 16px entre campos relacionados. |
| Cards | Padding Builder 24px; móvil 16px; Studio 16px. |
| Secciones/página | 32px entre bloques, 48px entre familias; márgenes desktop 32px/tablet 24px/móvil 16px. |
| Panel musical | Gap interno 16px; grupos separados 24px. |
| Studio compacto | Gap 12px/16px sin reducir tamaño de texto o target táctil. |
| CTA | 12px entre acciones; separación 24px del contenido. |

Radios: sm=6px para tag/tooltip; md=10px input/button/menu; lg=16px card/dialog; pill solo chips compactos/progreso. Input/select/button altura mínima 44px, opción cómoda 48px; IconButton 44×44, ícono 20px; Studio desktop compacto 36px solo donde no afecte móvil, con objetivo de toque 44px en coarse pointer. Textarea mínimo 120px, autoexpansión controlada. No radio arbitrario por componente.

Sidebar 240px desktop; panel asistente/contexto 304–336px si espacio, pero compositor Gemma único abajo. Dialog máximo 560px para decisión y 800px para diff; altura máxima viewport menos 32px y scroll interno accesible. Popover máximo 320px, dropdown mínimo ancho del trigger; tooltip texto breve, no formularios.

Elevation: superficie/borde antes que sombra. E0 plano; E1 card separada por surface/border; E2 menú/dialog con sombra única `0 12px 32px rgba(0,0,0,.24)` y borde; E3 overlay para bloqueo modal. Opacidad solo scrim/sombra, no texto significativo. Z-index semántico: base0, sticky10, menu20, sheet30, dialog40, tooltip50; coordinar popovers dentro de dialogs para evitar superposición cruzada.

## F. Component Inventory

Estados de inventario: **R** patrón/markup reutilizable existente, **P** parcial o nativo sin contrato completo, **N** nuevo contrato/componente. R no significa componente aislado listo. Extraer cuando se reutilice; no otra implementación paralela de un botón.

| Generic | Estado | Evolución |
| --- | --- | --- |
| Button / IconButton | R | Variantes primary/secondary/ghost/destructive; iconos SVG, loading, labels. |
| Input / Textarea / Select | R | Field wrapper label/help/error/origen; IDs únicos, validación compartida. |
| Checkbox / Radio / Slider | R/P | Controles nativos existentes; field común y valor numérico de slider. |
| Chip / Tag | R/P | Selección con texto/estado accesible; Tag informativo no interactivo. |
| Card | R | Surface semántica, heading y contenido; no cada tarjeta botón. |
| Modal / Dialog | R/P | Cambios sin guardar y borrar: verificar foco/trap/restauración; un primitive modal común. |
| Popover / Tooltip | P/N | Titles actuales no bastan; apertura teclado/touch y Escape. |
| Tabs / Stepper | P | Nav botones y fases; distinguir navegación de páginas de tabs ARIA. |
| Toast | P/N | Mensajes actuales; feedback efímero accesible, sin sustituir errores inline. |
| Progress / Skeleton | P/N | Jobs tienen estados; progreso indeterminado cuando no hay medida real. |
| Dropdown / ContextMenu | P/N | Select nativo ya sirve para opciones; menú de acciones solo cuando necesario, con alternativa botón visible. |

| Song-AI specific | Estado | Responsabilidad |
| --- | --- | --- |
| GenreSelector / MoodSelector / InstrumentPicker / VocalSelector | P | Fases tienen controles, faltan choices humanos + Otro + propuesta/origen. |
| MusicParameterControl | P | BPM/key/etc existentes; reunir recomendado, editor, unidades y validación. |
| AISuggestionCard / AIInferenceIndicator | P | Propuestas/detalles existentes; unificar label, diff, acciones y procedencia. |
| SongSectionCard | R/P | Lyric cards existentes; añadir locks/estado/dirección, no duplicar texto. |
| SongTimeline | P | Plan/secciones y previews históricos; requiere timeline interactiva sin DAW. |
| LyricsEditor | R/P | Texto por sección y transformaciones; añadir origen discreto, alcance y locks. |
| PreflightItem | P | Ficha/readiness actuales; diferenciar confirmado, propuesta y bloqueado. |
| GenerationStatus | R/P | Estado/polling/cancel; nombres humanos y recuperación. |
| Waveform | P/N | Audio real reproducible existe; barras decorativas no constituyen waveform real. |
| VersionSelector | P/N | Candidatos/comparación disponibles; asociar versión/revisión/artefacto. |
| LockedField / SectionEnergyControl | N | Locks de edición; energía relativa de intención, no DSP del motor. |

No instalar suite UI completa: HTML nativo, Vue y CSS actuales son suficientes como base. Si foco/dialog/menu requieren librería accesible, justificar una incorporación puntual con tamaño, API y auditoría antes de aprobarla. Iconografía no requiere otra librería UI.

## G. Component States

Separar ejes: interacción, validación, procedencia y aprobación. Evitar un enum único con todas las combinaciones. Un valor USER puede estar locked y tener error; no ocultar el error por mostrar lock.

| Estado estándar | Tratamiento y comportamiento |
| --- | --- |
| Default | Surface, texto y borde del tipo de control; label siempre presente. |
| Hover | Surface-secondary o token hover; sin desplazamiento vertical ni halo general. |
| Focus | Anillo focus con offset; permanece visible sobre seleccionado/error. |
| Active | Primary-active o surface-elevated según variante; no indicador de aprobación. |
| Selected | Selected-surface, icono check y aria-pressed/checked cuando aplica. |
| Disabled | Tokens disabled y razón visible; no depender de tooltip en elemento no enfocable. |
| Loading | Label de acción + indicador, aria-busy, evitar solicitudes duplicadas; layout estable. |
| Error | Texto/icono error inline y enlace al campo; aria-invalid y describedby. |
| Success | Texto/icono success: «Guardado» o «Validado», especificar qué comprobación. |

| Estado Song-AI | Tratamiento |
| --- | --- |
| USER_DEFINED | Neutral; «Tu decisión» en detalles/cambio relevante. |
| AI_SUGGESTED | Card ai-surface + icono + «Sugerencia de Song-AI»; Aplicar al borrador / Modificar / Ignorar. |
| AI_INFERRED | Icono/label «Interpretación por revisar» y frase interpretada, no check de aprobado. |
| DEFAULT | «Valor inicial» en detalles; diferenciar de preferencia confirmada. |
| SYSTEM | «Configurado por el sistema» en detalles efectivos, no atribuir a usuario. |
| LOCKED | Icono lock + «Protegido contra cambios de IA»; desbloqueo explícito. No promete conservar identidad acústica. |
| NEEDS_REVIEW | Warning + «Revisar» y motivo/acción. |

Ejemplo: card violeta «Sugerencia de Song-AI · Tempo», **74 BPM**, explicación contextual, tres acciones con peso secundario; CTA de página sigue siendo Continuar/Guardar revisión. Aceptar pasa a borrador visible; guardar/confirmar sigue siendo otra decisión. Origen AI permanece aunque confirmado. No llenar cada campo/línea de badges permanentes: procedencia resumida y detalles bajo demanda.

## H. Builder Layout

Patrón **híbrido**: shell persistente + stepper compacto + workspace progresivo, con acceso a pasos ya visitados. Stepper puro ocultaría la revisión cruzada; sidebar con todas las fases históricas carga al amateur; workspace sin hitos dificulta ver pendientes. Todos usan el mismo shell y controles; el detalle se despliega por tarea, sin selector de experiencia.

Jerarquía estable: contexto de proyecto → paso/título humano → pregunta/decisión → valor/borrador/propuesta → pendiente → acción principal. Preguntas globales: dónde estoy, qué defino, qué está guardado, qué falta, qué recomienda IA, qué sigue. Una CTA de alto contraste por pantalla; actions menores ghost/outline. Confirmación destructiva puede tener su propia CTA dominante dentro del dialog.

| Etapa | Workspace | Contexto y CTA |
| --- | --- | --- |
| Idea | Pregunta y textarea amplio, resumen interpretado debajo | «Revisar mi idea»; sin formulario gigante. |
| Sonido | Cards/chips por familia y texto Otro; voz y evolución | Contexto musical lateral discreto; «Continuar». |
| Composición | Recomendación de tempo/key/compás/duración; editor desplegable | «Continuar» tras decisiones explícitas; no números inferidos aprobados por silencio. |
| Estructura + letra | Timeline arriba, sección activa/editor debajo | Acciones de sección secundarias; «Revisar canción». |
| Preflight | Ficha humana, tres piezas, checklist y límites | «Confirmar y generar canción» solo listo; prueba opcional secundaria; corregir bloqueo domina si falta algo. |
| Generate | Estado humano, cancelación y enlace detalles | No múltiples botones de nueva generación; tarea existente visible. |

```text
Proyectos    Proyecto activo                         Ayuda contextual | Ficha de la canción
             Idea ✓ · Sonido ● · Composición · Letra · Revisar
             Cómo quieres que suene                 Resumen de intención
             [Familia de controles]                 Qué está confirmado
             [Otra descripción…]                    Sugerencia contextual
             [Ajustes avanzados]                    [Aplicar/Modificar/Ignorar]
             Cambios pendientes     [Atrás]          [Continuar]
Gemma · pregunta contextual [compositor único plegable]
```

Ancho del contenido de decisiones 720–880px, shell máximo orientativo 1440px. Pantalla amplia permite contexto, no multiplicar cards para ocupar espacio. Footer Gemma plegado ocupa una barra corta; expandido debe descontar espacio del workspace sin ocultar CTA/caret.

## I. Timeline + Lyrics UX

Timeline de **estructura prevista**, no partitura ni alineación de audio. Bloques tipo Intro/Verso/Coro con label, duración aproximada y estado; selected usa contraste/icono además de color. No asignar color único a cada tipo: demasiados colores compiten con procedencia/estado. Repeticiones numeradas; energía como texto «suave/media/intensa» o indicador discreto con valor accesible, no cantidad física del motor.

Operaciones: seleccionar, añadir, eliminar con confirmación si hay contenido, reordenar, duplicar, bloquear, ver estado/duración y propuestas. Drag and drop tiene alternativa botones mover anterior/siguiente; duplicar crea ID nuevo con contenido referenciado/copiado según revisión, nunca hereda aprobación de audio. Locks no impiden seleccionar/escuchar. Scroll horizontal móvil + lista accesible; no scroll horizontal de toda la página.

Lyrics: título de sección y área de texto cómodos, contenido separado de «Dirección musical» e instrucciones estructurales. Line lock en menú/contexto accesible de línea, marcador de margen solo cuando relevante; origen de sección en cabecera, provenance detallada bajo demanda. Evitar badge en cada verso. Propuesta IA se muestra en diff, no reemplaza al escribir.

Regeneración parcial: seleccionar alcance y motivo → preview → diff → aplicar al borrador → guardar. Preservar líneas/requisitos bloqueados y mostrar errores de límites/contradicciones. Ctrl/Cmd shortcuts opcionales documentados, acciones siempre visibles. No permitir instrucciones a cantar por accidente: preview de serialización antes de plan.

## J. Preflight UX

Dos bloques: **Tu canción** (deseos y tres piezas) y **Preparación del motor** (capacidad/configuración). Items estilo, voz, tempo, tonalidad, compás, duración, estructura, letra e instrumentos muestran confirmado/propuesto/delegado resuelto/pendiente/conflicto; check solo identifica la validación realizada, no calidad de audio.

Advertencia: icono + «El puente y el coro final tienen intensidad similar»; sugerencia separada con propuesta para bajar instrumentos y sus acciones. Recomendación creativa no bloquea por mero gusto del modelo. Restricción obligatoria incompatible sí muestra bloqueo y ruta de corrección.

CTA inicial: **«Confirmar y generar canción»**; ofrecer «Generar prueba» como alternativa opcional. No exigir sample previo. Si V1 es audio de duración completa, sigue siendo candidato por revisar. Esto adapta el ejemplo «Generar canción» sin eludir el gate del proyecto.

Resumen en lenguaje humano, letra exacta y defaults visibles; caption/request solo en detalles avanzados. No JSON obligatorio para usuario normal. Al guardar nueva revisión creativa se indica que plan/sample anteriores necesitan nueva revisión.

## K. Generation UX

| Estado visible | Estado interno/evidencia | Mensaje y acción |
| --- | --- | --- |
| Preparando tu canción | Validar/compilar/persistir spec y request | «Estamos comprobando tu configuración»; corregir si inválida. |
| Preparando el motor | Liberar LLM, memoria y cargar ACE | «Preparando la generación»; detalles diagnósticos opcionales. |
| Generando música | Task real en ejecución | Progreso indeterminado si no hay medida real; cancelar si backend lo permite. |
| Finalizando audio | Integridad/registro/export | «Comprobando el archivo generado». |
| Prueba disponible | Artefacto verificado, pendiente de escucha | «Escuchar en Studio». No label calidad final. |
| Falló/cancelada/interrumpida | Estado persistido correspondiente | Explicar y reintentar con inputs conservados; sin fallback creativo silencioso. |

No mostrar porcentajes ficticios ni temporizador como estimación fiable. Live region polite anuncia transiciones, no cada polling/token. Cancelar solicitado distinto de cancelación confirmada; no mostrar task cancelada antes de backend. Asistencia puede aparecer pausada durante audio, con motivo humano y reanudación disponible después de liberar ACE, sin prometer ambos modelos residentes.

### Estados globales y recuperación

| Estado | Mensaje/acción y representación |
| --- | --- |
| Empty | «Aún no tienes canciones» + Crear canción; no KPIs vacíos. |
| Loading / Skeleton | «Cargando proyecto» y skeleton de layout estático con reduced motion; no sustituir valores confirmados por placeholders al refrescar. |
| Success | «Revisión guardada» / «Archivo disponible», según evidencia; toast breve y estado persistente relevante. |
| Error | Qué falló, datos conservados y acción concreta; resumen inline, detalle técnico plegable. |
| Offline | «No hay conexión con la aplicación» cuando falla conexión; no asumir que ausencia de Internet impide ejecución local. Mantener borrador, reintentar conexión. |
| Backend unavailable | «No podemos conectar con Song-AI» + Reintentar y acceso a instrucciones de inicio; no simular guardado. |
| AI assistant unavailable | «La asistencia no está disponible» + Reintentar/editar manualmente; identificación explícita de fallback/mock. |
| ACE-Step unavailable | Motivo humano y «Revisar preparación del motor»; definir canción sigue disponible, generar bloqueado. |
| Generation queued | «Tu prueba está en espera» y task recuperable; no tiempo estimado inventado. |
| Generation running | Estado actual y cancelar si disponible; bloquear duplicación, permitir navegar recuperando task. |
| Generation failed | «La generación no terminó; tu configuración sigue guardada» + Reintentar/revisar bloqueo. |
| Generation cancelled | Confirmación del backend + volver a configuración o nueva prueba. |
| Unsaved changes | Indicador persistente y Guardar/Descartar/Seguir editando ante salida; no toast único. |
| Interrupted / Recovery | Recuperar estado de SQLite/task; explicar si requiere reiniciar ejecución, no fingir continuidad del proceso. |

Error importante usa alert; progreso/status usa polite; toast no roba foco. El estado de conexión no sustituye el estado creativo: spec guardada y motor no disponible pueden coexistir.

## L. Studio Layout

Studio mínimo centrado en audio y versiones, con densidad moderada:

```text
Proyecto / Studio            V1 candidato      [Versiones] [Ajustes]
[Play/Pause] 00:48 / 03:30    waveform real     [Selección de intervalo]
Estructura prevista: Intro | Verso | Coro | Puente | Coro final
Letra de sección             Qué quieres cambiar
Contenido y dirección        [Más intenso; conserva esta frase…]
Locks y origen discreto      [Proponer ajuste]
                             Diff · límites · operación compatible
[Comparar A/B]                [Guardar revisión y generar variante]
Sample pendiente/vigente     Final y descarga según evidencia
```

Waveform calculada del artefacto real, distinta de decoración. Tiempos planeados no cortan automáticamente regiones observadas: intervalo manual o alineación verificada. Feedback vinculado a versión/intervalo; operación compatible elegida después de diff/validación, no por slider inventado. Navegación a versiones/ajustes no reinicia Builder.

No mixer multipista, piano roll ni banco de plugins. «Menos guitarra» es intención de cambio, no un fader de stem inexistente. «Conserva voz» es requisito con límite explícito de identidad. V1/V2 mantiene padre, spec/request y evidencia; comparación no arranca reproductores simultáneos.

## M. Responsive Strategy

Breakpoints propuestos basados en contenido: móvil <768px; tablet 768–1199px; desktop ≥1200px. No trasladar automáticamente todas las reglas 900/920; comparar pantallas reales antes de reemplazar.

| Entorno | Adaptación |
| --- | --- |
| Desktop | Sidebar 240px, workspace + contexto opcional, compositor Gemma plegable; Studio waveform/lyrics/feedback visibles según ancho. |
| Tablet | Sidebar drawer o rail corto; contexto colapsable; Studio dos paneles apilables, orientación no obligatoria. |
| Mobile | Una columna, paso actual + progreso compacto; bottom sheet de avanzados/ayuda; timeline horizontal confinada; lyric editor ancho completo. |

Sticky actions solo donde ayudan, con padding de safe-area y espacio reservado; nunca cubrir campo/foco cuando aparece teclado. Compositor Gemma móvil sheet con trap de foco si modal y cierre accesible; feedback de Studio visible junto a selección, sin segunda conversación global.

Móvil debe permitir idea, parámetros básicos/avanzados bajo demanda, letra, escucha, feedback y A/B; versiones como lista/sheet, no dos waveform minúsculas. Inputs mínimo16px, targets44px, captions13px solo metadata. A 320px no overflow general; a 200% zoom y reflow 400% verificar contenido y foco, con excepción justificada solo para representación musical bidimensional que conserve alternativa.

## N. Accessibility

Objetivo WCAG 2.2 AA, pendiente de auditoría de producto. Contraste texto 4,5:1 y operativo 3:1 según C; foco visible/no oculto; controles por teclado; HTML semántico antes de ARIA. Requisito de tamaño mínimo WCAG 2.5.8 es 24×24 CSSpx con condiciones/excepciones; este diseño propone **44×44px** como objetivo táctil de producto, sin atribuirlo al mínimo AA. [W3C Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

Requisitos de aceptación:

- Skip link al workspace, landmarks y encabezados sin saltos arbitrarios; breadcrumb/proyecto/step accesibles.
- Labels permanentes y ayuda/error en describedby; aria-invalid ante error; placeholders no sustituyen label.
- IconButton con nombre de acción; SVG decorativo aria-hidden. Tooltips también por teclado y cierre Escape; información crítica inline.
- Dialog/sheet modal: foco inicial adecuado, trap, restaurar trigger y Escape cuando no destruya acción; backdrop no es único cierre.
- Navegación de pasos como enlaces/botones con estado actual; roles tablist solo si se implementa patrón de tabs completo.
- Timeline selectable keyboard, reordenación sin drag; slider con teclado/input; waveform con timestamps/intervalo editables y control de reproducción nativo/accesible.
- Nunca autoplay; reproducción y pausa inequívocas; estados/límites legibles sin color.
- Errores vinculados al campo y resumen navegable; anuncios limitados a cambios significativos, no polling continuo.
- Reduced motion y forced-colors: respetar preferencias y bordes/foco del sistema; no ocultar outline sin alternativa.

Problemas estáticos actuales: CTA con contraste insuficiente, ausencia de estrategia focus-visible/reduced-motion, iconos simbólicos/title que necesitan nombres consistentes y footer móvil voluminoso que requiere revisión de foco/teclado. No se certificó fallo de foco/modal/target ni conformidad global sin browser y lector de pantalla.

Motion: 120ms feedback hover/selection, 180ms expansión breve, 220ms panel/sheet; easing `cubic-bezier(.2,0,0,1)`. Sin parallax, glow pulsante permanente, salto en hover ni reproducción automática decorativa. Con prefers-reduced-motion: cambios instantáneos, skeleton estático e indicador textual de tarea; sin transiciones de desplazamiento. Animación nunca oculta retraso ni inventa progreso.

Iconografía: una familia de SVG outline, stroke 1,75–2, viewBox24, tamaños20/24, esquinas coherentes. Catálogo conceptual: sparkles (IA), play, pause, lock, unlock, rotate-cw (regenerar), pencil, plus, trash, copy, triangle-alert, circle-check, layers (versiones), sliders (ajustes). Propuesta de SVG locales reutilizables; elegir proveedor/licencia si se adopta paquete después, sin instalarlo aquí. Texto acompaña acciones poco conocidas; no emojis finales ni mezcla filled/outline accidental.

Navegación: **Proyectos → Crear canción → Builder → Prueba → Studio**. Dentro del proyecto: Studio, editar intención/configuración, versiones y ajustes. La librería actual evoluciona a Proyectos; fases históricas avanzadas quedan fuera del recorrido principal, conservadas por compatibilidad. Cualquier salida con borrador ofrece Guardar/Descartar/Seguir editando; una task en curso se recupera al volver, no se crea otra por navegar.

## O. Design Tokens

Estructura propuesta compatible con CSS actual: tokens base → semánticos por tema → componentes. Colores viven en tema; Button/Input/AI card consumen semánticos. Spacing/radius/type/motion compartidos; densidad modifica gap/padding, no color ni autoridad. `tokens.proposal.json` es artefacto de diseño, no una configuración activa duplicada.

Ejemplo conceptual de la migración futura, **no aplicado**:

```css
:root, [data-theme="dark"] {
  --color-background: #10131B;
  --color-surface: #181D28;
  --color-primary: #9D83F7;
  --color-text-on-primary: #10131B;
  --space-md: 1rem;
  --radius-md: .625rem;
  --motion-normal: 180ms;
}
.button-primary {
  background: var(--color-primary);
  color: var(--color-text-on-primary);
  border-radius: var(--radius-md);
}
```

Mapa temporal de compatibilidad: `--bg→--color-background`, `--panel→--color-surface`, `--text→--color-text-primary`, `--muted→--color-text-secondary`, `--accent→--color-primary`, `--ready→--color-success`, `--dirty/--outdated→--color-warning`, `--processing→--color-secondary`, `--error→--color-error`. Cada alias se retira cuando sus consumidores migran; no copiar valores hex en cada selector. Separar processing de info.

Ficheros propuestos al implementar: `src/styles/tokens.css`, `base.css`, `components.css`, `builder.css`, `studio.css`; `styles.css` mantiene imports compatibles. Vue primitives solo cuando compartan estado/semántica, no un componente por div. Evitar capasCSS/bibliotecas adicionales sin necesidad demostrada. Light usa el mismo conjunto de claves con `data-theme=light`; preferencia de usuario local persistida, default oscuro. No activar Light hasta revisar todas las pantallas; hoy no existe toggle.

## P. Migration Plan

| Fase / sprint relacionado | Trabajo tras aprobación | Evidencia para aceptar |
| --- | --- | --- |
| DS0 / S00 | Revisar propuesta/paleta/layout/footer/labels; contrastar browser a 320/768/1200/1440px | Aprobación visual y lista de diferencias; sin cierre por documento. |
| DS1 / S06A | Tokens y aliases, contraste CTA, type/spacing/focus/reduced-motion; una superficie piloto | CSS sin regressions de datos; contraste calculado y computado; screenshots antes/después. |
| DS2 / S06A–S06B | Primitives reutilizables y estados; Builder shell/pasos; mantener callbacks/revision guards | Teclado y móviles; una CTA; valores/propuestas no autopersistidos. |
| DS3 / S06B | Timeline/letra, locks/provenance/diffs | Reorder sin drag, editor legible, locks efectivos; no nuevas capacidades ficticias. |
| DS4 / S06C | Preflight/generación humana, detalles diagnósticos aparte | Contraste/announcements, cancelación real, persistencia/request antes del handoff. |
| DS5 / S06D–S06E | Studio/versiones/sample/export adaptados | Waveform real, intervalos adecuados, gate final y archivos verificados. |
| DS6 / S10 | Responsive/lector de pantalla/forced colors/reduced motion y piloto amateur | Evidencia por pantalla/tarea; registrar pendientes exactos. Light solo si aprobado y validado. |

No cambiar pantallas ajenas de una vez. Migrar una sección vertical usando clases/aliases compatibles, preservar endpoints/casos de uso, eliminar estilos muertos solo después de demostrar cero consumidores. No tests de estilos que repitan valores: verificar contrastes/flujo/foco/reflow y persistencia real. El sistema no cambia recursos/modelos ni arquitectura de generación.

## Q. Open Decisions

| Decisión para revisar | Propuesta |
| --- | --- |
| Paleta principal | Aprobar violeta con texto oscuro Dark, base grafito/navy y acento frío escaso. |
| Dark/Light | Dark primera entrega; tokens Light listos en diseño, toggle posterior. |
| Fuente | Sistema inicialmente; Inter local solo con motivo/packaging aprobado. |
| Iconos | SVG outline único; elegir paquete/licencia o conjunto local antes de implementar. |
| Compositor Gemma | Footer único plegable, sheet móvil; sugerencias contextuales fuera del chat. |
| CTA inicial | «Confirmar y generar canción»; prueba opcional secundaria y aceptación del resultado separada. |
| Densidad | Builder cómoda/Studio moderada; validar con sesiones de letra largas y móvil. |
| Timeline/audio | Estructura prevista separada de intervalos observados; selección manual inicial. |
| Aprobación del conjunto | Revisar este diseño y UX A–M antes de autorizar implementación; piloto amateur sigue necesario después. |

Estado de entrega: documento A–Q, inventario estático, paleta Dark/Light y reporte numérico de contraste. No aplicación visual nueva, inferencia/audio, screenshots de propuesta ni conformidad WCAG global acreditados. Los wireframes son conceptuales; construir un mockup visual navegable requerirá una siguiente tarea autorizada.
