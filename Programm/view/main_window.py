from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QTimer
from design.design import Ui_MainWindow
from auxiliary_functions.reader_from_file import reader_from_file
from classes.model_classes import Dot, Edge, Face
from algoorithms.draw_faces import draw_scene_with_objects
from draw.rotate_scene import update_action
from draw.camera import Camera
from settings.consts import *
from algoorithms.wave_algorithm import wave_path, path_to_real_coords
from classes.scene_object import SceneObject
from draw.move_car import move_car_to_target
import numpy as np



class MainApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()

        self.canvas = None
        self.dots: list[Dot] = []
        self.edges: list[Edge] = []
        self.faces: list[Face] = []
        self.dots_car: list[Dot] = []
        self.edges_car: list[Edge] = []
        self.faces_car: list[Face] = []

        self.start_position = np.array(START_POSITION, dtype=float)
        self.target_position = np.array(TARGET, dtype=float)
        self.car_speed = SPEED_CAR

        self.pressed_keys = set()
        self.car: SceneObject = None
        self.path_points = []
        self.current_target_index = 0

        self.camera = Camera(
            position=DEFAULT_CAMERA_POSITION,
            target=DEFAULT_CAMERA_LOOK_AT,
            up=DEFAULT_CAMERA_UP,
            fov=DEFAULT_CAMERA_FOV
        )

        self.initStart()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scene)
        self.timer.start(FRAME_TIME_MS)


    def initStart(self):
        self.setupUi(self)
        self.prepare_data()
        self.prepare_data_car()
        self.initCanvas()
        self.start_image()

    def prepare_data(self):
        reader_from_file(filename=FILENAME_MAP, dots=self.dots, edges=self.edges, faces=self.faces)

    def prepare_data_car(self):
        reader_from_file(FILENAME_CAR, self.dots_car, self.edges_car, self.faces_car)
        self.car = SceneObject(self.dots_car, self.edges_car, self.faces_car)

        start_r, start_c = START_IDX
        self.start_position = np.array(MATRIX_MAP_REAL_COORDS[start_r][start_c], dtype=float)
        self.car.position = self.start_position

        end_r, end_c = END_IDX
        self.target_position = np.array(MATRIX_MAP_REAL_COORDS[end_r][end_c], dtype=float)

        path = wave_path(MATRIX_MAP, START_IDX, END_IDX)
        if path is None:
            print("Путь не найден!")
            return

        self.path_points = path_to_real_coords(path, MATRIX_MAP_REAL_COORDS)
        self.current_target_index = 0


    def initCanvas(self):
        self.canvas = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
        self.canvas.fill(Qt.black)
        self.label_field.setPixmap(QPixmap.fromImage(self.canvas))


    def start_image(self):
        draw_scene_with_objects(self.label_field, self.faces, self.camera, objects=[self.car])


    def update_scene(self):
        if self.path_points and self.current_target_index < len(self.path_points):
            target = self.path_points[self.current_target_index]
            move_car_to_target(self.car, target, self.car_speed)
            if np.linalg.norm(self.car.position - target) < 0.1:
                self.current_target_index += 1
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
