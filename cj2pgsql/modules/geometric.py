
def transform_vertex(vertex, transform):
    vertex[0] = (vertex[0] * transform["scale"][0]) + transform["translate"][0]
    vertex[1] = (vertex[1] * transform["scale"][1]) + transform["translate"][1]
    vertex[2] = (vertex[2] * transform["scale"][2]) + transform["translate"][2]

    return vertex

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
    ### calculate bbox
    example = 'SRID=28992;POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))'
    return example