import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from design.py_files.design import Ui_MainWindow


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()