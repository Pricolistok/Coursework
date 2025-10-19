from settings.consts import *
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer
from design.design import Ui_MainWindow
from auxiliary_functions.reader_from_file import reader_from_file, print_all_data
from classes.model_classes import *
from draw.draw_faces import draw_scene_with_objects
from draw.rotate_scene import update_action
from draw.camera import Camera
from classes.scene_object import SceneObject
import numpy as np


class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.canvas = None
        self.dots: list[Dot] = []
        self.edges: list[Edge] = []
        self.faces: list[Face] = []
        self.pressed_keys = set()
        self.car: SceneObject = None

        self.camera = Camera(
            position=DEFAULT_CAMERA_POSITION,
            target=DEFAULT_CAMERA_LOOK_AT,
            up=DEFAULT_CAMERA_UP,
            fov=DEFAULT_CAMERA_FOV
        )

        self.initStart()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(FPS)


    def initStart(self):
        self.setupUi(self)
        self.prepare_data()
        self.initCanvas()
        self.start_image()


    def prepare_data(self):
        reader_from_file(filename=FILENAME_MAP, dots=self.dots, edges=self.edges, faces=self.faces)
        dots_car, edges_car, faces_car = [], [], []
        reader_from_file(FILENAME_CAR, dots_car, edges_car, faces_car)
        self.car = SceneObject(dots_car, edges_car, faces_car)
        self.car.position = np.array(START_POSITION, dtype=float)
        self.car_target = np.array(TARGET, dtype=float)
        self.car_speed = SPEED_CAR
        print_all_data(self.car.dots, self.car.edges, self.car.faces)


    def initCanvas(self):
        self.canvas = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
        self.canvas.fill(Qt.black)
        self.label_field.setPixmap(QPixmap.fromImage(self.canvas))


    def start_image(self):
        draw_scene_with_objects(self.label_field, self.faces, self.camera, objects=[self.car])


    def move_car_to_target(self):
        direction = self.car_target - self.car.position
        distance = np.linalg.norm(direction)
        if distance < 1e-3:
            return
        direction /= distance
        self.car.position += direction * min(self.car_speed, distance)


    def update_scene(self):
        self.move_car_to_target()
        update_action(self.label_field, self.faces, self.pressed_keys, self.camera, objects=[self.car])


    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        self.pressed_keys.add(event.key())


    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())
