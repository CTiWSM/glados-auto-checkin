from __future__ import annotations

import json
import logging
import math
import platform
import random
import shutil
import time
from pathlib import Path
from typing import Any

from .config import AppConfig, ConfigError


LOGIN_MARKERS = (
    "login your account",
    "email address",
    "access code",
    "get code",
    "start your free trial",
)


class BrowserFlowError(Exception):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


def get_playwright_bindings():
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ConfigError(
            "Playwright is not installed. Run `pip install glados-auto-checkin` "
            "or `pip install playwright`, then `playwright install` if needed."
        ) from exc
    return sync_playwright, PlaywrightError


def candidate_browser_paths() -> list[Path]:
    system = platform.system()
    home = Path.home()
    candidates: list[Path] = []

    if system == "Darwin":
        candidates.extend(
            [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            ]
        )
    elif system == "Windows":
        local_app_data = Path.home() / "AppData" / "Local"
        program_files = Path.home().anchor + "Program Files"
        program_files_x86 = Path.home().anchor + "Program Files (x86)"
        candidates.extend(
            [
                Path(local_app_data) / "Google/Chrome/Application/chrome.exe",
                Path(program_files) / "Google/Chrome/Application/chrome.exe",
                Path(program_files_x86) / "Google/Chrome/Application/chrome.exe",
                Path(local_app_data) / "Microsoft/Edge/Application/msedge.exe",
                Path(program_files) / "Microsoft/Edge/Application/msedge.exe",
                Path(program_files_x86) / "Microsoft/Edge/Application/msedge.exe",
            ]
        )
    else:
        for command in (
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "microsoft-edge",
        ):
            resolved = shutil.which(command)
            if resolved:
                candidates.append(Path(resolved))

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen or not candidate.exists():
            continue
        deduped.append(candidate)
        seen.add(key)
    return deduped


def browser_launch_candidates(config: AppConfig) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if config.browser.executable_path:
        candidates.append({"executable_path": config.browser.executable_path})
    if config.browser.channel:
        candidates.append({"channel": config.browser.channel})
    for path in candidate_browser_paths():
        candidates.append({"executable_path": str(path)})
    return candidates


def validate_browser_runtime(config: AppConfig) -> None:
    sync_playwright, PlaywrightError = get_playwright_bindings()
    errors: list[str] = []

    with sync_playwright() as playwright:
        for candidate in browser_launch_candidates(config):
            launch_kwargs = {"headless": True, **candidate}
            try:
                browser = playwright.chromium.launch(**launch_kwargs)
                browser.close()
                return
            except PlaywrightError as exc:
                errors.append(f"{candidate}: {exc}")

    raise ConfigError(
        "Playwright could not launch Chrome/Chromium. "
        "Tried the configured browser options and common browser paths.\n"
        + "\n".join(errors)
    )


def parse_cookie_header(header: str) -> list[dict[str, Any]]:
    cookies: list[dict[str, Any]] = []
    if not header.strip():
        return cookies

    for part in header.split("; "):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if not name:
            continue
        cookies.append(
            {
                "name": name,
                "value": value,
                "domain": "glados.rocks",
                "path": "/",
                "secure": True,
                "httpOnly": False,
                "sameSite": "Lax",
            }
        )
    return cookies


def prune_old_artifacts(artifacts_dir: Path, keep: int) -> None:
    if not artifacts_dir.exists():
        return
    run_dirs = sorted(path for path in artifacts_dir.iterdir() if path.is_dir())
    for stale in run_dirs[:-keep]:
        shutil.rmtree(stale, ignore_errors=True)


def create_run_dir(config: AppConfig, label: str) -> Path:
    base = Path(config.browser.artifacts_dir)
    base.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = base / f"{stamp}-{label}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prune_old_artifacts(base, config.browser.retain_artifact_runs)
    return run_dir


