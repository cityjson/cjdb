from flask import request, jsonify
from flask_restful import Resource
from sqlalchemy import update, delete

from cjdb_api.app.db import session, engine
from cjdb_api.app.resources import cityjson_schema, cityjson_list_schema, in_database, parse_json
from model.sqlalchemy_models import CjObjectModel, FamilyModel, ImportMetaModel


def delete_children(has_children):
    for child in has_children:
        has_child = session.query(FamilyModel).join(CjObjectModel,
                                                    CjObjectModel.object_id == FamilyModel.parent_id).filter(
            FamilyModel.parent_id == child.child_id).all()
        while has_child:
            delete_children(has_child)
        u = delete(FamilyModel)
        u = u.where(FamilyModel.parent_id == child.parent_id)
        c = delete(CjObjectModel)
        c = c.where(CjObjectModel.object_id == child.child_id)
        engine.execute(u)
        engine.execute(c)


class DelAttrib(Resource):
    @classmethod
    def get(cls):
        # required parameters: object_id, attribute
        object_id, attrib = request.args.get('object_id', None), request.args.get('attribute', None)

        if object_id is None:
            return {"message": "Invalid parameter. Please include the right object_id."}, 404
        elif object_id == "all":
            obs = session.query(CjObjectModel).all()
        else:
            in_database(object_id)
            obs = session.query(CjObjectModel).filter(CjObjectModel.object_id == object_id)

        for object in obs:
            if isinstance(object.attributes, dict):
                listObj = object.attributes
                del listObj[attrib]
                u = update(CjObjectModel)
                u = u.values({"attributes": listObj})
                u = u.where(CjObjectModel.object_id == object.object_id)
                engine.execute(u)

        if object_id == "all":
            show = session.query(CjObjectModel).limit(50)
            output = parse_json(cityjson_list_schema.dump(show))
        else:
            output = parse_json(cityjson_list_schema.dump(obs))

        return jsonify(output)


class DelObject(Resource):
    @classmethod
    def get(cls):
        # required parameters: object_id
        object_id = request.args.get('object_id', None)

        if object_id is None:
            return {"message": "Invalid parameter. Please include the right object_id."}, 404
        else:
            in_database(object_id)

        has_children = session.query(FamilyModel).join(CjObjectModel, CjObjectModel.object_id == FamilyModel.parent_id).filter(FamilyModel.parent_id == object_id).all()
        if has_children:
            delete_children(has_children)

        is_child = session.query(FamilyModel).join(CjObjectModel, CjObjectModel.object_id == FamilyModel.child_id).filter(FamilyModel.child_id == object_id).all()
        if is_child:
            for child in is_child:
                u = delete(FamilyModel)
                u = u.where(FamilyModel.child_id == child.child_id)
                engine.execute(u)

        u = delete(CjObjectModel)
        u = u.where(CjObjectModel.object_id == object_id)
        engine.execute(u)

        return ("Object " + object_id + "is deleted.")
