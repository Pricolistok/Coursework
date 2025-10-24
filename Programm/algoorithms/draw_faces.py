from PyQt5.QtGui import QPixmap, QImage
from settings.consts import *
import numpy as np

TEXTURES = {}


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

            byte_count = height * bytes_per_line
            ptr.setsize(byte_count)

            texture_data = np.frombuffer(ptr, np.uint8).copy()

            if bytes_per_line == width * 3:
                texture_array = texture_data.reshape((height, width, 3))
            else:
                texture_array = texture_data.reshape((height, bytes_per_line // 3, 3))
                texture_array = texture_array[:, :width, :].copy()

            # ИСПРАВЛЕНИЕ: преобразование BGR to RGB
            texture_array = texture_array[:, :, [2, 1, 0]]

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


def is_face_textured(face):
    color_key = tuple(face.color)
    return (face.uv is not None and
            color_key in TEXTURE_MAP and
            color_key in TEXTURES and
            TEXTURES[color_key] is not None)


def get_face_texture(face):
    color_key = tuple(face.color)
    return TEXTURES.get(color_key)


def project_vertex(dot, cam, mode='perspective'):
    x, y, z = cam.world_to_camera(dot)
    if mode == 'perspective':
        d = 800
        factor = d / (z + d + 1e-9)
        x_proj = x * factor
        y_proj = y * factor
    else:
        x_proj, y_proj = x, y
    screen_x = int(x_proj * SCALE + X_OFFSET)
    screen_y = int(y_proj * SCALE + Y_OFFSET)
    return screen_x, screen_y, z


def calculate_face_normal(vertices):
    if len(vertices) < 3:
        return None

    v0 = np.array([vertices[0].x, vertices[0].y, vertices[0].z])
    v1 = np.array([vertices[1].x, vertices[1].y, vertices[1].z])
    v2 = np.array([vertices[2].x, vertices[2].y, vertices[2].z])

    vec1 = v1 - v0
    vec2 = v2 - v0
    normal = np.cross(vec1, vec2)
    norm = np.linalg.norm(normal)

    if norm < 1e-9:
        return None

    return normal / norm


def create_uv_coords_planar(vertices, normal=None):
    if len(vertices) < 3:
        return None

    if normal is None:
        normal = calculate_face_normal(vertices)
        if normal is None:
            return None

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

    u_range = u_max - u_min
    v_range = v_max - v_min

    if u_range < 1e-9:
        u_range = 1.0
    if v_range < 1e-9:
        v_range = 1.0

    uv_coords = []
    for i in range(len(vertices)):
        u = (u_coords[i] - u_min) / u_range
        v = (v_coords[i] - v_min) / v_range
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        uv_coords.append((u, v))

    return uv_coords


def auto_uv_unwrap(faces):
    textured_faces = [face for face in faces if tuple(face.color) in TEXTURE_MAP]

    for face in textured_faces:
        if not hasattr(face, 'uv') or face.uv is None:
            if not hasattr(face, 'normal') or face.normal is None:
                face.normal = calculate_face_normal(face.vertices)

            face.uv = create_uv_coords_planar(face.vertices, face.normal)


def rasterize_face_zbuffer_optimized(face, zbuffer, img_array, proj_mode, cam):
    if not face.vertices or len(face.vertices) < 3:
        return

    verts_proj = []
    for vertex in face.vertices:
        screen_x, screen_y, z = project_vertex(vertex, cam=cam, mode=proj_mode)
        verts_proj.append((screen_x, screen_y, z))

    xs, ys, zs = zip(*verts_proj)
    xs, ys, zs = np.array(xs, dtype=np.float32), np.array(ys, dtype=np.float32), np.array(zs, dtype=np.float32)

    min_y = max(int(np.floor(np.min(ys))), 0)
    max_y = min(int(np.ceil(np.max(ys))), HEIGHT_CANVAS - 1)
    if max_y < min_y:
        return

    min_x = max(int(np.floor(np.min(xs))), 0)
    max_x = min(int(np.ceil(np.max(xs))), WIDTH_CANVAS - 1)
    if max_x < min_x:
        return

    is_textured = is_face_textured(face)
    texture_data = get_face_texture(face) if is_textured else None

    if is_textured and texture_data:
        texture_array = texture_data['array']
        texture_h, texture_w = texture_data['height'], texture_data['width']
        texture_repeat = TEXTURE_REPEAT_MAP.get(tuple(face.color), DEFAULT_TEXTURE_REPEAT)
    else:
        texture_array = None

    uv_coords = face.uv if is_textured else None
    n_vertices = len(verts_proj)

    for y in range(min_y, max_y + 1):
        intersections = []

        for i in range(n_vertices):
            x1, y1, z1 = xs[i], ys[i], zs[i]
            x2, y2, z2 = xs[(i + 1) % n_vertices], ys[(i + 1) % n_vertices], zs[(i + 1) % n_vertices]

            if (y1 <= y < y2) or (y2 <= y < y1):
                if abs(y2 - y1) < 1e-9:
                    continue

                t = (y - y1) / (y2 - y1)
                x_int = x1 + t * (x2 - x1)
                z_int = z1 + t * (z2 - z1)

                uv_int = None
                if is_textured and uv_coords:
                    uv1 = uv_coords[i]
                    uv2 = uv_coords[(i + 1) % n_vertices]
                    uv_int = (
                        uv1[0] + t * (uv2[0] - uv1[0]),
                        uv1[1] + t * (uv2[1] - uv1[1])
                    )

                intersections.append((x_int, z_int, uv_int))

        intersections.sort(key=lambda x: x[0])

        for i in range(0, len(intersections) - 1, 2):
            if i + 1 >= len(intersections):
                break

            x1, z1, uv1 = intersections[i]
            x2, z2, uv2 = intersections[i + 1]

            seg_start = max(int(np.floor(x1)), 0)
            seg_end = min(int(np.ceil(x2)), WIDTH_CANVAS - 1)

            if seg_start > seg_end:
                continue

            num_pixels = seg_end - seg_start + 1
            if num_pixels <= 0:
                continue

            pixels_x = np.arange(seg_start, seg_end + 1, dtype=np.int32)

            x_range = x2 - x1
            if abs(x_range) < 1e-9:
                continue

            t_segment = (pixels_x - x1) / x_range
            z_line = z1 + t_segment * (z2 - z1)

            valid_pixels = (pixels_x >= 0) & (pixels_x < WIDTH_CANVAS)
            if not np.any(valid_pixels):
                continue

            pixels_x_valid = pixels_x[valid_pixels]
            z_line_valid = z_line[valid_pixels]
            t_segment_valid = t_segment[valid_pixels]

            z_test = z_line_valid < zbuffer[y, pixels_x_valid]
            if not np.any(z_test):
                continue

            update_indices = pixels_x_valid[z_test]
            zbuffer[y, update_indices] = z_line_valid[z_test]

            if is_textured and texture_array is not None and uv1 is not None and uv2 is not None:
                u_coords = uv1[0] + t_segment_valid[z_test] * (uv2[0] - uv1[0])
                v_coords = uv1[1] + t_segment_valid[z_test] * (uv2[1] - uv1[1])

                u_coords = (u_coords * texture_repeat) % 1.0
                v_coords = (v_coords * texture_repeat) % 1.0

                tex_x = (u_coords * (texture_w - 1)).astype(np.int32)
                tex_y = (v_coords * (texture_h - 1)).astype(np.int32)

                tex_x = np.clip(tex_x, 0, texture_w - 1)
                tex_y = np.clip(tex_y, 0, texture_h - 1)

                try:
                    batch_size = 1000
                    num_pixels = len(update_indices)

                    for i in range(0, num_pixels, batch_size):
                        end_idx = min(i + batch_size, num_pixels)
                        batch_indices = update_indices[i:end_idx]
                        batch_tex_x = tex_x[i:end_idx]
                        batch_tex_y = tex_y[i:end_idx]

                        texture_colors = texture_array[batch_tex_y, batch_tex_x]
                        img_array[y, batch_indices] = texture_colors
                except Exception:
                    img_array[y, update_indices] = face.color
            else:
                img_array[y, update_indices] = face.color


def plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color):
    x_start = max(0, int(x - radius))
    x_end = min(WIDTH_CANVAS - 1, int(x + radius))
    y_start = max(0, int(y - radius))
    y_end = min(HEIGHT_CANVAS - 1, int(y + radius))

    for py in range(y_start, y_end + 1):
        for px in range(x_start, x_end + 1):
            if z < zbuffer[py, px]:
                zbuffer[py, px] = z
                img_array[py, px] = color


def rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, color_rgb, radius=DEFAULT_EDGE_THICKNESS):
    dx, dy, dz = abs(x1 - x0), abs(y1 - y0), z1 - z0
    x, y = x0, y0
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1

    if dx > dy:
        err = dx / 2.0
        for _ in range(int(dx) + 1):
            t = (x - x0) / (x1 - x0 + 1e-9)
            z = z0 + dz * t
            plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color_rgb)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        for _ in range(int(dy) + 1):
            t = (y - y0) / (y1 - y0 + 1e-9)
            z = z0 + dz * t
            plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color_rgb)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy


