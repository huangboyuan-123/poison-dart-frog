"""
箭毒蛙桌面端入口
一键启动: python src/sqlagent/desktop_app.py
"""
import sys
import threading


def _start_backend():
    """在后台线程启动 FastAPI 后端"""
    import uvicorn
    uvicorn.run("sqlagent.main:app", host="0.0.0.0", port=8000, log_level="warning")


def main():
    # 启动后端（后台守护线程，GUI关闭时自动退出）
    server_thread = threading.Thread(target=_start_backend, daemon=True)
    server_thread.start()

    from PySide6.QtWidgets import QApplication
    from .main_window import MainWindow
    from .theme import DARK_QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
