// Navigation projects the existing editors; MusicSpec remains the data source.
export const builderSteps = [
  {id:'idea',label:'Idea',tab:'intent',hint:'Describe para quién es la canción y qué quieres transmitir.'},
  {id:'sound',label:'Sonido',tab:'instrumental',hint:'Elige instrumentos y carácter sonoro. Revisa también la voz.'},
  {id:'composition',label:'Composición',tab:'music-plan',hint:'Define ritmo, tonalidad y evolución musical con ayuda.'},
  {id:'lyrics',label:'Estructura y letra',tab:'lyrics',hint:'Revisa las secciones y las palabras que se cantarán.'},
  {id:'review',label:'Revisar',tab:'production',hint:'Revisa las tres piezas, la ficha y las decisiones pendientes.',selector:'.specification-panel'},
  {id:'generate',label:'Generar',tab:'production',hint:'Confirma la configuración y revisa el plan antes de ejecutar.',selector:'.generation-preflight-panel'},
  {id:'studio',label:'Studio',tab:'production',hint:'Escucha candidatos, compara versiones y revisa la entrega.',selector:'.studio-panel'},
];

export function phaseToOpenAfterLoad(project, validTabs) {
  const saved = String(project?.ui_state?.last_active_phase || '').trim();
  if (saved && validTabs.includes(saved)) return saved;
  const phaseData = project?.phase_data || {};
  const firstIncomplete = builderSteps.find(step => step.tab !== 'production' && !phaseData[step.tab]?.status);
  return firstIncomplete?.tab || 'production';
}
