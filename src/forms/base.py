from dataclasses import dataclass
from enum import Enum
from typing import Callable


class FieldType(Enum):
    TEXT = "text"
    RADIO = "radio"
    CHECKBOX = "checkbox"


@dataclass
class FormField:
    field_name: str
    field_type: FieldType
    required: bool = False
    default_value: str = ""
    tooltip: str = ""
    validation_func: Callable[[str], bool] | None = None
