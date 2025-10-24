from PyQt5.QtWidgets import QGraphicsScene, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from settings.consts import *
from algoorithms.wave_algorithm import wave_path, path_to_real_coords
import numpy as np

ROAD_COLOR = QColor(0, 0, 0)
OBSTACLE_COLOR = QColor(0, 100, 0)
START_COLOR = QColor(0, 255, 0)
END_COLOR = QColor(255, 0, 0)


class MapManager:
    def __init__(self, map_view, scene_manager):
        self.map_view = map_view
        self.scene_manager = scene_manager
        self.map_scene = None
        self.start_idx = None
        self.end_idx = None
        self.start_position = None
        self.target_position = None
        self.path_points = []
        self.start_marker = None
        self.end_marker = None
        self.cell_items = {}
        self.on_path_calculated = None
        self.setup_map_view()

    def setup_map_view(self):
        self.map_scene = QGraphicsScene()
        self.map_view.setScene(self.map_scene)

        # Отключаем скроллбары
        self.map_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.map_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.draw_map_matrix()
        self.map_view.mousePressEvent = self.map_clicked

    def draw_map_matrix(self):
        rows = len(MATRIX_MAP)
        cols = len(MATRIX_MAP[0])

        map_view_width = self.map_view.width()
        map_view_height = self.map_view.height()

        cell_width = map_view_width / cols
        cell_height = map_view_height / rows

        for row in range(rows):
            for col in range(cols):
                x = col * cell_width
                y = row * cell_height

                if MATRIX_MAP[row][col] == 1:
                    color = ROAD_COLOR
                else:
                    color = OBSTACLE_COLOR

                rect = self.map_scene.addRect(x, y, cell_width, cell_height)
                rect.setBrush(QBrush(color))
                self.cell_items[(row, col)] = rect

    def map_clicked(self, event):
        scene_pos = self.map_view.mapToScene(event.pos())
        rows = len(MATRIX_MAP)
        cols = len(MATRIX_MAP[0])

        map_view_width = self.map_view.width()
        map_view_height = self.map_view.height()

        cell_width = map_view_width / cols
        cell_height = map_view_height / rows

        col = int(scene_pos.x() // cell_width)
        row = int(scene_pos.y() // cell_height)

        if not self.is_valid_point(row, col):
            QMessageBox.warning(None, "Ошибка", "Эта точка недоступна для перемещения!")
            return

        if event.button() == Qt.LeftButton:
            self.set_start_point(row, col)
        elif event.button() == Qt.RightButton:
            self.set_end_point(row, col)

        self.recalculate_path()

    def is_valid_point(self, row, col):
        if (row < 0 or row >= len(MATRIX_MAP) or
                col < 0 or col >= len(MATRIX_MAP[0])):
            return False
        return MATRIX_MAP[row][col] == 1

    def set_start_point(self, row, col):
        if self.start_idx and self.start_idx in self.cell_items:
            old_row, old_col = self.start_idx
            if MATRIX_MAP[old_row][old_col] == 1:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(ROAD_COLOR))
            else:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(OBSTACLE_COLOR))

        self.start_idx = (row, col)
        self.start_position = np.array(MATRIX_MAP_REAL_COORDS[row][col], dtype=float)

        if (row, col) in self.cell_items:
            self.cell_items[(row, col)].setBrush(QBrush(START_COLOR))

    def set_end_point(self, row, col):
        if self.end_idx and self.end_idx in self.cell_items:
            old_row, old_col = self.end_idx
            if MATRIX_MAP[old_row][old_col] == 1:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(ROAD_COLOR))
            else:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(OBSTACLE_COLOR))

        self.end_idx = (row, col)
        self.target_position = np.array(MATRIX_MAP_REAL_COORDS[row][col], dtype=float)

        if (row, col) in self.cell_items:
            self.cell_items[(row, col)].setBrush(QBrush(END_COLOR))

    def recalculate_path(self):
        if self.start_idx is not None and self.end_idx is not None:
            path = wave_path(MATRIX_MAP, self.start_idx, self.end_idx)
            if path is None:
                self.path_points = []
                if self.on_path_calculated:
                    self.on_path_calculated(False)
                return

            self.path_points = path_to_real_coords(path, MATRIX_MAP_REAL_COORDS)
            if self.on_path_calculated:
                self.on_path_calculated(True)

    def can_start_movement(self):
        return (self.start_idx is not None and
                self.end_idx is not None and
                len(self.path_points) > 0)

    def get_start_position(self):
        return self.start_position

    def get_path_points(self):
        return self.path_points