from __future__ import annotations

import datetime as dt
import logging
import socket
from pathlib import Path

from .browser import BrowserFlowError, bootstrap_login, clear_browser_state, retrying_browser_flow
from .config import AppConfig, ConfigError
from .mailer import build_failure_body, build_failure_subject, send_email
from .state import LockError, acquire_lock, read_state, write_state


def success_summary(result_type: str, message: str, left_days: str, account_email: str) -> str:
    verb = "success" if result_type == "success" else "already_done"
    return (
        f"result={verb} account={account_email or 'unknown'} "
        f"left_days={left_days} message={message}"
    )


def run_checkin(
    config: AppConfig,
    *,
    force: bool = False,
    status_only: bool = False,
    headed: bool = False,
) -> int:
    lock = None
    try:
        lock = acquire_lock(Path(config.runtime.state_file).with_suffix(".lock"), config.runtime.lock_stale_seconds)
        state = read_state(Path(config.runtime.state_file))
        today = dt.date.today().isoformat()

        if not force and state.get("last_success_date") == today and not status_only:
            logging.info("Skipping because today is already marked successful in local state.")
            return 0

        result = retrying_browser_flow(config, status_only=status_only, headed=headed)
        status_before = result.get("status_before") or {}
        status_after = result.get("status_after") or status_before
        account_email = status_after.get("account_email") or status_before.get("account_email") or ""
        left_days = status_after.get("left_days") or status_before.get("left_days") or "unknown"

        logging.info(
            "Browser status ready: account=%s left_days=%s url=%s",
            account_email or "unknown",
            left_days,
            status_after.get("url") or status_before.get("url") or "unknown",
        )

        if status_only:
            logging.info(
                "Status-only result: account=%s left_days=%s",
                account_email or "unknown",
                left_days,
            )
            return 0

        result_type = result.get("result_type") or "failure"
        message = result.get("message") or "Unknown browser automation result"
        run_dir = result.get("run_dir")

        if result_type in {"success", "duplicate"}:
            write_state(
                Path(config.runtime.state_file),
                {
                    "last_account_email": account_email,
                    "last_left_days": left_days,
                    "last_message": message,
                    "last_result": result_type,
                    "last_success_date": today,
                    "last_run_dir": run_dir or "",
                    "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
                },
            )
            logging.info(success_summary(result_type, message, left_days, account_email))
            return 0

        reason = f"Browser check-in returned an unexpected result: {message}"
        if not status_only:
            send_email(
                config,
                subject=build_failure_subject(config, account_email),
                body=build_failure_body(
                    config=config,
                    reason=reason,
                    account_email=account_email,
                    status_before=status_before,
                    checkin_result=result.get("checkin_result"),
                    status_after=status_after,
                    run_dir=run_dir,
                ),
            )
        logging.error(reason)
        return 1

    except LockError as exc:
        logging.exception("Lock acquisition failed: %s", exc)
        return 1
    except BrowserFlowError as exc:
        context = exc.context or {}
        status_before = context.get("status_before") or {}
        status_after = context.get("status_after") or {}
        account_email = status_after.get("account_email") or status_before.get("account_email") or ""
        logging.exception("Browser automation failed: %s", exc)
        if not status_only:
            try:
                send_email(
                    config,
                    subject=build_failure_subject(config, account_email),
                    body=build_failure_body(
                        config=config,
                        reason=str(exc),
                        account_email=account_email,
                        status_before=status_before,
                        checkin_result=context.get("checkin_result"),
                        status_after=status_after,
                        run_dir=context.get("run_dir"),
                    ),
                )
            except Exception:
                logging.exception("Failed to send browser-failure email.")
        return 1
    except Exception as exc:
        logging.exception("Unhandled error during browser automation check-in: %s", exc)
        try:
            if not status_only:
                body = "\n".join(
                    [
                        "GLaDOS automatic browser check-in crashed before finishing.",
                        "",
                        f"Time: {dt.datetime.now().isoformat(timespec='seconds')}",
                        f"Host: {socket.gethostname()}",
                        f"Config: {config.config_path}",
                        "",
                        f"Exception: {exc!r}",
                    ]
                )
                send_email(
                    config,
                    subject=f"{config.mail.subject_prefix} Crash on {socket.gethostname()}",
                    body=body,
                )
        except Exception:
            logging.exception("Failed to send crash email.")
        return 1
    finally:
        if lock is not None:
            lock.release()


def run_bootstrap_login(config: AppConfig) -> int:
    try:
        result = bootstrap_login(config)
    except Exception as exc:
        logging.exception("Bootstrap login failed: %s", exc)
        return 1
    logging.info(result["message"])
    return 0


def send_test_email(config: AppConfig) -> int:
    if not config.mail.enabled:
        raise ConfigError("Email is disabled in the config file.")
    subject = f"{config.mail.subject_prefix} Test from {socket.gethostname()}"
    body = "\n".join(
        [
            "This is a test email from GLaDOS Auto Check-in.",
            "",
            f"Time: {dt.datetime.now().isoformat(timespec='seconds')}",
            f"Host: {socket.gethostname()}",
            f"Config: {config.config_path}",
        ]
    )
    send_email(config, subject=subject, body=body)
    logging.info("Test email sent successfully.")
    return 0


def remove_browser_profile(config: AppConfig) -> int:
    clear_browser_state(config)
    logging.info("Deleted the dedicated browser state directory: %s", config.browser.user_data_dir)
    return 0
