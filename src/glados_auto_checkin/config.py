from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from platformdirs import user_config_path, user_data_path


APP_NAME = "glados-auto-checkin"
DISPLAY_NAME = "GLaDOS Auto Check-in"
DEFAULT_LOGIN_URL = "https://glados.rocks/login"
DEFAULT_CHECKIN_URL = "https://glados.rocks/console/checkin"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


class ConfigError(Exception):
    """Raised when the local config file is invalid."""


@dataclass
class BrowserConfig:
    login_url: str = DEFAULT_LOGIN_URL
    checkin_url: str = DEFAULT_CHECKIN_URL
    channel: str = "chrome"
    executable_path: str = ""
    headless: bool = True
    locale: str = "zh-CN"
    timezone_id: str = "Asia/Shanghai"
    user_agent: str = DEFAULT_USER_AGENT
    user_data_dir: str = ""
    artifacts_dir: str = ""
    manual_login_timeout_seconds: int = 900
    navigation_timeout_seconds: int = 90
    action_timeout_seconds: int = 20
    post_click_wait_seconds: int = 5
    retain_artifact_runs: int = 20
    seed_cookie_header: str = ""
    viewport_width: int = 1440
    viewport_height: int = 1100


@dataclass
class MailConfig:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_addr: str = ""
    to_addrs: list[str] | None = None
    subject_prefix: str = "[GLaDOS Check-in]"
    use_starttls: bool = True
    use_ssl: bool = False


@dataclass
class ScheduleConfig:
    window_start: str = "12:00"
    window_end: str = "16:00"


@dataclass
class RuntimeConfig:
    retry_count: int = 5
    retry_delay_seconds: int = 20
    lock_stale_seconds: int = 8 * 60 * 60
    state_file: str = ""
    log_file: str = ""


@dataclass
class AppConfig:
    browser: BrowserConfig
    mail: MailConfig
    schedule: ScheduleConfig
    runtime: RuntimeConfig
    config_path: Path


def default_paths() -> Dict[str, Path]:
    config_dir = Path(user_config_path(APP_NAME))
    data_dir = Path(user_data_path(APP_NAME))
    return {
        "config_dir": config_dir,
        "config_path": config_dir / "config.json",
        "data_dir": data_dir,
        "browser_profile": data_dir / "browser-profile",
        "artifacts_dir": data_dir / "artifacts",
        "state_file": data_dir / "state.json",
        "log_file": data_dir / "logs" / "checkin.log",
        "windows_wrapper": data_dir / "run_scheduled_checkin.cmd",
    }


def default_config(config_path: Path | None = None) -> AppConfig:
    paths = default_paths()
    if config_path is None:
        config_path = paths["config_path"]
    return AppConfig(
        browser=BrowserConfig(
            user_data_dir=str(paths["browser_profile"]),
            artifacts_dir=str(paths["artifacts_dir"]),
        ),
        mail=MailConfig(to_addrs=[]),
        schedule=ScheduleConfig(),
        runtime=RuntimeConfig(
            state_file=str(paths["state_file"]),
            log_file=str(paths["log_file"]),
        ),
        config_path=config_path,
    )


def _expand_path(value: str) -> str:
    return str(Path(os.path.expandvars(os.path.expanduser(value))).resolve())


def _require_non_empty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing required config value: {field_name}")
    return value.strip()


def _looks_like_placeholder(value: str) -> bool:
    normalized = value.strip().upper()
    return any(token in normalized for token in ("PASTE_", "CHANGEME", "YOUR_", "<", ">"))


