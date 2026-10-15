export function studioDeliveryState({projectId, sample, sampleAudio, running, canGenerate, finalMessage, exports = [], candidateAudio, candidateRunning}) {
  const finals = exports.filter(item => ['final_song_wav','final_song_mp3','final_song_flac'].includes(item.type) && item.url);
  let sampleText = 'Todavía no hay sample para este proyecto.';
  if (sample?.freshness_status === 'stale') sampleText = 'El sample quedó desactualizado: revisa o genera una nueva versión.';
  else if (sample && !sampleAudio) sampleText = 'Hay un checkpoint de prueba sin audio; no acredita la calidad de una canción.';
  else if (sample) sampleText = sample.approval_status === 'approved' ? 'Sample aprobado; el backend comprueba su vigencia y representatividad al continuar.' : 'Sample disponible para escuchar y revisar.';
  return {sampleText,
    finalText:candidateRunning ? 'Se está generando una nueva versión para escuchar.' : candidateAudio ? 'Hay una versión disponible para escuchar y descargar en WAV. Revisa su definición y tu opinión de escucha; puede corresponder a una revisión anterior.' : running ? 'La canción completa se está generando.' : finals.length ? 'Hay archivos finales disponibles. Su presencia no acredita aceptación de audio ni correspondencia con los últimos cambios.' : finalMessage || 'Todavía no hay archivos finales disponibles.',
    action:!projectId ? {label:'Elegir proyecto',destination:'library'}
      : candidateRunning ? {label:'Ver generación de la versión',destination:'candidate'}
      : candidateAudio ? {label:'Escuchar y descargar esta versión',destination:'candidate'}
      : running ? {label:'Ver generación en curso',destination:'final'}
      : finals.length ? {label:'Revisar archivos disponibles',destination:'final'}
      : canGenerate ? {label:'Revisar generación completa',destination:'final'}
      : sampleAudio ? {label:'Revisar sample opcional',destination:'sample'}
      : {label:'Revisar definición y requisitos',destination:'review'},
  };
}

export const StudioDelivery = {
  props:{state:{type:Object,required:true}},emits:['navigate'],
  template:`<section class="panel studio-delivery" aria-label="Estado de la entrega de la canción">
    <h2>De la escucha a la entrega</h2>
    <div class="grid two"><section><h3>Revisión corta</h3><p>{{ state.sampleText }}</p></section>
    <section><h3>Canción completa y archivos</h3><p>{{ state.finalText }}</p></section></div>
    <button type="button" @click="$emit('navigate',state.action.destination)">{{ state.action.label }}</button>
    <p>Escuchar, aprobar audio y descargar son pasos distintos. Aquí puedes revisar cada uno.</p>
  </section>`
};
