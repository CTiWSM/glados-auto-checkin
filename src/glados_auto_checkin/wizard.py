from __future__ import annotations

from pathlib import Path

from .config import AppConfig, MailConfig, default_config, save_config


def _ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    if value:
        return value
    return default or ""


def _ask_yes_no(prompt: str, default: bool) -> bool:
    label = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{label}]: ").strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please answer with y/yes or n/no.")


def _ask_choice(prompt: str, choices: dict[str, str], default: str) -> str:
    print(prompt)
    for key, label in choices.items():
        print(f"  {key}. {label}")
    while True:
        value = input(f"Choose one [{default}]: ").strip() or default
        if value in choices:
            return value
        print("Invalid choice. Please try again.")


def run_init_wizard(config_path: Path) -> AppConfig:
    config = default_config(config_path)

    print("Welcome to GLaDOS Auto Check-in.")
    print("This wizard will create a local config file for you.")
    print("")
    print("Login methods / 登录方式")
    choice = _ask_choice(
        "Choose how you want to provide your authenticated session:",
        {
            "1": "Manual browser login once (recommended for beginners)",
            "2": "Paste an existing Cookie header",
        },
        default="1",
    )
    if choice == "2":
        config.browser.seed_cookie_header = _ask("Paste the Cookie header")

    print("")
    print("Daily schedule window / 每日执行时间窗口")
    config.schedule.window_start = _ask("Start time (HH:MM)", config.schedule.window_start)
    config.schedule.window_end = _ask("End time (HH:MM)", config.schedule.window_end)

    print("")
    print("Optional email alerts / 可选邮件告警")
    if _ask_yes_no("Enable failure emails?", default=False):
        config.mail.enabled = True
        config.mail.smtp_host = _ask("SMTP host", "smtp.example.com")
        config.mail.smtp_port = int(_ask("SMTP port", "587"))
        config.mail.smtp_username = _ask("SMTP username", "your-email@example.com")
        config.mail.smtp_password = _ask("SMTP password or app password")
        config.mail.from_addr = _ask("From address", config.mail.smtp_username)
        to_addrs = _ask("Recipient emails (comma separated)", config.mail.smtp_username)
        config.mail.to_addrs = [item.strip() for item in to_addrs.split(",") if item.strip()]
        config.mail.use_ssl = _ask_yes_no("Use implicit SSL?", default=False)
        config.mail.use_starttls = False if config.mail.use_ssl else _ask_yes_no(
            "Use STARTTLS?", default=True
        )
    else:
        config.mail = MailConfig(enabled=False, to_addrs=[])

    save_config(config, config_path)
    return config
