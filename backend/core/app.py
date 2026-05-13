from config.settings import Settings
from builders.full_song_builder import FullSongBuilder
from builders.export_builder import ExportBuilder
from builders.sample_builder import SampleBuilder
from builders.set_builder import SetBuilder
from builders.template_builder import TemplateBuilder
from audio.mixer import AudioMixer
from core.menu import MainMenu
from core.storage import StorageManager
from explorers.mock_explorers import MockExplorerSuite
from providers.registry import ProviderRegistry


class SongAIApp:
    def __init__(self) -> None:
        self.settings = Settings.load()
        self.storage = StorageManager(self.settings.data_dir)
        self.explorers = MockExplorerSuite(self.storage)
        self.set_builder = SetBuilder(self.storage)
        self.sample_builder = SampleBuilder(self.storage)
        self.full_song_builder = FullSongBuilder(self.storage)
        self.audio_mixer = AudioMixer(self.storage)
        self.export_builder = ExportBuilder(self.storage)
        self.template_builder = TemplateBuilder(self.storage)
        self.provider_registry = ProviderRegistry()
        self.menu = MainMenu(
            self.settings,
            self.storage,
            self.explorers,
            self.set_builder,
            self.sample_builder,
            self.full_song_builder,
            self.audio_mixer,
            self.export_builder,
            self.template_builder,
            self.provider_registry,
        )

    def run(self) -> None:
        self.storage.ensure_project_layout()
        self.menu.run()

