import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow


def main(argv=None):
    app = QApplication(argv or sys.argv)
    window = MainWindow()
    window.show()
    if len(app.arguments()) > 1:
        window.load_file(app.arguments()[1])
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
