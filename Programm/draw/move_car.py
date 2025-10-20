import numpy as np
from classes.scene_object import SceneObject
from settings.consts import CAR_MAX_TURN_ANGLE_DEG


def move_car_to_target(car: SceneObject, car_target, car_speed):

    still_turning = car.rotate_towards(car_target, max_angle_deg=CAR_MAX_TURN_ANGLE_DEG)
    if still_turning:
        return

    direction = car_target - car.position
    direction[2] = 0
    distance = np.linalg.norm(direction)
    if distance < 1e-3:
        return

    direction /= distance
    car.position += direction * min(car_speed, distance)
