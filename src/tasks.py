from shell_operations import is_server_running, does_server_need_update
from server_operations import send_message, get_active_players, destroy_wild_dinos
import logging
from config import DEFAULT_CONFIG
import datetime
from utils import time_as_string
from collections import deque

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ArkServer

logger = logging.getLogger(__name__)


import datetime


class Task:
    def __init__(self, server: ArkServer, current_time: float):
        self.server = server
        self.task_config = DEFAULT_CONFIG["tasks"][self.task_name]

        self.current_time = current_time
        self.current_time_obj = datetime.datetime.fromtimestamp(current_time).time()

        self.interval = self.task_config.get("interval", 0) * 3600
        self.warnings = self.task_config.get("warnings", [])
        self.message = self.task_config.get("message", "")
        self.blackout_start_time, self.blackout_end_time = self._get_blackout_times()
        self.warning_times = deque(self.warnings)

        self.last_check = server.last.get(self.task_name, current_time)
        self.expected_execution_time = self._compute_next_execution_time()
        self.time_remaining = self.expected_execution_time - self.current_time_obj

    def _get_blackout_times(self) -> tuple[datetime.time | None, datetime.time | None]:
        """Convert blackout times to datetime.time objects."""
        blackout_times = self.task_config.get("blackout_times")
        if not blackout_times or blackout_times == ("00:00", "00:00"):
            return None, None

        try:
            start_time = datetime.time(*map(int, blackout_times[0].split(":")))
            end_time = datetime.time(*map(int, blackout_times[1].split(":")))
            # No special handling here; simply return the times.
            return start_time, end_time
        except ValueError:
            # Consider adding logging here for the error condition
            return None, None

    def _is_blackout_time(self, time=None) -> bool:
        """Check if a given time is within the blackout period."""
        time = time or self.current_time_obj
        if not all((self.blackout_start_time, self.blackout_end_time)):
            return False

        return (
            (self.blackout_start_time <= time <= self.blackout_end_time)
            if self.blackout_start_time <= self.blackout_end_time
            else (time >= self.blackout_start_time or time <= self.blackout_end_time)
        )

    def _compute_next_execution_time(self) -> datetime._Time:
        """Compute the next expected execution time for the task."""
        next_execution = datetime.datetime.fromtimestamp(
            self.current_time + self._time_until_next_execution()
        )

        # If the expected execution time is during the blackout period, adjust it
        while self._is_blackout_time(next_execution.time()):
            next_execution = self._adjust_for_blackout(next_execution)

        return next_execution.time()

    def _adjust_for_blackout(
        self, expected_execution_dt: datetime.datetime
    ) -> datetime.datetime:
        """Adjust the expected execution time to account for blackout period."""
        # If blackout wraps to the next day and expected time is during the blackout
        if (
            self.blackout_start_time > self.blackout_end_time
            and expected_execution_dt.time() >= self.blackout_start_time
        ):
            expected_execution_dt += datetime.timedelta(days=1)

        expected_execution_dt = datetime.datetime.combine(
            expected_execution_dt.date(), self.blackout_end_time
        )
        expected_execution_dt += datetime.timedelta(seconds=self.interval)
        return expected_execution_dt

    def send_warnings(self):
        """Send warnings if the time for a task is approaching."""
        if not self.warning_times:
            return

        time_until_execution = self.expected_execution_time - self.current_time

        while (
            self.warning_times
            and time_until_execution.total_seconds() <= self.warning_times[0] * 60
        ):
            warning_time = self.warning_times.popleft()
            print(f"Warning: Task will execute in {warning_time} minutes.")

    def _get_current_datetime(self) -> datetime.datetime:
        """Return current date and time as a datetime object."""
        return datetime.datetime.combine(datetime.date.today(), self.current_time_obj)

    def _get_datetime_with_expected_time(self) -> datetime.datetime:
        """Return expected execution date and time as a datetime object."""
        expected_time = self.expected_execution_time
        expected_execution_dt = datetime.datetime.combine(
            datetime.date.today(), expected_time
        )
        if expected_execution_dt < self._get_current_datetime():
            expected_execution_dt += datetime.timedelta(days=1)
        return expected_execution_dt

    def _should_warn(self, time_remaining: int, warning_time: int) -> bool:
        """Determine if a warning should be sent."""
        warning_seconds = warning_time * 60
        return (
            time_remaining <= warning_seconds and warning_time not in self.warned_times
        )

    def _send_warning_message(
        self, expected_execution_dt: datetime.datetime, warning_time: int
    ):
        """Send a warning message about the upcoming task execution."""
        send_message(
            f"Warning: Task '{self.task_name}' will execute in {warning_time} minutes at approximately {time_as_string(expected_execution_dt.time())}",
            discord_msg=False,
        )
        self.warned_times.add(warning_time)

    def _is_time_to_execute(self) -> bool:
        """Check if it's time to execute the task."""
        return (
            self.current_time_obj >= self.expected_execution_time
            and not self._is_blackout_time()
        )

    def _update_last_check(self):
        """Update the last check time after task execution."""
        self.server.last[self.task_name] = self.current_time

    def execute(self) -> bool:
        """Execute the task if it's time."""
        if self._is_time_to_execute():
            res = self.run_task()
            self._reset_sent_warnings()
            self._update_last_check()
            return res
        return False

    def run_task(self):
        """Placeholder for the actual task to be executed. Should be overridden in subclasses."""
        raise NotImplementedError("Subclasses should implement this!")

    def _reset_sent_warnings(self) -> None:
        """Reset the warned times list after task execution."""
        self.warned_times = set()


