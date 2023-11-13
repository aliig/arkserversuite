import pytest
from datetime import datetime
from time_tracker import TimeTracker

# Test cases
tests = [
    # Test cases for blackout period from 22:00 to 06:00
    {
        "start_time": "22:00",
        "end_time": "06:00",
        "dt_to_check": datetime(2023, 1, 1, 23, 30),  # Inside blackout
        "in_blackout": True,
        "expected_adjustment": (6, 30),
    },
    {
        "start_time": "22:00",
        "end_time": "06:00",
        "dt_to_check": datetime(2023, 1, 1, 20, 0),  # Outside blackout
        "in_blackout": False,
        "expected_adjustment": (0, 0),
    },
    {
        "start_time": "22:00",
        "end_time": "06:00",
        "dt_to_check": datetime(2023, 1, 1, 22, 0),  # At start of blackout
        "in_blackout": True,
        "expected_adjustment": (8, 0),
    },
    {
        "start_time": "22:00",
        "end_time": "06:00",
        "dt_to_check": datetime(2023, 1, 1, 6, 0),  # At end of blackout
        "in_blackout": False,
        "expected_adjustment": (0, 0),
    },
    # Test cases for blackout period from 00:00 to 12:00 (midnight to noon)
    {
        "start_time": "00:00",
        "end_time": "12:00",
        "dt_to_check": datetime(2023, 1, 1, 1, 0),  # Inside blackout
        "in_blackout": True,
        "expected_adjustment": (11, 0),
    },
    {
        "start_time": "00:00",
        "end_time": "12:00",
        "dt_to_check": datetime(2023, 1, 1, 13, 0),  # Outside blackout
        "in_blackout": False,
        "expected_adjustment": (0, 0),
    },
    # Test cases for blackout period during the day (10:00 to 16:00)
    {
        "start_time": "10:00",
        "end_time": "16:00",
        "dt_to_check": datetime(2023, 1, 1, 12, 0),  # Inside blackout
        "in_blackout": True,
        "expected_adjustment": (4, 0),
    },
    {
        "start_time": "10:00",
        "end_time": "16:00",
        "dt_to_check": datetime(2023, 1, 1, 9, 0),  # Outside blackout
        "in_blackout": False,
        "expected_adjustment": (0, 0),
    },
    # Test cases for a blackout period that does not cross midnight (e.g., 15:00 to 18:00)
    {
        "start_time": "15:00",
        "end_time": "18:00",
        "dt_to_check": datetime(2023, 1, 1, 16, 30),  # Inside blackout
        "in_blackout": True,
        "expected_adjustment": (1, 30),
    },
    {
        "start_time": "15:00",
        "end_time": "18:00",
        "dt_to_check": datetime(2023, 1, 1, 19, 0),  # Outside blackout
        "in_blackout": False,
        "expected_adjustment": (0, 0),
    },
]


@pytest.mark.parametrize("test_case", tests)
def test_blackout_logic(test_case):
    start_time = TimeTracker._parse_time(test_case["start_time"])
    end_time = TimeTracker._parse_time(test_case["end_time"])

    assert (
        TimeTracker.is_blackout_time(start_time, end_time, test_case["dt_to_check"])
        == test_case["in_blackout"]
    )

    if test_case["in_blackout"]:
        adjusted_time, hours_added, minutes_added = TimeTracker.adjust_for_blackout(
            end_time, test_case["dt_to_check"]
        )
        assert hours_added == test_case["expected_adjustment"][0]
        assert minutes_added == test_case["expected_adjustment"][1]
