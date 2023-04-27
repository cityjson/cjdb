import json
import os
import sys
import copy

from psycopg2 import sql


from cjdb.logger import logger
from cjdb.modules.exceptions import (InvalidCityJSONObjectException,
                                     InvalidFileException,
                                     InvalidMetadataException)

# exporter class
class Exporter:
    def __init__(self, connection, schema, sqlquery, output):
        self.connection = connection
        self.cur = None
        self.schema = schema
        self.sqlquery = sqlquery
        self.fout = open(output, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        self.fout.close()

    def run_export(self) -> None:
        self.cur = self.connection.cursor()
        #-- Fetch all the IDs (user-defined)
        # cur.execute("select cjo.id from cjdb.city_object cjo where cjo.type = 'TINRelief';")
        # cur.execute("select cjo.id from cjdb.city_object cjo where (attributes->'AbsoluteEavesHeight')::float > 20.1 order by id asc;")
        # TODO: add the schema to the query? It's unclear for the user really...
        self.cur.execute(self.sqlquery)
        rows = self.cur.fetchall()
        query_ids = list(map(lambda x: x[0], rows))
        if len(query_ids) == 0:
            logger.error(f"Query returns no city object IDs")
            return

        self.cur.execute(
            sql.SQL("select cjo.* from {}.city_object cjo where id = any (%s)")
                     .format(sql.Identifier(self.schema)),
            (query_ids,)
        )
        rows = self.cur.fetchall()
        bboxmin = self.find_min_bbox(rows)

        #-- first line of the CityJSONL stream
        self.cur.execute(
            sql.SQL("select m.* from {}.cj_metadata m")
                     .format(sql.Identifier(self.schema))
        )
        meta1 = self.cur.fetchone()
        j = {}
        j["type"] = "CityJSON"
        j["version"] = meta1[1]
        j["CityObjects"] = {}
        j["vertices"] = []
        j["transform"] = {}
        imp_digits = 3 #-- defined by users
        j["transform"]["scale"] = [1.0/pow(10, imp_digits), 1.0/pow(10, imp_digits), 1.0/pow(10, imp_digits)]
        j["transform"]["translate"] = bboxmin
        j["metadata"] = {}
        j["metadata"]["referenceSystem"] = meta1[2]["referenceSystem"]
        # TODO: what do we do with other metadata? Cannot merge really... so only CRS
        self.fout.write(json.dumps(j, separators=(',', ':')) + '\n')

        q = sql.SQL(
             "select cjo.object_id from {}.city_object cjo \
             left join {}.city_object_relationships f \
             on cjo.object_id = f.child_id  \
             where f.child_id is NULL;").format(
                sql.Identifier(self.schema),
                sql.Identifier(self.schema)
            )
        self.cur.execute(q)
        ids_not_a_child = set()
        for i in self.cur.fetchall():
            ids_not_a_child.add(i[0])

        q = sql.SQL(
             "select cjo.object_id as coid, cjo.type, cjo.attributes, cjo.geometry, array_agg(f.child_id) as children \
             from (select object_id, type, attributes, geometry from {}.city_object where id = any(%s)) cjo \
             left join {}.city_object_relationships  f \
             on cjo.object_id  = f.parent_id \
             group by cjo.object_id, cjo.type, cjo.attributes, cjo.geometry \
             order by cjo.object_id;").format(
                sql.Identifier(self.schema),
                sql.Identifier(self.schema)
            )            
        self.cur.execute(q, (query_ids,))
        rows = self.cur.fetchall()
        for row in rows:
            if row[0] in ids_not_a_child:
                j = {}
                j["type"] = "CityJSONFeature"
                j["id"] = row[0]
                j["CityObjects"] = {}
                j["CityObjects"][row[0]] = {}
                j["CityObjects"][row[0]]["type"] = row[1]
                if row[2] is not None:
                    j["CityObjects"][row[0]]["attributes"] = row[2]
                #-- parent first
                vertices = []
                g2, vs = self.reference_vertices_in_cjf(row[3], 3, bboxmin, len(vertices))
                vertices.extend(vs)
                if g2 is not None:      
                    j["CityObjects"][row[0]]["geometry"] = g2

                ls_parents_children = []
                for each in row[4]:
                    if each is not None:
                        ls_parents_children.append( (row[0], each) )
                while len(ls_parents_children) > 0:
                    pc = ls_parents_children.pop()
                    j, vertices, new_pc = self.add_child_to_cjf(j, pc[0], pc[1], vertices, bboxmin)
                    ls_parents_children.extend(new_pc)
                j["vertices"] = vertices
                j = self.remove_duplicate_vertices(j)
                self.fout.write(json.dumps(j, separators=(',', ':')) + '\n')
        logger.info(f"Exported succesfully (part of) the database to '{self.fout.name}'")


    def add_child_to_cjf(self, j, parent_id, child_id, vertices, bboxmin):
        if "children" not in j["CityObjects"][parent_id]:
            j["CityObjects"][parent_id]["children"] = []
        self.cur.execute(
            sql.SQL("select cjo.* from {}.city_object cjo where cjo.object_id = %s")
                     .format(sql.Identifier(self.schema)),
                     (child_id,)
        )
        r = self.cur.fetchone()
        j["CityObjects"][parent_id]["children"].append(child_id)
        j["CityObjects"][child_id] = {}
        j["CityObjects"][child_id]["type"] = r[2]
        if r[3] is not None:
            j["CityObjects"][child_id]["attributes"] = r[3]
        j["CityObjects"][child_id]["parents"] = [parent_id]
        g2, vs = self.reference_vertices_in_cjf(r[4], 3, bboxmin, len(vertices))
        vertices.extend(vs)
        if g2 is not None:
            j["CityObjects"][child_id]["geometry"] = g2 
        #-- does the child has children?
        ls_parents_children = []
        # (row[0], each)
        self.cur.execute(
            sql.SQL("select f.child_id from {}.city_object_relationships f \
                where f.parent_id = %s")
                     .format(sql.Identifier(self.schema)),
                     (child_id,)
        )
        for c in self.cur.fetchall():
            ls_parents_children.append( (child_id, c[0]))
        return (j, vertices, ls_parents_children)


    def find_min_bbox(self, rows):
        bboxmin = [sys.float_info.max, sys.float_info.max, sys.float_info.max]
        for row in rows:
            if row[4] is not None:
                for g in row[4]:
                    if g["type"] == "Solid":
                        for shell in g["boundaries"]:
                            for surface in shell:
                                for ring in surface:
                                    for vertex in ring:
                                        # print(vertex)
                                        for i in range(3):
                                            if vertex[i] < bboxmin[i]:
                                                bboxmin[i] = vertex[i]
                    elif g["type"] == "MultiSurface" or g["type"] == "CompositeSurface":
                        for surface in g["boundaries"]:
                            for ring in surface:
                                for vertex in ring:
                                    for i in range(3):
                                        if vertex[i] < bboxmin[i]:
                                            bboxmin[i] = vertex[i]
                    else:
                        # TODO: implement for MultiSolid
                        print("GEOMETRY NOT SUPPORTED YET")
        return bboxmin

    def remove_duplicate_vertices(self, j):
        def update_geom_indices(a, newids):
          for i, each in enumerate(a):
            if isinstance(each, list):
                update_geom_indices(each, newids)
            else:
                a[i] = newids[each]
        #--            
        h = {}
        newids = [-1] * len(j["vertices"])
        newvertices = []
        for i, v in enumerate(j["vertices"]):
            s = "{x} {y} {z}".format(x=v[0], y=v[1], z=v[2])
            if s not in h:
                newid = len(h)
                newids[i] = newid
                h[s] = newid
                newvertices.append(s)
            else:
                newids[i] = h[s]
        #-- update indices
        for theid in j["CityObjects"]:
            if 'geometry' in j['CityObjects'][theid]:
                for g in j['CityObjects'][theid]['geometry']:
                    update_geom_indices(g["boundaries"], newids)
        #-- replace the vertices, innit?
        newv2 = []
        for v in newvertices:
            a = list(map(int, v.split()))
            newv2.append(a)
        j["vertices"] = newv2
        return j


    def reference_vertices_in_cjf(self, gs, imp_digits, translate, offset=0):
        vertices = []
        if gs is None:
            return (gs, vertices)
        gs2 = copy.deepcopy(gs)
        p = '%.' + str(imp_digits) + 'f' 
        for (h, g) in enumerate(gs):
            if g["type"] == "Solid":
                for (i, shell) in enumerate(g["boundaries"]):
                    for (j, surface) in enumerate(shell):
                        for (k, ring) in enumerate(surface):
                            for (l, vertex) in enumerate(ring):
                                gs2[h]["boundaries"][i][j][k][l] = offset
                                offset += 1                    
                                v = [0., 0., 0.]
                                for r in range(3):
                                    v[r] = int((p % (vertex[r] - translate[r])).replace('.', ''))
                                vertices.append(v)
            elif g["type"] == "MultiSurface" or g["type"] == "CompositeSurface":
                for (j, surface) in enumerate(g["boundaries"]):
                    for (k, ring) in enumerate(surface):
                        for (l, vertex) in enumerate(ring):
                            gs2[h]["boundaries"][j][k][l] = offset
                            offset += 1                    
                            v = [0., 0., 0.]
                            for r in range(3):
                                v[r] = int((p % (vertex[r] - translate[r])).replace('.', ''))
                            vertices.append(v)  
            # TODO: MultiSolid                          
        return (gs2, vertices)



