import pytest
from unittest.mock import Mock, patch
from time_tracker import TimeTracker
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Add src directory to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))


# Mock the Task class
class MockTask:
    def __init__(self, name, config):
        self.task_name = name
        self.task_config = config


# Fixture for TimeTracker instance
@pytest.fixture
def time_tracker():
    task = MockTask(
        "Test Task",
        {"interval": 4, "blackout_period": {"start": "22:00", "end": "06:00"}},
    )
    return TimeTracker(task)


# Test for blackout period parsing
def test_get_blackout_times(time_tracker):
    start, end = time_tracker._get_blackout_times()
    assert start is not None and end is not None


# Test for checking blackout time
@patch("your_module.datetime")
def test_is_blackout_time(mock_datetime, time_tracker):
    mock_datetime.now.return_value = datetime(2023, 1, 1, 23, 0)
    time_tracker.reset()
    assert time_tracker._is_blackout_time(datetime(2023, 1, 1, 23, 30)) is True


# Test for adjusting execution time for blackout
@patch("your_module.datetime")
def test_adjust_for_blackout(mock_datetime, time_tracker):
    mock_datetime.now.return_value = datetime(2023, 1, 1, 5, 0)
    time_tracker.reset()
    adjusted_time = time_tracker._adjust_for_blackout(datetime(2023, 1, 1, 23, 0))
    assert adjusted_time > datetime(2023, 1, 1, 23, 0)
