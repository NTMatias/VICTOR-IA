"""Detección informativa. Ollama decide automáticamente la descarga a GPU."""
import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def detect_gpu():
    executable = shutil.which("nvidia-smi")
    if not executable:
        candidate = Path(os.environ.get("WINDIR", "C:/Windows")) / "System32/nvidia-smi.exe"
        executable = str(candidate) if candidate.is_file() else None
    if executable:
        try:
            result = subprocess.run([executable, "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if result.returncode == 0 and result.stdout.strip():
                return {"nvidia": True, "description": result.stdout.strip()[:300]}
        except (OSError, subprocess.TimeoutExpired):
            pass
    return {"nvidia": False, "description": "GPU NVIDIA no detectada; modo CPU disponible. Ollama puede detectar otros dispositivos."}
