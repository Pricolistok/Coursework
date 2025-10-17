from settings.consts import *
from PyQt5.QtCore import Qt
from algoorithms.rotate import rotate_x, rotate_y
from draw.draw_faces import draw_faces_zbuffer


def update_action(label_field, faces, pressed_keys):
    if not pressed_keys:
        return

    angle_x, angle_y = 0, 0

    if Qt.Key_W in pressed_keys:
        angle_x += ANGLE_CLICK
    if Qt.Key_S in pressed_keys:
        angle_x -= ANGLE_CLICK
    if Qt.Key_A in pressed_keys:
        angle_y += ANGLE_CLICK
    if Qt.Key_D in pressed_keys:
        angle_y -= ANGLE_CLICK

    if angle_x != 0 or angle_y != 0:
        for face in faces:
            for v in face.vertices:
                v.x, v.y, v.z = rotate_x(v.x, v.y, v.z, angle_x)
                v.x, v.y, v.z = rotate_y(v.x, v.y, v.z, angle_y)
        draw_faces_zbuffer(label_field, faces)