class CheckServerRunningAndRestart(Task):
    def run_task(self) -> bool:
        if not is_server_running():
            logger.info("Server is not running. Attempting to restart...")
            self.server.start()
            return True
        return False

    def execute(self):
        return self.run_task()


class SendAnnouncement(Task):
    task_name = "announcement"

    def __init__(self, server: ArkServer, current_time):
        super().__init__(server, current_time)

    def run_task(self) -> bool:
        send_message(self.message, discord_msg=False)
        self._update_last_check()
        return False  # Always return False so that the other tasks run


class HandleEmptyServerRestart(Task):
    task_name = "stale"

    def __init__(self, server: ArkServer, current_time):
        super().__init__(server, current_time)
        self.threshold = self.task_config.get("threshold", 0) * 60 * 60

    def run_task(self) -> bool:
        if get_active_players() == 0:
            if self.server.first_empty_server_time is None:
                logger.info("Server is empty, starting stale check timer...")
                self.server.first_empty_server_time = self.current_time
            elif (
                self.current_time - self.server.first_empty_server_time
                >= self.threshold
            ):
                logger.info("Server is stale, restarting...")
                self.server.restart("stale server", skip_warnings=True)
                self._update_last_check()
                return True
        else:
            if self.server.first_empty_server_time is not None:
                logger.info("Server is no longer empty, resetting stale check timer...")
                self.server.first_empty_server_time = None
        self._update_last_check()
        return False


class CheckForUpdatesAndRestart(Task):
    task_name = "update"

    def __init__(self, server: ArkServer, current_time):
        super().__init__(server, current_time)

    def run_task(self) -> bool:
        self._update_last_check()
        if does_server_need_update():
            self.server.restart("server update")
            return True
        return False


class PerformRoutineRestart(Task):
    task_name = "restart"

    def __init__(self, server: ArkServer, current_time):
        super().__init__(server, current_time)

    def run_task(self) -> bool:
        self.server.restart("routine restart")
        self._update_last_check()
        return True


class DestroyWildDinos(Task):
    task_name = "destroy_wild_dinos"

    def __init__(self, server: ArkServer, current_time):
        super().__init__(server, current_time)

    def run_task(self) -> bool:
        destroy_wild_dinos()
        self._update_last_check()
        return False
