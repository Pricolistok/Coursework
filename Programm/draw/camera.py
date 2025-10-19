import numpy as np

class Camera:
    def __init__(self, position=(0, 0, -20), target=(0, 0, 0), up=(0, 1, 0), fov=1.0):
        self.target = np.array(target, dtype=float)
        self.up_global = np.array(up, dtype=float)
        self.fov = fov

        self.position = np.array(position, dtype=float)

        self._update_spherical_coords()
        self._compute_view_matrix()


    def _update_spherical_coords(self):
        offset = self.position - self.target
        self.radius = np.linalg.norm(offset)
        if self.radius < 1e-6:
            self.radius = 1.0
            offset = np.array([0, 0, -1], dtype=float)
            self.position = self.target + offset

        x, y, z = offset
        self.theta = np.arctan2(x, z)
        self.phi = np.arcsin(np.clip(y / self.radius, -1.0, 1.0))


    def _compute_view_matrix(self):
        self.forward = self.target - self.position
        self.forward /= np.linalg.norm(self.forward)
        self.right = np.cross(self.forward, self.up_global)
        self.right /= np.linalg.norm(self.right)
        self.up_vec = np.cross(self.right, self.forward)
        self.up_vec /= np.linalg.norm(self.up_vec)

        R = np.array([self.right, self.up_vec, -self.forward])
        T = -self.position @ R.T
        self.view_matrix = np.eye(4)
        self.view_matrix[:3, :3] = R.T
        self.view_matrix[:3, 3] = T


    def rotate_orbit_horizontal(self, d_theta=0):
        self.theta += np.radians(d_theta)
        self._update_position_from_spherical()
        self._compute_view_matrix()


    def rotate_orbit_vertical(self, d_phi=0):
        if d_phi == 0:
            return

        current_phi = self.phi
        new_phi = current_phi + np.radians(d_phi)
        new_phi = np.clip(new_phi, np.radians(-90), np.radians(90))
        self.phi = new_phi

        self._update_position_from_spherical()
        self._compute_view_matrix()


    def move(self, dz=0):
        self.radius += dz
        self.radius = np.clip(self.radius, 1.0, 100.0)
        self._update_position_from_spherical()
        self._compute_view_matrix()


    def _update_position_from_spherical(self):
        x = self.radius * np.cos(self.phi) * np.sin(self.theta)
        y = self.radius * np.sin(self.phi)
        z = self.radius * np.cos(self.phi) * np.cos(self.theta)
        self.position = self.target + np.array([x, y, z])


    def world_to_camera(self, point):
        vec = np.array([point.x, point.y, point.z, 1.0])
        cam = self.view_matrix @ vec
        return cam[:3]

    def project(self, point, d=800):
        p_cam = self.world_to_camera(point)
        if abs(p_cam[2]) < 1e-6:
            p_cam[2] = 1e-6
        factor = d / p_cam[2]
        return p_cam[0] * factor, p_cam[1] * factor, p_cam[2]
