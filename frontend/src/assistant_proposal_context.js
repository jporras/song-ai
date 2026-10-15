// A proposal belongs to both the saved revision and the draft the assistant saw.
export function proposalContext(projectId, revisionId, phase, phaseData) {
  return {projectId, revisionId: revisionId || null, phase, draft: JSON.stringify(phaseData)};
}

export function proposalContextMatches(source, current) {
  return Boolean(source && current && source.projectId === current.projectId
    && source.revisionId === current.revisionId && source.phase === current.phase
    && source.draft === current.draft);
}
