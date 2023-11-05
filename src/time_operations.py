from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class TimeTracker:
    def __init__(self, task_config, timestamp: float, timezone: str = "EST"):
        self.timezone = ZoneInfo(timezone)
        self.task_config = task_config
        self.interval = task_config.get("interval", 60)  # default interval 60 seconds
        self.blackout_start_time, self.blackout_end_time = self._get_blackout_times()
        self.current_time = 0
        self._reset_times(timestamp)

    def _reset_times(self):
        self.last_time = self.current_time
        self.current_time = datetime.fromtimestamp(timestamp, tz=self.timezone)
        self.next_time = self.get_next_time(self.current_time.timestamp())
        self.seconds_until_next = round(
            (self.next_time - self.current_time).total_seconds()
        )

    def _get_blackout_times(self):
        """Convert blackout times to datetime.time objects."""
        blackout_times = self.task_config.get("blackout_times")
        if not blackout_times or blackout_times == ("00:00", "00:00"):
            return None, None

        try:
            start_time = datetime.strptime(blackout_times[0], "%H:%M").time()
            end_time = datetime.strptime(blackout_times[1], "%H:%M").time()
            return start_time, end_time
        except ValueError:
            # Consider adding logging here for the error condition
            return None, None

    def _is_blackout_time(self, time=None) -> bool:
        """Check if a given time is within the blackout period."""
        time = time or self.current_time.time()
        if not all((self.blackout_start_time, self.blackout_end_time)):
            return False

        return (
            (self.blackout_start_time <= time <= self.blackout_end_time)
            if self.blackout_start_time <= self.blackout_end_time
            else (time >= self.blackout_start_time or time <= self.blackout_end_time)
        )

    def _adjust_for_blackout(self, expected_execution_dt) -> datetime:
        """Adjust the expected execution time to account for blackout period."""
        if (
            self.blackout_start_time > self.blackout_end_time
            and expected_execution_dt.time() >= self.blackout_start_time
        ):
            # If blackout wraps to the next day and expected time is during the blackout
            expected_execution_dt += timedelta(days=1)
            expected_execution_dt = datetime.combine(
                expected_execution_dt.date(), self.blackout_end_time
            )
        else:
            # If blackout ends on the same day
            expected_execution_dt = datetime.combine(
                expected_execution_dt.date(), self.blackout_end_time
            )

        expected_execution_dt += timedelta(seconds=self.interval)
        return expected_execution_dt

    def get_next_time(self, current_time: float) -> datetime:
        self.current_time = datetime.fromtimestamp(current_time, tz=self.timezone)
        """Compute the next expected execution time for the task."""
        next_time = self.current_time + timedelta(seconds=self.interval)

        # If the expected execution time is during the blackout period, adjust it
        while self._is_blackout_time(next_time.time()):
            next_time = self._adjust_for_blackout(next_time)

        return next_time

    def display(self, time: datetime, time_format: str = "%I:%M %p %Z") -> str:
        # Display the time in the specified format and timezone
        return time.strftime(time_format)

    def display_next_time(self) -> str:
        return self.display(self.next_time)
