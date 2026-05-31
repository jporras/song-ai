@echo off
setlocal

REM ACE-Step 1.5 REST API launcher for Intel XPU using this project's .venv.
REM Based on the upstream XPU launcher, but keeps Song-AI's PyTorch XPU stack.

cd /d "%~dp0.."

set SYCL_CACHE_PERSISTENT=1
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set PYTORCH_DEVICE=xpu
set TORCH_COMPILE_BACKEND=eager
set TOKENIZERS_PARALLELISM=false
set CUDA_VISIBLE_DEVICES=

set ACESTEP_CONFIG_PATH=acestep-v15-turbo
set ACESTEP_LM_BACKEND=pt
if "%ACESTEP_LM_MODEL_PATH%"=="" set ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-0.6B
if "%ACESTEP_INIT_LLM%"=="" set ACESTEP_INIT_LLM=false
if "%ACESTEP_CHECKPOINTS_DIR%"=="" set ACESTEP_CHECKPOINTS_DIR=%CD%\data\models\music\acestep-1.5-2b-turbo
if "%ACESTEP_API_HOST%"=="" set ACESTEP_API_HOST=127.0.0.1
if "%ACESTEP_API_PORT%"=="" set ACESTEP_API_PORT=8001

if not exist ".venv\Scripts\python.exe" (
  echo [FAIL] .venv\Scripts\python.exe no existe. Ejecuta scripts\setup-local.ps1 primero.
  exit /b 1
)

".venv\Scripts\python.exe" -c "import torch; assert hasattr(torch, 'xpu') and torch.xpu.is_available(), 'Intel XPU no detectado'; print('[OK] XPU:', torch.xpu.get_device_name(0)); print('[OK] torch:', torch.__version__)"
if errorlevel 1 exit /b 1

echo [OK] ACESTEP_CONFIG_PATH=%ACESTEP_CONFIG_PATH%
echo [OK] ACESTEP_LM_BACKEND=%ACESTEP_LM_BACKEND%
echo [OK] ACESTEP_LM_MODEL_PATH=%ACESTEP_LM_MODEL_PATH%
echo [OK] ACESTEP_CHECKPOINTS_DIR=%ACESTEP_CHECKPOINTS_DIR%
echo [OK] API http://%ACESTEP_API_HOST%:%ACESTEP_API_PORT%

".venv\Scripts\python.exe" -u -m acestep.api_server --host %ACESTEP_API_HOST% --port %ACESTEP_API_PORT% --lm-model-path %ACESTEP_LM_MODEL_PATH%

endlocal
