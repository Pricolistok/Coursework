import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from settings.consts import *
from auxiliary_functions.reader_from_file import read_lights_from_file
from draw.shadows import ShadowCaster

# Глобальные кэши
TEXTURES = {}
LIGHTS_CACHE = None
SHADOW_CASTERS = []


def load_textures():
    global TEXTURES
    TEXTURES = {}

    if 'TEXTURE_MAP' not in globals() or not TEXTURE_MAP:
        return

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
            if ptr is None:
                TEXTURES[color_key] = None
                continue

            ptr.setsize(height * bytes_per_line)
            texture_data = np.frombuffer(ptr, np.uint8).copy()

            if bytes_per_line == width * 3:
                texture_array = texture_data.reshape((height, width, 3))
            else:
                texture_array = texture_data.reshape((height, bytes_per_line // 3, 3))
                texture_array = texture_array[:, :width, :].copy()

            TEXTURES[color_key] = {
                'array': texture_array,
                'width': width,
                'height': height,
                'path': texture_path
            }
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


def calculate_face_normal(vertices):
    """
    Вычисляет нормаль для расчета освещения.
    """
    if len(vertices) < 3:
        return np.array([0.0, 1.0, 0.0])

    v0 = np.array([vertices[0].x, vertices[0].y, vertices[0].z])
    v1 = np.array([vertices[1].x, vertices[1].y, vertices[1].z])
    v2 = np.array([vertices[2].x, vertices[2].y, vertices[2].z])

    vec1 = v1 - v0
    vec2 = v2 - v0
    normal = np.cross(vec1, vec2)
    norm = np.linalg.norm(normal)

    if norm < 1e-9:
        return np.array([0.0, 1.0, 0.0])

    return normal / norm


def create_uv_coords_planar(vertices, normal=None):
    if len(vertices) < 3: return None
    if normal is None:
        normal = calculate_face_normal(vertices)

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
            if not hasattr(face, 'normal') or face.normal is None:
                face.normal = calculate_face_normal(face.vertices)
            face.uv = create_uv_coords_planar(face.vertices, face.normal)


def project_vertex(dot, cam):
    x, y, z = cam.world_to_camera(dot)
    d = 800.0
    if z + d < 1.0:
        factor = d
    else:
        factor = d / (z + d)

    x_proj = x * factor
    y_proj = y * factor

    screen_x = x_proj * SCALE + X_OFFSET
    screen_y = y_proj * SCALE + Y_OFFSET
    return screen_x, screen_y, z


def rasterize_face_with_shadows(face, zbuffer, img_array, cam, shadow_casters):
    """
    Алгоритм 34: Построчное сканирование с Z-буфером.
    Корректно обрабатывает любую геометрию.
    """
    if len(face.vertices) < 3:
        return

    # Мы НЕ используем Backface Culling, так как модели имеют смешанную ориентацию вершин.
    # Z-буфер корректно обработает видимость пикселей.

    caster = shadow_casters[0] if shadow_casters else None

    # --- 1. Проекция ---
    screen_coords = []
    for v in face.vertices:
        sx, sy, sz = project_vertex(v, cam)
        if not (np.isfinite(sx) and np.isfinite(sy) and np.isfinite(sz)):
            return
        screen_coords.append((sx, sy, sz))

    xs = np.array([p[0] for p in screen_coords])
    ys = np.array([p[1] for p in screen_coords])

    # Отсечение по экрану
    min_x = int(np.floor(np.min(xs)))
    max_x = int(np.ceil(np.max(xs)))
    min_y = int(np.floor(np.min(ys)))
    max_y = int(np.ceil(np.max(ys)))

    # Если полигон полностью вне экрана
    if max_x < 0 or min_x >= WIDTH_CANVAS or max_y < 0 or min_y >= HEIGHT_CANVAS:
        return

    min_y = max(0, min_y)
    max_y = min(HEIGHT_CANVAS - 1, max_y)

    # --- Подготовка данных ---
    color_key = tuple(face.color)
    is_textured = (face.uv is not None and color_key in TEXTURES and TEXTURES[color_key] is not None)
    texture_data = TEXTURES[color_key] if is_textured else None
    uv_coords = face.uv if is_textured else None
    texture_repeat = TEXTURE_REPEAT_MAP.get(color_key, DEFAULT_TEXTURE_REPEAT)

    # Освещение (Двустороннее, т.к. нет Culling'а)
    normal = calculate_face_normal(face.vertices)
    light_dir = caster.light_dir if caster else np.array([0, 1, 0])
    # abs() нужен, чтобы стена была светлой с обеих сторон
    diffuse_factor = abs(np.dot(normal, light_dir))

    shadow_coords = []
    if caster:
        shadow_coords = caster.transform_poly_to_light_space(face.vertices)

    n_verts = len(face.vertices)

    # --- 2. Растеризация (Scanline) ---
    for y in range(min_y, max_y + 1):
        intersections = []
        for i in range(n_verts):
            v1_scr = screen_coords[i]
            v2_scr = screen_coords[(i + 1) % n_verts]

            y1, y2 = v1_scr[1], v2_scr[1]

            if (y1 <= y < y2) or (y2 <= y < y1):
                if abs(y2 - y1) < 1e-9: continue
                t = (y - y1) / (y2 - y1)

                # Интерполяция координат
                x_int = v1_scr[0] + t * (v2_scr[0] - v1_scr[0])
                z_int = v1_scr[2] + t * (v2_scr[2] - v1_scr[2])

                # Интерполяция теней
                s1 = shadow_coords[i] if caster else (0, 0, 0)
                s2 = shadow_coords[(i + 1) % n_verts] if caster else (0, 0, 0)
                sx_int = s1[0] + t * (s2[0] - s1[0])
                sy_int = s1[1] + t * (s2[1] - s1[1])
                sd_int = s1[2] + t * (s2[2] - s1[2])

                # Интерполяция текстур
                u1, v1_uv = uv_coords[i] if is_textured else (0, 0)
                u2, v2_uv = uv_coords[(i + 1) % n_verts] if is_textured else (0, 0)
                u_int = u1 + t * (u2 - u1)
                v_int = v1_uv + t * (v2_uv - v1_uv)

                intersections.append({
                    'x': x_int, 'z': z_int,
                    'sx': sx_int, 'sy': sy_int, 'sd': sd_int,
                    'u': u_int, 'v': v_int
                })

        intersections.sort(key=lambda p: p['x'])

        for k in range(0, len(intersections) - 1, 2):
            left = intersections[k]
            right = intersections[k + 1]

            x_start = int(np.ceil(left['x']))
            x_end = int(np.ceil(right['x']))

            x_start = max(0, x_start)
            x_end = min(WIDTH_CANVAS - 1, x_end)

            if x_end < x_start: continue

            span_width = right['x'] - left['x']
            if span_width < 1e-9: continue

            pixel_x = np.arange(x_start, x_end + 1, dtype=np.float32)
            t_span = (pixel_x - left['x']) / span_width

            z_vals = left['z'] + t_span * (right['z'] - left['z'])

            try:
                # --- Z-BUFFER TEST ---
                # Самое важное место алгоритма.
                # Сравниваем глубину текущего пикселя (z_vals) с тем, что в буфере.
                buffer_z = zbuffer[y, x_start:x_end + 1]
                visible_mask = z_vals < buffer_z

                if not np.any(visible_mask): continue

                indices = np.where(visible_mask)[0]
                full_indices = x_start + indices

                # Обновляем буфер, записывая новую ближайшую глубину
                zbuffer[y, full_indices] = z_vals[indices]

                t_valid = t_span[indices]

                # --- SHADOW MAPPING ---
                final_intensity = np.full(len(indices), AMBIENT_INTENSITY, dtype=np.float32)

                if caster:
                    ls_x = left['sx'] + t_valid * (right['sx'] - left['sx'])
                    ls_y = left['sy'] + t_valid * (right['sy'] - left['sy'])
                    ls_d = left['sd'] + t_valid * (right['sd'] - left['sd'])

                    map_x = ls_x.astype(np.int32)
                    map_y = ls_y.astype(np.int32)

                    in_map = (map_x >= 0) & (map_x < caster.resolution) & \
                             (map_y >= 0) & (map_y < caster.resolution) & \
                             (ls_d >= 0) & (ls_d <= 1.0)

                    valid_idx = np.where(in_map)[0]
                    if len(valid_idx) > 0:
                        vx = map_x[valid_idx]
                        vy = map_y[valid_idx]
                        v_d = ls_d[valid_idx]

                        closest = caster.shadow_buffer[vy, vx]
                        is_lit = v_d <= (closest + SHADOW_BIAS)
                        shadow_val = np.where(is_lit, 1.0, 0.0)

                        final_intensity[valid_idx] += (diffuse_factor * caster.intensity) * shadow_val

                final_intensity = np.clip(final_intensity, 0.0, 1.0)

                # --- COLORING ---
                if is_textured and texture_data:
                    u_c = left['u'] + t_valid * (right['u'] - left['u'])
                    v_c = left['v'] + t_valid * (right['v'] - left['v'])

                    u_c = (u_c * texture_repeat) % 1.0
                    v_c = (v_c * texture_repeat) % 1.0

                    tex_x = (u_c * (texture_data['width'] - 1)).astype(np.int32)
                    tex_y = (v_c * (texture_data['height'] - 1)).astype(np.int32)

                    base_colors = texture_data['array'][tex_y, tex_x].astype(np.float32)
                else:
                    base_colors = np.array(face.color, dtype=np.float32)

                res_colors = base_colors * final_intensity[:, np.newaxis]

                img_array[y, full_indices, 0] = res_colors[:, 2]
                img_array[y, full_indices, 1] = res_colors[:, 1]
                img_array[y, full_indices, 2] = res_colors[:, 0]

            except IndexError:
                continue


def draw_scene_with_objects(label_field, faces, cam, objects=[]):
    """
    Основной цикл отрисовки.
    """
    all_faces = []
    all_faces.extend(faces)

    for obj in objects:
        all_faces.extend(obj.transformed_faces())

    auto_uv_unwrap(all_faces)

    casters = init_lighting_system()
    if casters:
        casters[0].render_shadow_map(all_faces)

    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 4), dtype=np.uint8)
    img_array[:, :, 3] = 255

    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf, dtype=np.float32)

    for face in all_faces:
        rasterize_face_with_shadows(face, zbuffer, img_array, cam, casters)

    height, width, channels = img_array.shape
    bytes_per_line = channels * width
    image = QImage(img_array.data, width, height, bytes_per_line, QImage.Format_RGB32).copy()

    label_field.setPixmap(QPixmap.fromImage(image))