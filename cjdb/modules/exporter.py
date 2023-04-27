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
    def __init__(self, connection, schema, sqlquery):
        self.connection = connection
        self.schema = schema
        self.sqlquery = sqlquery

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def run_export(self) -> None:
        print("exporting...")
        cur = self.connection.cursor()
        #-- Fetch all the IDs (user-defined)
        # cur.execute("select cjo.id from cjdb.city_object cjo where cjo.type = 'TINRelief';")
        # cur.execute("select cjo.id from cjdb.city_object cjo where (attributes->'AbsoluteEavesHeight')::float > 20.1 order by id asc;")
        cur.execute(self.sqlquery)
        rows = cur.fetchall()
        query_ids = list(map(lambda x: x[0], rows))
        if len(query_ids) == 0:
            sys.exit() # TODO: return better error here

        cur.execute(
            sql.SQL("select cjo.* from {}.city_object cjo where id = any (%s)")
                     .format(sql.Identifier(self.schema)),
            (query_ids,)
        )
        # cur.execute("select cjo.* from {%s}.city_object cjo where id = any (%s);", (self.schema, query_ids,))
        rows = cur.fetchall()
        bboxmin = self.find_min_bbox(rows)

        #-- first line of the CityJSONL stream
        # cur.execute("select m.* from {%s}.cj_metadata m;", (self.schema,))
        cur.execute(
            sql.SQL("select m.* from {}.cj_metadata m")
                     .format(sql.Identifier(self.schema))
        )
        meta1 = cur.fetchone()
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
        sys.stdout.write(json.dumps(j, separators=(',', ':')) + '\n')
        logger.info(f"Exported (part of) database successfully")

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
                        print("GEOMETRY NOT SUPPORTED YET")
        return bboxmin




