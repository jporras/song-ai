import sys
import os

print("="*60)
print("SISTEMA DE DIAGNÓSTICO SONG-AI: INTEL XPU DETECTION")
print("="*60)

# 1. Información del Entorno Base
print(f"[*] Versión de Python: {sys.version}")
try:
    import torch
    print(f"[*] Versión de PyTorch: {torch.__version__}")
except ImportError:
    print("[CRÍTICO] PyTorch no está instalado en este entorno virtual.")
    sys.exit(1)

# 2. Verificación de Variables de Entorno Clave para Intel
print("\n[*] Variables de entorno detectadas:")
env_vars = ['ONEAPI_ROOT', 'XPU_DEVICE_ORDER', 'ZE_AFFINITY_MASK', 'PYTORCH_ENABLE_XPU_FALLBACK']
for var in env_vars:
    print(f"    - {var}: {os.environ.get(var, 'No definida')}")

# 3. Verificación de Disponibilidad de XPU
xpu_available = False
try:
    # Intentar importar la extensión de Intel si es necesaria en esta compilación de torch
    import intel_extension_for_pytorch as ipex
    print(f"[*] Intel Extension for PyTorch (IPEX) detectada: {ipex.__version__}")
except ImportError:
    print("[INFO] IPEX no importada explícitamente (Verificando soporte nativo de torch.xpu)...")

if hasattr(torch, 'xpu'):
    xpu_available = torch.xpu.is_available()
    print(f"[*] torch.xpu.is_available(): {xpu_available}")
else:
    print("[FALLO] El binario de PyTorch instalado no incluye el módulo torch.xpu")

# 4. Auditoría de Dispositivos y Prueba de Estrés de Memoria
if xpu_available:
    try:
        device_count = torch.xpu.device_count()
        print(f"[*] Cantidad de dispositivos XPU: {device_count}")
        
        for i in range(device_count):
            device_name = torch.xpu.get_device_name(i)
            print(f"    - Dispositivo [{i}]: {device_name}")
        
        # Seleccionar dispositivo por defecto
        current_dev = torch.xpu.current_device()
        print(f"[*] Dispositivo XPU activo por defecto: {current_dev} ({torch.xpu.get_device_name(current_dev)})")
        
        # PRUEBA DE CARGA: Forzar alojamiento de un tensor en la iGPU
        print("\n[*] Realizando prueba de asignación de tensores en XPU...")
        device = torch.device("xpu")
        x = torch.randn(5000, 5000, device=device) # Matriz aleatoria sustancial
        y = torch.matmul(x, x)
        torch.xpu.synchronize()
        print("[ÉXITO] Tensor alojado y multiplicado en iGPU correctamente.")
        
        # Memoria (si el driver lo reporta)
        if hasattr(torch.xpu, 'memory_allocated'):
            print(f"    - Memoria asignada en XPU: {torch.xpu.memory_allocated(current_dev) / 1024**2:.2f} MB")
            
    except Exception as e:
        print(f"[CRÍTICO] Error al interactuar con el dispositivo XPU: {e}")
        print("[MOTIVO] Probablemente incompatibilidad entre el driver gráfico de Intel y la versión de IPEX/Torch.")
else:
    print("\n[CRÍTICO] CRITERIO DE FALLO ALCANZADO: XPU no está disponible para PyTorch.")
    print("[CONSEJO] Verifica que tengas instalado el 'Intel Graphics Driver' más reciente y las 'oneAPI Base Toolkit' Runtimes.")

print("="*60)