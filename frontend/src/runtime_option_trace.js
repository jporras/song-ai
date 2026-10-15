const LABELS = {seed:'Semilla de variación',inference_steps:'Pasos de generación',
  guidance_scale:'Intensidad de condicionamiento',shift:'Distribución de pasos'};
const SOURCES = {approved_override:'Valor del plan aprobado',execution_profile:'Perfil de ejecución',
  wrapper_default_or_cli:'Valor del wrapper o su configuración'};

export function runtimeOptionRows(artifact) {
  const runtime = artifact?.metadata?.runtime_evidence;
  const trace = runtime?.runtime_options_trace;
  if (trace?.schema_version !== 'runtime_options_v1' || !Array.isArray(trace.entries)) return [];
  if (trace.spec_revision_id && artifact.metadata.spec_revision_id && trace.spec_revision_id !== artifact.metadata.spec_revision_id) return [];
  const observed = runtime?.generation_api?.engine_reported_options || {};
  return trace.entries.filter(entry=>Object.hasOwn(LABELS,entry.field)).map(entry=>({
    field:entry.field, label:LABELS[entry.field],
    requested:entry.requested_value ?? (entry.provenance?.source === 'explicit_user_delegation' ? 'Delegado por ti' : 'Sin ajuste manual registrado'),
    wrapper:entry.wrapper_value ?? 'Sin dato',
    source:SOURCES[entry.source] || 'Origen sin clasificar',
    engine:Object.hasOwn(observed,entry.field) ? observed[entry.field] : 'No reportado',
  }));
}
