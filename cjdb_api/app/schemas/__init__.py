from cjdb_api.app.ma import ma
from marshmallow import fields, post_load
from cjdb_api.app.models import CityJsonModel

class CityJsonSchema(ma.Schema):
    # here define fields for serialization
    id = fields.String()

    @post_load
    def make(self, data, **kwargs):
        return CityJsonModel(**data)

    class Meta:
        model = CityJsonModel
        load_instance = True
