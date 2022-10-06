from flask_restful import Resource
from model.sqlalchemy_models import CjObjectModel
from cjdb_api.app.schemas import CityJsonSchema
from cjdb_api.app.db import session, engine
cityjson_schema = CityJsonSchema()
cityjson_list_schema = CityJsonSchema(many=True)

##working
class all(Resource):
    @classmethod
    def get(cls):
        all = session.query(CjObjectModel).all()

        if not all:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(all)

class QueryByAttribute(Resource):
    @classmethod
    def get(cls, attrib: str, value: str):
        cj_object = session.query(CjObjectModel).filter(getattr(CjObjectModel, attrib) == str(value))

        if not cj_object:
            return {"message": "Object not found"}, 404

        return cityjson_list_schema.dump(cj_object)

class GetInfo(Resource):
    @classmethod
    def get(cls, attrib: str, object_id: str):
        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()
        attribute = getattr(cj_object, attrib)

        if not attribute:
            return {"message": "Object not found"}, 404

        return attribute


##in progress
class CalculateFootprint(Resource):
    @classmethod
    def get(cls, object_id: str):
        cj_object = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id).first()

        if not cj_object:
            return {"message": "Object not found"}, 404

        with engine.connect() as connection:
            area = connection.execute(cj_object.bbox.ST_Area())

            if not area:
                return {"message": "Object not found"}, 404
            print(area) # outputs: "<sqlalchemy.engine.cursor.LegacyCursorResult object at 0x000002322DFAA2B0>" But want to have the area

        return ("area")


class AddAttribute(Resource):
    @classmethod
    def get(cls):
        objects = session.query(CjObjectModel).all()
        for object in objects:
            listObj = object.attributes
            listObj["test_attribute"] = "test_value"
            object.attributes = listObj
            session.commit() # This is supposed to save the changes to the DB, but it doesn't

        return cityjson_list_schema.dump(objects)


#todo
class FilterAttributes(Resource):
    pass

class CalculateVolume (Resource):
    pass

class SomethingWithGeometry(Resource):
    pass

class Sequel(Resource):
    pass
