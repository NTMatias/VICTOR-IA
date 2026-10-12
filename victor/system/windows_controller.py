import os
import platform
import subprocess
from victor.errors import VictorError
from victor.system.apps import require_windows


class WindowsController:
    DIAGNOSTICS = {"ipconfig": ["ipconfig.exe"], "whoami": ["whoami.exe"], "hostname": ["hostname.exe"], "systeminfo": ["systeminfo.exe"]}

    def get_system_info(self):
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(os.path.abspath(os.sep))
        battery = psutil.sensors_battery()
        processes = []
        for p in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                processes.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda p: p.get("memory_percent") or 0, reverse=True)
        return {"sistema": platform.platform(), "cpu_porcentaje": psutil.cpu_percent(interval=0.25),
                "ram_porcentaje": memory.percent, "ram_usada_GB": round(memory.used / 2**30, 2),
                "ram_total_GB": round(memory.total / 2**30, 2), "disco_porcentaje": disk.percent,
                "disco_libre_GB": round(disk.free / 2**30, 2), "procesos_mayor_ram": processes[:25],
                "bateria": {"porcentaje": battery.percent, "cargando": battery.power_plugged} if battery else "No disponible"}

    def control_volume(self, level):
        require_windows()
        import comtypes
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        try:
            device = AudioUtilities.GetSpeakers()
            volume = device.EndpointVolume
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return {"volumen": round(volume.GetMasterVolumeLevelScalar() * 100)}
        finally:
            comtypes.CoUninitialize()

    def adjust_volume(self, action):
        require_windows()
        import comtypes
        from pycaw.pycaw import AudioUtilities
        comtypes.CoInitialize()
        try:
            endpoint = AudioUtilities.GetSpeakers().EndpointVolume
            if action == "mute":
                endpoint.SetMute(1, None)
                return {"silenciado": True}
            level = max(0, min(1, endpoint.GetMasterVolumeLevelScalar() + (0.1 if action == "up" else -0.1)))
            endpoint.SetMasterVolumeLevelScalar(level, None)
            return {"volumen": round(level * 100)}
        finally:
            comtypes.CoUninitialize()

    def open_settings(self):
        require_windows()
        os.startfile("ms-settings:")
        return {"solicitud_apertura": "Configuración de Windows"}

    def run_diagnostic(self, command):
        require_windows()
        if command not in self.DIAGNOSTICS:
            raise VictorError("Terminal restringida: solo ipconfig, whoami, hostname y systeminfo, sin argumentos.")
        executable = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "System32", self.DIAGNOSTICS[command][0])
        result = subprocess.run([executable], shell=False, capture_output=True, timeout=20,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        return {"codigo": result.returncode, "salida": result.stdout.decode("cp850", errors="replace")[:16000],
                "error": result.stderr.decode("cp850", errors="replace")[:2000]}
