import copy
import json
import sys

from psycopg2 import sql
from psycopg2.extras import DictCursor

from cjdb.logger import logger


# exporter class
class Exporter:
    def __init__(self, connection, schema, sqlquery, output):
        self.connection = connection
        self.schema = schema
        self.sqlquery = sqlquery
        self.fout = open(output, 'w')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        self.fout.close()

    def run_export(self) -> None:
        sql_query = f"""

            WITH only_parents AS (SELECT cjo.id, cjo.object_id
                                  FROM {self.schema}.city_object cjo
						          LEFT JOIN {self.schema}.city_object_relationships f
						          ON cjo.object_id = f.child_id
						          WHERE f.child_id IS NULL)
                    SELECT
                        cjo.id, cjo.object_id, cjo.type, cjo.attributes,
                        cjo.geometry, cjm.version, cjm.metadata,
                        cjm."transform", array_agg(f.child_id) as children
                    FROM
                        {self.schema}.city_object cjo
                    JOIN
                        {self.schema}.cj_metadata cjm
                    ON cjo.cj_metadata_id  = cjm.id
                    LEFT JOIN
                        {self.schema}.city_object_relationships  f
                    ON cjo.object_id  = f.parent_id
                    JOIN
                        only_parents op
                    ON cjo.id = op.id
                    WHERE cjo."id" IN ({self.sqlquery})
                    GROUP BY
                        cjo.id, cjo.object_id,
                        cjo.type, cjo.attributes,
                        cjo.geometry, cjm.version,
                        cjm.metadata, cjm."transform" ;
                  """

        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        if len(rows) == 0:
            logger.warning("No data from the input ids.")
            sys.exit(1)

        bboxmin = self.find_min_bbox(rows)

        # TODO: verify that all queried buildings have the same metadata.
        # For now we take the first.

        cjson = {}
        cjson["type"] = "CityJSON"
        cjson["version"] = rows[0]['version']
        cjson["CityObjects"] = {}
        cjson["vertices"] = []
        cjson["transform"] = rows[0]["transform"]
        cjson["metadata"] = rows[0]["metadata"]

        self.fout.write(json.dumps(cjson, separators=(',', ':')) + '\n')


        for row in rows:
            j = {}
            j["type"] = "CityJSONFeature"
            j["id"] = row['object_id']
            j["CityObjects"] = {}
            j["CityObjects"][row['object_id']] = {}
            j["CityObjects"][row['object_id']]["type"] = row['type']
            if row['attributes'] is not None:
                j["CityObjects"][row['object_id']]["attributes"] = row['attributes']
            #-- parent first
            vertices = []
            g2, vs = self.reference_vertices_in_cjf(row['geometry'], 3, bboxmin, len(vertices))
            vertices.extend(vs)
            if g2 is not None:      
                j["CityObjects"][row['object_id']]["geometry"] = g2

            ls_parents_children = []
            for each in row['children']:
                if each is not None:
                    ls_parents_children.append((row['object_id'], each))
            while len(ls_parents_children) > 0:
                pc = ls_parents_children.pop()
                j, vertices, new_pc = self.add_child_to_cjf(j, pc[0], pc[1], vertices, bboxmin)
                ls_parents_children.extend(new_pc)
            j["vertices"] = vertices
            j = self.remove_duplicate_vertices(j)
            self.fout.write(json.dumps(j, separators=(',', ':')) + '\n')
        logger.info(f"Exported succesfully to '{self.fout.name}'")

    def add_child_to_cjf(self, j, parent_id, child_id, vertices, bboxmin):
        if "children" not in j["CityObjects"][parent_id]:
            j["CityObjects"][parent_id]["children"] = []
        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(
            sql.SQL("select cjo.* from {}.city_object cjo where cjo.object_id = %s")
                     .format(sql.Identifier(self.schema)),
                     (child_id,)
        )
        r = cursor.fetchone()
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
        cursor.execute(
            sql.SQL("select f.child_id from {}.city_object_relationships f \
                where f.parent_id = %s")
                     .format(sql.Identifier(self.schema)),
                     (child_id,)
        )
        for c in cursor.fetchall():
            ls_parents_children.append( (child_id, c[0]))
        return (j, vertices, ls_parents_children)

    def find_min_bbox(self, rows):
        bboxmin = [sys.float_info.max, sys.float_info.max, sys.float_info.max]
        for row in rows:
            if row['geometry'] is not None:
                for g in row['geometry']:
                    if g["type"] == "Solid":
                        for shell in g["boundaries"]:
                            for surface in shell:
                                for ring in surface:
                                    for vertex in ring:
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
                        logger.warning("GEOMETRY NOT SUPPORTED YET")
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



