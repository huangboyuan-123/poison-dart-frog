"""
箭毒蛙桌面端入口
一键启动: python src/sqlagent/desktop_app.py
"""
import subprocess
import sys
import os
import atexit


_backend_process = None


def _start_backend():
    """启动后端子进程"""
    global _backend_process
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([os.path.dirname(os.path.dirname(os.path.dirname(__file__)))] + sys.path)
    _backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "sqlagent.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )


def _stop_backend():
    """关闭后端子进程"""
    global _backend_process
    if _backend_process:
        _backend_process.terminate()
        _backend_process.wait(timeout=3)


def main():
    _start_backend()
    atexit.register(_stop_backend)

    from PySide6.QtWidgets import QApplication
    from .main_window import MainWindow
    from .theme import DARK_QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    app.exec()
    _stop_backend()


if __name__ == '__main__':
    main()
