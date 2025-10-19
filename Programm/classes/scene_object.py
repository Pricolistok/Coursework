from classes.model_classes import Dot, Edge, Face
import numpy as np


class SceneObject:
    def __init__(self, dots, edges, faces):
        self.dots = dots
        self.edges = edges
        self.faces = faces
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.eye(3)  # матрица вращения 3x3

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
                color=face.color  # передаем оригинальный цвет
            ))
        return faces_transformed