def _normalize_mail_recipients(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ConfigError("mail.to_addrs must be a string or a list of strings")


def _validate_time_label(value: str, field_name: str) -> str:
    value = _require_non_empty(value, field_name)
    parts = value.split(":")
    if len(parts) != 2:
        raise ConfigError(f"{field_name} must be in HH:MM format")
    hour, minute = parts
    if not hour.isdigit() or not minute.isdigit():
        raise ConfigError(f"{field_name} must be in HH:MM format")
    hour_value = int(hour)
    minute_value = int(minute)
    if hour_value not in range(24) or minute_value not in range(60):
        raise ConfigError(f"{field_name} must be in HH:MM format")
    return f"{hour_value:02d}:{minute_value:02d}"


def load_config(path: str | Path | None = None) -> AppConfig:
    paths = default_paths()
    config_path = Path(path).expanduser().resolve() if path else paths["config_path"]
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file is not valid JSON: {config_path}: {exc}") from exc

    base = default_config(config_path)
    browser_raw = raw.get("browser") or {}
    mail_raw = raw.get("mail") or {}
    schedule_raw = raw.get("schedule") or {}
    runtime_raw = raw.get("runtime") or {}

    browser = BrowserConfig(
        login_url=_require_non_empty(browser_raw.get("login_url", base.browser.login_url), "browser.login_url"),
        checkin_url=_require_non_empty(
            browser_raw.get("checkin_url", base.browser.checkin_url), "browser.checkin_url"
        ),
        channel=str(browser_raw.get("channel", base.browser.channel)).strip(),
        executable_path=str(browser_raw.get("executable_path", "")).strip(),
        headless=bool(browser_raw.get("headless", base.browser.headless)),
        locale=str(browser_raw.get("locale", base.browser.locale)).strip(),
        timezone_id=str(browser_raw.get("timezone_id", base.browser.timezone_id)).strip(),
        user_agent=str(browser_raw.get("user_agent", base.browser.user_agent)).strip(),
        user_data_dir=_expand_path(str(browser_raw.get("user_data_dir", base.browser.user_data_dir))),
        artifacts_dir=_expand_path(str(browser_raw.get("artifacts_dir", base.browser.artifacts_dir))),
        manual_login_timeout_seconds=int(
            browser_raw.get("manual_login_timeout_seconds", base.browser.manual_login_timeout_seconds)
        ),
        navigation_timeout_seconds=int(
            browser_raw.get("navigation_timeout_seconds", base.browser.navigation_timeout_seconds)
        ),
        action_timeout_seconds=int(
            browser_raw.get("action_timeout_seconds", base.browser.action_timeout_seconds)
        ),
        post_click_wait_seconds=int(
            browser_raw.get("post_click_wait_seconds", base.browser.post_click_wait_seconds)
        ),
        retain_artifact_runs=int(browser_raw.get("retain_artifact_runs", base.browser.retain_artifact_runs)),
        seed_cookie_header=str(browser_raw.get("seed_cookie_header", "")).strip(),
        viewport_width=int(browser_raw.get("viewport_width", base.browser.viewport_width)),
        viewport_height=int(browser_raw.get("viewport_height", base.browser.viewport_height)),
    )

    mail = MailConfig(
        enabled=bool(mail_raw.get("enabled", base.mail.enabled)),
        smtp_host=str(mail_raw.get("smtp_host", "")).strip(),
        smtp_port=int(mail_raw.get("smtp_port", base.mail.smtp_port)),
        smtp_username=str(mail_raw.get("smtp_username", "")).strip(),
        smtp_password=str(mail_raw.get("smtp_password", "")).strip(),
        from_addr=str(mail_raw.get("from_addr", "")).strip(),
        to_addrs=_normalize_mail_recipients(mail_raw.get("to_addrs", [])),
        subject_prefix=str(mail_raw.get("subject_prefix", base.mail.subject_prefix)).strip(),
        use_starttls=bool(mail_raw.get("use_starttls", base.mail.use_starttls)),
        use_ssl=bool(mail_raw.get("use_ssl", base.mail.use_ssl)),
    )

    schedule = ScheduleConfig(
        window_start=_validate_time_label(
            str(schedule_raw.get("window_start", base.schedule.window_start)), "schedule.window_start"
        ),
        window_end=_validate_time_label(
            str(schedule_raw.get("window_end", base.schedule.window_end)), "schedule.window_end"
        ),
    )

    runtime = RuntimeConfig(
        retry_count=int(runtime_raw.get("retry_count", base.runtime.retry_count)),
        retry_delay_seconds=int(runtime_raw.get("retry_delay_seconds", base.runtime.retry_delay_seconds)),
        lock_stale_seconds=int(runtime_raw.get("lock_stale_seconds", base.runtime.lock_stale_seconds)),
        state_file=_expand_path(str(runtime_raw.get("state_file", base.runtime.state_file))),
        log_file=_expand_path(str(runtime_raw.get("log_file", base.runtime.log_file))),
    )

    config = AppConfig(browser=browser, mail=mail, schedule=schedule, runtime=runtime, config_path=config_path)
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.browser.manual_login_timeout_seconds <= 0:
        raise ConfigError("browser.manual_login_timeout_seconds must be > 0")
    if config.browser.navigation_timeout_seconds <= 0:
        raise ConfigError("browser.navigation_timeout_seconds must be > 0")
    if config.browser.action_timeout_seconds <= 0:
        raise ConfigError("browser.action_timeout_seconds must be > 0")
    if config.browser.viewport_width <= 0 or config.browser.viewport_height <= 0:
        raise ConfigError("browser viewport must be > 0")
    if config.browser.retain_artifact_runs <= 0:
        raise ConfigError("browser.retain_artifact_runs must be > 0")
    if config.runtime.retry_count <= 0:
        raise ConfigError("runtime.retry_count must be > 0")
    if config.runtime.retry_delay_seconds < 0:
        raise ConfigError("runtime.retry_delay_seconds must be >= 0")
    if config.runtime.lock_stale_seconds <= 0:
        raise ConfigError("runtime.lock_stale_seconds must be > 0")

    if config.schedule.window_end <= config.schedule.window_start:
        raise ConfigError("schedule.window_end must be later than schedule.window_start")

    if config.mail.enabled:
        _require_non_empty(config.mail.smtp_host, "mail.smtp_host")
        _require_non_empty(config.mail.smtp_username, "mail.smtp_username")
        _require_non_empty(config.mail.from_addr, "mail.from_addr")
        if not config.mail.to_addrs:
            raise ConfigError("mail.to_addrs must contain at least one email address")
        password = _require_non_empty(config.mail.smtp_password, "mail.smtp_password")
        if _looks_like_placeholder(password):
            raise ConfigError("mail.smtp_password still looks like a placeholder")


def save_config(config: AppConfig, path: str | Path | None = None) -> Path:
    target = Path(path).expanduser().resolve() if path else config.config_path
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(config)
    payload.pop("config_path", None)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        target.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return target
