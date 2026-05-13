from collections.abc import Callable

from builders.full_song_builder import FullSongBuilder
from builders.export_builder import ExportBuilder
from builders.sample_builder import SampleBuilder
from builders.set_builder import SetBuilder
from builders.template_builder import TemplateBuilder
from config.settings import Settings
from core import creative_options as options
from core.storage import StorageManager
from explorers.mock_explorers import MockExplorerSuite
from audio.mixer import AudioMixer
from providers.registry import ProviderRegistry


class MainMenu:
    def __init__(
        self,
        settings: Settings,
        storage: StorageManager,
        explorers: MockExplorerSuite,
        set_builder: SetBuilder,
        sample_builder: SampleBuilder,
        full_song_builder: FullSongBuilder,
        audio_mixer: AudioMixer,
        export_builder: ExportBuilder,
        template_builder: TemplateBuilder,
        provider_registry: ProviderRegistry,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.explorers = explorers
        self.set_builder = set_builder
        self.sample_builder = sample_builder
        self.full_song_builder = full_song_builder
        self.audio_mixer = audio_mixer
        self.export_builder = export_builder
        self.template_builder = template_builder
        self.provider_registry = provider_registry
        self.actions: dict[str, Callable[[], None]] = {
            "1": self.guide_instrumental,
            "2": self.guide_melody,
            "3": self.guide_lyrics,
            "4": self.list_drafts,
            "5": self.mark_favorite,
            "6": self.list_favorites,
            "7": self.create_first_valid_set,
            "8": self.create_sample_from_latest_set,
            "9": self.create_full_song_from_latest_sample,
            "10": self.list_providers,
            "11": self.prepare_mix,
            "12": self.prepare_exports,
            "13": self.save_template,
            "0": self.exit_menu,
        }
        self.running = True

    def run(self) -> None:
        while self.running:
            self.print_menu()
            choice = input("Selecciona una opcion: ").strip()
            action = self.actions.get(choice)
            if action is None:
                print("Opcion no valida.")
                continue
            action()

    def print_menu(self) -> None:
        print()
        print(f"=== {self.settings.app_name} ===")
        print("1. Explorar instrumental")
        print("2. Explorar melodia vocal")
        print("3. Crear letra")
        print("4. Listar drafts")
        print("5. Marcar draft favorito")
        print("6. Listar favoritos")
        print("7. Crear set valido con primeros drafts")
        print("8. Crear sample mock del ultimo set")
        print("9. Crear cancion completa mock del ultimo sample")
        print("10. Listar providers disponibles")
        print("11. Preparar mezcla mock")
        print("12. Preparar exportaciones")
        print("13. Guardar plantilla reutilizable")
        print("0. Salir")

    def guide_instrumental(self) -> None:
        print()
        print("=== Exploracion instrumental ===")
        print("El instrumental define ritmo, atmosfera, BPM, tonalidad e instrumentos.")
        print("1. Rapido: crear una base sugerida")
        print("2. Guiado: elegir estilo, energia e instrumentos")
        print("3. Desde perfil/base: variante mock reutilizable")
        print("0. Volver")
        choice = input("Como quieres empezar el instrumental?: ").strip()

        if choice == "0":
            return
        if choice == "1":
            draft_path = self.explorers.instrumentals.create_random()
        elif choice == "2":
            genre = self.ask_option("Estilo o genero", options.GENRES, "pop ballad")
            mood = self.ask_option("Atmosfera emocional", options.MOODS, "warm")
            bpm = self.ask_int_option("BPM", options.BPM_PRESETS, 96)
            key = self.ask_option("Tonalidad", options.KEYS, "C major")
            instruments = self.ask_multi_option(
                "Instrumentos",
                options.INSTRUMENTS,
                ["piano", "soft drums", "bass"],
            )
            energy = self.ask_option("Energia", options.ENERGIES, "medium", allow_custom=False)
            draft_path = self.explorers.instrumentals.create_from_intent(
                mood=mood,
                genre=genre,
                bpm=bpm,
                key=key,
                instruments=instruments,
                energy=energy,
                mode="guided",
            )
        elif choice == "3":
            profile_name = self.ask("Nombre del perfil/base", "default-profile")
            draft_path = self.explorers.instrumentals.create_from_intent(
                mood="cinematic",
                genre=f"profile variation: {profile_name}",
                bpm=100,
                key="A minor",
                instruments=["keys", "ambient guitar", "sub bass"],
                energy="medium",
                mode="profile_variation",
            )
        else:
            print("Opcion no valida.")
            return

        print()
        print(f"Instrumental guardado: {draft_path}")
        print("Siguiente paso sugerido: explora una melodia vocal en la opcion 2.")

    def guide_melody(self) -> None:
        print()
        print("=== Exploracion de melodia vocal ===")
        print("La melodia define guia vocal, rango, energia y estructura cantable.")
        print("1. Rapido: crear una guia sugerida")
        print("2. Guiado: elegir voz, rango y estructura")
        print("3. Basada en perfil: variante mock de una identidad vocal")
        print("0. Volver")
        choice = input("Como quieres crear la melodia?: ").strip()

        if choice == "0":
            return
        if choice == "1":
            draft_path = self.explorers.melodies.create_guided()
        elif choice == "2":
            vocal_style = self.ask_option("Estilo vocal", options.VOCAL_STYLES, "clear emotional delivery")
            range_hint = self.ask_option("Rango vocal", options.VOCAL_RANGES, "medium", allow_custom=False)
            structure = self.ask_option("Estructura", options.SONG_STRUCTURES, "verse, chorus")
            mood = self.ask_option("Intencion emocional", options.MOODS, "hopeful")
            energy = self.ask_option("Energia", options.ENERGIES, "medium", allow_custom=False)
            draft_path = self.explorers.melodies.create_from_intent(
                mood=mood,
                vocal_style=vocal_style,
                range_hint=range_hint,
                structure=structure,
                energy=energy,
                mode="guided",
            )
        elif choice == "3":
            profile_name = self.ask("Nombre del perfil vocal", "default-voice")
            draft_path = self.explorers.melodies.create_from_intent(
                mood="intimate",
                vocal_style=f"profile voice: {profile_name}",
                range_hint="medium",
                structure="intro, verse, chorus",
                energy="medium",
                mode="profile_based",
            )
        else:
            print("Opcion no valida.")
            return

        print()
        print(f"Melodia guardada: {draft_path}")
        print("Siguiente paso sugerido: crea una letra en la opcion 3.")

    def guide_lyrics(self) -> None:
        print()
        print("=== Creacion de letra ===")
        print("La letra guarda texto editable, placeholders y contexto lirico.")
        print("1. Rapido: crear plantilla markdown")
        print("2. Guiado: definir idioma, tono, tema y placeholders")
        print("3. Variacion IA mock: simular letra generada")
        print("0. Volver")
        choice = input("Como quieres crear la letra?: ").strip()

        if choice == "0":
            return
        if choice == "1":
            draft_path = self.explorers.lyrics.create_markdown()
        elif choice == "2":
            language = self.ask_option("Idioma", options.LANGUAGES, "Spanish", allow_custom=False)
            tone = self.ask_option("Tono emocional", options.MOODS, "grateful")
            theme = self.ask_option("Tema de la cancion", options.LYRIC_THEMES, "song for {name} about {occasion}")
            structure = self.ask_option("Estructura lirica", options.SONG_STRUCTURES, "verse, chorus")
            placeholders = self.ask_placeholders()
            draft_path = self.explorers.lyrics.create_from_intent(
                theme=theme,
                language=language,
                tone=tone,
                structure=structure,
                placeholders=placeholders,
                mode="guided",
            )
        elif choice == "3":
            occasion = self.ask_option("Ocasion", ["birthday", "anniversary", "wedding", "graduation", "tribute"], "birthday")
            draft_path = self.explorers.lyrics.create_from_intent(
                theme=f"AI mock variation for {{name}} and {occasion}",
                language="Spanish",
                tone="emotional",
                structure="verse, chorus, bridge",
                placeholders={"name": "Nombre"},
                mode="ai_mock",
            )
        else:
            print("Opcion no valida.")
            return

        print()
        print(f"Letra guardada: {draft_path}")
        print("Siguiente paso sugerido: revisa drafts en la opcion 4 o crea un set en la opcion 7.")

    def list_drafts(self) -> None:
        print()
        print("Drafts disponibles:")
        drafts = self.storage.list_asset_drafts()
        if not drafts:
            print("No hay drafts todavia.")
            return
        for draft in drafts:
            print(f"- {draft['asset_type']}: {draft['asset_id']} ({draft['path']})")

    def mark_favorite(self) -> None:
        asset_id = input("Asset ID favorito: ").strip()
        if not asset_id:
            print("Asset ID requerido.")
            return
        favorite = self.storage.favorite_asset(asset_id)
        print()
        if favorite is None:
            print("No encontre ese asset.")
            return
        print(f"Favorito guardado: {favorite['asset_type']} {favorite['asset_id']}")

    def list_favorites(self) -> None:
        print()
        print("Favoritos:")
        favorites = self.storage.list_favorites()
        if not favorites:
            print("No hay favoritos todavia.")
            return
        for favorite in favorites:
            print(f"- {favorite['asset_type']}: {favorite['asset_id']}")

    def create_first_valid_set(self) -> None:
        print()
        try:
            set_path = self.set_builder.create_first_valid_set()
        except ValueError as error:
            print(str(error))
            return
        print(f"Set creado: {set_path}")

    def create_sample_from_latest_set(self) -> None:
        print()
        try:
            sample_path = self.sample_builder.create_from_latest_set()
        except ValueError as error:
            print(str(error))
            return
        print(f"Sample mock creado: {sample_path}")

    def create_full_song_from_latest_sample(self) -> None:
        print()
        try:
            song_path = self.full_song_builder.create_from_latest_sample()
        except ValueError as error:
            print(str(error))
            return
        print(f"Cancion completa mock creada: {song_path}")

    def list_providers(self) -> None:
        print()
        print("Providers disponibles:")
        for provider_type, providers in self.provider_registry.summary().items():
            print(f"{provider_type}:")
            for provider in providers:
                capabilities = ", ".join(str(item) for item in provider["capabilities"])
                print(f"- {provider['name']}: {capabilities}")

    def prepare_mix(self) -> None:
        print()
        try:
            mix_path = self.audio_mixer.prepare_latest_song_mix()
        except ValueError as error:
            print(str(error))
            return
        print(f"Mezcla mock preparada: {mix_path}")

    def prepare_exports(self) -> None:
        print()
        try:
            exports_path = self.export_builder.prepare_latest_song_exports()
        except ValueError as error:
            print(str(error))
            return
        print(f"Exportaciones preparadas: {exports_path}")

    def save_template(self) -> None:
        print()
        try:
            template_path = self.template_builder.save_latest_set_template()
        except ValueError as error:
            print(str(error))
            return
        print(f"Plantilla guardada: {template_path}")

    def exit_menu(self) -> None:
        self.running = False
        print("Hasta luego.")

    def ask(self, label: str, default: str) -> str:
        value = input(f"{label} [{default}]: ").strip()
        return value or default

    def ask_int(self, label: str, default: int) -> int:
        value = input(f"{label} [{default}]: ").strip()
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            print(f"Valor invalido. Uso {default}.")
            return default

    def ask_list(self, label: str, default: list[str]) -> list[str]:
        value = input(f"{label} [{', '.join(default)}]: ").strip()
        if not value:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]

    def ask_choice(self, label: str, options: list[str], default: str) -> str:
        print(f"{label}: {', '.join(options)}")
        value = input(f"Seleccion [{default}]: ").strip()
        if value in options:
            return value
        if value:
            print(f"Opcion no reconocida. Uso {default}.")
        return default

    def ask_option(self, label: str, values: list[str], default: str, allow_custom: bool = True) -> str:
        print()
        print(f"{label}:")
        help_text = options.HELP_TEXTS.get(label)
        if help_text:
            print(f"Que es: {help_text}")
        for index, value in enumerate(values, start=1):
            print(f"{index}. {value}")
        print("L. Describir libremente para interpretar")
        if allow_custom:
            print("C. Escribir otra opcion")
        print("Enter. Usar recomendado")

        choice = input(f"Seleccion [{default}]: ").strip()
        if not choice:
            return default
        if choice.lower() == "l":
            free_text = self.ask_free_text(label)
            interpreted = self.interpret_free_option(label, free_text, values, default)
            print(f"Interpretacion local: {interpreted}")
            return interpreted
        if allow_custom and choice.lower() == "c":
            return self.ask(f"{label} personalizado", default)
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(values):
                return values[index - 1]
        if allow_custom:
            print(f"Uso opcion personalizada: {choice}")
            return choice
        print(f"Opcion no reconocida. Uso {default}.")
        return default

    def ask_int_option(self, label: str, values: list[str], default: int) -> int:
        selected = self.ask_option(label, values, str(default))
        try:
            return int(selected)
        except ValueError:
            print(f"Valor invalido. Uso {default}.")
            return default

    def ask_multi_option(self, label: str, values: list[str], default: list[str]) -> list[str]:
        if label == "Instrumentos":
            return self.ask_instruments(default)

        print()
        print(f"{label}:")
        help_text = options.HELP_TEXTS.get(label)
        if help_text:
            print(f"Que es: {help_text}")
        for index, value in enumerate(values, start=1):
            print(f"{index}. {value}")
        print("L. Describir libremente para interpretar")
        print("C. Escribir otra lista")
        print("Enter. Usar recomendado")
        print("Puedes elegir varios numeros separados por coma. Ejemplo: 1,4,6")

        choice = input(f"Seleccion [{', '.join(default)}]: ").strip()
        if not choice:
            return default
        if choice.lower() == "l":
            free_text = self.ask_free_text(label)
            interpreted = self.interpret_free_multi_option(free_text, values, default)
            print(f"Interpretacion local: {', '.join(interpreted)}")
            return interpreted
        if choice.lower() == "c":
            return self.ask_list(f"{label} personalizados separados por coma", default)

        selected: list[str] = []
        for item in choice.split(","):
            item = item.strip()
            if not item.isdigit():
                continue
            index = int(item)
            if 1 <= index <= len(values):
                selected.append(values[index - 1])

        if selected:
            return selected
        print("No reconoci la seleccion. Uso recomendado.")
        return default

    def ask_instruments(self, default: list[str]) -> list[str]:
        print()
        print("Instrumentos:")
        help_text = options.HELP_TEXTS.get("Instrumentos")
        if help_text:
            print(f"Que es: {help_text}")
        print("No es una lista total de todos los instrumentos posibles; es un catalogo base por familias.")
        print()
        print("Familias:")
        family_names = list(options.INSTRUMENT_FAMILIES)
        for index, family_name in enumerate(family_names, start=1):
            print(f"{index}. {family_name}")
        print("L. Describir libremente para interpretar")
        print("C. Escribir otra lista")
        print("Enter. Usar recomendado")
        print("Puedes elegir varias familias separadas por coma. Ejemplo: 1,4,7")

        family_choice = input(f"Familias [{', '.join(default)}]: ").strip()
        if not family_choice:
            return default
        if family_choice.lower() == "l":
            free_text = self.ask_free_text("Instrumentos")
            interpreted = self.interpret_free_multi_option(free_text, options.INSTRUMENTS, default)
            print(f"Interpretacion local: {', '.join(interpreted)}")
            return interpreted
        if family_choice.lower() == "c":
            return self.ask_list("Instrumentos personalizados separados por coma", default)

        selected_families: list[str] = []
        for item in family_choice.split(","):
            item = item.strip()
            if not item.isdigit():
                continue
            index = int(item)
            if 1 <= index <= len(family_names):
                selected_families.append(family_names[index - 1])

        if not selected_families:
            print("No reconoci las familias. Uso recomendado.")
            return default

        family_instruments: list[str] = []
        for family_name in selected_families:
            for instrument in options.INSTRUMENT_FAMILIES[family_name]:
                if instrument not in family_instruments:
                    family_instruments.append(instrument)

        print()
        print("Instrumentos disponibles en las familias elegidas:")
        for index, instrument in enumerate(family_instruments, start=1):
            print(f"{index}. {instrument}")
        print("A. Usar todos los instrumentos de esas familias")
        print("C. Escribir otra lista")
        print("Enter. Usar recomendado")
        print("Puedes elegir varios numeros separados por coma. Ejemplo: 1,3,5")

        instrument_choice = input(f"Instrumentos [{', '.join(default)}]: ").strip()
        if not instrument_choice:
            return default
        if instrument_choice.lower() == "a":
            return family_instruments
        if instrument_choice.lower() == "c":
            return self.ask_list("Instrumentos personalizados separados por coma", default)

        selected_instruments: list[str] = []
        for item in instrument_choice.split(","):
            item = item.strip()
            if not item.isdigit():
                continue
            index = int(item)
            if 1 <= index <= len(family_instruments):
                selected_instruments.append(family_instruments[index - 1])

        if selected_instruments:
            return selected_instruments
        print("No reconoci la seleccion. Uso recomendado.")
        return default

    def ask_placeholders(self) -> dict[str, str]:
        print()
        print("Placeholders disponibles para personalizacion:")
        print("Que es: Son campos variables que luego se reemplazan, como {name} o {occasion}.")
        preset_names = list(options.PLACEHOLDER_PRESETS)
        for index, preset_name in enumerate(preset_names, start=1):
            preset = options.PLACEHOLDER_PRESETS[preset_name]
            pairs = ", ".join(f"{key}={value}" for key, value in preset.items())
            print(f"{index}. {preset_name}: {pairs}")
        print("C. Escribir placeholders personalizados")
        print("L. Describir libremente para interpretar")
        print("Enter. Usar recomendado")

        choice = input("Seleccion [personal song]: ").strip()
        if not choice:
            return options.PLACEHOLDER_PRESETS["personal song"]
        if choice.lower() == "l":
            free_text = self.ask_free_text("Placeholders")
            interpreted = self.interpret_free_placeholders(free_text)
            pairs = ", ".join(f"{key}={value}" for key, value in interpreted.items())
            print(f"Interpretacion local: {pairs}")
            return interpreted
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(preset_names):
                return options.PLACEHOLDER_PRESETS[preset_names[index - 1]]
        if choice.lower() != "c":
            print("Opcion no reconocida. Puedes escribirlos manualmente.")

        print("Ejemplo: name=Nombre, occasion=Ocasion")
        value = input("Placeholders personalizados: ").strip()

        placeholders: dict[str, str] = {}
        for pair in value.split(","):
            if "=" not in pair:
                continue
            key, default = pair.split("=", 1)
            key = key.strip()
            default = default.strip()
            if key and default:
                placeholders[key] = default
        return placeholders or {"name": "Nombre", "occasion": "Ocasion"}

    def ask_free_text(self, label: str) -> str:
        hint = options.FREE_INPUT_HINTS.get(label, "Describe lo que quieres con tus palabras")
        value = input(f"{hint}: ").strip()
        return value

    def interpret_free_option(self, label: str, text: str, values: list[str], default: str) -> str:
        normalized = text.lower()
        if not normalized:
            return default

        if label == "BPM":
            digits = "".join(character for character in normalized if character.isdigit())
            if digits:
                return digits
            if any(word in normalized for word in ["lento", "slow", "balada", "tranquilo"]):
                return "84"
            if any(word in normalized for word in ["rapido", "fast", "bailable", "fiesta"]):
                return "120"
            return "96"

        keyword_matches = {
            "latin": "latin pop",
            "reggaeton": "reggaeton soft",
            "salsa": "salsa pop",
            "rock": "rock pop",
            "acust": "acoustic",
            "acoustic": "acoustic",
            "electron": "electronic pop",
            "cinematic": "cinematic",
            "romant": "romantic",
            "nostalg": "nostalgic",
            "cumple": "celebratory",
            "fiesta": "celebratory",
            "feliz": "celebratory",
            "celebr": "celebratory",
            "agradec": "grateful",
            "famil": "family tribute for {name}",
            "amist": "friendship song for {name}",
            "motiva": "motivational song for {name}",
            "amor": "love song for {name}",
            "birthday": "birthday song for {name}",
            "anniversary": "anniversary song for {name}",
            "spanglish": "Spanglish",
            "ingles": "English",
            "english": "English",
            "espanol": "Spanish",
            "español": "Spanish",
            "menor": "A minor",
            "triste": "A minor",
            "brillante": "G major",
            "alegre": "G major",
            "baja": "low",
            "media": "medium",
            "alta": "high",
            "tranquila": "low",
            "intensa": "high",
            "precoro": "verse, pre chorus, chorus",
            "puente": "verse, chorus, bridge",
            "intro": "intro, verse, chorus",
        }
        for keyword, interpreted in keyword_matches.items():
            if keyword in normalized and interpreted in values:
                return interpreted

        for value in values:
            if value.lower() in normalized:
                return value
        return default

    def interpret_free_multi_option(self, text: str, values: list[str], default: list[str]) -> list[str]:
        normalized = text.lower()
        if not normalized:
            return default

        aliases = {
            "guitarra acustica": "acoustic guitar",
            "guitarra acústica": "acoustic guitar",
            "guitarra nylon": "nylon guitar",
            "guitarra electrica": "electric guitar",
            "guitarra eléctrica": "electric guitar",
            "guitarra limpia": "clean guitar",
            "guitarra ambiental": "ambient guitar",
            "guitarra distorsionada": "distorted guitar",
            "percusion": "latin percussion",
            "percusión": "latin percussion",
            "bateria suave": "soft drums",
            "batería suave": "soft drums",
            "bateria": "pop drums",
            "batería": "pop drums",
            "bajo": "electric bass",
            "sub bajo": "sub bass",
            "cuerdas": "strings",
            "sintetizador": "synth pads",
            "metales": "brass",
            "trompeta": "trumpet",
            "saxofon": "saxophone",
            "saxofón": "saxophone",
            "flauta": "flute",
            "acordeon": "accordion",
            "acordeón": "accordion",
            "piano": "piano",
        }
        selected: list[str] = []
        for keyword, value in aliases.items():
            if keyword in normalized and value in values and value not in selected:
                selected.append(value)
        for value in values:
            if value.lower() in normalized and value not in selected:
                selected.append(value)
        return selected or default

    def interpret_free_placeholders(self, text: str) -> dict[str, str]:
        normalized = text.lower()
        placeholders = {"name": "Nombre"}
        if any(word in normalized for word in ["ocasion", "ocasión", "evento"]):
            placeholders["occasion"] = "Ocasion"
        if "edad" in normalized:
            placeholders["age"] = "Edad"
        if any(word in normalized for word in ["anos", "años", "aniversario"]):
            placeholders["years"] = "Anos"
        if any(word in normalized for word in ["recuerdo", "memoria"]):
            placeholders["memory"] = "Recuerdo"
        if any(word in normalized for word in ["familia", "mama", "mamá", "papa", "papá"]):
            placeholders["family_role"] = "Rol familiar"
        return placeholders

