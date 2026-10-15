export function builderProjectStatus(project, planReview, dirtyPhase = '') {
  if (!project?.set?.set_id) return {items:[],message:'Selecciona un proyecto para revisar sus decisiones.',action:{label:'Elegir proyecto',tab:'library'}};
  const set = project.set;
  const items = [{label:'Idea',ready:Boolean(project.project?.description?.trim()),tab:'intent'}];
  for (const [role, id, label, tab] of [['instrumental','instrumental_id','Instrumental','instrumental'],['melody','melody_id','Melodía vocal','voice'],['lyrics','lyrics_id','Letra','lyrics']]) {
    items.push({label,ready:Boolean(set[id] && project.assets?.[role]?.asset_id === set[id]),tab,
      detail:'Seleccionada; la calidad musical requiere revisión.'});
  }
  const spec = project.music_spec;
  const revision = project.music_spec_revision_id;
  const confirmed = Boolean(revision && spec?.revision?.revision_id === revision && spec.revision.user_confirmation_status === 'confirmed');
  items.push({label:'Ficha confirmada',ready:confirmed,tab:'production',detail:'Confirmación creativa de esta revisión; no aprobación del audio.'});
  const plan = Boolean(confirmed && planReview?.inputs_current === true && planReview.effective_status === 'approved' && planReview.plan?.spec_revision_id === revision);
  items.push({label:'Plan aprobado',ready:plan,tab:'production',detail:'La disponibilidad del motor se comprueba antes de ejecutar.'});
  const missing = items.find(item => !item.ready);
  return {items,message:dirtyPhase ? 'Hay un borrador sin guardar; este resumen refleja lo guardado.' : missing ? `Pendiente: ${missing.label.toLowerCase()}.` : 'Decisiones y plan preparados. Revisa disponibilidad y condiciones de generación.',
    action:dirtyPhase ? {label:'Guardar cambios',save:true} : {label:missing ? `Revisar ${missing.label.toLowerCase()}` : 'Revisar generación',tab:missing?.tab || 'production'}};
}
