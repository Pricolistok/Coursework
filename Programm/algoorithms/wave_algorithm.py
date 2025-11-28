from collections import deque
import numpy as np
from settings.consts import MATRIX_DIRECTIONS


def wave_path(matrix_map, start, end):
    """
    Поиск пути BFS с учетом матрицы направлений (MATRIX_DIRECTIONS).
    """
    rows = len(matrix_map)
    cols = len(matrix_map[0])
    sr, sc = start
    er, ec = end

    # Проверка на базовую проходимость (не стена)
    if matrix_map[sr][sc] == 0 or matrix_map[er][ec] == 0:
        # Можно вернуть None или вызвать ошибку, как вам удобнее
        print("Старт или финиш находятся в препятствии.")
        return None

    # came_from хранит: came_from[(r, c)] = (prev_r, prev_c)
    # Это нужно для восстановления пути в ориентированном графе
    came_from = {start: None}

    queue = deque([start])

    path_found = False

    while queue:
        r, c = queue.popleft()

        if (r, c) == end:
            path_found = True
            break

        # Получаем маску разрешенных направлений для ТЕКУЩЕЙ клетки
        # Если вдруг координаты выходят за границы матрицы направлений - движений нет
        if 0 <= r < len(MATRIX_DIRECTIONS) and 0 <= c < len(MATRIX_DIRECTIONS[0]):
            mask = MATRIX_DIRECTIONS[r][c]
        else:
            mask = 0

        # Список потенциальных ходов на основе маски
        # 1=UP, 2=RIGHT, 4=DOWN, 8=LEFT
        potential_moves = []

        if (mask & 1): potential_moves.append((-1, 0))  # Вверх
        if (mask & 2): potential_moves.append((0, 1))  # Вправо
        if (mask & 4): potential_moves.append((1, 0))  # Вниз
        if (mask & 8): potential_moves.append((0, -1))  # Влево

        for dr, dc in potential_moves:
            nr, nc = r + dr, c + dc

            # Проверки:
            # 1. В пределах карты
            # 2. Не стена (matrix_map == 1)
            # 3. Еще не посещали (нет в came_from)
            if 0 <= nr < rows and 0 <= nc < cols:
                if matrix_map[nr][nc] == 1 and (nr, nc) not in came_from:
                    came_from[(nr, nc)] = (r, c)
                    queue.append((nr, nc))

    if not path_found:
        return None

    # Восстановление пути от финиша к старту
    real_path = []
    curr = end
    while curr is not None:
        real_path.append(list(curr))
        curr = came_from[curr]

    real_path.reverse()
    return real_path


def path_to_real_coords(path, real_coords_matrix):
    real_path = []
    for r, c in path:
        real_path.append(np.array(real_coords_matrix[r][c], dtype=float))
    return real_path