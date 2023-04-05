from pyproj import datadir, CRS
from pyproj.transformer import TransformerGroup


def check_root_properties(found_extra_properties, defined_extra_properties):
    if found_extra_properties:
        base_msg = "Warning: An extended CityJSON root property: '{}' was not defined by any of the extensions."
        for prop_name in found_extra_properties:
            if not prop_name in defined_extra_properties:
                print(base_msg.format(prop_name))


def check_object_type(checked_type, allowed_types, extended_types):
    check_result = True
    message = ""
    all_types = allowed_types + extended_types
    if checked_type not in all_types:
        check_result = False
        message = f"Warning: CityJSON object type '{checked_type}' not allowed by main schema nor extensions."

    return check_result, message


# check if reprojection possible
# prints warnings, but doesn't stop the import
def check_reprojection(source_srid, target_srid):
    source_proj = CRS.from_epsg(source_srid)
    target_proj = CRS.from_epsg(target_srid)

    if len(target_proj.axis_info) < 3:
        print(f"Warning: The specified target SRID({target_srid}) " + \
                "lacks information about the Z-axis. The Z vertex values will remain unchanged.")

    group = TransformerGroup(source_proj, target_proj)
    # this prints a warning if there are some grids missing for the reprojection
    # more about this https://pyproj4.github.io/pyproj/stable/transformation_grids.html

    # attempt to download missing grids
    if not group.best_available:
        print("Attempting to download additional grids required for CRS transformation.")
        print(f"This can also be done manually, and the grid should be put in this folder:\n\t{datadir.get_data_dir()}")
        
        try:
            group.download_grids(datadir.get_data_dir())
        except:
            print("Failed to download the missing grids.")
        else:
            print("Download successful.")