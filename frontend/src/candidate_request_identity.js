// A network retry keeps one identity; a reviewed new plan starts a new action.
export function candidateRequestIdentity(previous, songId, planHash, createId = () => crypto.randomUUID()) {
  if (previous?.songId === songId && previous?.planHash === planHash) return previous;
  return {songId, planHash, requestId:createId()};
}
