version_help = "Get the current version"

host_help = "PostgreSQL database host"

port_help = "PostgreSQL database port"

user_help = "PostgreSQL database user name"

password_help = "PostgreSQL database user password"

database_help = "PostgreSQL database name"

schema_help = "PostgreSQL database schema name"

append_help = (
    "Run in append mode (as opposed to default create mode). "
    "This assumes the database structure exists already and "
    "new data is to be appended."
)

srid_help = (
    "Target coordinate system SRID. "
    "All 3D and 2D geometries will be reprojected."
)

index_help = (
    "CityObject attribute to be indexed using a btree index. "
    "Can be specified multiple times, for each attribute once."
)

partial_index_help = (
    "CityObject attribute to be indexed using a btree partial index. "
    "Can be specified multiple times, for each attribute once. "
    "This index indexes on a condition 'where {{ATTR_NAME}} is not null'. "
    "This means that it saves space and improves query performance when the "
    "attribute is not present for all imported CityObjects."
)

ignore_file_help = (
    "Ignore repeated file names warning when importing. "
    "By default, the importer will send out warnings if a specific "
    "file has already been imported."
)

overwrite_help = (
    "If the file has been imported before, delete all "
    "associated objects with this filename and reimport "
    "all objects in the file."
)


transform_help = ("Convert input geometries to the SRID of the existing schema")

output_help = (
    "Name of the output file. Default name: 'cj_export.city.json' "
)

query_help = (
    "SQL query with the ids of the objects to be exported."
)
