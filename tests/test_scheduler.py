from __future__ import annotations

from pathlib import Path

from glados_auto_checkin.config import default_config, save_config
from glados_auto_checkin.scheduler import (
    build_windows_wrapper,
    render_launchd_plist,
    render_systemd_service,
    render_systemd_timer,
)


def test_systemd_files_include_expected_command(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = default_config(config_path)
    save_config(config, config_path)

    service = render_systemd_service(config_path)
    timer = render_systemd_timer(config)

    assert "glados_auto_checkin" in service
    assert "OnCalendar=*-*-* 12:00:00" in timer


def test_launchd_plist_contains_config_path(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = default_config(config_path)
    save_config(config, config_path)

    plist = render_launchd_plist(config_path)
    assert str(config_path) in plist
    assert "<key>Hour</key>" in plist


def test_windows_wrapper_uses_module_invocation(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config = default_config(config_path)
    save_config(config, config_path)

    wrapper = build_windows_wrapper(config_path)
    assert "glados_auto_checkin" in wrapper
    assert str(config_path) in wrapper
