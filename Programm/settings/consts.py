import numpy as np


WIDTH_CANVAS = 1000
HEIGHT_CANVAS = 1000
X_OFFSET = WIDTH_CANVAS // 2
Y_OFFSET = HEIGHT_CANVAS // 2
SCALE = 25

ANGLE_CLICK = 2

FRAME_TIME_MS = 33

FILENAME_MAP = 'models/map.txt'
FILENAME_CAR = 'models/car.txt'

DEFAULT_CAMERA_POSITION = (0, 0, -20)
DEFAULT_CAMERA_LOOK_AT = (0, 0, 0)
DEFAULT_CAMERA_UP = (0, 1, 0)
DEFAULT_CAMERA_FOV = 1.0

DEFAULT_EDGE_THICKNESS = 1
DEFAULT_FILL_COLOR = np.array((0, 0, 255), dtype=np.uint8)
DEFAULT_EDGE_COLOR = np.array((0, 0, 0), dtype=np.uint8)

SPEED_CAR = 0.5
START_POSITION = (-5, 7, 0)
TARGET = (-5, -5, 0)
START_IDX = (3, 1)
END_IDX = (3, 4)
CAR_MAX_TURN_ANGLE_DEG = 5

MATRIX_MAP = (
    (0, 1, 0, 0, 1, 0, 1, 0),
    (1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 0, 0, 1, 0, 1, 0),
    (0, 1, 0, 0, 1, 0, 1, 0),
    (1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 0, 0, 1, 0, 1, 0),
    (1, 1, 1, 1, 1, 1, 1, 1),
    (0, 1, 0, 0, 1, 0, 1, 0)
    )

MATRIX_MAP_REAL_COORDS = (
    ((7, -7, 0), (5, -7, 0), (3, -7, 0), (1, -7, 0), (-1, -7, 0), (-3, -7, 0), (-5, -7, 0), (-7, -7, 0)),
    ((7, -5, 0), (5, -5, 0), (3, -5, 0), (1, -5, 0), (-1, -5, 0), (-3, -5, 0), (-5, -5, 0), (-7, -5, 0)),
    ((7, -3, 0), (5, -3, 0), (3, -3, 0), (1, -3, 0), (-1, -3, 0), (-3, -3, 0), (-5, -3, 0), (-7, -3, 0)),
    ((7, -1, 0), (5, -1, 0), (3, -1, 0), (1, -1, 0), (-1, -1, 0), (-3, -1, 0), (-5, -1, 0), (-7, -1, 0)),
    ((7, 1, 0), (5, 1, 0), (3, 1, 0), (1, 1, 0), (-1, 1, 0), (-3, 1, 0), (-5, 1, 0), (-7, 1, 0)),
    ((7, 3, 0), (5, 3, 0), (3, 3, 0), (1, 3, 0), (-1, 3, 0), (-3, 3, 0), (-5, 3, 0), (-7, 3, 0)),
    ((7, 5, 0), (5, 5, 0), (3, 5, 0), (1, 5, 0), (-1, 5, 0), (-3, 5, 0), (-5, 5, 0), (-7, 5, 0)),
    ((7, 7, 0), (5, 7, 0), (3, 7, 0), (1, 7, 0), (-1, 7, 0), (-3, 7, 0), (-5, 7, 0), (-7, 7, 0))
    )


