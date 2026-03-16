import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from view.main_window import MainApp
from settings.consts import ICON


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON))
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

