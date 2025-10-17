from PyQt5.QtGui import QPixmap, QImage
import numpy as np
from settings.consts import WIDTH_CANVAS, HEIGHT_CANVAS, SCALE, X_OFFSET, Y_OFFSET

def project_vertex(dot):
    x = int(dot.x * SCALE + X_OFFSET)
    y = int(dot.y * SCALE + Y_OFFSET)
    z = dot.z
    return x, y, z

def rasterize_face_zbuffer(face, zbuffer, img_array, color_rgb):
    verts = [project_vertex(v) for v in face.vertices]
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

        x_sorted_idx = np.argsort(x_intersections)
        x_intersections = np.array(x_intersections)[x_sorted_idx]
        z_intersections = np.array(z_intersections)[x_sorted_idx]

        x_start = int(max(min(x_intersections), 0))
        x_end = int(min(max(x_intersections), WIDTH_CANVAS - 1))
        if x_start >= x_end:
            continue

        col_range = np.arange(x_start, x_end + 1)
        z_line = np.interp(col_range, x_intersections, z_intersections)
        mask = z_line < zbuffer[y, col_range]
        zbuffer[y, col_range[mask]] = z_line[mask]
        img_array[y, col_range[mask]] = color_rgb

# функция для рисования «толстого пикселя» с учетом Z-buffer
def plot_thick_pixel(x, y, z, radius, zbuffer, img_array, color):
    for dx in range(-radius, radius+1):
        for dy in range(-radius, radius+1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < WIDTH_CANVAS and 0 <= ny < HEIGHT_CANVAS:
                if z < zbuffer[ny, nx]:
                    zbuffer[ny, nx] = z
                    img_array[ny, nx] = color

def rasterize_line_zbuffer(x0, y0, z0, x1, y1, z1, zbuffer, img_array, color_rgb, radius=1):
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

def draw_faces_zbuffer(label_field, faces, edge_thickness=1):
    image = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 3), dtype=np.uint8)
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf)

    fill_color = np.array([255, 0, 0], dtype=np.uint8)
    edge_color = np.array([255, 255, 255], dtype=np.uint8)

    # заливка граней
    for face in faces:
        rasterize_face_zbuffer(face, zbuffer, img_array, fill_color)

    # линии рёбер с Z-buffer и толщиной
    for face in faces:
        verts = [project_vertex(v) for v in face.vertices]
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
