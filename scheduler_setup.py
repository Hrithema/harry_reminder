"""
Registers or removes Windows Task Scheduler jobs that launch the reminder
app at specific times. Run this on Windows (uses schtasks.exe).

Usage:
    python scheduler_setup.py add --name WaterReminder --time 10:00 --message "Hey! Drink some water."
    python scheduler_setup.py add --name StretchReminder --time 14:30 --message "Stand up and stretch."
    python scheduler_setup.py remove --name WaterReminder
    python scheduler_setup.py list

Once packaged with PyInstaller, point EXE_PATH at HarryReminder.exe instead
of invoking python + main.py directly.
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

BASE_DIR = Path(__file__).resolve().parent

# After packaging, set this to the built exe, e.g. BASE_DIR / "dist" / "HarryReminder.exe"
EXE_PATH = BASE_DIR / "dist" / "HarryReminder.exe"
PYTHON_EXE = sys.executable
MAIN_SCRIPT = BASE_DIR / "main.py"

TASK_PREFIX = "HarryReminder_"


def build_command(message: str) -> str:
    if EXE_PATH:
        return f'"{EXE_PATH}" --message "{message}"'
    return f'"{PYTHON_EXE}" "{MAIN_SCRIPT}" --message "{message}"'


def build_command_parts(message: str) -> tuple[str, str]:
    """Same as build_command but split into (executable, arguments) —
    the XML task format needs these as separate fields."""
    if EXE_PATH:
        return str(EXE_PATH), f'--message "{message}"'
    return str(PYTHON_EXE), f'"{MAIN_SCRIPT}" --message "{message}"'


def add_task(name: str, time_str: str, message: str, daily: bool = True):
    task_name = TASK_PREFIX + name
    command = build_command(message)
    schedule = "DAILY" if daily else "ONCE"

    cmd = [
        "schtasks", "/Create",
        "/TN", task_name,
        "/TR", command,
        "/SC", schedule,
        "/ST", time_str,
        "/F",  # overwrite if it already exists
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Scheduled '{task_name}' for {time_str} ({schedule.lower()}).")
    else:
        print(f"Failed to create task: {result.stderr.strip()}")


RECURRING_TASK_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT{interval}M</Interval>
      </Repetition>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user_id}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT1M</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{command}</Command>
      <Arguments>{arguments}</Arguments>
      <WorkingDirectory>{working_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def add_recurring_from_login(name: str, message: str, interval_minutes: int = 75):
    """
    Fires as soon as you log into Windows, then repeats every
    `interval_minutes` indefinitely.

    schtasks.exe's simple flags (/SC ONLOGON /RI /DU) don't support
    repetition on a logon trigger — that combination is only exposed
    through the Task Scheduler XML format, so this builds and imports
    an XML task definition instead of using /TR + /SC directly.

    The Repetition block intentionally has no <Duration>: Task Scheduler
    treats a missing Duration as "repeat forever" (a fixed value like P4Y
    is rejected — the Duration field only accepts day/hour/minute/second
    units, not years), which is exactly the behavior we want here.

    Uses ONLOGON rather than ONSTART: ONSTART fires before any desktop
    exists, so a GUI overlay often fails to render. ONLOGON fires once
    you're actually logged in and have a desktop to draw onto.
    """
    task_name = TASK_PREFIX + name
    command, arguments = build_command_parts(message)

    user_id = f'{os.environ.get("USERDOMAIN", "")}\\{os.environ.get("USERNAME", "")}'

    xml_content = RECURRING_TASK_XML.format(
        interval=interval_minutes,
        user_id=escape(user_id),
        command=escape(command),
        arguments=escape(arguments),
        working_dir=escape(str(BASE_DIR)),
    )

    # Task Scheduler expects the XML file itself as UTF-16, matching the
    # encoding declared in the XML header above.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False, encoding="utf-16"
    ) as f:
        f.write(xml_content)
        xml_path = f.name

    try:
        cmd = ["schtasks", "/Create", "/TN", task_name, "/XML", xml_path, "/F"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"'{task_name}' will run at login, then every {interval_minutes} minutes.")
        else:
            print(f"Failed to create task: {result.stderr.strip()}")
    finally:
        os.unlink(xml_path)


def remove_task(name: str):
    task_name = TASK_PREFIX + name
    cmd = ["schtasks", "/Delete", "/TN", task_name, "/F"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"Removed '{task_name}'.")
    else:
        print(f"Failed to remove task: {result.stderr.strip()}")


def list_tasks():
    cmd = ["schtasks", "/Query", "/FO", "LIST"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    printing = False
    for line in lines:
        if line.startswith("TaskName:") and TASK_PREFIX in line:
            printing = True
        if printing:
            print(line)
        if line.strip() == "" and printing:
            printing = False


def main():
    parser = argparse.ArgumentParser(description="Manage Harry Reminder scheduled tasks.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_add = sub.add_parser("add", help="Create/update a scheduled reminder.")
    p_add.add_argument("--name", required=True, help="Unique short name for this reminder.")
    p_add.add_argument("--time", required=True, help="Time in HH:MM (24h), e.g. 14:30")
    p_add.add_argument("--message", required=True, help="Reminder text.")
    p_add.add_argument("--once", action="store_true", help="Run once instead of daily.")

    p_recurring = sub.add_parser(
        "add-recurring",
        help="Run at login, then repeat every N minutes indefinitely.",
    )
    p_recurring.add_argument("--name", required=True, help="Unique short name for this reminder.")
    p_recurring.add_argument("--message", required=True, help="Reminder text.")
    p_recurring.add_argument("--interval", type=int, default=75, help="Minutes between runs (default: 75).")

    p_remove = sub.add_parser("remove", help="Delete a scheduled reminder.")
    p_remove.add_argument("--name", required=True)

    sub.add_parser("list", help="List all HarryReminder scheduled tasks.")

    args = parser.parse_args()

    if args.action == "add":
        add_task(args.name, args.time, args.message, daily=not args.once)
    elif args.action == "add-recurring":
        add_recurring_from_login(args.name, args.message, interval_minutes=args.interval)
    elif args.action == "remove":
        remove_task(args.name)
    elif args.action == "list":
        list_tasks()


if __name__ == "__main__":
    main()