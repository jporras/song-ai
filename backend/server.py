import uvicorn

from bootstrap.docker_bootstrap import run_bootstrap


if __name__ == "__main__":
    bootstrap_summary = run_bootstrap()
    if bootstrap_summary["enabled"]:
        print(f"Song AI bootstrap: {bootstrap_summary}", flush=True)
    uvicorn.run("adapters.http.fastapi_app:app", host="0.0.0.0", port=8000)
