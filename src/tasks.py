from shell_operations import is_server_running
from update import does_server_need_update
from server_operations import send_message, get_active_players, destroy_wild_dinos
import logging
from config import DEFAULT_CONFIG
from datetime import datetime, timedelta
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from main import ArkServer

from time_operations import TimeTracker

logger = logging.getLogger(__name__)


class Task:
    def __init__(self, server: "ArkServer", task_name: str):
        self.task_name = task_name
        self.server = server

        # config
        self.task_config = DEFAULT_CONFIG["tasks"][self.task_name]
        self.description = self.task_config.get("description", "")

        # warning tracking
        self.warning_times = sorted(self.task_config.get("warnings", []), reverse=True)
        self.warned_times = set()

        # time
        self.time = TimeTracker(self.task_config)

    def _warn_before_task(self):
        """Send warnings if the time for a task is approaching."""
        if not self.warning_times:
            return

        minutes_until_task = (
            self.time.seconds_until_next / 60
        )  # Convert seconds to minutes

        # Iterate over the warning times that have not been warned yet
        for warning_minute in self.warning_times:
            if (
                minutes_until_task <= warning_minute
                and warning_minute not in self.warned_times
            ):
                self.warned_times.add(warning_minute)
                send_message(
                    f"Warning: {self.description} will occur in {warning_minute} minutes at approximately {self.time.display_next_time()}."
                )

    def _warn_then_wait(self):
        for cnt, warning_minute in enumerate(self.warning_times):
            send_message(
                f"Warning: {self.description} will occur in {warning_minute} minutes at approximately {self.time.display(datetime.now(self.timezone) + timedelta(minutes=warning_minute))}."
            )
            if cnt < len(self.warning_times) - 1:
                time.sleep((warning_minute - self.warning_times[cnt + 1]) * 60)
            else:
                time.sleep(warning_minute * 60)

    def _reset_sent_warnings(self) -> None:
        """Reset the warned times list after task execution."""
        self.warned_times = set()

    def _pre_run(self) -> None:
        self.time.current_time = datetime.now(self.timezone)
        self._warn_before_task()

    def _post_run(self) -> None:
        """Cleanup after task execution."""
        self._reset_sent_warnings()
        self.time.set_next_time()

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self._pre_run()
        if self.time.is_time_to_execute():
            res = self._run_task()
            self._post_run()
            return res
        return False

    def _run_task(self):
        """Placeholder for the actual task to be executed. Should be overridden in subclasses."""
        raise NotImplementedError("Subclasses should implement this!")


class SendAnnouncement(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        # general announcement
        send_message(self.description, discord_msg=False)
        # announce next expected dino wipe
        next_wipe = self.server.tasks["destroy_wild_dinos"].time.display_next_time()
        send_message(f"Next dino wipe: {next_wipe}", discord_msg=False)

        return False  # Always return False so that the other tasks run


class HandleEmptyServerRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)
        self.threshold = self.task_config.get("threshold", 0) * 60 * 60

    def _run_task(self) -> bool:
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
        return False


class CheckForUpdatesAndRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        self._update_last_check()
        if does_server_need_update():
            self._warn_then_wait()
            self.server.restart("server update")
            return True
        return False

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self.time.current_time = datetime.now(self.timezone)
        if self.time.is_time_to_execute():
            res = self._run_task()
            self._post_run()
            return res
        return False


class PerformRoutineRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        self.server.restart("routine restart")
        return True


class DestroyWildDinos(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        destroy_wild_dinos()
        return False
