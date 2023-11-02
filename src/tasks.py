from shell_operations import is_server_running, does_server_need_update
from server_operations import send_message, get_active_players, destroy_wild_dinos
import logging
from config import DEFAULT_CONFIG
import datetime
from utils import time_as_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ArkServer

logger = logging.getLogger(__name__)


class Task:
    def __init__(self, server: ArkServer, current_time):
        self.task_config = DEFAULT_CONFIG["tasks"][self.task_name]

        self.server = server

        # Convert the timestamp to a datetime object and extract the time part
        self.current_time_obj = datetime.datetime.fromtimestamp(current_time).time()
        self.current_time = current_time

        self.interval = (
            self.task_config.get("interval", 0) * 60 * 60
        )  # Convert to seconds
        self.warnings = self.task_config.get("warnings", [])
        if self.warnings:
            self.warnings = sorted(list(map(int, self.warnings)), reverse=True)
        self.message = self.task_config.get("message", "")

        # Convert blackout times to datetime.time during initialization
        self.blackout_start_time, self.blackout_end_time = self._get_blackout_times()

        # Use the dictionary to get the last check time
        self.last_check = self.server.last.get(self.task_name, current_time)

        self._reset_sent_warnings()

        self.expected_execution_time = self._compute_next_execution_time()

    def _get_blackout_times(self) -> tuple[datetime.time | None, datetime.time | None]:
        blackout_times = self.task_config.get("blackout_times")

        # If blackout_times is None or default, return None for both start and end
        if not blackout_times or blackout_times == ("00:00", "00:00"):
            return None, None

        try:
            h_start, m_start = map(int, blackout_times[0].split(":"))
            h_end, m_end = map(int, blackout_times[1].split(":"))
            return datetime.time(h_start, m_start), datetime.time(h_end, m_end)
        except ValueError:
            # Handle incorrect format by returning None values or raising a specific error
            return None, None

    def _is_blackout_time(self, time=None) -> bool:
        # Immediate return if no blackout times are set
        if self.blackout_start_time is None or self.blackout_end_time is None:
            return False

        if time is None:
            time = self.current_time_obj

        if (
            self.blackout_start_time > self.blackout_end_time
        ):  # The time wraps to the next day
            return time >= self.blackout_start_time or time <= self.blackout_end_time
        else:
            return self.blackout_start_time <= time <= self.blackout_end_time

    def _compute_next_execution_time(self) -> datetime.time:
        """
        Compute the expected next execution time for the task based on the last execution and interval.
        """
        time_passed_since_last = self.current_time - self.last_check
        remaining_seconds = self.interval - time_passed_since_last
        expected_execution_dt = datetime.datetime.fromtimestamp(
            self.current_time + remaining_seconds
        )

        while self._is_blackout_time(expected_execution_dt.time()):
            if (
                self.blackout_start_time > self.blackout_end_time
                and expected_execution_dt.time() >= self.blackout_start_time
            ):
                # If blackout wraps to next day and expected time is after start of blackout
                # Add a day to the expected execution date
                expected_execution_dt += datetime.timedelta(days=1)

            # Set the expected execution time to the end of the blackout period
            expected_execution_dt = datetime.datetime.combine(
                expected_execution_dt.date(), self.blackout_end_time
            )

            # Add the interval time since the task needs to run after the blackout period
            expected_execution_dt += datetime.timedelta(seconds=self.interval)

        return expected_execution_dt.time()

    def _send_warnings(self) -> None:
        """Send warnings if the time for a task is approaching."""
        if not self.warnings:
            return

        # Calculate the difference between expected execution time and current time
        expected_execution_dt = datetime.datetime.combine(
            datetime.date.today(), self.expected_execution_time
        )
        current_dt = datetime.datetime.combine(
            datetime.date.today(), self.current_time_obj
        )

        # Handle the scenario where expected_execution_time is on the next day
        if expected_execution_dt < current_dt:
            expected_execution_dt += datetime.timedelta(days=1)

        time_remaining = (expected_execution_dt - current_dt).seconds

        for warning_time in self.warnings:
            warning_seconds = warning_time * 60
            if (
                time_remaining <= warning_seconds
                and warning_time not in self.warned_times
            ):
                send_message(
                    f"Warning: Task '{self.task_name}' will execute in {warning_time} minutes at approximately {time_as_string(expected_execution_dt.time())}",
                    discord_msg=False,
                )
                self.warned_times.append(warning_time)
                break

    def _reset_sent_warnings(self) -> None:
        """Reset the warned times list after task execution."""
        self.warned_times = []

    def _is_time_to_execute(self) -> bool:
        return (
            self.current_time_obj >= self.expected_execution_time
            and not self._is_blackout_time()
        )

    def _update_last_check(self) -> None:
        self.server.last[self.task_name] = self.current_time

    def execute(self) -> bool:
        """Send warnings if needed and reset them if the task runs."""
        self._send_warnings()
        if self._is_time_to_execute():
            res = self.run_task()  # Execute the actual task defined in subclasses
            self._reset_sent_warnings()  # Reset the warned times after executing the task
            return res
        return False

    def run_task(self):
        """Placeholder for the actual task to be executed. Should be overridden in subclasses."""
        pass


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
