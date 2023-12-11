from .base import (
    FieldType,
    FormField,
    is_24_hour_format,
    is_comma_delimited_numbers,
    is_number,
)

TASK_SETTINGS = [
    FormField(
        field_name="Check interval (hours)",
        field_type=FieldType.TEXT,
        required=True,
        default_value="1",
        tooltip="How often this task will occur in hours",
        validation_func=is_number,
    ),
    FormField(
        field_name="Blackout period start",
        field_type=FieldType.TEXT,
        required=False,
        tooltip="The starting time of the blackout period in 24 hour format (e.g. 22:00)",
        validation_func=is_24_hour_format,
    ),
    FormField(
        field_name="Blackout period end",
        field_type=FieldType.TEXT,
        required=False,
        tooltip="The ending time of the blackout period in 24 hour format (e.g. 06:00)",
        validation_func=is_24_hour_format,
    ),
    FormField(
        field_name="Warning intervals (minutes)",
        field_type=FieldType.TEXT,
        required=False,
        tooltip="A comma delimited list of minutes before the task executes that a warning will be sent (e.g. 30,15,5)",
        validation_func=is_comma_delimited_numbers,
    ),
]
