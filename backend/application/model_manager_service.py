from __future__ import annotations


class ModelManagerService:
    def __init__(self, max_loaded_models: int = 1) -> None:
        self.max_loaded_models = max_loaded_models
        self.loaded_models: list[str] = []

    def load_model(self, model_name: str) -> dict[str, object]:
        if model_name not in self.loaded_models:
            while len(self.loaded_models) >= self.max_loaded_models:
                self.unload_model(self.loaded_models[0])
            self.loaded_models.append(model_name)
        return self.get_model_status(model_name)

    def unload_model(self, model_name: str) -> dict[str, object]:
        self.loaded_models = [name for name in self.loaded_models if name != model_name]
        return self.get_model_status(model_name)

    def run_model(self, model_name: str, input_payload: dict[str, object]) -> dict[str, object]:
        self.load_model(model_name)
        return {
            "model_name": model_name,
            "status": "completed",
            "memory_strategy": "load_on_demand_release_after_task",
            "input_keys": sorted(input_payload),
        }

    def get_model_status(self, model_name: str) -> dict[str, object]:
        return {
            "model_name": model_name,
            "loaded": model_name in self.loaded_models,
            "loaded_models": list(self.loaded_models),
            "max_loaded_models": self.max_loaded_models,
        }

    def estimate_memory(self, model_name: str) -> dict[str, object]:
        estimates = {
            "gemma": "4-8GB segun cuantizacion GGUF",
            "qwen": "4-8GB segun cuantizacion GGUF",
            "musicgen": "6-12GB segun modelo y device",
            "xtts": "4-8GB segun backend",
            "rvc": "2-6GB segun modelo",
        }
        key = model_name.lower()
        estimate = next((value for name, value in estimates.items() if name in key), "desconocido")
        return {
            "model_name": model_name,
            "estimated_memory": estimate,
            "policy": "no cargar todos los modelos al mismo tiempo",
        }
