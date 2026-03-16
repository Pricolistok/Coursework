from collections import deque
import numpy as np
from settings.consts import MATRIX_DIRECTIONS


def wave_path(matrix_map, start, end):
    rows = len(matrix_map)
    cols = len(matrix_map[0])
    sr, sc = start
    er, ec = end

    if matrix_map[sr][sc] == 0 or matrix_map[er][ec] == 0:
        print("Старт или финиш находятся в препятствии.")
        return None

    came_from = {start: None}

    queue = deque([start])

    path_found = False

    while queue:
        r, c = queue.popleft()

        if (r, c) == end:
            path_found = True
            break

        if 0 <= r < len(MATRIX_DIRECTIONS) and 0 <= c < len(MATRIX_DIRECTIONS[0]):
            mask = MATRIX_DIRECTIONS[r][c]
        else:
            mask = 0

        potential_moves = []

        if (mask & 1): potential_moves.append((-1, 0))
        if (mask & 2): potential_moves.append((0, 1))
        if (mask & 4): potential_moves.append((1, 0))
        if (mask & 8): potential_moves.append((0, -1))

        for dr, dc in potential_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if matrix_map[nr][nc] == 1 and (nr, nc) not in came_from:
                    came_from[(nr, nc)] = (r, c)
                    queue.append((nr, nc))

    if not path_found:
        return None

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