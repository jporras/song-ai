# Cómo generar una canción desde Production

Para el proyecto Alma observado el 2026-10-15, la revisión activa `spec_rev_c31ecd862373` estaba pendiente de confirmación y no existía un plan ACE-Step aprobado. Los WAV/MP3/FLAC de la lista pertenecen al historial; no prueban que los cambios actuales estén generados. La captura mostraba 96 % de memoria utilizada, así que la comprobación de recursos debe resolverse antes de ejecutar ACE-Step.

Recorrido visible:

1. Abre **Production** y usa **Siguiente paso** para ir a la ficha. Revisa la voz, instrumental, melodía, letra y demás decisiones. Si editas algo, pulsa **Guardar para revisar**. Pulsa **Confirmar esta configuración** solo cuando represente tu canción. La propuesta técnica de Qwen no se guarda ni se aprueba automáticamente.
2. En **Plan de creación para revisar**, pulsa **Preparar un nuevo plan**, comprueba la letra que se cantará y pulsa **Preparar para revisar**. Lee el plan, marca que revisaste la letra y pulsa **Aprobar este plan y letra**.
3. En la tarjeta **Generar canción**, pulsa **Generar canción completa**. El backend vuelve a validar set, revisión, plan, letra, archivos y recursos. El sample previo es opcional. Si recursos muestra bloqueo, sigue la recomendación concreta antes de repetir; no cierres procesos ajenos ni reduzcas el gate de memoria para forzar audio.
4. Cuando termine, escucha el resultado en **Studio**. En **Preparar descargas**, exporta y descarga los archivos finales verificados. La generación y la integridad de archivos no equivalen a aceptación musical.

La interfaz anterior mostraba una tarjeta de generación deshabilitada por el orden de fases heredadas aunque el flujo ACE-Step usa ficha y plan vigentes. Ahora esa tarjeta se habilita con esos dos requisitos para `text2music`, y una indicación superior lleva al siguiente control. Las decisiones creativas siguen siendo del usuario. No se confirmó la ficha de Alma ni se generó audio durante esta corrección.
