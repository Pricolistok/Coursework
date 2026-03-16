import numpy as np
from settings.consts import SHADOW_MAP_RES, LIGHT_ORTHO_SIZE


class ShadowCaster:
    def __init__(self, light_config):
        raw_dir = np.array(light_config['dir'], dtype=float)
        norm = np.linalg.norm(raw_dir)
        if norm == 0:
            self.light_dir = np.array([0.0, 1.0, 0.0])
        else:
            self.light_dir = raw_dir / norm

        self.color = light_config['color']
        self.intensity = light_config['intensity']

        self.resolution = SHADOW_MAP_RES
        self.ortho_size = LIGHT_ORTHO_SIZE

        self.shadow_buffer = np.full((self.resolution, self.resolution), np.inf, dtype=np.float32)

        self.view_matrix = np.eye(4)
        self.proj_matrix = np.eye(4)
        self.vp_matrix = np.eye(4)

        self._calculate_matrices()

    def _calculate_matrices(self):
        target = np.array([0.0, 0.0, 0.0])

        position = target + self.light_dir * 50.0

        # Вектор "Вверх"
        up = np.array([0.0, 1.0, 0.0])
        if abs(np.dot(self.light_dir, up)) > 0.95:
            up = np.array([0.0, 0.0, 1.0])

        forward = target - position
        forward /= np.linalg.norm(forward)

        right = np.cross(forward, up)
        right /= np.linalg.norm(right)

        real_up = np.cross(right, forward)

        self.view_matrix = np.eye(4)
        self.view_matrix[0, :3] = right
        self.view_matrix[1, :3] = real_up
        self.view_matrix[2, :3] = -forward
        self.view_matrix[:3, 3] = -np.array([
            np.dot(right, position),
            np.dot(real_up, position),
            np.dot(-forward, position)
        ])

        r = self.ortho_size
        l = -self.ortho_size
        t = self.ortho_size
        b = -self.ortho_size
        n = 1.0
        f = 100.0

        self.proj_matrix = np.array([
            [2 / (r - l), 0, 0, -(r + l) / (r - l)],
            [0, 2 / (t - b), 0, -(t + b) / (t - b)],
            [0, 0, -2 / (f - n), -(f + n) / (f - n)],
            [0, 0, 0, 1]
        ])

        self.vp_matrix = self.proj_matrix @ self.view_matrix

    def transform_poly_to_light_space(self, vertices):
        res_coords = []
        for v in vertices:
            vec = np.array([v.x, v.y, v.z, 1.0])
            clip = self.vp_matrix @ vec
            w = clip[3] if clip[3] != 0 else 1.0
            ndc_x = clip[0] / w
            ndc_y = clip[1] / w
            ndc_z = clip[2] / w

            screen_x = (ndc_x + 1) * 0.5 * (self.resolution - 1)
            screen_y = (1 - ndc_y) * 0.5 * (self.resolution - 1)

            depth = ndc_z * 0.5 + 0.5

            res_coords.append((screen_x, screen_y, depth))
        return res_coords

    def render_shadow_map(self, faces):
        self.shadow_buffer.fill(np.inf)

        for face in faces:
            coords = self.transform_poly_to_light_space(face.vertices)

            xs = [c[0] for c in coords]
            ys = [c[1] for c in coords]
            if max(xs) < 0 or min(xs) >= self.resolution or max(ys) < 0 or min(ys) >= self.resolution:
                continue

            n_verts = len(coords)
            min_y = max(0, int(np.floor(min(ys))))
            max_y = min(self.resolution - 1, int(np.ceil(max(ys))))

            for y in range(min_y, max_y + 1):
                intersections = []
                for i in range(n_verts):
                    v1 = coords[i]
                    v2 = coords[(i + 1) % n_verts]

                    if (v1[1] <= y < v2[1]) or (v2[1] <= y < v1[1]):
                        if abs(v2[1] - v1[1]) < 1e-9: continue
                        t = (y - v1[1]) / (v2[1] - v1[1])
                        x_int = v1[0] + t * (v2[0] - v1[0])
                        z_int = v1[2] + t * (v2[2] - v1[2])
                        intersections.append((x_int, z_int))

                intersections.sort(key=lambda p: p[0])

                for k in range(0, len(intersections) - 1, 2):
                    left = intersections[k]
                    right = intersections[k + 1]

                    x_start = max(0, int(np.ceil(left[0])))
                    x_end = min(self.resolution - 1, int(np.ceil(right[0])))

                    if x_end < x_start: continue

                    width = right[0] - left[0]
                    if width < 1e-9: continue

                    xx = np.arange(x_start, x_end + 1)
                    t_span = (xx - left[0]) / width
                    z_vals = left[1] + t_span * (right[1] - left[1])

                    current_depths = self.shadow_buffer[y, x_start:x_end + 1]
                    mask = z_vals < current_depths
                    self.shadow_buffer[y, x_start:x_end + 1][mask] = z_vals[mask]