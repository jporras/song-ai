export function protectedLinesUnchanged(section, text) {
  const before = section.text.split('\n');
  const after = text.split('\n');
  return (section.protected_lines || []).every(index => before[index] === after[index]);
}
