import logging
import os
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from config import CONFIG
from mods import Mod, mods_needing_update
from rcon import broadcast, destroy_wild_dinos, get_active_players
from serverapi import serverapi_needs_update, use_serverapi
from time_tracker import TimeTracker
from update import does_server_need_update

if TYPE_CHECKING:
    from main import ArkServer


logger = logging.getLogger(__name__)


class Task:
    def __init__(self, server: "ArkServer", task_name: str):
        self.task_name = task_name
        self.server = server

        # config
        self.task_config = CONFIG["tasks"][self.task_name]
        self.description = self.task_config.get("description", "")

        # warning tracking
        self.warning_times = sorted(self.task_config.get("warnings", []), reverse=True)
        self.warned_times = set()

        # time
        self.time = TimeTracker(self)

    def _warn_before_task(self, extra: str = ""):
        """Send warnings if the time for a task is approaching."""
        if not self.warning_times:
            return

        minutes_until_task = round(self.time.seconds_until() / 60)
        # logger.debug(f"Minutes until {self.task_name}: {minutes_until_task}")

        # Iterate over the warning times that have not been warned yet
        for warning_minute in self.warning_times:
            if (
                minutes_until_task <= warning_minute
                and warning_minute not in self.warned_times
            ):
                self.warned_times.add(warning_minute)
                msg = f"Warning: {self.description} will occur in {warning_minute} {'minute' if warning_minute == 1 else 'minutes'} at approximately {self.time.display_next_time()}"
                if extra:
                    msg += f", ({extra})"
                msg += "."
                broadcast(msg)

    def _warn_then_wait(self, extra: str = ""):
        for cnt, warning_minute in enumerate(self.warning_times):
            msg = f"Warning: {self.description} will occur in {warning_minute} {'minute' if warning_minute == 1 else 'minutes'} at approximately {self.time.display(datetime.now() + timedelta(minutes=warning_minute))}"
            if extra:
                msg += f", ({extra})"
            msg += "."
            broadcast(msg)
            if cnt < len(self.warning_times) - 1:
                time.sleep((warning_minute - self.warning_times[cnt + 1]) * 60)
            else:
                time.sleep(warning_minute * 60)

    def _reset_sent_warnings(self) -> None:
        """Reset the warned times list after task execution."""
        self.warned_times = set()

    def _pre_run(self) -> None:
        self.time.current_time = datetime.now()
        self._warn_before_task()

    def _post_run(self) -> None:
        """Cleanup after task execution."""
        self._reset_sent_warnings()
        self.time.save_state()
        self.time.set_next_time()

    def _run_task(self):
        """Placeholder for the actual task to be executed. Should be overridden in subclasses."""
        raise NotImplementedError("Subclasses should implement this!")

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self._pre_run()
        if self.time.is_time_to_execute():
            res = self._run_task()
            self._post_run()
            return res
        return False


class SendAnnouncement(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        # general announcement
        # announce next expected dino wipe
        broadcast(self.description, discord_msg=False)
        # next_wipe = self.server.tasks["destroy_wild_dinos"].time.display_next_time()
        # broadcast(f"Next dino wipe: {next_wipe}", discord_msg=False)

        return False  # Always return False so that the other tasks run


class HandleEmptyServerRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)
        self.threshold = self.task_config.get("threshold", 0) * 60 * 60
        self.first_empty_server_time = None

    def _run_task(self) -> bool:
        if get_active_players() == 0:
            if self.first_empty_server_time is None:
                logger.info("Server is empty, starting stale check timer...")
                self.first_empty_server_time = self.time.current_time
            elif self.time.current_time - self.first_empty_server_time >= timedelta(
                hours=self.threshold
            ):
                logger.info("Server is stale, restarting...")
                self.server.restart("stale server", skip_warnings=True)
                return True
        else:
            if self.first_empty_server_time is not None:
                logger.info("Server is no longer empty, resetting stale check timer...")
                self.first_empty_server_time = None
        return False


class CheckForArkUpdatesAndRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        if does_server_need_update():
            self._warn_then_wait()
            self.server.restart("server update")
            return True
        return False

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self.time.current_time = datetime.now()
        if self.time.is_time_to_execute():
            res = self._run_task()
            self._post_run()
            return res
        return False


class CheckForModUpdatesAndRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        mods: list[Mod] = mods_needing_update()
        if len(mods) > 0:
            # make a string of all the mod names needing update
            mod_names = ", ".join([mod.name for mod in mods])
            self._warn_then_wait(extra=mod_names)
            self.server.restart(f"mod update ({mod_names})")
            return True
        return False

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self.time.current_time = datetime.now()
        if self.time.is_time_to_execute():
            res = self._run_task()
            self._post_run()
            return res
        return False


class CheckForServerAPIUpdateAndRestart(Task):
    def __init__(self, server: "ArkServer", task_name: str):
        super().__init__(server, task_name)

    def _run_task(self) -> bool:
        if use_serverapi() and (res := serverapi_needs_update()):
            # make a string of all the mod names needing update
            self._warn_then_wait(f"upgrade to version {res['name']}")
            self.server.restart(f"ServerAPI update")
            return True
        return False

    def execute(self) -> bool:
        """Execute the task if it's time."""
        self.time.current_time = datetime.now()
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
