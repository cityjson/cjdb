class InvalidMetadataException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return """The CityJSON object has invalid 'metadata'."""


class InvalidCityJSONObjectException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return ("The first object of the file should be "
                    "a valid CityJSON object.")


class InvalidFileException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return ("The file should be a "
                    ".jsonl file. Use cjio to convert your city.json "
                    "file to city.jsonl.")
        

class MissingCRSException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return ("No Coordinate Reference System specified "
                    "for the dataset. Use -I/--srid flag to "
                    "define the SRID.")


class InconsistentCRSException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return ("Inconsistent Coordinate Reference Systems detected. "
                    "Use the '-I/--srid' flag to reproject everything "
                    "to a single specified CRS or modify source data or "
                    "create a new schema.")


class InvalidLodException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return """The Geomerty object has invalid value for 'lod'."""
