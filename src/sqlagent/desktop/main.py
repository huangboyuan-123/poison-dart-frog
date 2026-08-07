"""
箭毒蛙桌面端入口
一键启动: python src/sqlagent/desktop_app.py
Docker部署: docker compose up -d
"""
import subprocess
import sys
import os
import atexit
import socket


_backend_process = None


def _port_in_use(port: int) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def _start_backend():
    """启动后端子进程（仅当端口未被占用时）"""
    global _backend_process
    if _port_in_use(8000):
        return  # Docker 或已有后端在运行
    env = os.environ.copy()
    _backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "sqlagent.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
    )


def _stop_backend():
    global _backend_process
    if _backend_process:
        _backend_process.terminate()
        _backend_process.wait(timeout=3)


def main():
    _start_backend()
    # atexit removed

    from PySide6.QtWidgets import QApplication
    from .main_window import MainWindow
    from .theme import DARK_QSS

    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 启用自定义滚动条
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    # close backend on exit
    app.aboutToQuit.connect(_stop_backend)
    app.exec()
    _stop_backend()


if __name__ == '__main__':
    main()
