import struct
import json

class ShapeFileException(Exception):
    pass

class WrongFileCode(ShapeFileException):
    pass

class WrongVersion(ShapeFileException):
    pass

class BadShape(ShapeFileException):
    pass

def read_sf(path):
    with open(path, 'rb') as f:
        header_bytes1 = f.read(28)
        file_code, *_, file_length_in_shorts = struct.unpack('>7i', header_bytes1)
        if file_code != 9994:
            raise WrongFileCode(f'wrong file code: {file_code}')
        file_length = file_length_in_shorts // 2
        header_bytes2 = f.read(100 - 28)
        version, shape_type, xmin, ymin, xmax, ymax, zmin, zmax, mmin, mmax \
            = struct.unpack('<2i8d', header_bytes2)
        if version != 1000:
            raise WrongVersion(f'wrong version: {version}')

        parse_record = parser_for_type(shape_type)

        records = []
        while (f.tell() < file_length):
            record_number, record_length_in_shorts = struct.unpack('>2i', f.read(8))
            record_length = record_length_in_shorts * 2
            print(f'record: {record_number}')
            print(f'record: {record_length}')
            record = f.read(record_length)
            records.append(parse_record(record, 0))
        return records

def parser_for_type(shape_type):
    # if shape_type == 0:
    #     return parse_null
    if shape_type == 1:
        return parse_point
    if shape_type == 3:
        return parse_polyline
    if shape_type == 5:
        return parse_polygon
    # if shape_type == 8:
    #     return parse_multipoint
    # if shape_type == 11:
    #     return parse_pointz
    # if shape_type == 13:
    #     return parse_polylinez
    # if shape_type == 15:
    #     return parse_polygonz
    # if shape_type == 18:
    #     return parse_multipointz
    # if shape_type == 21:
    #     return parse_pointm
    # if shape_type == 23:
    #     return parse_polylinem
    # if shape_type == 25:
    #     return parse_polygonm
    # if shape_type == 28:
    #     return parse_multipointm
    # if shape_type == 31:
    #     return parse_multipatch
    raise BadShape(f'bad shape type: {shape_type}')

def parse_point(record, off):
    shape_type, x, y = struct.unpack_from('<idd', record, off)
    assert shape_type == 1, shape_type
    return [x, y], off + 20

def parse_point_no_type(record, off):
    if len(record) - off < 16:
        raise ValueError(f'too short {len(record)} {off} {len(record) - off} "{record[off:].hex()}"')
    x, y = struct.unpack_from('<dd', record, off)
    return [x, y], off + 16

def parse_polyline(record, off):
    # _record = record
    # try:
    shape_type, xmin, ymin, xmax, ymax, n_parts, n_points \
        = struct.unpack_from('<i4d2i', record, off)
    print(f'polyline: n_parts {n_parts}')
    print(f'polyline: n_points {n_points}')
    print(f'polyline: {record[off:(off + 44 + 4 * n_parts * 16 * n_parts)].hex()}')
    off += 44
    assert shape_type == 3, shape_type
    parts = list(struct.unpack_from(f'{n_parts}i', record, off))
    off += n_parts * 4
    points = []
    for i in range(n_points):
        point, newoff = parse_point_no_type(record, off)
        points.append(point)
        off = newoff

    d = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}

    rings = []
    for left, right in zip(parts, parts[1:] + [len(points)]):
        rings.append(points[left:right])
    d['parts'] = rings
    return d
    # except Exception as e:
    #     raise ValueError(f'off {off}, {_record[off:(off + 44 + 4 * n_parts * 16 * n_parts)].hex()}') from e

def parse_polygon(record, off):
    # FIXME: ring orderings
    shape_type, xmin, ymin, xmax, ymax, n_parts, n_points \
        = struct.unpack_from('<i4d2i', record, off)
    off += 44
    assert shape_type == 5, shape_type
    parts = list(struct.unpack_from(f'{n_parts}i', record, off))
    off += n_parts * 4
    points = []
    for _ in range(n_points):
        point, newoff = parse_point_no_type(record, off)
        points.append(point)
        off = newoff

    d = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}

    rings = []
    for left, right in zip(parts, parts[1:] + [len(points)]):
        rings.append(points[left:right])
    # FIXME: maybe call this parts?
    d['rings'] = rings
    return d

def polygon_sf_to_gj(d):
    return {'type': 'Feature',
            'geometry': {
                'type': 'Polygon',
                'coordinates': d['rings']},
            'properties': None}

def polyline_sf_to_gj(d):
    return {'type': 'Feature',
            'geometry': {
                'type': 'MultiLineString',
                'coordinates': d['parts']},
            'properties': None}

def gj_feature_collection(ds):
    return {'type': 'FeatureCollection',
            'features': ds}

def write_gj(path, gj):
    with open(path, 'w') as f:
        json.dump(gj, f)
