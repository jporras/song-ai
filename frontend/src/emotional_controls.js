export const emotionalControls = [
  {key:'warmth',label:'Calidez',help:'Sensación acogedora: 0 distante, 100 muy cálida.'},
  {key:'energy',label:'Energía',help:'Intensidad deseada: 0 tranquila, 100 muy intensa.'},
  {key:'nostalgia',label:'Nostalgia',help:'Sensación de recuerdo: 0 presente, 100 muy nostálgica.'},
  {key:'cinematic',label:'Sensación cinematográfica',help:'Carácter de banda sonora: 0 sencillo, 100 muy evocador.'},
];
export function validEmotionalValues(intent) {
  return emotionalControls.every(({key}) => typeof intent[key] === 'number'
    && Number.isFinite(intent[key]) && intent[key] >= 0 && intent[key] <= 100);
}
