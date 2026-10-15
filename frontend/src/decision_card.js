export function decisionValue(value) {
  if (value === null || value === undefined || value === '') return 'Por decidir';
  if (typeof value === 'boolean') return value ? 'Sí' : 'No';
  if (Array.isArray(value)) return value.length ? value.map(decisionValue).join(', ') : 'Por decidir';
  if (typeof value === 'object') return Object.keys(value).length ? JSON.stringify(value, null, 2) : 'Por decidir';
  return String(value);
}

export const DecisionCard = {
  props:{field:{type:Object,required:true},busy:Boolean},
  emits:['delegate'],
  methods:{decisionValue},
  template:`<article :class="['specification-field', 'is-' + field.coverage_status]">
    <div><strong>{{ field.label }}</strong><small>{{ field.help }}</small>
      <details><summary>Cómo revisar este ajuste</summary>
        <template v-if="field.detailed_help"><p>{{ field.detailed_help.meaning }}</p><p><strong>Efecto:</strong> {{ field.detailed_help.effect }}</p><p><strong>Ejemplo:</strong> {{ field.detailed_help.example }}</p></template>
        <p>{{ field.review_action }}</p><p v-if="field.source_note">{{ field.source_note }}</p>
      </details>
      <small v-if="field.applicable === false">No se usa en la acción seleccionada.</small>
      <small v-else-if="field.execution_status === 'candidate_plan_only'">Entrada para preparar el plan; ejecución pendiente de integrar.</small>
    </div>
    <span class="decision-value">{{ field.decision_status === 'delegated' ? 'Lo elige el perfil automático' : decisionValue(field.value) }}</span>
    <em>{{ field.required_for_spec ? 'Necesario para esta etapa' : 'Opcional' }} · {{ field.decision_label }}</em>
    <button v-if="field.can_delegate_to_profile && field.decision_status !== 'delegated'" type="button" :disabled="busy" @click="$emit('delegate', field)">Guardar: dejar {{ field.label.toLowerCase() }} al perfil automático</button>
  </article>`
};
