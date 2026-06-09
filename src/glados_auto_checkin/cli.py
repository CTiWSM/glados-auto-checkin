from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .browser import validate_browser_runtime
from .config import APP_NAME, ConfigError, default_config, load_config, save_config, validate_config
from .logging_utils import setup_logging
from .runner import remove_browser_profile, run_bootstrap_login, run_checkin, send_test_email
from .scheduler import install_schedule, uninstall_schedule, wait_until_random_window
from .wizard import run_init_wizard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cross-platform GLaDOS auto check-in.")
    parser.add_argument(
        "--config",
        default="",
        help="Path to config JSON. Defaults to the standard per-user config path.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Interactive setup wizard for beginners.")
    subparsers.add_parser("validate", help="Validate config and browser runtime.")
    subparsers.add_parser("bootstrap-login", help="Open a browser and let you log in manually once.")
    subparsers.add_parser("status", help="Open the page without clicking the sign-in button.")
    subparsers.add_parser("checkin", help="Run the check-in immediately.")
    subparsers.add_parser("scheduled-run", help="Internal command used by the scheduled task.")
    subparsers.add_parser("install-schedule", help="Install the daily scheduled task for this OS.")
    subparsers.add_parser("uninstall-schedule", help="Remove the scheduled task for this OS.")
    subparsers.add_parser("test-email", help="Send a test alert email.")
    subparsers.add_parser("clear-browser-state", help="Delete the saved browser profile.")
    return parser


def _config_path_from_args(raw: str) -> Path:
    base = default_config().config_path
    if not raw:
        return base
    return Path(raw).expanduser().resolve()


def _load_config_for_runtime(config_path: Path):
    config = load_config(config_path)
    validate_config(config)
    setup_logging(Path(config.runtime.log_file))
    return config


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config_path = _config_path_from_args(args.config)

    if args.command == "init":
        config = run_init_wizard(config_path)
        print("")
        print(f"Config saved to: {config.config_path}")
        print("Next steps:")
        print("  1. glados-auto-checkin validate")
        print("  2. glados-auto-checkin bootstrap-login    (recommended for beginners)")
        print("     or keep using Cookie mode if you pasted a Cookie")
        print("  3. glados-auto-checkin install-schedule")
        return 0

    try:
        config = _load_config_for_runtime(config_path)
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 2

    try:
        if args.command == "validate":
            validate_browser_runtime(config)
            logging.info("Configuration and browser runtime are valid: %s", config.config_path)
            return 0

        if args.command == "bootstrap-login":
            return run_bootstrap_login(config)

        if args.command == "status":
            return run_checkin(config, status_only=True)

        if args.command == "checkin":
            return run_checkin(config)

        if args.command == "scheduled-run":
            target = wait_until_random_window(config)
            logging.info("Scheduled run target for today: %s", target.isoformat(timespec="seconds"))
            return run_checkin(config)

        if args.command == "install-schedule":
            message = install_schedule(config)
            print(message)
            return 0

        if args.command == "uninstall-schedule":
            message = uninstall_schedule(config)
            print(message)
            return 0

        if args.command == "test-email":
            return send_test_email(config)

        if args.command == "clear-browser-state":
            return remove_browser_profile(config)
    except ConfigError as exc:
        logging.error("Configuration error: %s", exc)
        return 2

    parser.print_help()
    return 2