def save_text_artifact(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_message(payload: dict[str, Any]) -> str:
    message = payload.get("message")
    if isinstance(message, str) and message.strip():
        return message.strip()
    return json.dumps(payload, ensure_ascii=False)


def extract_user_email(status_payload: dict[str, Any]) -> str:
    data = status_payload.get("data")
    if isinstance(data, dict):
        value = data.get("email") or data.get("mail")
        if isinstance(value, str):
            return value.strip()
    return ""


def extract_left_days(status_payload: dict[str, Any]) -> str:
    data = status_payload.get("data")
    if not isinstance(data, dict):
        return "unknown"
    value = data.get("leftDays")
    if value in (None, ""):
        return "unknown"
    try:
        return str(math.floor(float(str(value))))
    except (TypeError, ValueError):
        return str(value)


def classify_checkin(payload: dict[str, Any], body_text: str) -> str:
    message = extract_message(payload).lower()
    body_lower = body_text.lower()
    duplicate_tokens = (
        "repeats",
        "try tomorrow",
        "return tomorrow",
        "observation logged",
        "checked in",
        "已签到",
        "重复签到",
    )
    success_tokens = (
        "checkin! got",
        "checkin! get",
        "签到成功",
        "success",
    )

    if any(token in message for token in duplicate_tokens) or any(
        token in body_lower for token in duplicate_tokens
    ):
        return "duplicate"
    if any(token in message for token in success_tokens):
        return "success"
    if payload.get("code") == 0:
        return "success"
    if payload.get("code") == 1 and "today" in message:
        return "duplicate"
    return "failure"


def is_login_page(url: str, body_text: str) -> bool:
    url_lower = url.lower()
    body_lower = body_text.lower()
    if "/login" in url_lower:
        return True
    return any(marker in body_lower for marker in LOGIN_MARKERS)


def should_retry(exc: Exception) -> bool:
    text = repr(exc).lower()
    return any(
        token in text
        for token in (
            "timeout",
            "connection reset",
            "net::err",
            "closed",
            "target closed",
            "context closed",
            "navigation failed",
        )
    )


def _launch_context(playwright, config: AppConfig, *, headed: bool):
    browser_cfg = config.browser
    base_kwargs = {
        "headless": not headed,
        "user_agent": browser_cfg.user_agent,
        "viewport": {
            "width": browser_cfg.viewport_width,
            "height": browser_cfg.viewport_height,
        },
        "locale": browser_cfg.locale,
        "timezone_id": browser_cfg.timezone_id,
        "args": [f"--lang={browser_cfg.locale}"],
    }

    errors: list[str] = []
    for candidate in browser_launch_candidates(config):
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=browser_cfg.user_data_dir,
                **base_kwargs,
                **candidate,
            )
            context.set_default_timeout(browser_cfg.action_timeout_seconds * 1000)
            context.set_default_navigation_timeout(browser_cfg.navigation_timeout_seconds * 1000)
            return context
        except Exception as exc:  # pragma: no cover - depends on local browser install
            errors.append(f"{candidate}: {exc}")

    raise BrowserFlowError(
        "Could not launch a supported browser. "
        "Run `glados-auto-checkin validate` to see detailed browser errors.",
        context={"launch_errors": errors},
    )


def ensure_seeded_cookies(context, config: AppConfig) -> bool:
    existing = context.cookies("https://glados.rocks")
    names = {cookie["name"] for cookie in existing}
    if {"koa:sess", "koa:sess.sig"}.issubset(names):
        return False

    cookies = parse_cookie_header(config.browser.seed_cookie_header)
    if not cookies:
        return False

    context.add_cookies(cookies)
    logging.info("Seeded the dedicated browser profile using configured cookies.")
    return True


def attach_api_collectors(page):
    api_events: list[dict[str, Any]] = []
    failed_requests: list[dict[str, Any]] = []

    def on_response(response):
        if "/api/" not in response.url:
            return
        try:
            text = response.text()
        except Exception as exc:  # pragma: no cover - defensive
            text = f"<response-read-error: {exc!r}>"
        api_events.append(
            {
                "method": response.request.method,
                "url": response.url,
                "status": response.status,
                "body": text[:3000],
            }
        )

    def on_request_failed(request):
        failed_requests.append(
            {
                "method": request.method,
                "url": request.url,
                "failure": request.failure,
            }
        )

    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)
    return api_events, failed_requests


