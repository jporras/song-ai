export const BuilderShell = {
  props:{steps:{type:Array,required:true},current:{type:Object,required:true},projectName:String,projectId:String,revision:String,dirty:Boolean,busy:Boolean},
  emits:['navigate','library','voice'],
  computed:{
    index(){return this.steps.findIndex(step=>step.id===this.current.id);},
    previous(){return this.steps[this.index-1];},
    next(){return this.steps[this.index+1];},
  },
  template:`<section class="builder-flow" aria-label="Recorrido de creación de canción">
    <header class="builder-context"><strong>{{ projectName || 'Tu nueva canción' }}</strong>
      <span>Paso {{ index + 1 }} de {{ steps.length }} · {{ current.label }}</span>
      <span v-if="projectId">{{ dirty ? 'Borrador con cambios sin guardar' : 'Mostrando la configuración guardada' }}</span>
    </header>
    <nav aria-label="Pasos para crear la canción"><ol class="builder-steps">
      <li v-for="(step,index) in steps" :key="step.id"><button type="button" :aria-current="current.id === step.id ? 'step' : undefined" @click="$emit('navigate',step)">{{ index + 1 }}. {{ step.label }}</button></li>
    </ol></nav>
    <p>{{ current.hint }}</p>
    <p v-if="!projectId">Selecciona un proyecto en Biblioteca para guardar tus decisiones.</p>
    <p v-else-if="dirty" role="status">Hay cambios sin guardar. Puedes guardarlos o revisarlos antes de continuar.</p>
    <div class="builder-actions">
      <button v-if="previous" type="button" @click="$emit('navigate',previous)">Volver a {{ previous.label }}</button>
      <button v-if="next" type="button" @click="$emit('navigate',next)">Ir a {{ next.label }}</button>
      <button v-if="current.id === 'sound'" type="button" @click="$emit('voice')">Revisar melodía y voz</button>
      <button type="button" @click="$emit('library')">Mis proyectos</button>
    </div>
    <details v-if="revision"><summary>Revisión guardada de la definición</summary><p>{{ revision }}</p><p>Confirma los cambios creativos antes de generar. La aprobación del audio se registra después de escucharlo.</p></details>
  </section>`
};
