
from shapely.geometry import box, MultiPolygon
from shapely.ops import transform
from pyproj import CRS, Transformer
import numpy as np


def get_srid(crs):
    if crs:
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


def transform_with_rotation(vertex, transform):
    homo_vertex = np.array([vertex + [1]]).T
    t_matrix = np.reshape(transform, (4, 4))

    transformed_vertex = np.dot(t_matrix, homo_vertex)
    return list(transformed_vertex.T[0])[:-1]


def geometry_from_extent(extent):
    bbox = box(extent[0], extent[1], extent[3], extent[4])
    return bbox


def resolve(lod_level, vertices):
    for boundary in lod_level['boundaries']:
        for i, shell in enumerate(boundary):
            if type(shell[0]) is list:
                for j, ring in enumerate(shell):
                    new_ring = []
                    for vertex_id in ring:
                        xyz = vertices[vertex_id]
                        new_ring.append(xyz)
                    shell[j] = new_ring
            else:
                new_shell = []
                for vertex_id in shell:
                    xyz = vertices[vertex_id]
                    new_shell.append(xyz)
                boundary[i] = new_shell


def resolve_template(lod_level, transformed_vertices, geometry_templates):
    # get anchor point
    vertex_id = lod_level["boundaries"][0]
    anchor = transformed_vertices[vertex_id]

    # apply transformation matrix to the template vertices
    template_vertices = [transform_with_rotation(v, lod_level["transformationMatrix"]) 
            for v in geometry_templates["vertices-templates"]]

    # add anchor point to the vertices
    template_vertices = [list(np.array(v) + anchor) for v in template_vertices]

    # dereference template vertices
    template_id = lod_level["template"]
    template = geometry_templates["templates"][template_id]
    resolve(template, template_vertices)

    return template


def resolve_geometry_vertices(geometry, vertices, transform, geometry_templates):
    transformed_vertices = [transform_vertex(v, transform) for v in vertices]
        
    # todo
    # reprojecting to a different crs could be done here
    # think however, what would happen to the Z coordinate? Do we only reproject X and Y?

    for i, lod_level in enumerate(geometry):
        if lod_level["type"] == "GeometryInstance":
            resolved_template = resolve_template(lod_level, 
                                                transformed_vertices, 
                                                geometry_templates)
            geometry[i] = resolved_template
        else:
            # resolve without geometry template
            resolve(lod_level, transformed_vertices)

    return geometry


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