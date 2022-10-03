
from shapely.geometry import box, MultiPolygon
from shapely.ops import transform
from pyproj import CRS, Transformer

def get_srid(crs):
    proj = CRS.from_string(crs)
    srid = proj.to_epsg()

    return srid


def to_ewkt(wkt, srid):
    if srid:
        wkt = f"SRID={srid};{wkt}"

    return wkt


def reproject(geom, source_srid, target_srid):
    source_proj = CRS.from_epsg(source_srid)
    target_proj = CRS.from_epsg(target_srid)

    projection = Transformer.from_crs(source_proj, target_proj, always_xy=True).transform
    reprojected_geom = transform(projection, geom)

    return reprojected_geom


def transform_vertex(vertex, transform):
    vertex[0] = (vertex[0] * transform["scale"][0]) + transform["translate"][0]
    vertex[1] = (vertex[1] * transform["scale"][1]) + transform["translate"][1]
    vertex[2] = (vertex[2] * transform["scale"][2]) + transform["translate"][2]

    return vertex

def geometry_from_extent(extent):
    bbox = box(extent[0], extent[1], extent[3], extent[4])
    return bbox

def resolve_geometry_vertices(geometry, vertices, transform):
    transformed_vertices = [transform_vertex(v, transform) for v in vertices]
    # todo
    # reprojecting to a different crs could be done here
    # think however, what would happen to the Z coordinate? Do we only reproject X and Y?

    for lod_level in geometry:
        for boundary in lod_level['boundaries']:
            for i, shell in enumerate(boundary):
                if type(shell[0]) is list:
                    for j, ring in enumerate(shell):
                        new_ring = []
                        for vertex_id in ring:
                            xyz = transformed_vertices[vertex_id]
                            new_ring.append(xyz)
                            if type(xyz) != list:
                                pass
                        shell[j] = new_ring
                else:
                    new_shell = []
                    for vertex_id in shell:
                        xyz = vertices[vertex_id]
                        xyz = transformed_vertices[vertex_id]
                        new_shell.append(xyz)
                        if type(xyz) != list:
                                pass
                    boundary[i] = new_shell
    return geometry

# todo
# should return geometry as EWKT format
def calculate_object_bbox(geometry):
    min_X, min_Y = float('inf'), float('inf')
    max_X, max_Y = -float('inf'), -float('inf')

    for boundary in geometry[0]["boundaries"]:
        for i, shell in enumerate(boundary):
            if type(shell[0]) is list:
                if type(shell[0][0]) is list:
                    for ring in shell:
                        for x, y, z in ring:
                            if min_X > x: min_X = x
                            if min_Y > y: min_Y = y
                            if max_X < x: max_X = x
                            if max_Y < y: max_Y = y
                else:
                    for x, y, z in shell:
                        if min_X > x: min_X = x
                        if min_Y > y: min_Y = y
                        if max_X < x: max_X = x
                        if max_Y < y: max_Y = y
         
    return box(min_X, min_Y, max_X, max_Y)


# todo by Lan Yan
def get_ground_geometry(geometry):
    # returns a shapely multipolygon (see shapely.geometry.MultiPolygon)
    # the MultiPolygon should be a 2D geometry (Z coordinate is omitted)
    # this geometry should be obtained by parsing the "geometry" object from cityjson -> the argument of this function
    # the geometry is a multipolygon of all the ground surfaces in the lowest available LOD

    pass