from __future__ import annotations

from dataclasses import dataclass
import math
import re
import wave
from pathlib import Path


KEY_ROOTS = {
    "C": 261.63,
    "D": 293.66,
    "E": 329.63,
    "F": 349.23,
    "G": 392.00,
    "A": 440.00,
    "B": 493.88,
}

MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11, 12)
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10, 12)
VOWELS = ("a", "e", "i", "o", "u")


@dataclass(frozen=True)
class MockSongRenderContext:
    project_name: str
    description: str
    instrumental_intent: dict[str, object]
    melody_intent: dict[str, object]
    lyrics_intent: dict[str, object]
    lyrics_markdown: str


class MockSongRenderer:
    sample_rate = 44100
    sample_width = 2
    channel_count = 1

    def render(self, context: MockSongRenderContext, exports_dir: Path, stems_dir: Path) -> dict[str, object]:
        exports_dir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        bpm = self._bpm(context)
        key = self._key(context)
        scale = MINOR_SCALE if "minor" in key.lower() else MAJOR_SCALE
        root = self._root_frequency(key)
        lyric_lines = self._lyric_lines(context.lyrics_markdown)
        duration_seconds = self._duration_seconds(lyric_lines, bpm)

        instrumental = self._instrumental_frames(duration_seconds, bpm, root, scale)
        melody = self._melody_frames(duration_seconds, bpm, root, scale, lyric_lines)
        vocals = self._vocal_frames(duration_seconds, bpm, root, scale, lyric_lines)
        final_mix = self._mix_frames(instrumental, melody, vocals)

        instrumental_path = stems_dir / "instrumental.wav"
        melody_path = stems_dir / "melody_guide.wav"
        vocals_path = stems_dir / "vocals.wav"
        final_mix_path = exports_dir / "final_mix.wav"

        self._write_wav(instrumental_path, instrumental)
        self._write_wav(melody_path, melody)
        self._write_wav(vocals_path, vocals)
        self._write_wav(final_mix_path, final_mix)

        return {
            "mode": "mock_vocal_guide_audio",
            "bpm": bpm,
            "key": key,
            "duration_seconds": duration_seconds,
            "lyric_lines_used": len(lyric_lines),
            "stems": {
                "instrumental": str(instrumental_path),
                "melody_guide": str(melody_path),
                "vocals": str(vocals_path),
            },
            "wav": str(final_mix_path),
            "note": (
                "Maqueta mock audible: instrumental sintetico + guia vocal de vocales. "
                "No pronuncia la letra ni reemplaza una voz cantada real; para eso falta conectar RVC/ACE-Step "
                "u otro provider de voz."
            ),
        }

    def _instrumental_frames(self, duration_seconds: int, bpm: int, root: float, scale: tuple[int, ...]) -> list[int]:
        total_frames = duration_seconds * self.sample_rate
        beat_seconds = 60 / bpm
        bar_seconds = beat_seconds * 4
        chords = (
            (0, 4, 7),
            (5, 9, 12),
            (7, 11, 14),
            (4, 7, 11),
        )
        frames: list[int] = []
        for frame in range(total_frames):
            time = frame / self.sample_rate
            chord = chords[int(time / bar_seconds) % len(chords)]
            pad = 0.0
            for degree in chord:
                pad += math.sin(2 * math.pi * self._transpose(root, degree) * time) * 0.10
            pulse_degree = scale[int(time / beat_seconds) % len(scale)] - 12
            pulse = math.sin(2 * math.pi * self._transpose(root, pulse_degree) * time) * 0.12
            bell = 0.0
            beat_position = time % beat_seconds
            if beat_position < 0.14:
                bell_freq = self._transpose(root, scale[int(time / beat_seconds) % len(scale)] + 12)
                bell = math.sin(2 * math.pi * bell_freq * time) * self._decay(beat_position, 0.14) * 0.16
            frames.append(self._clip((pad + pulse + bell) * 9000))
        return frames

    def _melody_frames(
        self,
        duration_seconds: int,
        bpm: int,
        root: float,
        scale: tuple[int, ...],
        lyric_lines: list[str],
    ) -> list[int]:
        total_frames = duration_seconds * self.sample_rate
        beat_seconds = 60 / bpm
        note_seconds = beat_seconds * 1.5
        phrase_pause_seconds = beat_seconds * 0.5
        notes = [scale[index] + 12 for index in (0, 2, 4, 5, 4, 2, 1, 0)]
        line_words = [max(1, len(re.findall(r"\w+", line))) for line in lyric_lines] or [8]
        frames: list[int] = []
        for frame in range(total_frames):
            time = frame / self.sample_rate
            phrase_index = int(time / (note_seconds * 4 + phrase_pause_seconds))
            word_count = line_words[phrase_index % len(line_words)]
            phrase_time = time % (note_seconds * 4 + phrase_pause_seconds)
            if phrase_time > note_seconds * 4:
                frames.append(0)
                continue
            note_index = int(phrase_time / note_seconds)
            note_time = phrase_time % note_seconds
            scale_degree = notes[(phrase_index + note_index + word_count) % len(notes)]
            frequency = self._transpose(root, scale_degree)
            vibrato = 1 + 0.006 * math.sin(2 * math.pi * 5.2 * time)
            envelope = min(1.0, note_time / 0.08) * self._decay(note_time, note_seconds)
            voice = math.sin(2 * math.pi * frequency * vibrato * time)
            soft_formant = math.sin(2 * math.pi * frequency * 2 * time) * 0.18
            frames.append(self._clip((voice + soft_formant) * envelope * 4500))
        return frames

    def _vocal_frames(
        self,
        duration_seconds: int,
        bpm: int,
        root: float,
        scale: tuple[int, ...],
        lyric_lines: list[str],
    ) -> list[int]:
        total_frames = duration_seconds * self.sample_rate
        beat_seconds = 60 / bpm
        syllable_seconds = beat_seconds * 0.82
        phrase_seconds = syllable_seconds * 6
        words = self._lyric_words(lyric_lines)
        notes = [scale[index] + 12 for index in (0, 1, 2, 4, 5, 4, 2, 0)]
        frames: list[int] = []
        for frame in range(total_frames):
            time = frame / self.sample_rate
            phrase_index = int(time / phrase_seconds)
            phrase_time = time % phrase_seconds
            syllable_index = int(phrase_time / syllable_seconds)
            syllable_time = phrase_time % syllable_seconds
            word = words[(phrase_index * 6 + syllable_index) % len(words)]
            vowel = self._dominant_vowel(word)
            scale_degree = notes[(phrase_index + syllable_index + len(word)) % len(notes)]
            frequency = self._transpose(root, scale_degree)
            vibrato = 1 + 0.01 * math.sin(2 * math.pi * 4.8 * time)
            envelope = self._adsr(syllable_time, syllable_seconds, 0.06, 0.16)
            breath = math.sin(2 * math.pi * frequency * vibrato * time) * 0.58
            first_harmonic = math.sin(2 * math.pi * frequency * 2 * vibrato * time) * 0.20
            second_harmonic = math.sin(2 * math.pi * frequency * 3 * vibrato * time) * 0.08
            vowel_color = self._vowel_color(vowel, frequency, time) * 0.44
            frames.append(self._clip((breath + first_harmonic + second_harmonic + vowel_color) * envelope * 10500))
        return frames

    def _mix_frames(self, instrumental: list[int], melody: list[int], vocals: list[int]) -> list[int]:
        return [
            self._clip(instrument * 0.42 + guide * 0.16 + voice * 0.86)
            for instrument, guide, voice in zip(instrumental, melody, vocals)
        ]

    def _write_wav(self, path: Path, frames: list[int]) -> None:
        with wave.open(str(path), "wb") as wav_file:
            wav_file.setnchannels(self.channel_count)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            for value in frames:
                wav_file.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))

    def _bpm(self, context: MockSongRenderContext) -> int:
        raw_bpm = context.instrumental_intent.get("bpm") or context.melody_intent.get("bpm") or 88
        return max(52, min(144, int(raw_bpm)))

    def _key(self, context: MockSongRenderContext) -> str:
        return str(context.instrumental_intent.get("key") or context.melody_intent.get("key") or "C major")

    def _root_frequency(self, key: str) -> float:
        match = re.search(r"[A-G]", key.upper())
        return KEY_ROOTS.get(match.group(0), KEY_ROOTS["C"]) if match else KEY_ROOTS["C"]

    def _duration_seconds(self, lyric_lines: list[str], bpm: int) -> int:
        beat_seconds = 60 / bpm
        estimated = max(8, len(lyric_lines) * beat_seconds * 4)
        return int(min(75, max(18, estimated)))

    def _lyric_lines(self, lyrics_markdown: str) -> list[str]:
        lines: list[str] = []
        for raw_line in lyrics_markdown.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or ":" in line:
                continue
            lines.append(line)
        return lines

    def _lyric_words(self, lyric_lines: list[str]) -> list[str]:
        words = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]+", " ".join(lyric_lines).lower())
        return words or ["canta", "suave", "amor"]

    def _dominant_vowel(self, word: str) -> str:
        for letter in word:
            normalized = self._normalize_vowel(letter)
            if normalized in VOWELS:
                return normalized
        return "a"

    def _normalize_vowel(self, letter: str) -> str:
        return {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
        }.get(letter.lower(), letter.lower())

    def _vowel_color(self, vowel: str, frequency: float, time: float) -> float:
        formants = {
            "a": (2.0, 3.0, 4.0),
            "e": (2.4, 3.6, 5.0),
            "i": (3.0, 4.4, 6.0),
            "o": (1.6, 2.4, 3.4),
            "u": (1.3, 2.0, 2.8),
        }[vowel]
        return sum(
            math.sin(2 * math.pi * frequency * ratio * time) * (0.24 / (index + 1))
            for index, ratio in enumerate(formants)
        )

    def _adsr(self, time: float, length: float, attack: float, release: float) -> float:
        if time < attack:
            return time / attack
        if time > length - release:
            return max(0.0, (length - time) / release)
        return 1.0

    def _transpose(self, root: float, semitones: int) -> float:
        return root * (2 ** (semitones / 12))

    def _decay(self, time: float, length: float) -> float:
        if length <= 0:
            return 0
        position = min(1.0, max(0.0, time / length))
        return max(0.0, 1 - position * position)

    def _clip(self, value: float) -> int:
        return max(-32767, min(32767, int(value)))
