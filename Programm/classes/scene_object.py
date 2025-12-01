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
        # Вектор "Вперед" для машины (зависит от модели, у вас это -Y)
        self.forward = np.array([0.0, -1.0, 0.0])

    def get_transformed_dots(self):
        """
        Оптимизированная версия трансформации вершин.
        Использует матричные операции NumPy вместо цикла for по каждой точке.
        """
        # 1. Быстро извлекаем координаты всех точек в массив NumPy (N, 3)
        # Это все еще цикл Python, но он простой
        coords = np.array([[dot.x, dot.y, dot.z] for dot in self.dots], dtype=float)

        # 2. Векторизированное умножение (Матрица * Матрица) + Смещение
        # Это происходит очень быстро (на уровне C)
        transformed_coords = coords @ self.rotation.T + self.position

        # 3. Собираем обратно в объекты Dot (требование структуры данных)
        return [Dot(x, y, z) for x, y, z in transformed_coords]

    def transformed_faces(self):
        # Получаем трансформированные точки
        transformed_dots = self.get_transformed_dots()

        # Создаем грани с новыми точками
        # Здесь сложно оптимизировать без смены структуры, так как faces хранят ссылки
        faces_transformed = []
        for face in self.faces:
            # Находим соответствующие трансформированные вершины по индексу
            new_vertices = [transformed_dots[self.dots.index(v)] for v in face.vertices]

            faces_transformed.append(Face(
                vertices=new_vertices,
                color=face.color,
                uv=getattr(face, 'uv', None)
            ))
        return faces_transformed

    def rotate_towards(self, target, max_angle_deg=CAR_MAX_TURN_ANGLE_DEG):
        """
        Поворачивает объект передом к цели (Танковый разворот).
        """
        # Вектор на цель
        direction_to_target = target - self.position
        direction_to_target[2] = 0  # Игнорируем высоту

        dist = np.linalg.norm(direction_to_target)
        if dist < 1e-4:
            return False

        direction_to_target /= dist  # Нормализуем

        current_forward = self.forward[:2]
        target_dir_2d = direction_to_target[:2]

        # Вычисляем угол
        dot = np.clip(np.dot(current_forward, target_dir_2d), -1.0, 1.0)
        angle_diff = np.arccos(dot)

        if angle_diff < np.radians(2.0):  # Допуск
            return False

        # Определяем направление поворота
        cross = current_forward[0] * target_dir_2d[1] - current_forward[1] * target_dir_2d[0]

        max_angle_rad = np.radians(max_angle_deg)
        step = min(angle_diff, max_angle_rad)

        if cross < 0:
            step = -step

        c, s = np.cos(step), np.sin(step)
        rot_z = np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1]
        ])

        self.rotation = rot_z @ self.rotation
        self.forward = rot_z @ self.forward

        return True