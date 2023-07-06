import copy
import json
import sys

from psycopg2 import sql
from psycopg2.extras import DictCursor

from cjdb.logger import logger

import multiprocessing as mp


# exporter class
class Exporter:
    def __init__(self, connection, schema, sqlquery, output):
        self.connection = connection
        self.schema = schema
        self.sqlquery = sqlquery
        # self.fout = open(output, "w")
        self.output = output
        self.bboxmin = [0.0, 0.0, 0.0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()
        # self.fout.close()

    def run_export_fast(self) -> None:
        sql_query = f"""
            WITH only_parents AS (
                SELECT cjo.id, cjo.object_id
                FROM {self.schema}.city_object cjo
                LEFT JOIN {self.schema}.city_object_relationships f
                ON cjo.id = f.child_id
                WHERE f.child_id IS NULL)
            SELECT
                cjo.id, cjo.object_id, array_agg(f.child_id) as children
            FROM
                {self.schema}.city_object cjo
            LEFT JOIN
                {self.schema}.city_object_relationships  f
            ON cjo.id  = f.parent_id
            JOIN
                only_parents op
            ON cjo.id = op.id
            WHERE cjo."id" IN ({self.sqlquery})
            GROUP BY
                cjo.id, cjo.object_id;
            """

        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        if len(rows) == 0:
            logger.warning("No data from the input ids.")
            sys.exit(1)

        #-- get the parent-[children]        
        pcrel = {}
        for r in rows:
            pcrel[r['id']] = r['children']

        #-- first line of the CityJSONL stream with some metadata
        cursor.execute(
            sql.SQL("select m.* from {}.cj_metadata m")
                     .format(sql.Identifier(self.schema))
        )
        meta1 = cursor.fetchone()
        j = {}
        j["type"] = "CityJSON"
        j["version"] = meta1[1]
        j["CityObjects"] = {}
        j["vertices"] = []
        j["transform"] = {}
        imp_digits = 3 #-- TODO: defined by users so expose
        j["transform"]["scale"] = [1.0/pow(10, imp_digits), 1.0/pow(10, imp_digits), 1.0/pow(10, imp_digits)]
        j["metadata"] = {}
        if "referenceSystem" in meta1:
            # TODO: Fetch the referenceSystem from the SRID
            # Can be quried from the DB with
            # "ST_SRID(cjo.ground_geometry) as epsg".
            # Will be tricky because the buildings with parts
            # do not have a ground_geometry.
            j["metadata"]["referenceSystem"] = meta1["metadata"][
                "referenceSystem"
            ]
        else:
            j["metadata"]["referenceSystem"] = "https://www.opengis.net/def/crs/EPSG/0/" + str(meta1["srid"])
        
        #-- fetch in memory all we need, won't work for super large datasets
        sq = f"select * from {self.schema}.city_object;"
        cursor.execute(sq)
        rows = cursor.fetchall()
        self.bboxmin = self.find_min_bbox(rows)
        j["transform"]["translate"] = self.bboxmin
        
        f_out = open(self.output, "w") 
        print(json.dumps(j, separators=(',', ':')), file=f_out)
        
        #-- modify the dict for quick access
        d = {}
        for r in rows:
            d[r["id"]] = r

        #-- iterate over each and write to the file
        for key, children in pcrel.items():
            re = write_cjf_fast(key, children, d, pcrel, self.bboxmin)
            print(re, file=f_out)
        #-- testing multiprocessing
        # t = []
        # for key, children in pcrel.items():
            # t.append([key, children, d, pcrel, self.bboxmin])
        # with mp.Pool() as p:
            # for result in p.starmap(write_cjf_fast, t):
                # print(result, file=f_out)
        f_out.close()

    def run_export(self) -> None:
        sql_query = f"""
            WITH only_parents AS (
                SELECT cjo.id, cjo.object_id
                FROM {self.schema}.city_object cjo
                LEFT JOIN {self.schema}.city_object_relationships f
                ON cjo.object_id = f.child_id
                WHERE f.child_id IS NULL)
            SELECT
                cjo.id, cjo.object_id, cjo.type, cjo.attributes,
                cjo.geometry, cjm.version, cjm.metadata, cjm.srid,
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
                cjm.srid, cjm.metadata,
                cjm."transform";
            """

        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        if len(rows) == 0:
            logger.warning("No data from the input ids.")
            sys.exit(1)

        # TODO: verify that all queried buildings have the same metadata.
        # For now we take the first.

        cjson = {}
        cjson["type"] = "CityJSON"
        cjson["version"] = rows[0]["version"]
        cjson["CityObjects"] = {}
        cjson["vertices"] = []
        cjson["transform"] = rows[0]["transform"]
        cjson["metadata"] = {}
        if "referenceSystem" in rows[0]["metadata"].keys():
            # TODO: Fetch the referenceSystem from the SRID
            # Can be quried from the DB with
            # "ST_SRID(cjo.ground_geometry) as epsg".
            # Will be tricky because the buildings with parts
            # do not have a ground_geometry.
            cjson["metadata"]["referenceSystem"] = rows[0]["metadata"][
                "referenceSystem"
            ]
        else:
            cjson["metadata"]["referenceSystem"] = rows[0]["srid"]

        # TODO: add geometry-template from all imported files or select only the ones relevant?
        #       We could iterate over the ids and fetch the ones having '+' but that's tricky
        #       Outputting an extension that is not used is not a huge issue though
        # TODO: add extra-properties? Tricky to know which ones to be honest, maybe a flag?
        self.fout.write(json.dumps(cjson, separators=(",", ":")) + "\n")

        # print(type(rows))
        # pool = multiprocessing.Pool(processes=16)
        # outputs_async = pool.map(self.write_cjf, rows)
        # outputs_async.get() 
        for row in rows:
            self.write_cjf(row)
        logger.info(f"Exported succesfully to '{self.fout.name}'")
 

    def write_cjf(self, row):
        j = {}
        j["type"] = "CityJSONFeature"
        j["id"] = row["object_id"]
        j["CityObjects"] = {}
        j["CityObjects"][row["object_id"]] = {}
        j["CityObjects"][row["object_id"]]["type"] = row["type"]
        if row["attributes"] is not None:
            j["CityObjects"][row["object_id"]]["attributes"] =\
                row["attributes"]
        # parent first
        vertices = []
        g2, vs = self.reference_vertices_in_cjf(
            row["geometry"], 3, self.bboxmin, len(vertices)
        )
        vertices.extend(vs)
        if g2 is not None:
            j["CityObjects"][row["object_id"]]["geometry"] = g2

        ls_parents_children = []
        for each in row["children"]:
            if each is not None:
                ls_parents_children.append((row["object_id"], each))
        while len(ls_parents_children) > 0:
            pc = ls_parents_children.pop()
            j, vertices, new_pc = self.add_child_to_cjf(
                j, pc[0], pc[1], vertices, self.bboxmin
            )
            ls_parents_children.extend(new_pc)
        j["vertices"] = vertices
        j = self.remove_duplicate_vertices(j)
        self.fout.write(json.dumps(j, separators=(",", ":")) + "\n")       


    def add_child_to_cjf(self, j, parent_id, child_id, vertices, bboxmin):
        if "children" not in j["CityObjects"][parent_id]:
            j["CityObjects"][parent_id]["children"] = []
        cursor = self.connection.cursor(cursor_factory=DictCursor)
        cursor.execute(
            sql.SQL(
                """SELECT cjo.*
                       FROM {}.city_object cjo
                       WHERE cjo.object_id = %s"""
            ).format(sql.Identifier(self.schema)),
            (child_id,),
        )
        r = cursor.fetchone()
        j["CityObjects"][parent_id]["children"].append(child_id)
        j["CityObjects"][child_id] = {}
        j["CityObjects"][child_id]["type"] = r[2]
        if r[3] is not None:
            j["CityObjects"][child_id]["attributes"] = r[3]
        j["CityObjects"][child_id]["parents"] = [parent_id]
        g2, vs = \
            self.reference_vertices_in_cjf(r[4], 3, bboxmin, len(vertices))
        vertices.extend(vs)
        if g2 is not None:
            j["CityObjects"][child_id]["geometry"] = g2
        #   does the child has children?
        ls_parents_children = []
        # (row[0], each)
        cursor.execute(
            sql.SQL(
                """SELECT f.child_id
                    FROM {}.city_object_relationships f \
                    WHERE f.parent_id = %s"""
            ).format(sql.Identifier(self.schema)),
            (child_id,),
        )
        for c in cursor.fetchall():
            ls_parents_children.append((child_id, c[0]))
        return (j, vertices, ls_parents_children)

    def find_min_bbox(self, rows):
        bboxmin = [sys.float_info.max, sys.float_info.max, sys.float_info.max]
        for row in rows:
            if row["geometry"] is not None:
                for g in row["geometry"]:
                    if g["type"] == "Solid":
                        for shell in g["boundaries"]:
                            for surface in shell:
                                for ring in surface:
                                    for vertex in ring:
                                        for i in range(3):
                                            if vertex[i] < bboxmin[i]:
                                                bboxmin[i] = vertex[i]
                    elif g["type"] == "MultiSurface" \
                                      or g["type"] == "CompositeSurface":
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
        # update indices
        for theid in j["CityObjects"]:
            if "geometry" in j["CityObjects"][theid]:
                for g in j["CityObjects"][theid]["geometry"]:
                    update_geom_indices(g["boundaries"], newids)
        # replace the vertices, innit?
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
        p = "%." + str(imp_digits) + "f"
        for h, g in enumerate(gs):
            if g["type"] == "Solid":
                for i, shell in enumerate(g["boundaries"]):
                    for j, surface in enumerate(shell):
                        for k, ring in enumerate(surface):
                            for l, vertex in enumerate(ring):
                                gs2[h]["boundaries"][i][j][k][l] = offset
                                offset += 1
                                v = [0.0, 0.0, 0.0]
                                for r in range(3):
                                    v[r] = int(
                                        (p % (vertex[r] - translate[r]))
                                        .replace(
                                            ".", ""
                                        )
                                    )
                                vertices.append(v)
            elif g["type"] == "MultiSurface" \
                              or g["type"] == "CompositeSurface":
                for j, surface in enumerate(g["boundaries"]):
                    for k, ring in enumerate(surface):
                        for l, vertex in enumerate(ring):
                            gs2[h]["boundaries"][j][k][l] = offset
                            offset += 1
                            v = [0.0, 0.0, 0.0]
                            for r in range(3):
                                v[r] = int(
                                    (p % (vertex[r] - translate[r]))
                                    .replace(".", "")
                                )
                            vertices.append(v)
            # TODO: MultiSolid
        return (gs2, vertices)



def write_cjf_fast(parent, children, d, pcrel, bboxmin):
    poid = d[parent]["object_id"]
    j = {}
    j["type"] = "CityJSONFeature"
    j["id"] = poid
    j["CityObjects"] = {}
    j["CityObjects"][poid] = {}
    j["CityObjects"][poid]["type"] = d[parent]["type"]
    if d[parent]["attributes"] is not None:
        j["CityObjects"][poid]["attributes"] =\
            d[parent]["attributes"]
    # parent first
    vertices = []
    g2, vs = reference_vertices_in_cjf_fast(
        d[parent]["geometry"], 3, bboxmin, len(vertices)
    )
    vertices.extend(vs)
    if g2 is not None:
        j["CityObjects"][poid]["geometry"] = g2
    ls_parents_children = []
    for child in children:
        if child is not None:
            ls_parents_children.append((parent, child))
    while len(ls_parents_children) > 0:
        pc = ls_parents_children.pop()
        j, vertices = add_child_to_cjf_fast(
            j, pc[0], pc[1], vertices, bboxmin, d
        )
        # ls_parents_children.extend(new_pc)
        if pc[1] in pcrel:
            ls_parents_children.extend(pcrel[pc[1]])
    j["vertices"] = vertices
    j = remove_duplicate_vertices(j)
    return json.dumps(j, separators=(",", ":"))
    # fout.write(json.dumps(j, separators=(",", ":")) + "\n")





def add_child_to_cjf_fast(j, parent_id, child_id, vertices, bboxmin, d):
    poid = d[parent_id]["object_id"]
    coid = d[child_id]["object_id"]
    if "children" not in j["CityObjects"][poid]:
        j["CityObjects"][poid]["children"] = []
    j["CityObjects"][poid]["children"].append(coid)
    j["CityObjects"][coid] = {}
    j["CityObjects"][coid]["type"] = d[child_id]["type"]
    if "attributes" in d[child_id]:
        j["CityObjects"][coid]["attributes"] = d[child_id]["attributes"]
    j["CityObjects"][coid]["parents"] = [poid]
    g2, vs = \
        reference_vertices_in_cjf_fast(d[child_id]["geometry"], 3, bboxmin, len(vertices))
    vertices.extend(vs)
    if g2 is not None:
        j["CityObjects"][coid]["geometry"] = g2
    return (j, vertices)

def remove_duplicate_vertices(j):
    def update_geom_indices(a, newids):
        for i, each in enumerate(a):
            if isinstance(each, list):
                update_geom_indices(each, newids)
            else:
                a[i] = newids[each]

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
    # update indices
    for theid in j["CityObjects"]:
        if "geometry" in j["CityObjects"][theid]:
            for g in j["CityObjects"][theid]["geometry"]:
                update_geom_indices(g["boundaries"], newids)
    # replace the vertices, innit?
    newv2 = []
    for v in newvertices:
        a = list(map(int, v.split()))
        newv2.append(a)
    j["vertices"] = newv2
    return j

def reference_vertices_in_cjf_fast(gs, imp_digits, translate, offset=0):
        vertices = []
        if gs is None:
            return (gs, vertices)
        gs2 = copy.deepcopy(gs)
        p = "%." + str(imp_digits) + "f"
        for h, g in enumerate(gs):
            if g["type"] == "Solid":
                for i, shell in enumerate(g["boundaries"]):
                    for j, surface in enumerate(shell):
                        for k, ring in enumerate(surface):
                            for l, vertex in enumerate(ring):
                                gs2[h]["boundaries"][i][j][k][l] = offset
                                offset += 1
                                v = [0.0, 0.0, 0.0]
                                for r in range(3):
                                    v[r] = int(
                                        (p % (vertex[r] - translate[r]))
                                        .replace(
                                            ".", ""
                                        )
                                    )
                                vertices.append(v)
            elif g["type"] == "MultiSurface" \
                              or g["type"] == "CompositeSurface":
                for j, surface in enumerate(g["boundaries"]):
                    for k, ring in enumerate(surface):
                        for l, vertex in enumerate(ring):
                            gs2[h]["boundaries"][j][k][l] = offset
                            offset += 1
                            v = [0.0, 0.0, 0.0]
                            for r in range(3):
                                v[r] = int(
                                    (p % (vertex[r] - translate[r]))
                                    .replace(".", "")
                                )
                            vertices.append(v)
            # TODO: MultiSolid
        return (gs2, vertices)

