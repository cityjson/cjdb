filepath_help = "Source CityJSONL file or a directory with CityJSONL files. " \
    + "STDIN if not specified. " \
    + "If specifying a directory, all the *.jsonl files inside of it will be imported."

host_help = "PostgreSQL database host"

port_help = "PostgreSQL database port"

user_help = "PostgreSQL database user name"

password_help = "PostgreSQL database user password"

database_help = "PostgreSQL database name"

schema_help = "Target database schema"

srid_help = "Target coordinate system SRID. " +\
    "All 3D and 2D geometries will be reprojected."

index_help = "CityObject attribute to be indexed using a btree index. " +\
    "Can be specified multiple times, for each attribute once."

append_help = "Run in append mode (as opposed to default create mode). " +\
            "This assumes the database structure exists already and new data is to be appended."

overwrite_help = "Overwrite the data that is currently in the database schema. " + \
                "Warning: this causes the loss of what was imported before to the database schema."

ignore_file_help = "Ignore repeated file names warning when importing. " +\
    "By default, the importer will send out warnings if a specific file has already been imported."

skip_existing = "Check if the object with given ID exists before inserting, and skip it if it does. " +\
    "By default, the importer does not check existence for performance reasons, " +\
    "which means that importing the same object twice will result in an error."

update_existing = "Check if the object with given ID exists before inserting, and update it if it does. " +\
    "The old object will be updated with the new object's properties."
