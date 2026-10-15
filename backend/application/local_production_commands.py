"""Compose only the dependencies needed by the selected local command."""
from application.local_production_context import LocalProductionContext


class LocalProductionCommands:
    def __init__(self, storage, settings=None):
        self.storage, self.settings = storage, settings

    def execute(self, operation, song_id, **kwargs):
        context = LocalProductionContext(self.storage)
        config = self.settings.local_models if self.settings else None
        resources = self.settings.resource_monitor if self.settings else None
        timeout = config.local_command_timeout_seconds if config else 3600
        if operation == 'music_plan':
            from application.local_planning_commands import GenerateLocalMusicPlan
            from application.music_plan_service import MusicPlanService
            command = GenerateLocalMusicPlan(context, MusicPlanService(self.storage))
        elif operation == 'midi':
            from application.local_planning_commands import GenerateLocalMidi
            from application.midi_generation_service import MidiGenerationService
            command = GenerateLocalMidi(context, MidiGenerationService(self.storage))
        elif operation == 'instrumental':
            from application.local_stem_commands import GenerateLocalInstrumental
            from application.instrumental_generation_service import InstrumentalGenerationService
            command = GenerateLocalInstrumental(context, InstrumentalGenerationService(self.storage,
                command_template=config.soundtrack_command if config else '', timeout_seconds=timeout))
        elif operation == 'vocals':
            from application.local_stem_commands import GenerateLocalVocals
            from application.vocal_synthesis_service import VocalSynthesisService
            command = GenerateLocalVocals(context, VocalSynthesisService(self.storage,
                command_template=config.singing_voice_command if config else '', timeout_seconds=timeout,
                resource_settings=resources))
        elif operation == 'voice_conversion':
            from application.local_stem_commands import ConvertLocalVoice
            from application.voice_conversion_service import VoiceConversionService
            command = ConvertLocalVoice(context, VoiceConversionService(self.storage,
                command_template=config.voice_conversion_command if config else '', timeout_seconds=timeout))
        elif operation == 'mix':
            from application.local_mix_command import MixLocalSong
            from application.mixing_service import MixingService
            command = MixLocalSong(context, MixingService(self.storage))
        elif operation == 'master':
            from application.local_master_command import MasterLocalSong
            from application.professional_full_song_service import ProfessionalFullSongService
            from application.mixing_service import MixingService
            from application.mastering_service import MasteringService
            command = MasterLocalSong(context, ProfessionalFullSongService(self.storage,
                command_template=config.full_song_command if config else '', timeout_seconds=timeout,
                resource_settings=resources), MixingService(self.storage), MasteringService(self.storage))
        else:
            raise ValueError('Comando de producción no reconocido.')
        return command.execute(song_id, **kwargs)
