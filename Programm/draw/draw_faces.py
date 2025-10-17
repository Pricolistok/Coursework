from PyQt5.QtGui import QPixmap, QColor, QImage, QPainter, QPen
from PyQt5.QtCore import Qt
import numpy as np

from settings.consts import WIDTH_CANVAS, HEIGHT_CANVAS, SCALE, X_OFFSET, Y_OFFSET


def project_vertex(dot):
    """
    Проецирует 3D-вершину в экранные координаты.
    """
    x = int(dot.x * SCALE + X_OFFSET)
    y = int(dot.y * SCALE + Y_OFFSET)
    z = dot.z
    return x, y, z


# ============ РАСТЕРИЗАЦИЯ С Z-БУФЕРОМ (ЗАПОЛНЕНИЕ) ============
def rasterize_face_zbuffer(face, zbuffer, img_array, color_rgb):
    """
    Растеризация одной грани с Z-буфером (построчная заливка).
    """
    verts = np.array([project_vertex(v) for v in face.vertices])
    xs, ys, zs = verts[:, 0], verts[:, 1], verts[:, 2]

    min_y = max(int(np.min(ys)), 0)
    max_y = min(int(np.max(ys)), HEIGHT_CANVAS - 1)
    if max_y < min_y:
        return

    avg_z = np.mean(zs)

    for y in range(min_y, max_y + 1):
        x_intersections = []
        n = len(xs)
        for i in range(n):
            x1, y1 = xs[i], ys[i]
            x2, y2 = xs[(i + 1) % n], ys[(i + 1) % n]

            if (y1 <= y < y2) or (y2 <= y < y1):
                # Линейная интерполяция X
                t = (y - y1) / (y2 - y1 + 1e-9)
                x_intersections.append(x1 + t * (x2 - x1))

        if len(x_intersections) < 2:
            continue

        x_intersections.sort()
        x_start = int(max(min(x_intersections), 0))
        x_end = int(min(max(x_intersections), WIDTH_CANVAS - 1))

        if x_start >= x_end:
            continue

        # Используем NumPy для массовой записи
        row = y
        col_range = np.arange(x_start, x_end + 1)

        mask = avg_z < zbuffer[row, col_range]
        zbuffer[row, col_range[mask]] = avg_z
        img_array[row, col_range[mask]] = color_rgb


# ============ ОСНОВНАЯ ОТРИСОВКА ============
def draw_faces_zbuffer(canvas: QImage, label_field, faces):
    """
    Отрисовка всех граней модели с Z-буфером и контурами рёбер.
    """
    # Создаём изображение и Z-буфер
    image = QImage(WIDTH_CANVAS, HEIGHT_CANVAS, QImage.Format_RGB32)
    img_array = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 3), dtype=np.uint8)
    zbuffer = np.full((HEIGHT_CANVAS, WIDTH_CANVAS), np.inf)

    fill_color = np.array([255, 0, 0], dtype=np.uint8)   # цвет заливки (красный)
    edge_color = QColor(255, 255, 255)                   # цвет рёбер (белый)

    # Заполняем все грани
    for face in faces:
        rasterize_face_zbuffer(face, zbuffer, img_array, fill_color)

    # Преобразуем NumPy-массив в QImage
    image_bits = image.bits()
    image_bits.setsize(WIDTH_CANVAS * HEIGHT_CANVAS * 4)

    img_rgba = np.zeros((HEIGHT_CANVAS, WIDTH_CANVAS, 4), dtype=np.uint8)
    img_rgba[..., :3] = img_array
    img_rgba[..., 3] = 255  # непрозрачный альфа-канал

    np.copyto(
        np.frombuffer(image_bits, np.uint8).reshape((HEIGHT_CANVAS, WIDTH_CANVAS, 4)),
        img_rgba
    )

    # ---- ОТРИСОВКА РЁБЕР ПОВЕРХ ----
    painter = QPainter(image)
    pen = QPen(edge_color)
    pen.setWidth(1)
    painter.setPen(pen)

    for face in faces:
        verts = [project_vertex(v) for v in face.vertices]
        for i in range(len(verts)):
            x1, y1, _ = verts[i]
            x2, y2, _ = verts[(i + 1) % len(verts)]
            painter.drawLine(x1, y1, x2, y2)

    painter.end()

    # Отображаем результат
    label_field.setPixmap(QPixmap.fromImage(image))
