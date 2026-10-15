"""Explanations of connected inputs; no claim of runtime availability."""
_HELP = {
    'generation_api': ('Ruta que entrega el plan al motor.', 'Directa usa el handler; el LM opcional requiere pesos y memoria adicionales.', 'Empieza con Directa y revisa disponibilidad antes de probar el LM.'),
    'lm_model_path': ('Modelo musical interno de ACE-Step, distinto de Gemma y Qwen.', 'Solo se usa al crear desde texto por la ruta LM; puede estimar metadatos.', 'En Directa este ajuste no se usa.'),
    'task_type': ('Operación: crear, transformar, corregir, añadir, separar o completar.', 'Determina audio fuente, intervalo y pistas necesarios.', 'Para una idea nueva elige Crear; para retocar un audio elige Corregir una parte.'),
    'ace_step_config': ('Variante del modelo generador.', 'Añadir, separar y completar necesitan Base. La instalación se verifica antes de ejecutar.', 'Para añadir guitarra usa Base y la acción Añadir.'),
    'source_artifact_id': ('Audio de esta canción que quieres editar.', 'Debe pertenecer al proyecto y superar la verificación del archivo.', 'Selecciona un candidato de esta canción para corregir su verso.'),
    'src_audio': ('Archivo del audio fuente seleccionado.', 'Se obtiene del artefacto verificado; no escribas una ruta.', 'Seleccionar el audio fuente completa esta información.'),
    'reference_artifact_id': ('Referencia musical opcional registrada.', 'Orienta música; no acredita clonación ni identidad vocal. Puedes crear sin referencia.', 'Usa audio propio para orientar el ambiente o deja la referencia vacía.'),
    'reference_audio': ('Archivo de la referencia musical.', 'Se deriva del artefacto verificado; no es un control de clonación.', 'Seleccionar una referencia proporciona el archivo automáticamente.'),
    'instruction': ('Operación técnica sobre las pistas del audio.', 'Debe corresponder a la acción y pistas objetivo; su traducción se valida.', 'Para separar voz selecciona vocals y revisa la instrucción del plan.'),
    'target_tracks': ('Partes que quieres añadir, separar o completar.', 'Añadir y separar usan una pista; completar admite una o más pistas conectadas.', 'Usa guitar para añadir guitarra o vocals para separar voz.'),
    'repainting_start': ('Segundo inicial de la parte seleccionada.', 'El intervalo debe quedar dentro del audio; no cambia por sí solo la duración total.', 'Para trabajar entre 20 y 30 segundos, el inicio es 20.'),
    'repainting_end': ('Segundo final de la parte seleccionada.', 'Debe seguir al inicio; -1 significa hasta el final según la acción.', 'Elige 30 para terminar en el segundo 30 o -1 para llegar al final.'),
    'audio_cover_strength': ('Conservación del audio fuente al crear otra versión.', 'Se usa en Cover, entre 0 y 1; no garantiza notas exactas ni identidad vocal.', 'Compara candidatos por escucha; no lo interpretes como un porcentaje garantizado.'),
}
CONTROL_HELP = {key:dict(zip(('meaning','effect','example'), text)) for key,text in _HELP.items()}
