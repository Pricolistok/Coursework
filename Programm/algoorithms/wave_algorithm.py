from collections import deque
import numpy as np


def wave_path(matrix, start, end):
    rows, cols = len(matrix), len(matrix[0])
    sr, sc = start
    er, ec = end

    if matrix[sr][sc] == 0 or matrix[er][ec] == 0:
        raise ValueError("Начальная или конечная точка недоступна (0).")

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    dist = [[-1] * cols for _ in range(rows)]
    dist[sr][sc] = 0

    queue = deque([(sr, sc)])
    while queue:
        r, c = queue.popleft()
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] == 1 and dist[nr][nc] == -1:
                dist[nr][nc] = dist[r][c] + 1
                queue.append((nr, nc))

    if dist[er][ec] == -1:
        return None

    path = [[er, ec]]
    r, c = er, ec
    while (r, c) != (sr, sc):
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and dist[nr][nc] == dist[r][c] - 1:
                path.append([nr, nc])
                r, c = nr, nc
                break
    path.reverse()
    return path


def path_to_real_coords(path, real_coords_matrix):
    real_path = []
    for r, c in path:
        real_path.append(np.array(real_coords_matrix[r][c], dtype=float))
    return real_path
