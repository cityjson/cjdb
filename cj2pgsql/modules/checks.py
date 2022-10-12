
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
