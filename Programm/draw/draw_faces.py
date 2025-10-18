from PyQt5.QtGui import QPixmap, QImage
from draw.camera import Camera
from settings.consts import *

# Создаем камеру
camera = Camera(position=DEFAULT_CAMERA_POSITION,
                look_at=DEFAULT_CAMERA_LOOK_AT,
                up=DEFAULT_CAMERA_UP,
                fov=DEFAULT_CAMERA_FOV)

# === ПРОЕКЦИИ ===
def project_vertex(dot, cam=camera, mode='perspective'):
    """
    mode: 'perspective' или 'orthographic'
    """
    x, y, z = cam.world_to_camera(dot)
    if mode == 'perspective':
        d = 800  # расстояние до плоскости проекции
        factor = d / (z + d + 1e-9)
        x_proj = x * factor
        y_proj = y * factor
    else:  # ортографическая
        x_proj, y_proj = x, y

    screen_x = int(x_proj * SCALE + X_OFFSET)
    screen_y = int(y_proj * SCALE + Y_OFFSET)
    return screen_x, screen_y, z

# === Z-BUFFER ФУНКЦИИ ===
def rasterize_face_zbuffer(face, zbuffer, img_array, color_rgb, proj_mode='perspective'):
    verts = [project_vertex(v, mode=proj_mode) for v in face.vertices]
    xs, ys, zs = zip(*verts)
    xs = np.array(xs)
    ys = np.array(ys)
    zs = np.array(zs)

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
        zbuffer[y, col_range[mask]] = z_line[mask]
        img_array[y, col_range[mask]] = color_rgb

def plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color):
    # используем векторизацию для ускорения
    xs = np.arange(-radius, radius + 1)
    ys = np.arange(-radius, radius + 1)
    for dx in xs:
        nx = x + dx
        if nx < 0 or nx >= WIDTH_CANVAS:
            continue
        for dy in ys:
            ny = y + dy
            if 0 <= ny < HEIGHT_CANVAS and z < zbuffer[ny, nx]:
                zbuffer[ny, nx] = z
                img_array[ny, nx] = color

def rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, color_rgb, radius=DEFAULT_EDGE_THICKNESS):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    dz = z1 - z0
    x, y = x0, y0
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

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

# === ОТРИСОВКА ВСЕЙ СЦЕНЫ ===
def draw_faces_zbuffer(label_field, faces, edge_thickness=DEFAULT_EDGE_THICKNESS,
                       fill_color=DEFAULT_FILL_COLOR, edge_color=DEFAULT_EDGE_COLOR,
                       proj_mode='perspective'):
    image = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 3), dtype=np.uint8)
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf)

    for face in faces:
        rasterize_face_zbuffer(face, zbuffer, img_array, fill_color, proj_mode)

    for face in faces:
        verts = [project_vertex(v, mode=proj_mode) for v in face.vertices]
        n = len(verts)
        for i in range(n):
            x0, y0, z0 = verts[i]
            x1, y1, z1 = verts[(i + 1) % n]
            rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, edge_color, radius=edge_thickness)

    # копирование в QImage
    image_bits = image.bits()
    image_bits.setsize(WIDTH_CANVAS * HEIGHT_CANVAS * 4)
    img_rgba = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 4), dtype=np.uint8)
    img_rgba[..., :3] = img_array
    img_rgba[..., 3] = 255
    np.copyto(np.frombuffer(image_bits, np.uint8).reshape((HEIGHT_CANVAS, WIDTH_CANVAS, 4)), img_rgba)

    label_field.setPixmap(QPixmap.fromImage(image))
