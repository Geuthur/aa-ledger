# Standard Library
from decimal import Decimal


def get_footer_text_class(value: int | float | Decimal, mining=False) -> str:
    """Get the text class for a value.

    A positive value will return "text-success", a negative value will return "text-danger", and a zero value will return an empty string.
    If the value is related to mining, a positive value will return "text-primary" instead of "text-success".

    Args:
        value (int | float | Decimal): The value to get the text class for.
        mining (bool, optional): Whether the value is related to mining. Defaults to False.
    Returns:
        str: The text class for the value.
    """
    if value > 0:
        if mining:
            return "text-info"
        return "text-success"
    if value < 0:
        return "text-danger"
    return ""
