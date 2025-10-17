from math import radians, sin, cos

def rotate_dot(x, y, z, angle):
    angle = radians(angle)
    x, y, z = rotate_x(x, y, z, angle)
    x, y, z = rotate_y(x, y, z, angle)
    x, y, z = rotate_z(x, y, z, angle)
    return x, y, z


def rotate_x(x, y, z, ax):
    y_new = y * cos(ax) - z * sin(ax)
    z_new = y * sin(ax) + z * cos(ax)
    return x, y_new, z_new


def rotate_y(x, y, z, ay):
    x_new = x * cos(ay) + z * sin(ay)
    z_new = -x * sin(ay) + z * cos(ay)
    return x_new, y, z_new


def rotate_z(x, y, z, az):
    x_new = x * cos(az) - y * sin(az)
    y_new = x * sin(az) + y * cos(az)
    return x_new, y_new, z
