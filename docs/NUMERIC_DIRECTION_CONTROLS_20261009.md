# Controles numéricos de dirección — 2026-10-09

## Implementado

15 deslizadores reciben entrada numérica sincronizada: intensidad por sección, cuatro valores instrumentales, nivel de capa instrumental, cuatro valores vocales, nivel de capa vocal y cuatro controles MIDI legados. Cada entrada tiene su propia etiqueta. No se añade MIDI como requisito de generación.

Validación modular en UI y backend antes de persistir: rechaza valores fuera del rango, booleanos, texto y números no finitos; admite campos ausentes históricos. No recorta valores ni transforma propuestas en decisiones confirmadas.

La ayuda de sonido y voz explica escalas y ejemplos. Las descripciones de capas y voz declaran que son dirección retenida; no prometen ganancias DSP ni síntesis MIDI ejecutada por ACE-Step.

## Verificación agrupada

- 2 pruebas frontend aprobadas (rangos de fases y emoción).
- 1 prueba backend aprobada, con casos por familias y límites.
- Vite build aprobado después de separar etiquetas de controles.
- Playwright MCP sobre SQLite QA aislado: 24 instancias visibles verificadas (8 instrumental, 7 voz, 5 intensidades por sección y 4 MIDI legado). Entrada 31 sincronizada con cada deslizador; guardado HTTP 200 y recarga conservaron todos los valores.
- Vibrato 101: UI rechazó guardar con explicación; petición directa recibió HTTP 400. Consulta posterior mantuvo vibrato 31 y revisión `spec_rev_08ddc93c84f6`, sin mutación no autorizada.
- Se corrigieron etiquetas vacías de BPM/emoción introducidas por la modificación anterior. La primera comprobación de composición incluía erróneamente BPM entre los pares de deslizador; corregida la etiqueta y repetido el lote completo.
- Los avisos beforeunload interrumpieron dos intentos del harness; no se contaron como pruebas aprobadas. La comprobación final de rechazo usó consulta HTTP posterior para comparar revisión y valor persistido.
- Navegador y servidor QA cerrados. Datos de producción y modelos reales sin modificar.

S06-01 conserva D1/V0,5. Global D/V 90,5%. Sin inferencia ni nueva generación de audio.
