from datetime import datetime, timedelta
from typing import TYPE_CHECKING
import os

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

        outdir = os.path.join(
            DEFAULT_CONFIG["advanced"].get("output_directory", "output"), "state"
        )
        os.makedirs(outdir, exist_ok=True)
        self.state_file_path = os.path.join(outdir, f"{self.task_name}.txt")

        self.reset()

    @staticmethod
    def _parse_time(time_str):
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return None

    def _get_blackout_times(
        self,
    ) -> tuple[datetime.time, datetime.time] | tuple[None, None]:
        blackout_period = self.task_config.get("blackout_period")

        if not blackout_period:
            return None, None

        start_time = self._parse_time(blackout_period.get("start"))
        end_time = self._parse_time(blackout_period.get("end"))

        if not start_time or not end_time or start_time == end_time:
            return None, None

        logger.debug(f"Blackout period for {self.task_name}: {start_time}-{end_time}")
        return start_time, end_time

    @staticmethod
    def is_blackout_time(
        start_t: datetime.time, end_t: datetime.time, dt_to_check: datetime
    ) -> bool:
        now = datetime.now()
        blackout_start = datetime.combine(now.date(), start_t)
        blackout_end = datetime.combine(now.date(), end_t)
        if blackout_end < blackout_start:
            blackout_end += timedelta(days=1)

        time_to_check = datetime.combine(now.date(), dt_to_check.time())

        return blackout_start <= time_to_check < blackout_end

    def _is_blackout_time(self, datetime_to_check: datetime) -> bool:
        if not all((self.blackout_start_time, self.blackout_end_time)):
            return False
        return self.is_blackout_time(
            self.blackout_start_time, self.blackout_end_time, datetime_to_check
        )

    @staticmethod
    def adjust_for_blackout(
        blackout_end_time: datetime.time, dt_to_adjust: datetime
    ) -> tuple[datetime, int, int]:
        # Calculate the end of the blackout period
        blackout_end_datetime = datetime.combine(dt_to_adjust.date(), blackout_end_time)
        if blackout_end_datetime < dt_to_adjust:
            blackout_end_datetime += timedelta(days=1)

        # Adjust the expected execution time to just after the blackout period
        adjusted_execution_dt = blackout_end_datetime

        # Calculate the adjustment duration
        adjustment_duration = adjusted_execution_dt - dt_to_adjust
        hours_added, remainder = divmod(adjustment_duration.seconds, 3600)
        minutes_added = remainder // 60

        return adjusted_execution_dt, hours_added, minutes_added

    def _adjust_for_blackout(self, expected_execution_dt: datetime) -> datetime:
        """Adjust the expected execution time to account for the blackout period."""
        logger.debug(
            f"Unadjusted {self.task_name} execution time: {expected_execution_dt}"
        )
        is_during_blackout = self._is_blackout_time(expected_execution_dt)
        logger.debug(
            f"Is {self.task_name} execution during blackout? {is_during_blackout}"
        )

        if is_during_blackout:
            (
                expected_execution_dt,
                hours_added,
                minutes_added,
            ) = self.adjust_for_blackout(self.blackout_end_time, expected_execution_dt)
            logger.debug(
                f"Added {hours_added} hours, {minutes_added} minutes; Adjusted {self.task_name} execution time: {expected_execution_dt}"
            )
        return expected_execution_dt

    def _get_prev_state(self) -> datetime | None:
        if os.path.exists(self.state_file_path):
            # logger.debug(f"Opening {self.task_name} state file: {self.state_file_path}")
            # read the previous time from the file
            with open(self.state_file_path, "r") as f:
                try:
                    prev_time = datetime.fromisoformat(f.read())
                    logger.debug(f"Previous {self.task_name} execution: {prev_time}")
                    return prev_time
                except ValueError:
                    logger.error(f"Invalid datetime in {self.state_file_path}")
        else:
            logger.debug(
                f"No {self.task_name} state file found: {self.state_file_path}"
            )
        return None

    def save_state(self) -> None:
        logger.debug(f"Saving {self.task_name} state file: {self.state_file_path}")
        # write the current time to the file
        with open(self.state_file_path, "w") as f:
            f.write(str(self.current_time))

    def set_next_time(self):
        """Compute the next expected execution time for the task."""
        prev_state = self._get_prev_state()
        ref_time = self.current_time if prev_state is None else prev_state

        self.next_time = self._adjust_for_blackout(
            ref_time + timedelta(hours=self.interval)
        )
        logger.info(f"Next {self.task_name} execution: {self.display_next_time()}")

    def seconds_until(self):
        return (self.next_time - self.current_time).total_seconds()

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
