import numpy as np
from classes.scene_object import SceneObject
from settings.consts import CAR_MAX_TURN_ANGLE_DEG


def move_car_to_target(car: SceneObject, car_target, car_speed):
    # 1. Сначала поворачиваемся
    is_turning = car.rotate_towards(car_target, max_angle_deg=CAR_MAX_TURN_ANGLE_DEG)

    # Если мы еще поворачиваемся (функция вернула True), то выходим и НЕ двигаем позицию.
    # Машина будет крутиться на месте.
    if is_turning:
        return

    # 2. Если повернулись - едем вперед
    direction = car_target - car.position
    direction[2] = 0

    distance = np.linalg.norm(direction)
    if distance < 1e-3:
        return

    direction /= distance
    car.position += direction * min(car_speed, distance)