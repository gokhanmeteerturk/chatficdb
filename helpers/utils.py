
def str_to_bool(text):
    """
    Convert a string representation of a boolean value to its corresponding boolean value.

    Parameters:
        text (str): The string representation of the boolean value.

    Returns:
        bool: The corresponding boolean value.

    Raises:
        ValueError: If the string representation is not a valid boolean value.

    """
    if text.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif text.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ValueError