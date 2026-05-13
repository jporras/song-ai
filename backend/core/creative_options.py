GENRES = [
    "pop ballad",
    "latin pop",
    "reggaeton soft",
    "acoustic",
    "rock pop",
    "r&b",
    "salsa pop",
    "regional",
    "electronic pop",
    "cinematic",
]

MOODS = [
    "warm",
    "hopeful",
    "romantic",
    "nostalgic",
    "celebratory",
    "grateful",
    "intimate",
    "uplifting",
    "melancholic",
    "cinematic",
]

ENERGIES = ["low", "medium", "high"]

BPM_PRESETS = ["72", "84", "96", "108", "120", "128", "140"]

KEYS = [
    "C major",
    "G major",
    "D major",
    "A major",
    "E major",
    "A minor",
    "E minor",
    "D minor",
    "F major",
    "Bb major",
]

INSTRUMENT_FAMILIES = {
    "keys": [
        "piano",
        "electric piano",
        "organ",
        "synth keys",
        "music box",
    ],
    "guitars": [
        "acoustic guitar",
        "nylon guitar",
        "electric guitar",
        "clean guitar",
        "ambient guitar",
        "distorted guitar",
    ],
    "bass": [
        "electric bass",
        "synth bass",
        "sub bass",
        "upright bass",
    ],
    "drums and percussion": [
        "soft drums",
        "pop drums",
        "rock drums",
        "electronic drums",
        "latin percussion",
        "congas",
        "bongos",
        "timbales",
        "shaker",
        "claps",
    ],
    "strings": [
        "strings",
        "violin",
        "cello",
        "string quartet",
        "cinematic strings",
    ],
    "brass and winds": [
        "brass",
        "trumpet",
        "trombone",
        "saxophone",
        "flute",
        "clarinet",
    ],
    "synths and textures": [
        "synth pads",
        "lead synth",
        "arpeggiator",
        "ambient textures",
        "choir pad",
    ],
    "latin and regional": [
        "accordion",
        "tres",
        "cuatro",
        "vihuela",
        "maracas",
        "guira",
        "cajon",
    ],
    "vocals and effects": [
        "vocal chops",
        "background vocals",
        "handclaps",
        "risers",
        "impacts",
    ],
}

INSTRUMENTS = [instrument for family in INSTRUMENT_FAMILIES.values() for instrument in family]

VOCAL_STYLES = [
    "clear emotional delivery",
    "soft lead",
    "intimate tenor guide",
    "warm female lead",
    "bright pop vocal",
    "raspy emotional vocal",
    "spoken intro with sung chorus",
]

VOCAL_RANGES = ["low", "medium", "high"]

SONG_STRUCTURES = [
    "verse, chorus",
    "intro, verse, chorus",
    "verse, pre chorus, chorus",
    "verse, chorus, bridge",
    "intro, verse, pre chorus, chorus, outro",
]

LANGUAGES = ["Spanish", "English", "Spanglish"]

LYRIC_THEMES = [
    "song for {name} about {occasion}",
    "birthday song for {name}",
    "anniversary song for {name}",
    "love song for {name}",
    "family tribute for {name}",
    "friendship song for {name}",
    "motivational song for {name}",
]

PLACEHOLDER_PRESETS = {
    "personal song": {"name": "Nombre", "occasion": "Ocasion"},
    "birthday": {"name": "Nombre", "age": "Edad"},
    "anniversary": {"name": "Nombre", "years": "Anos"},
    "love": {"name": "Nombre", "memory": "Recuerdo"},
    "family": {"name": "Nombre", "family_role": "Rol familiar"},
}

HELP_TEXTS = {
    "Estilo o genero": "Define la familia musical de la base: pop, salsa, rock, electronica, cinematico, etc.",
    "Atmosfera emocional": "Describe como debe sentirse la cancion: alegre, intima, nostalgica, romantica o intensa.",
    "BPM": "BPM significa beats per minute: mide la velocidad. 72 es lento, 96 medio, 120+ mas movido.",
    "Tonalidad": "La tonalidad es el centro armonico. Mayor suele sentirse mas luminosa; menor suele sentirse mas emotiva.",
    "Instrumentos": "Son los sonidos principales del arreglo. Primero eliges familias y luego sonidos especificos.",
    "Energia": "Controla que tan tranquila o intensa se siente la interpretacion.",
    "Estilo vocal": "Define el caracter de la voz guia: suave, brillante, intima, rasposa o hablada/cantada.",
    "Rango vocal": "Indica si la melodia debe estar en notas bajas, medias o altas.",
    "Estructura": "Orden de secciones de la cancion: verso, coro, puente, intro u outro.",
    "Intencion emocional": "La emocion que debe transmitir la melodia vocal.",
    "Idioma": "Idioma principal de la letra.",
    "Tono emocional": "Color emocional de las palabras: agradecido, romantico, celebratorio, nostalgico, etc.",
    "Tema de la cancion": "Idea central de la letra. Puede incluir placeholders como {name} u {occasion}.",
    "Estructura lirica": "Forma textual de la letra: verso, coro, puente y otras secciones.",
    "Ocasion": "Contexto para la variacion de letra: cumpleanos, aniversario, boda, homenaje, etc.",
}

FREE_INPUT_HINTS = {
    "Estilo o genero": "Ejemplo: algo bailable latino pero romantico",
    "Atmosfera emocional": "Ejemplo: feliz pero un poco nostalgica",
    "BPM": "Ejemplo: lento, medio, rapido o 112",
    "Tonalidad": "Ejemplo: algo triste, brillante o en G major",
    "Instrumentos": "Ejemplo: guitarra acustica con percusion latina y bajo",
    "Energia": "Ejemplo: tranquila, balanceada o intensa",
    "Estilo vocal": "Ejemplo: voz femenina calida y emocional",
    "Rango vocal": "Ejemplo: que no sea muy alta",
    "Estructura": "Ejemplo: verso, precoro y coro grande",
    "Intencion emocional": "Ejemplo: esperanzadora y cercana",
    "Idioma": "Ejemplo: mezcla de espanol e ingles",
    "Tono emocional": "Ejemplo: agradecida y familiar",
    "Tema de la cancion": "Ejemplo: una cancion de cumpleanos para {name}",
    "Estructura lirica": "Ejemplo: versos cortos y coro repetible",
    "Ocasion": "Ejemplo: aniversario de bodas",
}
