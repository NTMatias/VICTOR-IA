"""Disposable UI benchmark, no real sessions or microphone, includes GUI process tree."""
import json
import os
from pathlib import Path
import tempfile
import time
import psutil
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtWidgets import QApplication
from victor.config import ConfigManager
from victor.gui.app import GUIManager

def main():
    root=Path(__file__).resolve().parents[1];qt=QApplication.instance() or QApplication([]);qt.setQuitOnLastWindowClosed(False)
    process=psutil.Process();report={'microphone_enabled':False,'browser_sessions_loaded':False,'tts_enabled':False,'real_4gb_hardware':False}
    def wait(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:qt.processEvents();time.sleep(.01)
    with tempfile.TemporaryDirectory() as folder:
        gui=GUIManager(ConfigManager(Path(folder)))
        try:
            gui.show();wait(1);gui.showMinimized();wait(1);cpu=process.cpu_times();start=time.monotonic();wait(5)
            elapsed=time.monotonic()-start;after=process.cpu_times()
            report.update(seconds=elapsed,gui_rss=process.memory_info().rss,tree_rss=sum(p.memory_info().rss for p in [process]+process.children(recursive=True)),
                          cpu_percent_one_core=(after.user+after.system-cpu.user-cpu.system)/elapsed*100)
        finally:
            gui.close();deadline=time.monotonic()+10
            while not gui.closed_cleanly and time.monotonic()<deadline:wait(.1)
            report['closed_cleanly']=gui.closed_cleanly
    (root/'docs/background_benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
