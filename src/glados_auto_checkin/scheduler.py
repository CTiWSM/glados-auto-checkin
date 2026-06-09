from __future__ import annotations

import datetime as dt
import os
import platform
import random
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .config import APP_NAME, AppConfig, ConfigError, DISPLAY_NAME, default_paths
from .state import read_state, write_state


SYSTEMD_UNIT = APP_NAME
WINDOWS_TASK_NAME = "GLaDOS Auto Check-in"
LAUNCHD_LABEL = "com.glados-auto-checkin.daily"


def parse_clock_label(value: str) -> tuple[int, int]:
    hour_str, minute_str = value.split(":")
    return int(hour_str), int(minute_str)


def _window_bounds_for_day(config: AppConfig, day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    start_hour, start_minute = parse_clock_label(config.schedule.window_start)
    end_hour, end_minute = parse_clock_label(config.schedule.window_end)
    start_at = dt.datetime.combine(day, dt.time(hour=start_hour, minute=start_minute))
    end_at = dt.datetime.combine(day, dt.time(hour=end_hour, minute=end_minute))
    if end_at <= start_at:
        raise ConfigError("schedule.window_end must be later than schedule.window_start")
    return start_at, end_at


def choose_daily_target(config: AppConfig) -> dt.datetime:
    state_path = Path(config.runtime.state_file)
    state = read_state(state_path)
    today = dt.date.today()
    today_str = today.isoformat()
    planned = state.get("scheduled_target_at")
    if state.get("scheduled_target_date") == today_str and isinstance(planned, str):
        try:
            return dt.datetime.fromisoformat(planned)
        except ValueError:
            pass

    start_at, end_at = _window_bounds_for_day(config, today)
    span_seconds = int((end_at - start_at).total_seconds())
    target = start_at + dt.timedelta(seconds=random.randint(0, span_seconds))
    state["scheduled_target_date"] = today_str
    state["scheduled_target_at"] = target.isoformat(timespec="seconds")
    write_state(state_path, state)
    return target


def wait_until_random_window(config: AppConfig) -> dt.datetime:
    target = choose_daily_target(config)
    now = dt.datetime.now()
    if now < target:
        delay = (target - now).total_seconds()
        time.sleep(delay)
    return target


def module_command(config_path: Path) -> list[str]:
    return [sys.executable, "-m", "glados_auto_checkin", "scheduled-run", "--config", str(config_path)]


def render_systemd_service(config_path: Path) -> str:
    command = " ".join(f'"{part}"' if " " in part else part for part in module_command(config_path))
    return textwrap.dedent(
        f"""\
        [Unit]
        Description={DISPLAY_NAME}
        Wants=network-online.target
        After=network-online.target
        ConditionPathExists={config_path}

        [Service]
        Type=oneshot
        Environment=PYTHONUNBUFFERED=1
        ExecStart={command}

        [Install]
        WantedBy=default.target
        """
    )


def render_systemd_timer(config: AppConfig) -> str:
    hour, minute = parse_clock_label(config.schedule.window_start)
    return textwrap.dedent(
        f"""\
        [Unit]
        Description=Run {DISPLAY_NAME} once per day

        [Timer]
        OnCalendar=*-*-* {hour:02d}:{minute:02d}:00
        AccuracySec=1min
        Persistent=false
        Unit={SYSTEMD_UNIT}.service

        [Install]
        WantedBy=timers.target
        """
    )


def render_launchd_plist(config_path: Path) -> str:
    hour, minute = parse_clock_label(load_config_for_schedule_only(config_path).schedule.window_start)
    args = module_command(config_path)
    arg_xml = "\n".join(f"      <string>{escape(part)}</string>" for part in args)
    log_path = escape(str(load_config_for_schedule_only(config_path).runtime.log_file))
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
          <dict>
            <key>Label</key>
            <string>{LAUNCHD_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
        {arg_xml}
            </array>
            <key>StartCalendarInterval</key>
            <dict>
              <key>Hour</key>
              <integer>{hour}</integer>
              <key>Minute</key>
              <integer>{minute}</integer>
            </dict>
            <key>StandardOutPath</key>
            <string>{log_path}</string>
            <key>StandardErrorPath</key>
            <string>{log_path}</string>
            <key>RunAtLoad</key>
            <false/>
          </dict>
        </plist>
        """
    )


def build_windows_wrapper(config_path: Path) -> str:
    command = subprocess.list2cmdline(module_command(config_path))
    return f"@echo off\r\n{command}\r\n"


def windows_task_command(config_path: Path, wrapper_path: Path) -> list[str]:
    hour, minute = parse_clock_label(load_config_for_schedule_only(config_path).schedule.window_start)
    return [
        "schtasks",
        "/Create",
        "/F",
        "/SC",
        "DAILY",
        "/TN",
        WINDOWS_TASK_NAME,
        "/ST",
        f"{hour:02d}:{minute:02d}",
        "/TR",
        str(wrapper_path),
    ]


def load_config_for_schedule_only(config_path: Path) -> AppConfig:
    from .config import load_config

    return load_config(config_path)


def install_schedule(config: AppConfig) -> str:
    system = platform.system()
    config_path = config.config_path

    if system == "Linux":
        unit_dir = Path.home() / ".config" / "systemd" / "user"
        unit_dir.mkdir(parents=True, exist_ok=True)
        service_path = unit_dir / f"{SYSTEMD_UNIT}.service"
        timer_path = unit_dir / f"{SYSTEMD_UNIT}.timer"
        service_path.write_text(render_systemd_service(config_path), encoding="utf-8")
        timer_path.write_text(render_systemd_timer(config), encoding="utf-8")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", timer_path.name], check=True)
        return f"Installed systemd timer at {timer_path}"

    if system == "Darwin":
        launch_agents = Path.home() / "Library" / "LaunchAgents"
        launch_agents.mkdir(parents=True, exist_ok=True)
        plist_path = launch_agents / f"{LAUNCHD_LABEL}.plist"
        plist_path.write_text(render_launchd_plist(config_path), encoding="utf-8")
        subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
        subprocess.run(["launchctl", "load", "-w", str(plist_path)], check=True)
        return f"Installed launchd job at {plist_path}"

    if system == "Windows":
        wrapper_path = default_paths()["windows_wrapper"]
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        wrapper_path.write_text(build_windows_wrapper(config_path), encoding="utf-8", newline="\r\n")
        subprocess.run(windows_task_command(config_path, wrapper_path), check=True)
        return f"Installed Windows Task Scheduler task '{WINDOWS_TASK_NAME}'"

    raise ConfigError(f"Scheduling is not supported on this platform: {system}")


def uninstall_schedule(config: AppConfig) -> str:
    system = platform.system()

    if system == "Linux":
        unit_dir = Path.home() / ".config" / "systemd" / "user"
        service_path = unit_dir / f"{SYSTEMD_UNIT}.service"
        timer_path = unit_dir / f"{SYSTEMD_UNIT}.timer"
        subprocess.run(["systemctl", "--user", "disable", "--now", timer_path.name], check=False)
        service_path.unlink(missing_ok=True)
        timer_path.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        return "Removed the Linux systemd timer."

    if system == "Darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
        plist_path.unlink(missing_ok=True)
        return "Removed the macOS launchd job."

    if system == "Windows":
        subprocess.run(["schtasks", "/Delete", "/F", "/TN", WINDOWS_TASK_NAME], check=False)
        default_paths()["windows_wrapper"].unlink(missing_ok=True)
        return "Removed the Windows scheduled task."

    raise ConfigError(f"Scheduling is not supported on this platform: {system}")
