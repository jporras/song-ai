from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config.settings import Settings
from core.storage import StorageManager
from providers.registry import ProviderRegistry


def main() -> None:
    settings = Settings.load()
    storage = StorageManager(settings.data_dir)
    providers = ProviderRegistry(settings.hf_models, settings.local_models)
    created = storage.ensure_project_layout()
    studio_status = providers.studio_status()

    print("=== Song AI Diagnostics ===")
    print(f"Raiz del proyecto: {settings.project_root}")
    print(f"Directorio de datos: {settings.data_dir}")
    print("Providers: preparados para mocks/local/pro")
    print(f"Roles listos: {', '.join(studio_status['ready_roles'])}")
    print("Assets: instrumental, melodia y letra separados")
    print()

    if created:
        print("Carpetas creadas:")
        for folder in created:
            print(f"- {folder}")
    else:
        print("La estructura de carpetas ya estaba lista.")

    print()
    print("Carpetas de datos:")
    for folder in storage.list_data_folders():
        print(f"- {folder}")


if __name__ == "__main__":
    main()
