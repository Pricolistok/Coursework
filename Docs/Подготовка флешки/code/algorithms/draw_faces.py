import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from settings.consts import *
from auxiliary_functions.reader_from_file import read_lights_from_file
from draw.shadows import ShadowCaster

TEXTURES = {}
LIGHTS_CACHE = None
SHADOW_CASTERS = []


def load_textures():
    global TEXTURES
    TEXTURES = {}
    if 'TEXTURE_MAP' not in globals() or not TEXTURE_MAP: return
    for color_key, texture_path in TEXTURE_MAP.items():
        try:
            texture_img = QImage(texture_path)
            if texture_img.isNull():
                TEXTURES[color_key] = None
                continue
            texture_img = texture_img.convertToFormat(QImage.Format_RGB888)
            width = texture_img.width()
            height = texture_img.height()
            bytes_per_line = texture_img.bytesPerLine()
            ptr = texture_img.bits()
            ptr.setsize(height * bytes_per_line)
            texture_data = np.frombuffer(ptr, np.uint8).copy()
            if bytes_per_line == width * 3:
                texture_array = texture_data.reshape((height, width, 3))
            else:
                texture_array = texture_data.reshape((height, bytes_per_line // 3, 3))
                texture_array = texture_array[:, :width, :].copy()
            TEXTURES[color_key] = {'array': texture_array, 'width': width, 'height': height}
        except Exception:
            TEXTURES[color_key] = None


try:
    load_textures()
except Exception:
    pass


def init_lighting_system():
    global LIGHTS_CACHE, SHADOW_CASTERS
    if LIGHTS_CACHE is None:
        LIGHTS_CACHE = read_lights_from_file(FILENAME_LIGHTS)
        if not LIGHTS_CACHE:
            LIGHTS_CACHE = [{'dir': [15.0, 25.0, 10.0], 'color': [1, 1, 1], 'intensity': 1.0}]
        SHADOW_CASTERS = [ShadowCaster(l_cfg) for l_cfg in LIGHTS_CACHE]
    return SHADOW_CASTERS


def reload_lights():
    """Сбрасывает кэш освещения, заставляя перечитать файл lights.txt"""
    global LIGHTS_CACHE, SHADOW_CASTERS
    LIGHTS_CACHE = None
    SHADOW_CASTERS = []


def calculate_face_normal(vertices):
    if len(vertices) < 3: return np.array([0.0, 1.0, 0.0])
    v0 = np.array([vertices[0].x, vertices[0].y, vertices[0].z])
    v1 = np.array([vertices[1].x, vertices[1].y, vertices[1].z])
    v2 = np.array([vertices[2].x, vertices[2].y, vertices[2].z])
    vec1 = v1 - v0
    vec2 = v2 - v0
    normal = np.cross(vec1, vec2)
    norm = np.linalg.norm(normal)
    if norm < 1e-9: return np.array([0.0, 1.0, 0.0])
    return normal / norm


def create_uv_coords_planar(vertices, normal=None):
    if len(vertices) < 3: return None
    if normal is None: normal = calculate_face_normal(vertices)
    abs_normal = np.abs(normal)
    if abs_normal[0] >= abs_normal[1] and abs_normal[0] >= abs_normal[2]:
        u_coords = [v.y for v in vertices]
        v_coords = [v.z for v in vertices]
    elif abs_normal[1] >= abs_normal[0] and abs_normal[1] >= abs_normal[2]:
        u_coords = [v.x for v in vertices]
        v_coords = [v.z for v in vertices]
    else:
        u_coords = [v.x for v in vertices]
        v_coords = [v.y for v in vertices]
    u_min, u_max = min(u_coords), max(u_coords)
    v_min, v_max = min(v_coords), max(v_coords)
    u_range = max(1e-9, u_max - u_min)
    v_range = max(1e-9, v_max - v_min)
    uv_coords = []
    for i in range(len(vertices)):
        u = (u_coords[i] - u_min) / u_range
        v = (v_coords[i] - v_min) / v_range
        uv_coords.append((u, v))
    return uv_coords


def auto_uv_unwrap(faces):
    textured_faces = [face for face in faces if tuple(face.color) in TEXTURE_MAP]
    for face in textured_faces:
        if not hasattr(face, 'uv') or face.uv is None:
            face.normal = calculate_face_normal(face.vertices)
            face.uv = create_uv_coords_planar(face.vertices, face.normal)


def project_vertex(dot, cam, scale):
    x, y, z = cam.world_to_camera(dot)
    d = 800.0
    factor = d / (z + d) if (z + d) >= 1.0 else d
    x_proj = x * factor * scale + X_OFFSET
    y_proj = y * factor * scale + Y_OFFSET
    return x_proj, y_proj, z


def rasterize_face_with_shadows(face, zbuffer, img_array, cam, shadow_casters, current_scale):
    if len(face.vertices) < 3: return

    screen_coords = []
    for v in face.vertices:
        sx, sy, sz = project_vertex(v, cam, current_scale)
        if not (np.isfinite(sx) and np.isfinite(sy) and np.isfinite(sz)): return
        screen_coords.append((sx, sy, sz))

    xs = np.array([p[0] for p in screen_coords])
    ys = np.array([p[1] for p in screen_coords])

    min_x, max_x = int(np.floor(np.min(xs))), int(np.ceil(np.max(xs)))
    min_y, max_y = int(np.floor(np.min(ys))), int(np.ceil(np.max(ys)))

    if max_x < 0 or min_x >= WIDTH_CANVAS or max_y < 0 or min_y >= HEIGHT_CANVAS: return
    min_y = max(0, min_y)
    max_y = min(HEIGHT_CANVAS - 1, max_y)

    color_key = tuple(face.color)
    is_textured = (face.uv is not None and color_key in TEXTURES and TEXTURES[color_key] is not None)
    texture_data = TEXTURES[color_key] if is_textured else None
    uv_coords = face.uv if is_textured else None
    texture_repeat = TEXTURE_REPEAT_MAP.get(color_key, DEFAULT_TEXTURE_REPEAT)

    normal = calculate_face_normal(face.vertices)

    casters_data = []
    for caster in shadow_casters:
        light_dir = caster.light_dir
        diff = abs(np.dot(normal, light_dir))

        s_coords = caster.transform_poly_to_light_space(face.vertices)

        casters_data.append({
            'caster': caster,
            'diffuse': diff,
            's_coords': s_coords
        })

    n_verts = len(face.vertices)

    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(n_verts):
            v1 = screen_coords[i]
            v2 = screen_coords[(i + 1) % n_verts]
            y1, y2 = v1[1], v2[1]

            if (y1 <= y < y2) or (y2 <= y < y1):
                if abs(y2 - y1) < 1e-9: continue
                t = (y - y1) / (y2 - y1)
                x_int = v1[0] + t * (v2[0] - v1[0])
                z_int = v1[2] + t * (v2[2] - v1[2])

                sc_list = []
                for c_data in casters_data:
                    s_poly = c_data['s_coords']
                    s1 = s_poly[i]
                    s2 = s_poly[(i + 1) % n_verts]
                    s_int = (
                        s1[0] + t * (s2[0] - s1[0]),
                        s1[1] + t * (s2[1] - s1[1]),
                        s1[2] + t * (s2[2] - s1[2])
                    )
                    sc_list.append(s_int)

                uvc = (0, 0)
                if is_textured:
                    u1, v1_uv = uv_coords[i]
                    u2, v2_uv = uv_coords[(i + 1) % n_verts]
                    uvc = (u1 + t * (u2 - u1), v1_uv + t * (v2_uv - v1_uv))

                intersections.append((x_int, z_int, sc_list, uvc))

        intersections.sort(key=lambda p: p[0])

        for k in range(0, len(intersections) - 1, 2):
            left = intersections[k]
            right = intersections[k + 1]

            x_start = int(np.ceil(left[0]))
            x_end = int(np.ceil(right[0]))

            x_start = max(0, min(x_start, WIDTH_CANVAS - 1))
            x_end = max(0, min(x_end, WIDTH_CANVAS - 1))
            if x_end <= x_start: continue

            span_width = right[0] - left[0]
            if span_width < 1e-9: continue

            pixel_x = np.arange(x_start, x_end + 1, dtype=np.float32)
            t_span = (pixel_x - left[0]) / span_width

            z_left, z_right = left[1], right[1]
            z_vals = z_left + t_span * (z_right - z_left)

            current_z = zbuffer[y, x_start:x_end + 1]
            visible_mask = z_vals < current_z

            if not np.any(visible_mask): continue

            indices = np.where(visible_mask)[0]
            full_indices = x_start + indices

            zbuffer[y, full_indices] = z_vals[indices]

            t_vis = t_span[indices]

            final_intensity = np.full(len(indices), AMBIENT_INTENSITY, dtype=np.float32)

            for idx, c_data in enumerate(casters_data):
                caster = c_data['caster']
                diffuse = c_data['diffuse']

                sl = np.array(left[2][idx])
                sr = np.array(right[2][idx])

                s_vis = sl + t_vis[:, np.newaxis] * (sr - sl)

                map_x = s_vis[:, 0].astype(np.int32)
                map_y = s_vis[:, 1].astype(np.int32)
                v_d = s_vis[:, 2]

                in_map = (map_x >= 0) & (map_x < caster.resolution) & \
                         (map_y >= 0) & (map_y < caster.resolution) & \
                         (v_d >= 0) & (v_d <= 1.0)

                light_contrib = np.zeros(len(indices), dtype=np.float32)

                if np.any(in_map):
                    valid_d = v_d[in_map]
                    closest = caster.shadow_buffer[map_y[in_map], map_x[in_map]]

                    lit_mask = valid_d <= (closest + SHADOW_BIAS)

                    light_contrib[in_map] += np.where(lit_mask, 1.0, 0.0) * (diffuse * caster.intensity)

                final_intensity += light_contrib

            final_intensity = np.clip(final_intensity, 0.0, 1.0)

            if is_textured and texture_data:
                uv_l = np.array(left[3])
                uv_r = np.array(right[3])
                uv_vis = uv_l + t_vis[:, np.newaxis] * (uv_r - uv_l)

                tex_w = texture_data['width'] - 1
                tex_h = texture_data['height'] - 1
                tex_img = texture_data['array']

                u_fin = (uv_vis[:, 0] * texture_repeat) % 1.0
                v_fin = (uv_vis[:, 1] * texture_repeat) % 1.0

                tx = (u_fin * tex_w).astype(np.int32)
                ty = (v_fin * tex_h).astype(np.int32)

                base_colors = tex_img[ty, tx].astype(np.float32)
            else:
                base_colors = np.array(face.color, dtype=np.float32)

            res_colors = base_colors * final_intensity[:, np.newaxis]

            img_array[y, full_indices, 0] = res_colors[:, 2]
            img_array[y, full_indices, 1] = res_colors[:, 1]
            img_array[y, full_indices, 2] = res_colors[:, 0]


def draw_scene_with_objects(label_field, faces, cam, current_scale, objects=[]):
    all_faces = []
    all_faces.extend(faces)
    for obj in objects:
        all_faces.extend(obj.transformed_faces())
    auto_uv_unwrap(all_faces)

    casters = init_lighting_system()

    if casters:
        for caster in casters:
            caster.render_shadow_map(all_faces)

    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 4), dtype=np.uint8)
    img_array[:, :, 3] = 255
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf, dtype=np.float32)

    for face in all_faces:
        rasterize_face_with_shadows(face, zbuffer, img_array, cam, casters, current_scale)

    height, width, channels = img_array.shape
    bytes_per_line = channels * width
    image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB32).copy()
    label_field.setPixmap(QPixmap.fromImage(image))