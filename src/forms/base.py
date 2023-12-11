import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class FieldType(Enum):
    TEXT = "text"
    RADIO = "radio"
    CHECKBOX = "checkbox"


def is_integer(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_comma_delimited_integers(value):
    try:
        integers = [int(x.strip()) for x in value.split(",")]
        return all(isinstance(x, int) for x in integers)
    except ValueError:
        return False


def is_comma_delimited_numbers(value):
    try:
        numbers = [float(x.strip()) for x in value.split(",")]
        return all(isinstance(x, float) for x in numbers)
    except ValueError:
        return False


def is_24_hour_format(time_str):
    pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"
    return re.match(pattern, time_str) is not None


@dataclass
class FormField:
    field_name: str
    field_type: FieldType
    required: bool = False
    default_value: str = ""
    tooltip: str = ""
    validation_func: Callable[[str], bool] | None = None
