export function lyricsReplacementBlockReason(sections, pendingUnlocks = []) {
  if (sections.some(section => section.locked || section.direction_locked || section.protected_lines?.length)) return 'Desbloquea y guarda las secciones, líneas o direcciones protegidas antes de sustituir toda la letra.';
  if (pendingUnlocks.length) return 'Guarda los desbloqueos antes de cargar otra letra o plantilla.';
  return '';
}
