export const MAX_REVIEWED_PROPOSALS = 20;

export function appendAppliedProposal(proposals, proposal) {
  if (proposals.length >= MAX_REVIEWED_PROPOSALS) {
    throw new Error('Guarda o descarta los cambios antes de aplicar más propuestas.');
  }
  return [...proposals, JSON.parse(JSON.stringify(proposal))];
}
