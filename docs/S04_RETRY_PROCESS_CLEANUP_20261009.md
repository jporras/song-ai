# S04 — Reintentos y limpieza del proceso de audio

## Entrega

La solicitud de candidato acepta `request_id` opcional. Misma canción, identidad y parámetros devuelven el job SQLite original antes de repetir preflight o dispatch, incluso después de reabrir el almacenamiento y si el plan dejó de ser el actual: recuperar ese job es una consulta del intento previo, no una generación nueva. Reutilizar la identidad con parámetros distintos se rechaza. Nueva acción explícita o proyecto diferente tiene otra identidad. Se conserva compatibilidad para clientes sin `request_id`.

La UI mantiene esa identidad durante un reintento tras error de red en la misma sesión. Cambiar canción/plan crea otra; una respuesta recibida libera la identidad para una acción posterior. El identificador queda persistido en el payload del job y el router lo acepta en `candidate.start`. Recargar la UI conserva jobs en SQLite, pero no recupera la identidad pendiente en memoria del navegador; no se anuncia almacenamiento de esta identidad en sessionStorage.

Los IDs de jobs con request_id se derivan de canción/identidad mediante SHA256 y la clave primaria SQLite impide insertar el mismo ID dos veces. La instancia de jobs mantiene su lock y exclusividad existentes. No se anuncia soporte de múltiples workers/distribución: la coordinación global entre procesos diferentes y recuperación física de workers continúa pendiente.

El runner termina y espera al proceso hijo desde `finally`, antes de restaurar modelos de texto. Esto también cubre fallos de monitor/persistencia mientras el hijo sigue ejecutándose, que antes podían dejarlo vivo. Cancelación y timeout comparten la limpieza; no se publica un WAV parcial como candidato terminado.

## Verificación agrupada

38 pruebas backend aprobadas: jobs, request replay/reapertura, identidad conflictiva/proyecto distinto, validación de request, router, ejecución, recursos, candidatos y comandos locales. Dos escenarios dentro del test de limpieza arrancan procesos Python reales desechables: cancelación y fallo del monitor; ambos verifican que el hijo murió antes de restaurar modelos. Los procesos no cargan ACE-Step, no generan música y no usan GPU.

55 pruebas frontend aprobadas; build Vite aprobado. No se realizó una nueva corrida ACE-Step ni ensayo de cancelación con pesos cargados. S04-01 ya tenía D/V=1: se fortalece su evidencia sin sumar de nuevo. S04-02/S04-03 conservan verificación parcial porque la cancelación/recuperación del motor y liberación física de memoria siguen pendientes.

## Piloto preparado

Entregado `AMATEUR_PILOT_PROTOCOL.md`: preparación QA, guion en lenguaje común, sample opcional, registro de observaciones, escenarios y criterios de cierre. S10-08 desarrollo 0→0.5; ejecución con participantes, correcciones y aceptación continúan pendientes. Preparar el protocolo no acredita usabilidad.
