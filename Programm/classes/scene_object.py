import numpy as np
from classes.model_classes import Dot, Face
from settings.consts import *


class SceneObject:
    def __init__(self, dots, edges, faces):
        self.dots = dots
        self.edges = edges
        self.faces = faces
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.eye(3)
        self.forward = np.array([0.0, -1.0, 0.0])  # вперед по -Y

    def get_transformed_dots(self):
        transformed = []
        for dot in self.dots:
            rotated = self.rotation @ np.array([dot.x, dot.y, dot.z])
            transformed.append(Dot(*(rotated + self.position)))
        return transformed

    def transformed_faces(self):
        transformed_dots = self.get_transformed_dots()
        faces_transformed = []
        for face in self.faces:
            faces_transformed.append(Face(
                [transformed_dots[self.dots.index(v)] for v in face.vertices],
                color=face.color
            ))
        return faces_transformed

    def rotate_towards(self, target, max_angle_deg=CAR_MAX_TURN_ANGLE_DEG):
        """
        Поворот машины к цели.
        Возвращает True, если еще нужно поворачивать (остановка на месте)
        """
        max_angle = np.radians(max_angle_deg)
        direction = target - self.position
        direction[2] = 0
        dist = np.linalg.norm(direction)
        if dist < 1e-5:
            return False

        direction /= dist
        fwd = self.forward[:2]
        target_dir = direction[:2]

        cos_theta = np.clip(np.dot(fwd, target_dir), -1.0, 1.0)
        angle = np.arccos(cos_theta)
        cross = fwd[0] * target_dir[1] - fwd[1] * target_dir[0]

        # если угол > 90°, значит ехать нужно задом, разворачиваемся
        if angle > np.pi / 2:
            angle = angle - np.pi  # будем ехать назад
            direction = -direction  # меняем направление движения

        if abs(angle) < 1e-3:
            return False

        angle_to_rotate = np.sign(cross) * min(max_angle, abs(angle))
        c, s = np.cos(angle_to_rotate), np.sin(angle_to_rotate)
        rot_z = np.array([[c, -s, 0],
                          [s, c, 0],
                          [0, 0, 1]])

        self.rotation = rot_z @ self.rotation
        self.forward = rot_z @ self.forward
        return True
