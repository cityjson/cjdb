import json

import requests

from cjdb.logger import logger


class ExtensionHandler:
    def __init__(self, extensions):
        self.full_definitions = {}
        self.extra_root_properties = []
        self.extra_attributes = {}
        self.extra_city_objects = []

        if extensions:
            self.get_extensions(extensions)

    def get_extensions(self, extensions):
        for ext_name, content in extensions.items():
            url = content.get("url")
            if url:
                try:
                    resp = requests.get(url, timeout=10)
                except Exception as e:
                    resp = None

                if resp and resp.status_code == 200:
                    try:
                        ext_definition = json.loads(resp.text)
                        self.full_definitions[ext_name] = ext_definition
                    except ValueError as e:
                        logger.error(
                            "Extension url: %s did not provide a correct json"
                            " schema", url
                        )
                        # raise
                        # throw this exception or ignore it?
                        return

                    for prop_name in ext_definition["extraRootProperties"]:
                        self.extra_root_properties.append(prop_name)

                    for obj_type, extra_attributes in ext_definition[
                        "extraAttributes"
                    ].items():
                        if obj_type not in self.extra_attributes:
                            self.extra_attributes[obj_type] = []
                        for attr_name in extra_attributes:
                            self.extra_attributes[obj_type].append(attr_name)

                    for obj_type in ext_definition["extraCityObjects"]:
                        self.extra_city_objects.append(obj_type)
                else:
                    msg = f"Extension url: {url} did not return a correct response"
                    # raise Exception(msg)
                    return
