

def is_modifier_present(target_modifier_name, app_inst):
    return any(
            [modifier["name"] == target_modifier_name for modifier in app_inst.modifiers]
            )
