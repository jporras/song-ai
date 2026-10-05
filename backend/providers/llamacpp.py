from __future__ import annotations

import json
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

from config.model_settings import LocalModelSettings
from providers.base import InterpreterProvider, LyricsProvider


class LlamaCppError(RuntimeError):
    pass


class LlamaCppClient:
    def __init__(self, settings: LocalModelSettings, base_url: str | None = None, template: str = "gemma") -> None:
        self.settings = settings
        self.base_url = (base_url or settings.llama_cpp_base_url).rstrip("/")
        self.template = template

    def complete(self, prompt: str, system_prompt: str = "", n_predict: int | None = None) -> str:
        payload = {
            "prompt": self._format_prompt(prompt, system_prompt),
            "n_predict": n_predict or self.settings.llama_cpp_n_predict,
            "temperature": self.settings.llama_cpp_temperature,
            "stop": ["</s>", "<end_of_turn>", "<|im_end|>"],
        }
        data = self._post_json("/completion", payload)
        content = self._clean_content(str(data.get("content") or data.get("response") or ""))
        if not str(content).strip():
            raise LlamaCppError("llama.cpp respondio sin contenido.")
        return str(content).strip()

    def _clean_content(self, content: str) -> str:
        cleaned = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()

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
        if self.template == "qwen":
            qwen_prompt = f"/no_think\n{prompt.strip()}"
            if system_prompt:
                return (
                    "<|im_start|>system\n"
                    f"{system_prompt.strip()}<|im_end|>\n"
                    "<|im_start|>user\n"
                    f"{qwen_prompt}<|im_end|>\n"
                    "<|im_start|>assistant\n"
                )
            return f"<|im_start|>user\n{qwen_prompt}<|im_end|>\n<|im_start|>assistant\n"
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
        self.client = LlamaCppClient(settings, settings.llama_cpp_interpreter_base_url, template="gemma")

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
        content = self.client.complete(text, n_predict=self.settings.llama_cpp_interpreter_n_predict)
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
        self.client = LlamaCppClient(settings, settings.llama_cpp_technical_base_url, template="qwen")

    def name(self) -> str:
        return "llamacpp-qwen-technical"

    def capabilities(self) -> list[str]:
        return [
            "song_spec_compilation_and_review",
            "music_and_singing_feasibility",
            "engine_capability_alignment",
            "production_and_fidelity_review",
            "user_creative_decisions_preserved",
        ]

    def interpret(self, text: str, target: str) -> dict[str, object]:
        content = self.client.complete(text, n_predict=self.settings.llama_cpp_technical_n_predict)
        return {
            "target": target,
            "input": text,
            "mode": "llama_cpp",
            "model": self.settings.technical_model,
            "summary": content,
        }
