from datetime import datetime, timedelta
from config import DEFAULT_CONFIG


class TimeTracker:
    def __init__(self, task_config):
        self.task_config = task_config
        self.interval = task_config.get("interval", 4)
        self.current_time = datetime.now()
        self.blackout_start, self.blackout_end = self._get_blackout_period()
        self.time_until = None
        self.set_next_time()

    def _get_blackout_period(
        self,
    ) -> tuple[datetime.time, datetime.time] | tuple[None, None]:
        blackout_times = self.task_config.get("blackout_times")

        if not blackout_times or blackout_times in [("00:00", "00:00"), (), []]:
            return None, None

        try:
            # Get the current date
            current_date = self.current_time.date()

            # Parse the blackout start and end times
            start_time = datetime.strptime(blackout_times[0], "%H:%M").time()
            end_time = datetime.strptime(blackout_times[1], "%H:%M").time()

            # Combine current date with blackout start and end times
            start = datetime.combine(current_date, start_time)
            end = datetime.combine(current_date, end_time)

            # spans midnight
            if start > end:
                end = end + timedelta(days=1)
            elif start == end:
                return None, None
            print(f"Blackout period: {start} - {end}")
            return start, end
        except (ValueError, IndexError):
            # Log the error condition here
            return None, None

    def _is_blackout_time(self, time_to_check=None) -> bool:
        """Check if a given time is within the blackout period."""
        time_to_check = time_to_check or self.current_time

        if not all((self.blackout_start, self.blackout_end)):
            return False

        if self.blackout_start < self.current_time < self.blackout_end:
            return True

    def set_next_time(self):
        """Compute the next expected execution time for the task."""
        next_time = self.current_time + timedelta(hours=self.interval)

        while self._is_blackout_time(next_time):
            next_time = next_time + timedelta(hours=self.interval)

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
