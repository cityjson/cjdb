class InvalidMetadataException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"InvalidMetadataException: {self.msg}"
        else:
            return """InvalidMetadataException: the CityJSON object
                      has invalid 'metadata'."""


class InvalidCityJSONObjectException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"InvalidCityJSONObjectException: {self.msg}"
        else:
            return """InvalidCityJSONObjectException: the first object of the
                      file should be a valid CityJSON object."""
