from sys import orig_argv

from settings.consts import *
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer
from design.design import Ui_MainWindow
from reader_from_file import reader_from_file
from classes.model_classes import *
from draw.draw_faces import draw_faces_zbuffer
from copy import deepcopy
from algoorithms.rotate import rotate_dot


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.canvas = None
        self.filename = 'models/model_data.txt'
        self.dots: list[Dot] = []
        self.edges: list[Edge] = []
        self.faces: list[Face] = []

        self.setupUi(self)
        self.prepare_data()
        self.initCanvas()

        self.original_faces = deepcopy(self.faces)
        self.angle = 1

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(1)

    def prepare_data(self):
        reader_from_file(filename=self.filename, dots=self.dots, edges=self.edges, faces=self.faces)

    def initCanvas(self):
        self.canvas = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
        self.canvas.fill(Qt.black)
        self.label_field.setPixmap(QPixmap.fromImage(self.canvas))

    def update_animation(self):
        for face in self.original_faces:
            for v in face.vertices:
                v.x, v.y, v.z = rotate_dot(v.x, v.y, v.z, self.angle)

        draw_faces_zbuffer(self.canvas, self.label_field, self.original_faces)
