"""Run with the project's Python: python scripts/audit_studio.py --output docs/studio-audit.json."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from adapters.runtime_audit import RuntimeAudit
from config.settings import Settings
from adapters.runtime_probe import probe_runtime
from adapters.acestep_import_probe import probe_acestep_import


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only studio capability audit; no model execution.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--probe-runtime", action="store_true", help="Probe torch devices and loopback health; no weights or generation.")
    parser.add_argument("--probe-api-import", action="store_true", help="Import ACE-Step in isolated process without instantiating a model.")
    args = parser.parse_args()
    settings = Settings.load().local_models
    report = RuntimeAudit(ROOT, settings).run()
    if args.probe_runtime:
        report["runtime_probe"] = probe_runtime(ROOT, {
            "gemma": settings.llama_cpp_interpreter_base_url,
            "qwen": settings.llama_cpp_technical_base_url,
        })
        report["limitations"][0] = "Runtime probe imports torch in bounded subprocess; no weights, generation or audio evaluation."
    if args.probe_api_import:
        report["ace_step_import_probe"] = probe_acestep_import(ROOT)
        report["limitations"].append("Opt-in API import probe does not instantiate a handler or prove checkpoint execution.")
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Audit saved: {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
