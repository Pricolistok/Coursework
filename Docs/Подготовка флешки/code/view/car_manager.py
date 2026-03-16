from auxiliary_functions.reader_from_file import reader_from_file
from classes.scene_object import SceneObject
from draw.move_car import move_car_to_target
from settings.consts import *
import numpy as np


class CarManager:
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.car = None
        self.path_points = []
        self.current_target_index = 0
        self.is_moving = False
        self.car_speed = SPEED_CAR
        self.on_movement_finished = None

        self.dots_car, self.edges_car, self.faces_car = [], [], []

    def load_car_data(self):
        if self.car is not None:
            return

        reader_from_file(FILENAME_CAR, self.dots_car, self.edges_car, self.faces_car)

        self.car = SceneObject(self.dots_car, self.edges_car, self.faces_car)
        initial_position = self.find_initial_position()
        self.car.position = initial_position

        self.scene_manager.add_object(self.car)
        print(f"Машина создана в позиции: {initial_position}")

    def find_initial_position(self):
        return np.array([-5, 7, 0], dtype=float)

    def start_movement(self, start_position, path_points):
        self.car.position = start_position.copy()
        self.path_points = path_points
        self.current_target_index = 0
        self.is_moving = True

    def update_movement(self):
        if not self.is_moving or not self.path_points:
            return

        if self.current_target_index < len(self.path_points):
            target = self.path_points[self.current_target_index]
            move_car_to_target(self.car, target, self.car_speed)

            if np.linalg.norm(self.car.position - target) < 0.1:
                self.current_target_index += 1

                if self.current_target_index >= len(self.path_points):
                    self.is_moving = False
                    if self.on_movement_finished:
                        self.on_movement_finished()