def latest_matching_json(
    events: list[dict[str, Any]],
    *,
    url_fragment: str,
    method: str | None = None,
) -> dict[str, Any] | None:
    for event in reversed(events):
        if url_fragment not in event["url"]:
            continue
        if method and event["method"] != method:
            continue
        try:
            payload = json.loads(event["body"])
        except json.JSONDecodeError:
            payload = {"message": event["body"]}
        payload["http_status"] = event["status"]
        payload["url"] = event["url"]
        return payload
    return None


def get_body_text(page) -> str:
    body = page.locator("body")
    body.wait_for(state="attached", timeout=10000)
    return body.inner_text(timeout=10000)


def save_page_snapshot(page, run_dir: Path, name: str) -> tuple[str, Path]:
    body_text = get_body_text(page)
    png_path = run_dir / f"{name}.png"
    txt_path = run_dir / f"{name}.txt"
    try:
        page.screenshot(path=str(png_path), full_page=True, animations="disabled", timeout=30000)
    except Exception as exc:
        logging.warning("Could not save screenshot %s: %s", png_path.name, exc)
    save_text_artifact(txt_path, body_text)
    return body_text, png_path


def get_status_summary(page, api_events: list[dict[str, Any]], body_text: str) -> dict[str, Any]:
    status_payload = latest_matching_json(api_events, url_fragment="/api/user/status", method="GET")
    return {
        "url": page.url,
        "title": page.title(),
        "body_excerpt": body_text[:2000],
        "status_payload": status_payload or {},
        "account_email": extract_user_email(status_payload or {}),
        "left_days": extract_left_days(status_payload or {}),
    }


