// These are retained creative directions, not independent ACE-Step DSP inputs.
export function validPhaseRanges(phase, data) {
  const definitions = {
    instrumental: ['instrumental', ['depth', 'brightness', 'movement', 'stereoWidth'], 'stems'],
    voice: ['voice', ['breaths', 'humanization', 'vibrato', 'layerBlend'], 'layers'],
    'music-plan': ['musicPlan', [], 'sections'],
    midi: ['midiPlan', ['humanization', 'velocity', 'melodyDensity', 'swing'], null],
  };
  const definition = definitions[phase];
  if (!definition) return true;
  const [section, keys, collection] = definition;
  const values = data[section] || {};
  const valid = (value, max = 100) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= max;
  if (!keys.every(key => !(key in values) || valid(values[key], key === 'velocity' ? 127 : key === 'swing' ? 60 : 100))) return false;
  if (!collection || !(collection in values)) return true;
  return Array.isArray(values[collection]) && values[collection].every(item => item && typeof item === 'object' && (!((phase === 'music-plan' ? 'intensity' : 'level') in item) || valid(item[phase === 'music-plan' ? 'intensity' : 'level'])));
}
