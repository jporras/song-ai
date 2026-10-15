// Presentation projection only: integration rules arrive from the backend catalog.
export function capabilityControls(catalog, draft = {}) {
  const profile = catalog?.capability_profile;
  if (!profile?.version || !profile?.choices || !profile?.modes) return null;
  const mode = profile.modes[draft.task_type || "text2music"];
  const ranges = profile.numeric_ranges_by_config?.[draft.ace_step_config] || {};
  const fixed = profile.fixed_values_by_config?.[draft.ace_step_config] || {};
  return {
    version: profile.version,
    choices: profile.choices,
    mode: mode || null,
    selectionIssues: mode ? [
      ...(draft.generation_api === 'high_level_lm' && draft.task_type !== 'text2music' ? ['La ruta con LM musical solo admite crear desde texto. Elige Directa o API sin LM para editar audio.'] : []),
      ...(mode.requires_base && draft.ace_step_config !== 'acestep-v15-base' ? ['Selecciona Base: esta acción no admite Turbo.'] : []),
      ...(mode.track_cardinality === 'one' && draft.target_tracks?.length !== 1 ? ['Selecciona exactamente una pista objetivo.'] : []),
      ...(mode.track_cardinality === 'one_or_more' && !draft.target_tracks?.length ? ['Selecciona al menos una pista objetivo.'] : []),
    ] : ['Selecciona una acción del catálogo recibido.'],
    requirements: mode ? [
      mode.requires_source ? 'Selecciona un audio fuente de este proyecto; el backend comprobará el archivo.' : 'Puedes crear desde texto sin audio fuente.',
      ...(mode.requires_base ? ['Esta acción requiere el modelo Base instalado y disponible.'] : []),
      ...(mode.uses_interval ? ['Revisa inicio y final del intervalo en segundos dentro del audio fuente.'] : []),
      ...(mode.track_cardinality === 'one' ? ['Elige exactamente una pista objetivo.'] : []),
      ...(mode.track_cardinality === 'one_or_more' ? ['Elige una o más pistas objetivo.'] : []),
      'La referencia musical es opcional; no acredita clonación de voz.',
    ] : [],
    help: profile.control_help || {},
    label(value) {
      return ({text2music: 'Crear desde mi idea', cover: 'Crear otra versión de un audio',
        repaint: 'Corregir una parte', lego: 'Añadir una parte instrumental o vocal',
        extract: 'Separar una parte de la mezcla', complete: 'Completar el arreglo',
        'acestep-v15-base': 'Base', 'acestep-v15-turbo': 'Turbo',
        direct: 'Directa (predeterminada)', high_level: 'API de alto nivel sin LM',
        high_level_lm: 'API con LM musical (experimental)',
        'acestep-5Hz-lm-0.6B': '0.6B', 'acestep-5Hz-lm-1.7B': '1.7B'})[value] || value;
    },
    lmApplicable: draft.task_type === "text2music" && draft.generation_api === "high_level_lm",
    range(field) {
      return field in fixed ? [fixed[field], fixed[field]] : ranges[field] || [];
    },
  };
}
