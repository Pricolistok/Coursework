import numpy as np
from classes.model_classes import Dot, Face
from settings.consts import CAR_MAX_TURN_ANGLE_DEG


class SceneObject:
    def __init__(self, dots, edges, faces):
        self.dots = dots
        self.edges = edges
        self.faces = faces
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.eye(3)

        # ИСПРАВЛЕНИЕ: Меняем направление вектора "Вперед".
        # Было [0, 1, 0], ставим [0, -1, 0].
        # Теперь программа будет знать, где у модели настоящий капот.
        self.forward = np.array([0.0, -1.0, 0.0])

    def get_transformed_dots(self):
        transformed = []
        for dot in self.dots:
            # Сначала вращаем, потом перемещаем
            vec = np.array([dot.x, dot.y, dot.z])
            rotated = self.rotation @ vec
            transformed.append(Dot(*(rotated + self.position)))
        return transformed

    def transformed_faces(self):
        transformed_dots = self.get_transformed_dots()
        faces_transformed = []
        for face in self.faces:
            faces_transformed.append(Face(
                [transformed_dots[self.dots.index(v)] for v in face.vertices],
                color=face.color,
                uv=getattr(face, 'uv', None)
            ))
        return faces_transformed

    def rotate_towards(self, target, max_angle_deg=CAR_MAX_TURN_ANGLE_DEG):
        """
        Поворачивает объект передом к цели.
        """
        # Вектор на цель
        direction_to_target = target - self.position
        direction_to_target[2] = 0  # Игнорируем высоту

        dist = np.linalg.norm(direction_to_target)
        if dist < 1e-4:
            return False

        direction_to_target /= dist  # Нормализуем

        # Текущий вектор "вперед" объекта с учетом поворота
        # Мы должны использовать self.forward, который уже повернут,
        # НО self.forward мы обновляем вручную.
        # Проще взять исходный forward и повернуть его текущей матрицей rotation,
        # но в коде ниже мы храним актуальный forward в self.forward.

        current_forward = self.forward[:2]
        target_dir_2d = direction_to_target[:2]

        # Вычисляем косинус угла
        dot = np.clip(np.dot(current_forward, target_dir_2d), -1.0, 1.0)
        angle_diff = np.arccos(dot)

        # Если угол мал - мы повернулись
        if angle_diff < np.radians(2.0):  # Допуск 2 градуса
            return False

        # Определяем направление поворота (Cross Product)
        cross = current_forward[0] * target_dir_2d[1] - current_forward[1] * target_dir_2d[0]

        # Шаг поворота
        max_angle_rad = np.radians(max_angle_deg)
        step = min(angle_diff, max_angle_rad)

        if cross < 0:
            step = -step

        # Матрица поворота вокруг Z
        c, s = np.cos(step), np.sin(step)
        rot_z = np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1]
        ])

        # Применяем поворот
        self.rotation = rot_z @ self.rotation
        self.forward = rot_z @ self.forward

        return True