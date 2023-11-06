from datetime import datetime, timedelta
from config import DEFAULT_CONFIG


class TimeTracker:
    def __init__(self, task_config):
        self.task_config = task_config
        self.interval = task_config.get("interval", 4)
        self.blackout_start_time, self.blackout_end_time = self._get_blackout_times()
        self.current_time = datetime.now()
        self.time_until = None
        self.set_next_time()

    def _get_blackout_times(
        self,
    ) -> tuple[datetime.time, datetime.time] | tuple[None, None]:
        blackout_times = self.task_config.get("blackout_times")

        if not blackout_times or blackout_times in [("00:00", "00:00"), (), []]:
            return None, None

        try:
            start_time = datetime.strptime(blackout_times[0], "%H:%M").time()
            end_time = datetime.strptime(blackout_times[1], "%H:%M").time()

            if start_time == end_time:
                return None, None
            return start_time, end_time
        except (ValueError, IndexError):
            # Log the error condition here
            return None, None

    def _is_blackout_time(self, time_to_check=None) -> bool:
        """Check if a given time is within the blackout period."""
        time_to_check = time_to_check or self.current_time.time()

        if not all((self.blackout_start_time, self.blackout_end_time)):
            return False

        if self.blackout_start_time <= self.blackout_end_time:
            return self.blackout_start_time <= time_to_check <= self.blackout_end_time
        else:  # blackout period spans midnight
            return (
                time_to_check >= self.blackout_start_time
                or time_to_check <= self.blackout_end_time
            )

    def _adjust_for_blackout(self, expected_execution_dt) -> datetime:
        """Adjust the expected execution time to account for the blackout period."""
        if self.blackout_start_time <= self.blackout_end_time:
            # Blackout does not span midnight
            return datetime.combine(
                expected_execution_dt.date(), self.blackout_end_time
            ) + timedelta(hours=self.interval)
        else:
            # Blackout spans midnight
            if expected_execution_dt.time() >= self.blackout_start_time:
                next_day = expected_execution_dt.date() + timedelta(days=1)
                return datetime.combine(next_day, self.blackout_end_time) + timedelta(
                    hours=self.interval
                )
            else:
                return datetime.combine(
                    expected_execution_dt.date(), self.blackout_end_time
                ) + timedelta(hours=self.interval)

    def set_next_time(self):
        """Compute the next expected execution time for the task."""
        next_time = self.current_time + timedelta(hours=self.interval)

        while self._is_blackout_time(next_time.time()):
            next_time = self._adjust_for_blackout(next_time)

        self.next_time = next_time
        self.time_until = self.next_time - self.current_time

    def reset_next_time(self):
        self.current_time = datetime.now()
        self.set_next_time()

    def is_time_to_execute(self) -> bool:
        """Check if it's time to execute the task."""
        return self.current_time >= self.next_time

    def display(self, time: datetime) -> str:
        # if the time is on a future date, print out the date as well
        if time.date() > datetime.now().date():
            time_format: str = "%a %b %d %I:%M %p"
        else:
            time_format: str = "%I:%M %p"

        return f"{time.strftime(time_format)} {DEFAULT_CONFIG['server']['timezone']}"

    def display_next_time(self) -> str:
        return self.display(self.next_time)
