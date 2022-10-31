import copy
from shapely.geometry import box, MultiPolygon, Point, Polygon
from shapely.validation import explain_validity
from pyproj import CRS, Transformer
from pyproj.transformer import TransformerGroup
import numpy as np


# get srid from a CRS string definition
def get_srid(crs):
    if crs:
        proj = CRS.from_string(crs)
        srid = proj.to_epsg()

        return srid


def transform_vertex(vertex, transform):
    new_v = vertex.copy()
    new_v[0] = (new_v[0] * transform["scale"][0]) + transform["translate"][0]
    new_v[1] = (new_v[1] * transform["scale"][1]) + transform["translate"][1]
    new_v[2] = (new_v[2] * transform["scale"][2]) + transform["translate"][2]

    return new_v


def transform_with_rotation(vertex, transform):
    # matrix multiplication as in https://www.cityjson.org/dev/geom-templates/
    homo_vertex = np.array([vertex + [1]]).T
    t_matrix = np.reshape(transform, (4, 4))

    transformed_vertex = np.dot(t_matrix, homo_vertex)
    return list(transformed_vertex.T[0])[:-1]


def reproject_vertex_list(vertices, srid_from, srid_to):
    source_proj = CRS.from_epsg(srid_from)
    target_proj = CRS.from_epsg(srid_to)

    # prepare transformer from crs to crs
    transformer = Transformer.from_crs(source_proj, target_proj, always_xy=True)

    # transform all the coordinates
    reprojected_xyz = transformer.transform(*zip(*vertices))
    reprojected_xyz = [list(i) for i in zip(*reprojected_xyz)]

    return reprojected_xyz


def resolve(lod_level, vertices, inplace=True):
    if inplace:
        resolvable = lod_level
    else:
        resolvable = copy.deepcopy(lod_level)

    for boundary in resolvable['boundaries']:
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

    return resolvable

def resolve_template(lod_level, vertices, geometry_templates, source_target_srid):
    # get anchor point
    vertex_id = lod_level["boundaries"][0]
    anchor = vertices[vertex_id]

    # apply transformation matrix to the template vertices
    template_vertices = [transform_with_rotation(v, lod_level["transformationMatrix"]) 
            for v in geometry_templates["vertices-templates"]]

    # add anchor point to the vertices
    template_vertices = [list(np.array(v) + anchor) for v in template_vertices]

    # reproject vertices if needed
    if source_target_srid:
        template_vertices = reproject_vertex_list(template_vertices, *source_target_srid)

    # dereference template vertices
    template_id = lod_level["template"]
    template = geometry_templates["templates"][template_id]
    
    # inplace=False, because the template can be resolved differently for some other cityobject
    resolved_template = resolve(template, template_vertices, inplace=False)
    return resolved_template


def resolve_geometry_vertices(geometry, vertices, 
                                geometry_templates, source_target_srid):

    # use ready vertices to resolve coordinate values for the geometry (or geometry template)
    for i, lod_level in enumerate(geometry):
        if lod_level["type"] == "GeometryInstance":
            resolved_template = resolve_template(lod_level, 
                                                vertices,
                                                geometry_templates,
                                                source_target_srid)
            geometry[i] = resolved_template
        else:
            # resolve without geometry template
            resolve(lod_level, vertices)

    return geometry


def get_ground_geometry(geometry):
    # returns a shapely multipolygon (see shapely.geometry.MultiPolygon)
    # the MultiPolygon should be a 2D geometry (Z coordinate is omitted)
    # this geometry should be obtained by parsing the "geometry" object from cityjson -> the argument of this function
    # the geometry is a multipolygon of all the ground surfaces in the lowest available LOD

    polygons=[]
    planes=dict()
    z_min=0
    for boundary in geometry[0]["boundaries"]:
        for i, shell in enumerate(boundary):
            if type(shell[0]) is list:
                if type(shell[0][0]) is list:
                    for ring in shell:
                        Point_list=[]
                        z_tot=0
                        z_count=0
                        for x, y,z in ring:
                            z_tot=z+z_tot
                            z_count=z_count+1
                            p=Point(x,y,z)
                            Point_list.append(p)
                        z_avg=round(z_tot/z_count,4)
                        z_min=z_avg
                        planes[str(z_avg)]=Point_list                
                else:
                    Point_list=[]                   
                    z_tot=0
                    z_count=0
                    for x,y,z in shell:
                        z_tot=z+z_tot
                        z_count=z_count+1
                        p=Point(x,y,z)
                        Point_list.append(p)
                    z_avg=round(z_tot/z_count,4)
                    planes[str(z_avg)]=Point_list
    
    
    for key in planes:
        z_num=float(key)
        if(z_num<z_min):
            z_min=z_num

    ground_points=[]

    for key in planes:
        if(abs(float(key)-z_min)<0.3):
            poly = Polygon([[p.x, p.y] for p in planes[key]])
            for p in planes[key]:
                ground_points.append(p)
                
    ground_polygon=Polygon([[p.x, p.y] for p in ground_points])
    if(ground_polygon.is_valid==False):
        ground_polygon=ground_polygon.buffer(0)
        if(ground_polygon.is_valid==False):
            print(explain_validity(ground_polygon))

    if (type(ground_polygon) is Polygon):
        ground_polygon=MultiPolygon([ground_polygon])
    
    return ground_polygon