def draw_faces_zbuffer_optimized(label_field, faces, cam, edge_thickness=DEFAULT_EDGE_THICKNESS,
                                 proj_mode='perspective'):
    auto_uv_unwrap(faces)

    image = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 3), dtype=np.uint8)
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf)

    solid_faces = [face for face in faces if not is_face_textured(face)]
    textured_faces = [face for face in faces if is_face_textured(face)]

    for face in solid_faces:
        rasterize_face_zbuffer_optimized(face, zbuffer, img_array, proj_mode, cam)

    for face in textured_faces:
        rasterize_face_zbuffer_optimized(face, zbuffer, img_array, proj_mode, cam)

    if edge_thickness > 0:
        for face in faces:
            verts = [project_vertex(v, cam=cam, mode=proj_mode) for v in face.vertices]
            n = len(verts)
            for i in range(n):
                x0, y0, z0 = verts[i]
                x1, y1, z1 = verts[(i + 1) % n]
                rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array,
                                       DEFAULT_EDGE_COLOR, radius=edge_thickness)

    image_bits = image.bits()
    image_bits.setsize(WIDTH_CANVAS * HEIGHT_CANVAS * 4)
    target_array = np.frombuffer(image_bits, np.uint8).reshape((HEIGHT_CANVAS, WIDTH_CANVAS, 4))

    target_array[..., 0] = img_array[..., 2]
    target_array[..., 1] = img_array[..., 1]
    target_array[..., 2] = img_array[..., 0]
    target_array[..., 3] = 255

    label_field.setPixmap(QPixmap.fromImage(image))


def draw_scene_with_objects_optimized(label_field, faces, cam, objects=[]):
    all_faces = faces.copy()

    for obj in objects:
        if hasattr(obj, 'transformed_faces'):
            obj_faces = obj.transformed_faces()
            all_faces.extend(obj_faces)

    draw_faces_zbuffer_optimized(label_field, all_faces, cam)


def rasterize_face_zbuffer(face, zbuffer, img_array, proj_mode, cam):
    rasterize_face_zbuffer_optimized(face, zbuffer, img_array, proj_mode, cam)


def draw_faces_zbuffer(label_field, faces, cam, edge_thickness=DEFAULT_EDGE_THICKNESS,
                       proj_mode='perspective'):
    draw_faces_zbuffer_optimized(label_field, faces, cam, edge_thickness, proj_mode)


def draw_scene_with_objects(label_field, faces, cam, objects=[]):
    draw_scene_with_objects_optimized(label_field, faces, cam, objects)