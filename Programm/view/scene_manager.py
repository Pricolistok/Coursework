from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from auxiliary_functions.reader_from_file import reader_from_file
from draw.rotate_scene import update_action
from draw.camera import Camera
from settings.consts import *


class SceneManager:
    def __init__(self, label_field):
        self.label_field = label_field
        self.dots, self.edges, self.faces = [], [], []
        self.objects = []
        self.pressed_keys = set()
        self.camera = Camera(
            position=DEFAULT_CAMERA_POSITION,
            target=DEFAULT_CAMERA_LOOK_AT,
            up=DEFAULT_CAMERA_UP,
            fov=DEFAULT_CAMERA_FOV
        )

        self.init_canvas()

    def init_canvas(self):
        self.canvas = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
        self.canvas.fill(Qt.black)
        self.label_field.setPixmap(QPixmap.fromImage(self.canvas))

    def load_scene_data(self):
        reader_from_file(filename=FILENAME_MAP, dots=self.dots, edges=self.edges, faces=self.faces)

    def add_object(self, obj):
        self.objects.append(obj)

    def update_scene(self):
        update_action(self.label_field, self.faces, self.pressed_keys, self.camera, objects=self.objects)

    def key_press_event(self, event):
        if event.isAutoRepeat():
            return
        self.pressed_keys.add(event.key())

    def key_release_event(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in self.pressed_keys:
            self.pressed_keys.remove(event.key())
