import numpy as np

class Camera:
    """
    Простая камера для 3D-рендеринга с перспективой.
    position: координаты камеры (x, y, z)
    look_at: точка, на которую смотрит камера
    up: вектор 'вверх' камеры
    fov: масштаб для перспективы
    """
    def __init__(self, position=(0,0,-10), look_at=(0,0,0), up=(0,1,0), fov=1.0):
        self.position = np.array(position, dtype=float)
        self.look_at = np.array(look_at, dtype=float)
        self.up = np.array(up, dtype=float)
        self.fov = fov
        self._compute_basis()

    def _compute_basis(self):
        forward = self.look_at - self.position
        forward /= np.linalg.norm(forward)
        right = np.cross(forward, self.up)
        right /= np.linalg.norm(right)
        up_vec = np.cross(right, forward)
        self.forward = forward
        self.right = right
        self.up_vec = up_vec
        self.view_matrix = np.stack([right, up_vec, -forward], axis=1)

    def world_to_camera(self, point):
        p = np.array([point.x, point.y, point.z]) - self.position
        p_cam = self.view_matrix.T @ p
        return p_cam

    def project(self, point, d=800):
        """
        Перспективная проекция точки.
        d — расстояние до плоскости проекции
        """
        p_cam = self.world_to_camera(point)
        z = p_cam[2] + d
        if z == 0:
            z = 1e-6
        factor = d / z
        x_proj = p_cam[0] * factor
        y_proj = p_cam[1] * factor
        return x_proj, y_proj, p_cam[2]
