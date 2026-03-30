# -*- coding: utf-8 -*-
"""
runtime_capabilities.py — Jarvis V5 GPU & Hardware Detection
Detects VRAM to help ModelRouter avoid crashing the system or running out of memory.
"""

import shutil
import platform
import subprocess

class RuntimeCapabilities:
    def __init__(self):
        self.info = self._detect()

    def _detect(self) -> dict:
        info = {
            "os": platform.system(),
            "gpu_available": False,
            "gpu_name": None,
            "vram_gb": 0.0,
            "recommended_primary": "llama3:8b",
            "recommended_fast": "phi3:mini"
        }
        
        # Check for NVIDIA SMI
        try:
            if shutil.which("nvidia-smi"):
                out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                    encoding="utf-8"
                ).strip()
                if out:
                    parts = out.split(",")
                    info["gpu_available"] = True
                    info["gpu_name"] = parts[0].strip()
                    # Example: "8192 MiB" -> 8.0 GB
                    mem_str = parts[1].strip()
                    if "MiB" in mem_str:
                        info["vram_gb"] = round(int(mem_str.replace("MiB", "").strip()) / 1024, 1)

            # Apple Silicon detection fallback
            elif platform.system() == "Darwin" and platform.machine() == "arm64":
                info["gpu_available"] = True
                info["gpu_name"] = "Apple Silicon"
                info["vram_gb"] = 16.0  # Unified memory assumption

        except Exception as e:
            print(f"[Runtime] Hardware detection error: {e}")

        # Scale down recommendations if memory is very tight
        if info["gpu_available"] and info["vram_gb"] < 6.0:
            info["recommended_primary"] = "phi3:mini"
            info["recommended_fast"] = "tinydolphin"
            
        return info

    def get_summary(self) -> dict:
        return self.info
