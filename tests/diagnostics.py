from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from config.settings import Settings
from core.storage import StorageManager


def main() -> None:
    settings = Settings.load()
    storage = StorageManager(settings.data_dir)
    created = storage.ensure_project_layout()

    print("=== Song AI Diagnostics ===")
    print(f"Raiz del proyecto: {settings.project_root}")
    print(f"Directorio de datos: {settings.data_dir}")
    print("Providers: preparados para mocks/local/pro")
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
