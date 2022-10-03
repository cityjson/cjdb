
from shapely.geometry import box
from pyproj import CRS

def transform_vertex(vertex, transform):
    vertex[0] = (vertex[0] * transform["scale"][0]) + transform["translate"][0]
    vertex[1] = (vertex[1] * transform["scale"][1]) + transform["translate"][1]
    vertex[2] = (vertex[2] * transform["scale"][2]) + transform["translate"][2]

    return vertex

def geometry_from_extent(extent, ref_system):
    bbox = box(extent[0], extent[1], extent[3], extent[4])
    proj = CRS.from_string(ref_system)
    srid = proj.to_epsg()

    geom = bbox.wkt
    if ref_system:
        geom = f"SRID={srid};{geom}"
    return geom

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
                        shell[j] = new_ring
                else:
                    new_shell = []
                    for vertex_id in shell:
                        xyz = vertices[vertex_id]
                        xyz = transformed_vertices[vertex_id]
                        new_shell.append(xyz)
                    boundary[i] = new_shell
                    
    return geometry

# todo
# should return geometry as EWKT format
def calculate_object_bbox(geometry):
    return None
    # min_X, min_Y = 99999999
    # max_X, max_Y = 0

    # for lod_level in geometry:
    #     for boundary in lod_level["boundaries"]:
    #         for i,shell in enumerate(boundary):
    #             if type(shell[0]) is list:
    #                     for j, ring in enumerate(shell):
    #                         for vertex in ring:
    #                             if min_X > vertex[j][0]: min_X = vertex[j][0]
    #                             if min_Y > vertex[j][1]: min_Y = vertex[j][1]
    #                             if max_X < vertex[j][0]: max_X = vertex[j][0]
    #                             if max_Y < vertex[j][1]: max_Y = vertex[j][1]
    #                         break
    #             else:
    #                     for vertex in shell:
    #                         if min_X > vertex[0]: min_X = vertex[0]
    #                         if min_Y > vertex[1]: min_Y = vertex[1]
    #                         if max_X < vertex[0]: max_X = vertex[0]
    #                         if max_Y < vertex[1]: max_Y = vertex[1]
    #                     break
    #         break
    #     break
    
    # bbox = "SRID=28992;POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))".format(min_X,min_Y,max_X,min_Y,max_X,max_Y,min_X,max_Y,min_X,min_Y)
    # return bbox