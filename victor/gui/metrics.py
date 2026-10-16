import threading
import time
import psutil
from victor.system.hardware import detect_gpu


class MetricsWorker:
    def __init__(self, emit):
        self.emit = emit
        self.stop_event = threading.Event()
        self.background=lambda:False
        self.thread = threading.Thread(target=self.run, name="victor-metrics", daemon=True)

    def start(self):
        self.thread.start()

    def run(self):
        try:
            self.emit("hardware", detect_gpu())
            previous = psutil.net_io_counters()
            stamp = time.monotonic()
            psutil.cpu_percent()
            while not self.stop_event.wait(10 if self.background() else 2):
                current = psutil.net_io_counters()
                now = time.monotonic()
                rate = max(0, current.bytes_recv + current.bytes_sent - previous.bytes_recv - previous.bytes_sent) / max(.1, now-stamp)
                self.emit("metrics", {"cpu": psutil.cpu_percent(), "ram": psutil.virtual_memory().percent, "network": rate})
                previous, stamp = current, now
        except Exception:
            self.emit("notice", "Las métricas del sistema no están disponibles.")
