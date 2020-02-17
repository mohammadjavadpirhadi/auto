import math
import polyline
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


def dot(v, w):
    x1, y1, z1 = v
    x2, y2, z2 = w
    return x1*x2 + y1*y2 + z1*z2


def length(v):
    x, y, z = v
    return math.sqrt(x*x + y*y + z*z)


def vector(b, e):
    x1, y1, z1 = b
    x2, y2, z2 = e
    return x2-x1, y2-y1, z2-z1


def unit(v):
    x, y, z = v
    mag = length(v)
    return x/mag, y/mag, z/mag


def distance(p0, p1):
    return length(vector(p0, p1))


def scale(v, sc):
    x, y, z = v
    return x*sc, y*sc, z*sc


def add(v, w):
    x1, y1, z1 = v
    x2, y2, z2 = w
    return x1+x2, y1+y2, z1+z2


# Given a line with coordinates 'start' and 'end' and the
# coordinates of a point 'pnt' the proc returns the shortest
# distance from pnt to the line and the coordinates of the
# nearest point on the line.
#
# 1  Convert the line segment to a vector ('line_vec').
# 2  Create a vector connecting start to pnt ('pnt_vec').
# 3  Find the length of the line vector ('line_len').
# 4  Convert line_vec to a unit vector ('line_unit_vec').
# 5  Scale pnt_vec by line_len ('pnt_vec_scaled').
# 6  Get the dot product of line_unit_vec and pnt_vec_scaled ('t').
# 7  Ensure t is in the range 0 to 1.
# 8  Use t to get the nearest location on the line to the end
#    of vector pnt_vec_scaled ('nearest').
# 9  Calculate the distance from nearest to pnt_vec_scaled.
# 10 Translate nearest back to the start/end line.

def point_distance_from_line(pnt, start, end):
    line_vec = vector(start, end)
    pnt_vec = vector(start, pnt)
    line_len = length(line_vec)
    line_unit_vec = unit(line_vec)
    pnt_vec_scaled = scale(pnt_vec, 1.0/line_len)
    t = dot(line_unit_vec, pnt_vec_scaled)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    nearest = scale(line_vec, t)
    dist = distance(nearest, pnt_vec)
    nearest_point = add(nearest, start)
    return dist, nearest_point


def lat_lon_to_xyz(lat, lon):
    cos_lat = math.cos(lat * math.pi / 180.0)
    sin_lat = math.sin(lat * math.pi / 180.0)
    cos_lon = math.cos(lon * math.pi / 180.0)
    sin_lon = math.sin(lon * math.pi / 180.0)
    rad = 6378137.0
    f = 1.0 / 298.257224
    c = 1.0 / math.sqrt(cos_lat * cos_lat + (1 - f) * (1 - f) * sin_lat * sin_lat)
    s = (1.0 - f) * (1.0 - f) * c
    h = 0.0
    x = (rad * c + h) * cos_lat * cos_lon
    y = (rad * c + h) * cos_lat * sin_lon
    z = (rad * s + h) * sin_lat

    return x, y, z


def lat_lon_to_xyz_point(point):
    lat, lon = point[0], point[1]
    return lat_lon_to_xyz(lat, lon)


@api_view()
def point_distance_from_path_view(request):
    if 'access_token' in request.query_params and request.query_params.get('access_token') == '1':
        if 'lat' in request.query_params and 'lng' in request.query_params:
            try:
                point = (float(request.query_params.get('lat')), float(request.query_params.get('lng')))
            except Exception as e:
                return Response({"info": "Bad request: " + str(e.args)}, status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"info": "lat and lng parameters are necessary"}, status.HTTP_400_BAD_REQUEST)

        lines_range = polyline.decode('a~l~Fjk~uOwHJy@P')

        point_xyz = lat_lon_to_xyz_point(point)
        lines_range_xyz = list(map(lat_lon_to_xyz_point, lines_range))

        min_distance = 99999999999
        for i in range(len(lines_range_xyz) - 1):
            point_distance = point_distance_from_line(point_xyz, lines_range_xyz[i], lines_range_xyz[i + 1])[0]
            if point_distance <= min_distance:
                min_distance = point_distance

        return Response({"distance": min_distance}, status.HTTP_200_OK)
    else:
        return Response({"info": "You don\'t have permission to do this action!"}, status.HTTP_403_FORBIDDEN)
