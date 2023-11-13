from datetime import datetime, timedelta


def _is_blackout_time(
    blackout_start: datetime, blackout_end: datetime, time_to_check: datetime
) -> bool:
    return blackout_start < time_to_check <= blackout_end


now = datetime.now()

start_time_str = "07:00"
end_time_str = "02:00"
time_to_check_str = "09:01"

blackout_start_time = datetime.strptime(start_time_str, "%H:%M").time()
blackout_end_time = datetime.strptime(end_time_str, "%H:%M").time()
time_to_check_time = datetime.strptime(time_to_check_str, "%H:%M").time()

blackout_start = datetime.combine(now.date(), blackout_start_time)
blackout_end = datetime.combine(now.date(), blackout_end_time)
time_to_check = datetime.combine(now.date(), time_to_check_time)
if blackout_end < blackout_start:
    blackout_end += timedelta(days=1)

print(f"Blackout start time: {blackout_start}")
print(f"Blackout end time: {blackout_end}")
print(f"Time to check: {time_to_check}")

x = _is_blackout_time(blackout_start, blackout_end, time_to_check)
print(f"Is blackout? {x}")
