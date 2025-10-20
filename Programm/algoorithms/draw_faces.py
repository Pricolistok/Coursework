from PyQt5.QtGui import QPixmap, QImage
from settings.consts import *
import numpy as np

# === ЗАГРУЗКА ТЕКСТУРЫ ===
try:
    TEXTURE_IMG = QImage(TEXTURE_PATH).convertToFormat(QImage.Format_RGB888)
    width = TEXTURE_IMG.width()
    height = TEXTURE_IMG.height()
    ptr = TEXTURE_IMG.bits()
    ptr.setsize(height * TEXTURE_IMG.bytesPerLine())
    TEXTURE_ARRAY = np.frombuffer(ptr, np.uint8).reshape((height, TEXTURE_IMG.bytesPerLine() // 3, 3))[:, :width, :]
    print(f"✅ Текстура загружена: {width}x{height}")
except Exception as e:
    print("⚠ Ошибка загрузки текстуры:", e)
    TEXTURE_ARRAY = None


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


def rasterize_face_zbuffer(face, zbuffer, img_array, proj_mode, cam):
    # Проверяем, нужно ли текстурировать
    is_textured = tuple(face.color) == TEXTURE_COLOR_KEY and TEXTURE_ARRAY is not None

    verts = [project_vertex(v, cam=cam, mode=proj_mode) for v in face.vertices]
    xs, ys, zs = zip(*verts)
    xs, ys, zs = np.array(xs), np.array(ys), np.array(zs)

    min_y = max(int(np.min(ys)), 0)
    max_y = min(int(np.max(ys)), HEIGHT_CANVAS - 1)
    if max_y < min_y:
        return

    n = len(xs)
    for y in range(min_y, max_y + 1):
        x_intersections = []
        z_intersections = []
        for i in range(n):
            x1, y1, z1 = xs[i], ys[i], zs[i]
            x2, y2, z2 = xs[(i + 1) % n], ys[(i + 1) % n], zs[(i + 1) % n]

            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1 + 1e-9)
                x_int = x1 + t * (x2 - x1)
                z_int = z1 + t * (z2 - z1)
                x_intersections.append(x_int)
                z_intersections.append(z_int)

        if len(x_intersections) < 2:
            continue

        idx_sort = np.argsort(x_intersections)
        x_intersections = np.array(x_intersections)[idx_sort]
        z_intersections = np.array(z_intersections)[idx_sort]

        x_start = int(max(min(x_intersections), 0))
        x_end = int(min(max(x_intersections), WIDTH_CANVAS - 1))
        if x_start >= x_end:
            continue

        col_range = np.arange(x_start, x_end + 1)
        z_line = np.interp(col_range, x_intersections, z_intersections)
        mask = z_line < zbuffer[y, col_range]

        if not np.any(mask):
            continue

        zbuffer[y, col_range[mask]] = z_line[mask]

        if is_textured:
            # Применяем UV текстуру
            h, w, _ = TEXTURE_ARRAY.shape
            xs_tex = ((col_range / WIDTH_CANVAS) * w * TEXTURE_REPEAT).astype(int) % w
            ys_tex = int((y / HEIGHT_CANVAS) * h * TEXTURE_REPEAT) % h
            img_array[y, col_range[mask]] = TEXTURE_ARRAY[ys_tex, xs_tex[mask]]
        else:
            img_array[y, col_range[mask]] = face.color



def plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color):
    xs = np.arange(-radius, radius + 1)
    ys = np.arange(-radius, radius + 1)
    for dx in xs:
        nx = x + dx
        if nx < 0 or nx >= WIDTH_CANVAS:
            continue
        for dy in ys:
            ny = y + dy
            if 0 <= ny < HEIGHT_CANVAS:
                if z < zbuffer[ny, nx]:
                    zbuffer[ny, nx] = z
                    img_array[ny, nx] = color


def rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, color_rgb, radius=DEFAULT_EDGE_THICKNESS):
    dx, dy, dz = abs(x1 - x0), abs(y1 - y0), z1 - z0
    x, y = x0, y0
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)

    if dx > dy:
        err = dx / 2
        for _ in range(dx + 1):
            t = (x - x0) / (x1 - x0 + 1e-9)
            z = z0 + dz * t
            plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color_rgb)
            x += sx
            err -= dy
            if err < 0:
                y += sy
                err += dx
    else:
        err = dy / 2
        for _ in range(dy + 1):
            t = (y - y0) / (y1 - y0 + 1e-9)
            z = z0 + dz * t
            plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color_rgb)
            y += sy
            err -= dx
            if err < 0:
                x += sx
                err += dy


def draw_faces_zbuffer(label_field, faces, cam, edge_thickness=DEFAULT_EDGE_THICKNESS,
                       proj_mode='perspective'):
    image = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 3), dtype=np.uint8)
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf)

    for face in faces:
        rasterize_face_zbuffer(face, zbuffer, img_array, proj_mode, cam)

    for face in faces:
        verts = [project_vertex(v, cam=cam, mode=proj_mode) for v in face.vertices]
        n = len(verts)
        for i in range(n):
            x0, y0, z0 = verts[i]
            x1, y1, z1 = verts[(i + 1) % n]
            rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, DEFAULT_EDGE_COLOR, radius=edge_thickness)

    image_bits = image.bits()
    image_bits.setsize(WIDTH_CANVAS * HEIGHT_CANVAS * 4)
    img_rgba = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 4), dtype=np.uint8)
    img_rgba[..., :3] = img_array
    img_rgba[..., 3] = 255
    np.copyto(np.frombuffer(image_bits, np.uint8).reshape((HEIGHT_CANVAS, WIDTH_CANVAS, 4)), img_rgba)

    label_field.setPixmap(QPixmap.fromImage(image))


def draw_scene_with_objects(label_field, faces, cam, objects=[]):
    all_faces = faces.copy()
    for obj in objects:
        all_faces.extend(obj.transformed_faces())

    draw_faces_zbuffer(label_field, all_faces, cam)
