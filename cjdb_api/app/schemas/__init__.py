from cjdb_api.app.ma import ma
from marshmallow import fields, post_load
from model.sqlalchemy_models import CjObjectModel

class CjObjectSchema(ma.Schema):
    # here define fields for serialization
    object_id = fields.String()
    type = fields.String()
    attributes = fields.Field()
    geometry = fields.Field() 
    # bbox = fields.String()

    @post_load
    def make(self, data, **kwargs):
        return CjObjectModel(**data)

    class Meta:
        model = CjObjectModel
        load_instance = True
