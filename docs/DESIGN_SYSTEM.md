# Song-AI Design System

## Filosofia

Song-AI debe sentirse como un estudio musical cinematografico asistido por IA: oscuro, moderno, calmado y profesional. No debe parecer dashboard administrativo, CRUD, chatbot generico ni panel gamer.

## Layout Global

- Sidebar persistente para navegacion, proyecto activo y fases.
- Workspace central para la fase actual.
- Footer persistente para Gemma. Gemma no debe aparecer como tarjeta dentro de las fases.
- Production concentra ejecucion, diagnostico, actividad y exportables.

## Paleta

- Fondo principal: `#0F1115`
- Paneles: `#171A21`
- Sidebar: `#0B0D12`
- Bordes: `#2A2F3A`
- Texto principal: `#F3F5F7`
- Texto secundario: `#A5ADBA`
- Accent: `#7C8CFF`

Estados:

- Ready: `#4ADE80`
- Dirty: `#FACC15`
- Outdated: `#FB923C`
- Processing: `#60A5FA`
- Error: `#F87171`

## Componentes

### Fases Laterales

La sidebar muestra el estado compacto de fases guardadas. Debe ser rapida de leer y no competir con Production.

### Procesos De Production

Los procesos no son fases editables; son ejecuciones. Deben mostrarse como lista ordenada, no como mosaico de tarjetas densas.

Cada proceso debe mostrar:

- icono de estado,
- nombre humano,
- resumen corto,
- badge de estado,
- accion disponible.

No mostrar codigos tecnicos como texto principal. Si se necesitan, deben ir en tooltip, diagnostico o logs.

### Actividad

Actividad, logs, recursos y diagnosticos solo viven en Production. En fases creativas el usuario guarda configuracion, no ejecuta procesos pesados.

## Reglas UX

- Accion secundaria a la izquierda, accion principal a la derecha.
- Guardar configuracion no debe generar audio ni cargar modelos pesados.
- Cambiar fases no debe regenerar dependencias automaticamente.
- El usuario habla siempre con Gemma; Qwen es interno.
- El diseño debe priorizar claridad musical sobre informacion tecnica.
