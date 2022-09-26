
def transform_vertex(vertex, transform):
    vertex[0] = (vertex[0] * transform["scale"][0]) + transform["translate"][0]
    vertex[1] = (vertex[1] * transform["scale"][1]) + transform["translate"][1]
    vertex[2] = (vertex[2] * transform["scale"][2]) + transform["translate"][2]

    return vertex

def resolve_geometry_vertices(geometry, vertices, transform):
    for lod_level in geometry:
        for boundary in lod_level['boundaries']:
            for i, shell in enumerate(boundary):
                if type(shell[0]) is list:
                    for j, ring in enumerate(shell):
                        new_ring = []
                        for vertex_id in ring:
                            xyz = vertices[vertex_id]
                            xyz = transform_vertex(xyz, transform)
                            new_ring.append(xyz)
                        shell[j] = new_ring
                else:
                    new_shell = []
                    for vertex_id in shell:
                        xyz = vertices[vertex_id]
                        xyz = transform_vertex(xyz, transform)
                        new_shell.append(xyz)
                    boundary[i] = new_shell
                    
    return geometry

# todo
def calculate_object_bbox():
    pass
