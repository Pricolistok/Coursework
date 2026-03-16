from copy import deepcopy
from PyQt5.QtGui import QImage, QPainter, QPen, QColor, QPixmap
from PyQt5.QtCore import Qt
from algorithms.rotate import rotate_dot
from settings.consts import *


def prepare_line(edge):
    x_s = edge.start_dot.x * SCALE + X_OFFSET
    y_s = edge.start_dot.y * SCALE + Y_OFFSET
    x_e = edge.end_dot.x * SCALE + X_OFFSET
    y_e = edge.end_dot.y * SCALE + Y_OFFSET
    return int(x_s), int(y_s), int(x_e), int(y_e)


def draw_wire_model(image: QImage, label_field, edges):
    image.fill(Qt.black)
    painter = QPainter(image)
    pen = QPen(QColor(255, 0, 0), 1)
    painter.setPen(pen)

    for edge in edges:
        painter.drawLine(*prepare_line(edge))

    painter.end()
    label_field.setPixmap(QPixmap.fromImage(image))


def anim_rotate_wire_model(image: QImage, label_field, edges):
    tmp_edges = deepcopy(edges)
    angle = 60

    for edge in tmp_edges:
        edge.start_dot.x, edge.start_dot.y, edge.start_dot.z = rotate_dot(
            edge.start_dot.x, edge.start_dot.y, edge.start_dot.z, angle)
        edge.end_dot.x, edge.end_dot.y, edge.end_dot.z = rotate_dot(
            edge.end_dot.x, edge.end_dot.y, edge.end_dot.z, angle)

    draw_wire_model(image, label_field, tmp_edges)