def wait_for_ready(page, checkin_url: str) -> None:
    page.goto(checkin_url, wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("load", timeout=15000)
    except Exception:
        pass
    page.locator("body").wait_for(state="attached", timeout=10000)
    for _ in range(5):
        body_text = get_body_text(page)
        if body_text.strip():
            return
        page.wait_for_timeout(1000)
    page.wait_for_timeout(2000)


def perform_browser_checkin(config: AppConfig, *, status_only: bool, headed: bool) -> dict[str, Any]:
    browser_cfg = config.browser
    run_dir = create_run_dir(config, "browser-run")
    result: dict[str, Any] = {"run_dir": str(run_dir)}
    playwright = None
    context = None

    try:
        sync_playwright, _ = get_playwright_bindings()
        playwright = sync_playwright().start()
        context = _launch_context(playwright, config, headed=headed)
        page = context.pages[0] if context.pages else context.new_page()
        api_events, failed_requests = attach_api_collectors(page)
        seeded = ensure_seeded_cookies(context, config)
        if seeded:
            context.storage_state(path=str(run_dir / "storage-state-after-seed.json"))

        wait_for_ready(page, browser_cfg.checkin_url)
        body_before, _ = save_page_snapshot(page, run_dir, "01-open")

        if is_login_page(page.url, body_before):
            raise BrowserFlowError(
                "Browser profile is not authenticated. Run `glados-auto-checkin bootstrap-login`.",
                context={
                    "status_before": get_status_summary(page, api_events, body_before),
                    "failed_requests": failed_requests,
                    "run_dir": str(run_dir),
                },
            )

        status_before = get_status_summary(page, api_events, body_before)
        result["status_before"] = status_before

        if status_only:
            result["result_type"] = "status_only"
            result["message"] = "Authenticated browser state is valid."
            result["status_after"] = status_before
            return result

        button = page.get_by_role("button", name="签到")
        if button.count() == 0:
            raise BrowserFlowError(
                "Could not find the sign-in button on the check-in page.",
                context={
                    "status_before": status_before,
                    "failed_requests": failed_requests,
                    "run_dir": str(run_dir),
                },
            )

        with page.expect_response(
            lambda response: "/api/user/checkin" in response.url and response.request.method == "POST",
            timeout=browser_cfg.action_timeout_seconds * 1000,
        ) as response_info:
            button.first.click()

        page.wait_for_timeout(browser_cfg.post_click_wait_seconds * 1000)
        response = response_info.value
        try:
            payload = response.json()
        except Exception:
            payload = {"message": response.text()}
        payload["http_status"] = response.status
        payload["url"] = response.url

        body_after, _ = save_page_snapshot(page, run_dir, "02-after-click")
        status_after = get_status_summary(page, api_events, body_after)
        result_type = classify_checkin(payload, body_after)

        result.update(
            {
                "result_type": result_type,
                "message": extract_message(payload),
                "checkin_result": payload,
                "status_after": status_after,
                "failed_requests": failed_requests,
            }
        )

        save_text_artifact(run_dir / "api-events.json", json.dumps(api_events, ensure_ascii=False, indent=2))
        if failed_requests:
            save_text_artifact(
                run_dir / "failed-requests.json",
                json.dumps(failed_requests, ensure_ascii=False, indent=2),
            )
        return result
    finally:
        if context is not None:
            context.close()
        if playwright is not None:
            playwright.stop()


def retrying_browser_flow(config: AppConfig, *, status_only: bool, headed: bool) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(1, config.runtime.retry_count + 1):
        try:
            return perform_browser_checkin(config, status_only=status_only, headed=headed)
        except BrowserFlowError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt >= config.runtime.retry_count or not should_retry(exc):
                break
            sleep_seconds = min(config.runtime.retry_delay_seconds * (2 ** (attempt - 1)), 180)
            sleep_seconds += random.uniform(0, 3)
            logging.warning(
                "Browser automation failed on attempt %s/%s: %s; retrying in %.1fs",
                attempt,
                config.runtime.retry_count,
                exc,
                sleep_seconds,
            )
            time.sleep(sleep_seconds)

    if last_exc is None:
        raise BrowserFlowError("Browser automation did not return a result.")
    raise last_exc


def bootstrap_login(config: AppConfig) -> dict[str, Any]:
    browser_cfg = config.browser
    run_dir = create_run_dir(config, "bootstrap-login")
    playwright = None
    context = None

    try:
        sync_playwright, _ = get_playwright_bindings()
        playwright = sync_playwright().start()
        context = _launch_context(playwright, config, headed=True)
        page = context.pages[0] if context.pages else context.new_page()
        api_events, _ = attach_api_collectors(page)
        ensure_seeded_cookies(context, config)
        wait_for_ready(page, browser_cfg.checkin_url)
        body_text, _ = save_page_snapshot(page, run_dir, "01-bootstrap-open")

        if not is_login_page(page.url, body_text):
            context.storage_state(path=str(run_dir / "storage-state.json"))
            return {
                "run_dir": str(run_dir),
                "message": "Browser profile is already authenticated.",
                "status_after": get_status_summary(page, api_events, body_text),
            }

        logging.info(
            "A browser window should now be visible. Complete the GLaDOS login flow manually within %ss.",
            browser_cfg.manual_login_timeout_seconds,
        )
        deadline = time.time() + browser_cfg.manual_login_timeout_seconds
        while time.time() < deadline:
            wait_for_ready(page, browser_cfg.checkin_url)
            body_text = get_body_text(page)
            if not is_login_page(page.url, body_text):
                save_page_snapshot(page, run_dir, "02-bootstrap-success")
                context.storage_state(path=str(run_dir / "storage-state.json"))
                return {
                    "run_dir": str(run_dir),
                    "message": "Manual login completed and browser state was saved.",
                    "status_after": get_status_summary(page, api_events, body_text),
                }
            time.sleep(3)

        save_page_snapshot(page, run_dir, "02-bootstrap-timeout")
        raise BrowserFlowError(
            "Manual login was not completed before the timeout expired.",
            context={"run_dir": str(run_dir)},
        )
    finally:
        if context is not None:
            context.close()
        if playwright is not None:
            playwright.stop()


def clear_browser_state(config: AppConfig) -> None:
    user_data_dir = Path(config.browser.user_data_dir)
    if user_data_dir.exists():
        shutil.rmtree(user_data_dir)
