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
            return "The first object of the file should be a valid CityJSON object."


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
            return (
                "The file should be a "
                ".jsonl file. Use cjio to convert your city.json "
                "file to city.jsonl."
            )


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
            return (
                "No Coordinate Reference System specified "
                "for the dataset. Use -I/--srid flag to "
                "define the SRID."
            )


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
            return (
                "Inconsistent Coordinate Reference Systems detected. "
                "File has different CRS than the existing schema. "
                "Use the '--transform' flag to reproject everything "
                "to the existing schema's CRS or create a new schema."
            )


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


class NoSchemaSridException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return (
                "Schema does not have a previously defined SRID. "
                "Therefore no transformation is possible. "
                "If you want the file's SRID to be used as the "
                "schema SRID remove the --transform flag."
            )


class PathNotFoundException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return "The specified input path does not exist."


class GeometryTooLargeException(Exception):
    def __init__(self, *args):
        if args:
            self.msg = args[0]
        else:
            self.msg = None

    def __str__(self):
        if self.msg:
            return f"{self.msg}"
        else:
            return (
                "The geometry of a CityJSON object is too large to be stored "
                "in a single PostgreSQL jsonb column (limit ~256 MB). "
                "Simplify or split the geometry in the source file."
            )
