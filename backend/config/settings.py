from dataclasses import dataclass
from pathlib import Path

from config.model_settings import HuggingFaceModelSettings, LocalModelSettings


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    hf_models: HuggingFaceModelSettings
    local_models: LocalModelSettings
    app_name: str = "Song AI Generator"

    @classmethod
    def load(cls) -> "Settings":
        project_root = Path(__file__).resolve().parents[2]
        return cls(
            project_root=project_root,
            data_dir=project_root / "data",
            hf_models=HuggingFaceModelSettings.load(project_root),
            local_models=LocalModelSettings.load(project_root),
        )
