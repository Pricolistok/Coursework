from settings.consts import *
from PyQt5.QtCore import Qt
from algoorithms.draw_faces import draw_scene_with_objects


def update_action(label_field, faces, pressed_keys, camera, objects=[]):
    pitch = 0
    yaw = 0

    if Qt.Key_W in pressed_keys:
        pitch += ANGLE_CLICK
    if Qt.Key_S in pressed_keys:
        pitch -= ANGLE_CLICK

    if Qt.Key_A in pressed_keys:
        yaw -= ANGLE_CLICK
    if Qt.Key_D in pressed_keys:
        yaw += ANGLE_CLICK

    if yaw != 0:
        camera.rotate_orbit_horizontal(d_theta=yaw)

    if pitch != 0:
        camera.rotate_orbit_vertical(d_phi=pitch)

    draw_scene_with_objects(label_field, faces, camera, objects)
