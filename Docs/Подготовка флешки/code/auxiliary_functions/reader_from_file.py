import numpy as np
from classes.model_classes import Dot, Edge, Face

def read_dots_from_file(file, dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        parts = tmp.split()
        if len(parts) >= 3:
            dot_x, dot_y, dot_z = map(float, parts)
            dots.append(Dot(dot_x, dot_y, dot_z))
        tmp = file.readline()
    file.readlines(2)

def read_edges_from_file(file, edges: list[Edge], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        parts = tmp.split()
        if len(parts) >= 2:
            start, end = map(int, parts)
            if start < len(dots) and end < len(dots):
                edges.append(Edge(dots[start], dots[end]))
        tmp = file.readline()
    file.readlines(2)

def read_faces_from_file(file, faces: list[Face], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '':
        parts = tmp.split()
        if len(parts) >= 4:  # Минимум 1 вершина + 3 компонента цвета
            # Формат: idx1 idx2 ... idxN R G B
            try:
                color = list(map(int, parts[-3:]))
                vertex_indices = list(map(int, parts[:-3]))
                valid_indices = [i for i in vertex_indices if i < len(dots)]
                if len(valid_indices) >= 3:
                    faces.append(Face([dots[i] for i in valid_indices], color=color))
            except ValueError:
                pass
        tmp = file.readline()

def reader_from_file(filename: str, dots: list[Dot], edges: list[Edge], faces: list[Face]):
    try:
        with open(filename, encoding="utf-8") as file:
            file.readline() # Пропуск заголовка
            read_dots_from_file(file, dots)
            read_edges_from_file(file, edges, dots)
            read_faces_from_file(file, faces, dots)
    except FileNotFoundError:
        print(f"Ошибка: Файл {filename} не найден.")

def read_lights_from_file(filename: str):
    lights = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 7:
                    d = np.array([float(parts[0]), float(parts[1]), float(parts[2])])
                    # Нормализуем цвет к 0..1
                    c = np.array([float(parts[3]), float(parts[4]), float(parts[5])]) / 255.0
                    i = float(parts[6])
                    lights.append({'dir': d, 'color': c, 'intensity': i})
    except FileNotFoundError:
        print(f"Предупреждение: Файл света {filename} не найден. Используется дефолтный свет.")
        lights.append({'dir': np.array([1, 2, 1]), 'color': np.array([1,1,1]), 'intensity': 0.8})
    return lights


def reader_bin_matrix_from_file(filename):
    with open(filename, 'r') as file:
        return tuple(tuple(map(int, row.replace('\n', '').split())) for row in file.readlines())

def reader_matrix_real_coords_map_from_file(filename):
    result = []
    with open(filename, 'r') as file:
        for i in file.readlines():
            i = list(map(int, i.split()))
            saver = []
            for j in range(0, len(i) - 2, 3):
                saver.append(tuple([i[j], i[j + 1], i[j + 2]]))
            result.append(tuple(saver))
        return tuple(result)

def reader_directions_from_file(filename):
    matrix = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    row = [int(x) for x in parts]
                    matrix.append(row)
    except FileNotFoundError:
        print(f"Файл направлений {filename} не найден. Используется пустая матрица.")
        return []
    except ValueError:
        print(f"Ошибка формата в файле {filename}.")
        return []
    return matrix
