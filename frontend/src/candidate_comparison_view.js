export const CandidateComparisonView={
  props:{report:{type:Object,required:true}},
  template:`<section aria-label="Comparación de objetivos y resultados A/B">
    <p>{{ report.samePlan ? 'Ambos candidatos conservan el mismo plan registrado.' : 'Los planes son distintos o falta evidencia del plan.' }} {{ report.sameRevision ? 'Comparten revisión de la ficha.' : 'Las fichas pueden ser distintas; compara sus objetivos antes de elegir.' }}</p>
    <div class="comparison-scroll" tabindex="0" role="region" aria-label="Tabla A/B desplazable"><table><caption>Objetivos y observaciones de cada candidato</caption><thead><tr><th>Aspecto</th><th>A · actual</th><th>B · anterior</th></tr></thead><tbody>
      <tr v-for="check in report.checks" :key="check.id"><th scope="row">{{ check.label }}<p v-if="check.expectedChanged">Objetivo diferente</p><p v-if="check.missingReport">Informe incompleto</p></th>
      <td><details><summary>Objetivo A</summary><p class="decision-value">{{ check.expectedA }}</p></details><p>{{ check.observedA }}</p></td>
      <td><details><summary>Objetivo B</summary><p class="decision-value">{{ check.expectedB }}</p></details><p>{{ check.observedB }}</p></td></tr>
    </tbody></table></div>
    <p>Esta comparación no elige un ganador ni acredita fidelidad musical. Escucha ambos y registra tu opinión del candidato actual.</p>
  </section>`
};
