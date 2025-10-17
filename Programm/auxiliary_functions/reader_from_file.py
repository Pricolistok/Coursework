from classes.model_classes import *


def read_dots_from_file(file, dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        dot_x, dot_y, dot_z = list(map(float, tmp.split()))
        dots.append(Dot(dot_x, dot_y, dot_z))
        tmp = file.readline()
    file.readlines(2)


def read_edges_from_file(file, edges: list[Edge], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '' and tmp != '\n':
        tmp_edge_start, tmp_edge_end = list(map(int, tmp.split()))
        edges.append(Edge(dots[tmp_edge_start], dots[tmp_edge_end]))
        tmp = file.readline()
    file.readlines(2)


def read_faces_from_file(file, faces: list[Face], dots: list[Dot]):
    tmp = file.readline()
    while tmp != '':
        faces.append(Face([dots[i] for i in list(map(int, tmp.split()))]))
        tmp = file.readline()



def reader_from_file(filename: str, dots: list[Dot], edges: list[Edge], faces: list[Face]):
    with open(filename) as file:
        file.readline()
        read_dots_from_file(file, dots)
        read_edges_from_file(file, edges, dots)
        read_faces_from_file(file, faces, dots)


def print_all_data(dots: list[Dot], edges: list[Edge], faces: list[Face]):
    print('Dots')
    for i in dots:
        print(f'Dot x: {i.x} y: {i.y}, z: {i.z}')

    print('Edges')
    for i in edges:
        print(f'x_s: {i.start_dot.x} y_s: {i.start_dot.y}, z_s: {i.start_dot.z} '
              f'x_e: {i.end_dot.x} y_e: {i.end_dot.y}, z_e: {i.end_dot.z}')

    print('Faces')
    for i in faces:
        for j in i.vertices:
            print(f'x: {j.x} y: {j.y}, z: {j.z}', end=' ')
        print()

