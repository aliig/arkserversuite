from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from config import DEFAULT_CONFIG
from logger import get_logger

if TYPE_CHECKING:
    from tasks import Task

logger = get_logger(__name__)


class TimeTracker:
    def __init__(self, task: "Task"):
        self.task_config = task.task_config
        self.task_name = task.task_name
        self.interval = task.task_config.get("interval", 4)
        self.blackout_start_time, self.blackout_end_time = self._get_blackout_times()
        self.reset()

    def _get_blackout_times(
        self,
    ) -> tuple[datetime.time, datetime.time] | tuple[None, None]:
        blackout_period = self.task_config.get("blackout_period")

        if not blackout_period:
            return None, None

        start_time_str = blackout_period.get("start")
        end_time_str = blackout_period.get("end")

        if not start_time_str or not end_time_str:
            return None, None

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            if start_time == end_time:
                return None, None
            return start_time, end_time
        except ValueError:
            return None, None

    def _is_blackout_time(self, time_to_check: datetime) -> bool:
        """Check if a given datetime is within the blackout period."""
        if not all((self.blackout_start_time, self.blackout_end_time)):
            return False

        # Normalize dates by setting them to the same date
        blackout_start = datetime.combine(
            time_to_check.date(), self.blackout_start_time
        )
        blackout_end = datetime.combine(time_to_check.date(), self.blackout_end_time)

        if self.blackout_start_time <= self.blackout_end_time:
            # Blackout does not span midnight
            return blackout_start <= time_to_check <= blackout_end
        else:
            # Blackout period spans midnight
            if time_to_check < blackout_start:
                # Check if time is before today's blackout start. If so, compare with yesterday's blackout end
                yesterday_blackout_end = blackout_end - timedelta(days=1)
                return time_to_check <= yesterday_blackout_end
            else:
                # Check if time is after today's blackout start. If so, compare with today's blackout end
                blackout_end += timedelta(days=1)  # Add a day to the end time
                return time_to_check <= blackout_end

    def _adjust_for_blackout(self, expected_execution_dt: datetime) -> datetime:
        """Adjust the expected execution time to account for the blackout period."""
        original_time = expected_execution_dt  # Store original time for logging
        logger.debug(f"Original {self.task_name} execution time: {original_time}")
        is_during_blackout = self._is_blackout_time(expected_execution_dt)
        logger.debug(
            f"Is {self.task_name} execution during blackout? {is_during_blackout}"
        )
        if is_during_blackout:
            blackout_start = datetime.combine(
                expected_execution_dt.date(), self.blackout_start_time
            )
            blackout_end = datetime.combine(
                expected_execution_dt.date(), self.blackout_end_time
            )

            if self.blackout_end_time < self.blackout_start_time:
                # Blackout spans midnight
                if expected_execution_dt < blackout_start:
                    # Current time is before blackout starts, adjust to today's blackout end
                    adjusted_time = blackout_end
                else:
                    # Current time is after blackout starts, adjust to tomorrow's blackout end
                    adjusted_time = blackout_end + timedelta(days=1)
            else:
                # Blackout does not span midnight
                adjusted_time = blackout_end

            time_adjustment = adjusted_time - expected_execution_dt
            logger.debug(
                f"Time adjusted by {time_adjustment} for blackout during {self.task_name} execution."
            )
            return adjusted_time
        else:
            return expected_execution_dt

    def set_next_time(self):
        """Compute the next expected execution time for the task."""
        self.next_time = self._adjust_for_blackout(
            self.current_time + timedelta(hours=self.interval)
        )
        logger.info(f"Next {self.task_name} execution: {self.display_next_time()}")
        self.time_until = self.next_time - self.current_time

    def reset(self):
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
