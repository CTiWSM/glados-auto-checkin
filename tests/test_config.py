from __future__ import annotations

import json
from pathlib import Path

import pytest

from glados_auto_checkin.config import ConfigError, default_config, load_config, save_config


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = default_config(config_path)
    config.schedule.window_start = "08:00"
    config.schedule.window_end = "09:00"
    save_config(config, config_path)

    loaded = load_config(config_path)
    assert loaded.schedule.window_start == "08:00"
    assert loaded.schedule.window_end == "09:00"


def test_invalid_schedule_window_raises(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.json"
    payload = {
        "browser": {
            "login_url": "https://glados.rocks/login",
            "checkin_url": "https://glados.rocks/console/checkin",
            "channel": "chrome",
            "executable_path": "",
            "headless": True,
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "user_agent": "ua",
            "user_data_dir": str(tmp_path / "profile"),
            "artifacts_dir": str(tmp_path / "artifacts"),
            "manual_login_timeout_seconds": 900,
            "navigation_timeout_seconds": 90,
            "action_timeout_seconds": 20,
            "post_click_wait_seconds": 5,
            "retain_artifact_runs": 20,
            "seed_cookie_header": "",
            "viewport_width": 1440,
            "viewport_height": 1100
        },
        "mail": {
            "enabled": False,
            "to_addrs": []
        },
        "schedule": {
            "window_start": "10:00",
            "window_end": "09:00"
        },
        "runtime": {
            "retry_count": 5,
            "retry_delay_seconds": 20,
            "lock_stale_seconds": 60,
            "state_file": str(tmp_path / "state.json"),
            "log_file": str(tmp_path / "checkin.log")
        }
    }
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path)
