from classes.model_classes import *


def read_dots_from_file(file, dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        dot_x, dot_y, dot_z = map(float, tmp.split())
        dots.append(Dot(dot_x, dot_y, dot_z))
        tmp = file.readline()
    file.readlines(2)


def read_edges_from_file(file, edges: list[Edge], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        start, end = map(int, tmp.split())
        edges.append(Edge(dots[start], dots[end]))
        tmp = file.readline()
    file.readlines(2)


def read_faces_from_file(file, faces: list[Face], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '':
        parts = tmp.split()
        color = list(map(int, parts[-3:]))
        vertex_indices = list(map(int, parts[:-3]))
        faces.append(Face([dots[i] for i in vertex_indices], color=color))
        tmp = file.readline()


def reader_from_file(filename: str, dots: list[Dot], edges: list[Edge], faces: list[Face]):
    with open(filename, encoding="utf-8") as file:
        file.readline()
        read_dots_from_file(file, dots)
        read_edges_from_file(file, edges, dots)
        read_faces_from_file(file, faces, dots)


def print_all_data(dots: list[Dot], edges: list[Edge], faces: list[Face]):
    print('Dots:')
    for i in dots:
        print(f'  x: {i.x}, y: {i.y}, z: {i.z}')

    print('Edges:')
    for i in edges:
        print(f'  start: ({i.start_dot.x}, {i.start_dot.y}, {i.start_dot.z}), '
              f'end: ({i.end_dot.x}, {i.end_dot.y}, {i.end_dot.z})')

    print('Faces:')
    for i in faces:
        verts_str = ', '.join([f'({v.x},{v.y},{v.z})' for v in i.vertices])
        print(f'  vertices: [{verts_str}], color: {i.color}')

