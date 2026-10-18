export function productionNextAction({projectId, dirty, editing, planDraftOpen, revision, plan, running, exportReady, resourceBlocked}) {
  if (!projectId) return {message:"Elige tu proyecto en Biblioteca para preparar la canción.",label:"Ir a Biblioteca",target:"library"};
  if (dirty || editing) return {message:"Hay cambios sin guardar. Guárdalos o descártalos antes de continuar.",label:"Revisar cambios",target:"spec"};
  if (revision?.user_confirmation_status !== "confirmed") return {
    message:"Revisa la ficha de la canción y pulsa «Confirmar esta configuración». La propuesta técnica no confirma por ti.",
    label:"Ir a la ficha",target:"spec"};
  if (planDraftOpen) return {
    message:"Ya estás revisando la letra. Pulsa «Crear plan para revisar» debajo del cuadro de texto.",
    label:"Ir a «Crear plan para revisar»",target:"plan-editor"};
  if (plan?.effective_status === "candidate" && plan?.inputs_current === true
      && plan?.plan?.spec_revision_id === revision?.revision_id) return {
    message:"El plan está preparado. Revisa la letra exacta y apruébalo para habilitar la generación.",
    label:"Ir a aprobar el plan",target:"plan-approval"};
  if (plan?.effective_status !== "approved" || plan?.inputs_current !== true
      || plan?.plan?.spec_revision_id !== revision?.revision_id) return {
    message:"Prepara el plan ACE-Step, revisa la letra y aprueba el plan vigente.",
    label:"Ir al plan",target:"plan"};
  if (running) return {message:"La generación está en curso. Consulta el estado antes de iniciar otra.",label:"Ver generación",target:"final"};
  if (exportReady) return {message:"Hay archivos finales disponibles para esta revisión. Revísalos antes de descargar.",label:"Ver descargas",target:"downloads"};
  if (resourceBlocked) return {message:"La configuración está lista, pero el diagnóstico de recursos muestra un bloqueo. Revisa las recomendaciones antes de generar.",
    label:"Ver recursos",target:"resources"};
  return {message:"La ficha y el plan están listos. Puedes generar la canción completa; el sample previo es opcional.",
    label:"Ir a generar canción completa",target:"final"};
}
