from abc import ABC, abstractmethod


class MusicProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError


class VoiceProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError


class LyricsProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError


class InterpreterProvider(ABC):
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def interpret(self, text: str, target: str) -> dict[str, object]:
        raise NotImplementedError
