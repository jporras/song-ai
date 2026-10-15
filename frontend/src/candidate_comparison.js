const stable = value => {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(key => [key, stable(value[key])]));
  return value;
};
const show = value => value === null || value === undefined ? "Sin dato" : typeof value === "object" ? JSON.stringify(value) : String(value);
const measured = check => {
  if (check?.id !== "duration" || check.method !== "wav_frames_sample_rate" || typeof check.observed !== "number" || !Number.isFinite(check.observed)) return "Pendiente de analisis o escucha";
  const verdict = { within_tolerance: "dentro del margen aprobado", outside_tolerance: "fuera del margen aprobado", tolerance_pending: "falta margen aprobado", not_evaluated: "cumplimiento sin evaluar" }[check.status] || "cumplimiento sin evaluar";
  return `${check.observed} segundos · ${verdict}`;
};

export function compareCandidateReports(a, b) {
  const left = new Map((a?.checks || []).map(check => [check.id, check]));
  const right = new Map((b?.checks || []).map(check => [check.id, check]));
  const samePlan = Boolean(a?.plan_sha256 && b?.plan_sha256 && a.plan_sha256 === b.plan_sha256);
  const sameRevision = Boolean(a?.spec_revision_id && b?.spec_revision_id && a.spec_revision_id === b.spec_revision_id);
  return { samePlan, sameRevision, checks: [...new Set([...left.keys(), ...right.keys()])].map(id => {
    const x = left.get(id), y = right.get(id);
    return { id, label: x?.label || y?.label || id, expectedA: show(x?.expected), expectedB: show(y?.expected),
      observedA: measured(x), observedB: measured(y),
      expectedChanged: JSON.stringify(stable(x?.expected)) !== JSON.stringify(stable(y?.expected)),
      missingReport: !x || !y };
  }), finalQualityVerified: false };
}
