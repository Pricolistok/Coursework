from PyQt5.QtWidgets import QGraphicsScene, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from settings.consts import *
from algoorithms.wave_algorithm import wave_path, path_to_real_coords
import numpy as np

ROAD_COLOR = QColor(0, 0, 0)
OBSTACLE_COLOR = QColor(0, 100, 0)
START_COLOR = QColor(0, 255, 0)
END_COLOR = QColor(255, 0, 0)
ARROW_COLOR = QColor(255, 255, 255)  # Цвет стрелок


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

                # Отрисовка фона клетки (дорога или препятствие)
                if MATRIX_MAP[row][col] == 1:
                    color = ROAD_COLOR
                else:
                    color = OBSTACLE_COLOR

                rect = self.map_scene.addRect(x, y, cell_width, cell_height)
                rect.setBrush(QBrush(color))
                self.cell_items[(row, col)] = rect

                # Отрисовка стрелок только на дорогах
                if MATRIX_MAP[row][col] == 1:
                    self.draw_arrows(row, col, x, y, cell_width, cell_height)

    def draw_arrows(self, row, col, x, y, w, h):
        """Рисует стрелки направлений на клетке."""
        # Проверяем, есть ли данные в матрице направлений для этой клетки
        if row >= len(MATRIX_DIRECTIONS) or col >= len(MATRIX_DIRECTIONS[0]):
            return

        mask = MATRIX_DIRECTIONS[row][col]
        cx = x + w / 2  # Центр клетки X
        cy = y + h / 2  # Центр клетки Y
        length = min(w, h) * 0.35  # Длина стрелки

        pen = QPen(ARROW_COLOR, 2)

        # Функция для рисования одной стрелки (линия + наконечник)
        def draw_arrow_shape(start_x, start_y, end_x, end_y):
            self.map_scene.addLine(start_x, start_y, end_x, end_y, pen)

            # Вектор стрелки
            vx = end_x - start_x
            vy = end_y - start_y

            # Нормализация для наконечника
            mag = (vx ** 2 + vy ** 2) ** 0.5
            if mag == 0: return
            vx /= mag
            vy /= mag

            # Размер наконечника
            tip_size = 5

            # Перпендикулярный вектор
            px = -vy
            py = vx

            # Точки наконечника (назад от конца стрелки)
            p1x = end_x - vx * tip_size + px * tip_size * 0.5
            p1y = end_y - vy * tip_size + py * tip_size * 0.5

            p2x = end_x - vx * tip_size - px * tip_size * 0.5
            p2y = end_y - vy * tip_size - py * tip_size * 0.5

            self.map_scene.addLine(end_x, end_y, p1x, p1y, pen)
            self.map_scene.addLine(end_x, end_y, p2x, p2y, pen)

        # 1 = ВВЕРХ
        if mask & 1:
            draw_arrow_shape(cx, cy, cx, cy - length)

        # 2 = ВПРАВО
        if mask & 2:
            draw_arrow_shape(cx, cy, cx + length, cy)

        # 4 = ВНИЗ
        if mask & 4:
            draw_arrow_shape(cx, cy, cx, cy + length)

        # 8 = ВЛЕВО
        if mask & 8:
            draw_arrow_shape(cx, cy, cx - length, cy)

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
        # Восстановление цвета предыдущей точки старта
        if self.start_idx and self.start_idx in self.cell_items:
            old_row, old_col = self.start_idx
            if MATRIX_MAP[old_row][old_col] == 1:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(ROAD_COLOR))
            else:
                self.cell_items[(old_row, old_col)].setBrush(QBrush(OBSTACLE_COLOR))

            # При перерисовке кистью стрелки не пропадают, так как они отдельные элементы (QGraphicsLineItem),
            # лежащие поверх RectItem. Но чтобы быть уверенным в чистоте, здесь можно ничего не делать.
            pass

        self.start_idx = (row, col)
        self.start_position = np.array(MATRIX_MAP_REAL_COORDS[row][col], dtype=float)

        if (row, col) in self.cell_items:
            self.cell_items[(row, col)].setBrush(QBrush(START_COLOR))

    def set_end_point(self, row, col):
        # Восстановление цвета предыдущей точки финиша
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
                # Если пути нет - можно показать предупреждение, но не блокирующее
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