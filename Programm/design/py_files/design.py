from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPainter, QPen, QColor


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1163, 860)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.image_widget = Image_Widget(self.centralwidget)
        self.image_widget.setGeometry(QtCore.QRect(40, 40, 991, 651))
        self.image_widget.setObjectName("image_widget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(1050, 320, 75, 24))
        self.pushButton.setObjectName("pushButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1163, 33))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))


class Image_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor(30, 30, 30))
        pen = QPen(QColor(255, 0, 0))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(20, 20, 100, 100)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
