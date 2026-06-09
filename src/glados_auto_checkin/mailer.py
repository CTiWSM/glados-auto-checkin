from __future__ import annotations

import datetime as dt
import json
import logging
import smtplib
import socket
import ssl
from email.message import EmailMessage

from .config import AppConfig


class IPv4FallbackSMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        last_error = None
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ipv4_infos = [info for info in infos if info[0] == socket.AF_INET]
        other_infos = [info for info in infos if info[0] != socket.AF_INET]

        for family, socktype, proto, _, sockaddr in ipv4_infos + other_infos:
            try:
                sock = socket.socket(family, socktype, proto)
                if timeout is not None:
                    sock.settimeout(timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sockaddr)
                return sock
            except OSError as exc:
                last_error = exc

        if last_error is None:
            raise OSError(f"Could not resolve any socket addresses for {host}:{port}")
        raise last_error


class IPv4FallbackSMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        last_error = None
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ipv4_infos = [info for info in infos if info[0] == socket.AF_INET]
        other_infos = [info for info in infos if info[0] != socket.AF_INET]

        for family, socktype, proto, _, sockaddr in ipv4_infos + other_infos:
            try:
                sock = socket.socket(family, socktype, proto)
                if timeout is not None:
                    sock.settimeout(timeout)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sockaddr)
                return self.context.wrap_socket(sock, server_hostname=host)
            except OSError as exc:
                last_error = exc

        if last_error is None:
            raise OSError(f"Could not resolve any socket addresses for {host}:{port}")
        raise last_error


def send_email(config: AppConfig, *, subject: str, body: str) -> None:
    if not config.mail.enabled:
        logging.info("Email alerts are disabled, skipping email send.")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.mail.from_addr
    msg["To"] = ", ".join(config.mail.to_addrs or [])
    msg.set_content(body)

    smtp_cls = IPv4FallbackSMTP_SSL if config.mail.use_ssl else IPv4FallbackSMTP
    smtp_kwargs = {"timeout": 30}
    if config.mail.use_ssl:
        smtp_kwargs["context"] = ssl.create_default_context()

    with smtp_cls(config.mail.smtp_host, config.mail.smtp_port, **smtp_kwargs) as smtp:
        smtp.ehlo()
        if config.mail.use_starttls:
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
        smtp.login(config.mail.smtp_username, config.mail.smtp_password.replace(" ", ""))
        smtp.send_message(msg)


def build_failure_subject(config: AppConfig, account_email: str) -> str:
    prefix = config.mail.subject_prefix
    hostname = socket.gethostname()
    target = account_email or "unknown-account"
    return f"{prefix} Failure on {hostname} ({target})"


def build_failure_body(
    *,
    config: AppConfig,
    reason: str,
    account_email: str,
    status_before: dict,
    checkin_result: dict | None,
    status_after: dict,
    run_dir: str | None,
) -> str:
    return "\n".join(
        [
            "GLaDOS automatic browser check-in failed.",
            "",
            f"Time: {dt.datetime.now().isoformat(timespec='seconds')}",
            f"Host: {socket.gethostname()}",
            f"Account: {account_email or 'unknown'}",
            f"Reason: {reason}",
            f"Config: {config.config_path}",
            f"Artifacts: {run_dir or 'n/a'}",
            "",
            "Status before:",
            json.dumps(status_before or {}, ensure_ascii=False, indent=2),
            "",
            "Check-in result:",
            json.dumps(checkin_result or {}, ensure_ascii=False, indent=2),
            "",
            "Status after:",
            json.dumps(status_after or {}, ensure_ascii=False, indent=2),
            "",
            "Most likely next step: run `glados-auto-checkin bootstrap-login` and sign in again.",
        ]
    )
