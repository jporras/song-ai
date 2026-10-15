# Corrección: protección de revisión al abrir propuesta — 2026-10-09

La UI comprobaba inputs_current y task_id al incorporar una propuesta en los controles, pero inputs_current es una observación de la última lectura del backend. Una revisión de ficha posterior podía dejar una propuesta almacenada en memoria vigente solo en apariencia.

openCandidateCorrectionConfiguration ahora exige que spec_revision_id de la propuesta coincida con revision_id de la ficha observada antes de abrir el borrador. Si difieren, explica que se debe actualizar la revisión de escucha y preparar una propuesta vigente. No guarda, ejecuta ni confirma nada. La validación del backend sigue siendo necesaria al guardar/generar.

## Verificación agrupada

- 3 pruebas frontend aprobadas: aplicación sin modificar MusicSpec, copia independiente de pistas, rechazo de revisión distinta/task distinta/propuesta no vigente/borrador ya abierto y URL de descarga vinculada al mismo proyecto/task/checksum.
- 22 pruebas backend aprobadas: corrección, revisión técnica y opinión de escucha; incluye rechazos, recuperación SQLite y procedencia. Providers/dobles de prueba; no inferencia.
- Build Vite aprobado.

Este lote cubre componentes de S06-06/S10-07. El recorrido completo mediante controles visibles con nueva confirmación/plan/job simulado/descarga sigue pendiente; no se presenta como E2E cerrado. Audio real permanece en el último bloque. Estados y global D/V89,9% sin cambios. Sin commit/push ni modificaciones a canciones de producción.
