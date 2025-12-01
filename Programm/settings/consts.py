import numpy as np
import sys
import os
from auxiliary_functions.reader_from_file import reader_bin_matrix_from_file, reader_matrix_real_coords_map_from_file, reader_directions_from_file

# --- ФУНКЦИЯ ДЛЯ РАБОТЫ ПУТЕЙ В EXE ---
def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает и для dev, и для PyInstaller """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

WIDTH_CANVAS = 1200
HEIGHT_CANVAS = 1200
# Ваши настройки смещения
X_OFFSET = WIDTH_CANVAS // 2 - 100
Y_OFFSET = HEIGHT_CANVAS // 2
SCALE = 40

ANGLE_CLICK = 5
FRAME_TIME_MS = 5

FILENAME_MAP = resource_path('models/map.txt')
FILENAME_CAR = resource_path('models/car.txt')
FILENAME_LIGHTS = resource_path('models/lights.txt')
FILENAME_MAP_BIN_MATRIX = resource_path('models/map_road_bin_matrix.txt')
FILENAME_MAP_REAL_COORDS_MAP_MATRIX = resource_path('models/map_matrix_real_coords.txt')
FILENAME_DIRECTIONS = resource_path('models/directions.txt')


DEFAULT_CAMERA_POSITION = np.array([0.0, 0.0, -20.0])
DEFAULT_CAMERA_LOOK_AT = np.array([0.0, 0.0, 0.0])
DEFAULT_CAMERA_UP = np.array([0.0, 1.0, 0.0])
DEFAULT_CAMERA_FOV = 1.0

DEFAULT_EDGE_THICKNESS = 1
DEFAULT_FILL_COLOR = np.array((0, 0, 255), dtype=np.uint8)
DEFAULT_EDGE_COLOR = np.array((0, 0, 0), dtype=np.uint8)

SPEED_CAR = 0.5
START_IDX = (3, 1)
END_IDX = (3, 4)
INITIAL_POS = [-5, 7, 0]
CAR_MAX_TURN_ANGLE_DEG = 30

MATRIX_MAP = reader_bin_matrix_from_file(FILENAME_MAP_BIN_MATRIX)

MATRIX_MAP_REAL_COORDS = reader_matrix_real_coords_map_from_file(FILENAME_MAP_REAL_COORDS_MAP_MATRIX)

MATRIX_DIRECTIONS = reader_directions_from_file(FILENAME_DIRECTIONS)

TEXTURE_MAP = {
    (11, 72, 22): resource_path("textures/grass.jpg"),
    (72, 72, 72): resource_path("textures/road.jpg"),
    (59, 57, 60): resource_path("textures/building_1.jpg"),
    (37, 37, 37): resource_path("textures/roof.jpg"),
    (51, 48, 0): resource_path("textures/building_2.jpg"),
    (81, 44, 18): resource_path("textures/wood.jpg"),
    (255, 0, 13): resource_path("textures/red.jpg"),
    (0, 99, 255): resource_path("textures/glass.jpg"),
}

TEXTURE_REPEAT_MAP = {
    (11, 72, 22): 1.0,
    (72, 72, 72): 1.0,
    (59, 57, 60): 1,
    (51, 48, 0): 1,
    (0, 99, 255): 1
}
DEFAULT_TEXTURE_REPEAT = 2.0

ROAD_COLOR = (0, 0, 0)
OBSTACLE_COLOR = (0, 100, 0)
START_COLOR = (0, 255, 0)
END_COLOR = (255, 0, 0)

ICON = resource_path('pictures/icon.png')

AMBIENT_INTENSITY = 0.4       # Освещенность в тени (0.0 - полная чернота, 1.0 - нет теней)
SHADOW_MAP_RES = 1024         # Разрешение карты теней (выше = четче, но медленнее)
LIGHT_ORTHO_SIZE = 35.0
SHADOW_BIAS = 0.005

ABOUT_PROGRAM_TITLE = "О программе"
ABOUT_PROGRAM_TEXT = """
Визуализация движения автомобиля в трехмерной городской среде 
с использованием алгоритма поиска пути

Основные функции:
• Трехмерное моделирование городской среды
• Поддержка текстур
• Алгоритм поиска кратчайшего пути по дорожной сети
• Управление камерой в реальном времени
• Поддержка теней и бесконечно удаленных источников света
• Интуитивный интерфейс для задания маршрута

Технические особенности:
• Визуализация трехмерных моделей с текстурами
• Реализация волнового алгоритма для поиска пути
• Управление камерой

"""

ABOUT_CREATOR_TITLE = "О разработчике"
ABOUT_CREATOR_TEXT = """
Московский государственный технический университет 
имени Н.Э. Баумана
(национальный исследовательский университет)
(МГТУ им. Н.Э. Баумана)

Кафедра: Программное обеспечение ЭВМ и информационные технологии

Студент группы ИУ7-52Б
Доколин Георгий Александрович

2025 год
"""

# --- НОВЫЕ НАСТРОЙКИ ЗУМА ---
MAX_SCALE = 150.0      # Максимальное приближение
ZOOM_SPEED = 2.0       # Скорость зума