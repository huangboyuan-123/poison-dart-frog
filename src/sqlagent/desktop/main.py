"""
箭毒蛙桌面端入口
运行: python -m sqlagent.desktop.main
    或: python src/sqlagent/desktop/main.py
"""
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow
from .theme import DARK_QSS


def main():
    app = QApplication([])
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
