from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from config.model_settings import LocalModelSettings
from providers.base import InterpreterProvider, LyricsProvider


class LlamaCppError(RuntimeError):
    pass


class LlamaCppClient:
    def __init__(self, settings: LocalModelSettings) -> None:
        self.settings = settings
        self.base_url = settings.llama_cpp_base_url.rstrip("/")

    def complete(self, prompt: str, system_prompt: str = "") -> str:
        payload = {
            "prompt": self._format_prompt(prompt, system_prompt),
            "n_predict": self.settings.llama_cpp_n_predict,
            "temperature": self.settings.llama_cpp_temperature,
            "stop": ["</s>", "<end_of_turn>"],
        }
        data = self._post_json("/completion", payload)
        content = data.get("content") or data.get("response") or ""
        if not str(content).strip():
            raise LlamaCppError("llama.cpp respondio sin contenido.")
        return str(content).strip()

    def status(self) -> dict[str, object]:
        try:
            data = self._get_json("/health")
            return {"available": True, "endpoint": "/health", "data": data}
        except LlamaCppError:
            try:
                data = self._get_json("/props")
                return {"available": True, "endpoint": "/props", "data": data}
            except LlamaCppError as error:
                return {"available": False, "endpoint": self.base_url, "error": str(error)}

    def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._request_json(request)

    def _get_json(self, path: str) -> dict[str, object]:
        request = Request(f"{self.base_url}{path}", method="GET")
        return self._request_json(request)

    def _request_json(self, request: Request) -> dict[str, object]:
        try:
            with urlopen(request, timeout=self.settings.llama_cpp_timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as error:
            raise LlamaCppError(str(error)) from error

    def _format_prompt(self, prompt: str, system_prompt: str) -> str:
        if system_prompt:
            return (
                "<start_of_turn>user\n"
                f"{system_prompt.strip()}\n\n{prompt.strip()}"
                "<end_of_turn>\n<start_of_turn>model\n"
            )
        return f"<start_of_turn>user\n{prompt.strip()}<end_of_turn>\n<start_of_turn>model\n"


class LlamaCppInterpreterProvider(InterpreterProvider):
    def __init__(self, settings: LocalModelSettings) -> None:
        self.settings = settings
        self.client = LlamaCppClient(settings)

    def name(self) -> str:
        return "llamacpp-gemma-interpreter"

    def capabilities(self) -> list[str]:
        return [
            "active_project_assistance",
            "missing_step_detection",
            "songwriting_guidance_from_sqlite_context",
            "llama_cpp_completion",
        ]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        system_prompt = (
            "Eres Gemma dentro de Song AI. Ayudas al usuario a completar una cancion completa "
            "desde proyecto activo hasta MP3 final, preservando intencion instrumental, vocal y lirica."
        )
        content = self.client.complete(text, system_prompt=system_prompt)
        return {
            "target": target,
            "input": text,
            "mode": "llama_cpp",
            "model": self.settings.interpreter_model,
            "summary": content,
        }

    def status(self) -> dict[str, object]:
        return self.client.status()


class LlamaCppLyricsProvider(LyricsProvider):
    def __init__(self, settings: LocalModelSettings) -> None:
        self.settings = settings

    def name(self) -> str:
        return "llamacpp-gemma-lyrics"

    def capabilities(self) -> list[str]:
        return [
            "complete_original_lyrics",
            "meter_and_rhyme_guidance",
            "song_structure_review",
            "music_prompt_generation",
        ]


class LlamaCppTechnicalProvider(InterpreterProvider):
    def __init__(self, settings: LocalModelSettings) -> None:
        self.settings = settings
        self.client = LlamaCppClient(settings)

    def name(self) -> str:
        return "llamacpp-qwen-technical"

    def capabilities(self) -> list[str]:
        return [
            "code_and_debugging_support",
            "architecture_adjustments",
            "worker_pipeline_guidance",
            "ffmpeg_audio_export_support",
            "non_creative_technical_role",
        ]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        system_prompt = (
            "Eres Qwen3 dentro de Song AI. Tu rol es tecnico: codigo, debugging, arquitectura, "
            "workers, ffmpeg, SQLite y pipeline. No reemplazas a Gemma en creatividad musical."
        )
        content = self.client.complete(text, system_prompt=system_prompt)
        return {
            "target": target,
            "input": text,
            "mode": "llama_cpp",
            "model": self.settings.technical_model,
            "summary": content,
        }
