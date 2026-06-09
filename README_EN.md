# GLaDOS Auto Check-in

Chinese version: [README.md](README.md)

Cross-platform browser automation for **GLaDOS daily check-in**, designed for personal use on **Windows / macOS / Linux**.

## What This Project Does

- Opens the GLaDOS check-in page.
- Reuses a dedicated browser profile or a pasted Cookie.
- Clicks the daily check-in button automatically.
- Installs a daily scheduled task for your operating system.
- Optionally sends failure notification emails.

This project intentionally focuses on one thing: daily auto check-in for your own GLaDOS account.

## Beginner-Friendly Setup

This project includes:

- Interactive setup wizard: `glados-auto-checkin init`
- Two authentication modes: browser login once, or pasted Cookie
- Daily scheduler installation
- Optional email alerts
- Detailed docs for setup and troubleshooting

If you are new to JSON, SMTP, Playwright, or system schedulers, start here:

1. [Quick Start](docs/QUICK_START.md)
2. [FAQ](docs/FAQ.md)
3. [Troubleshooting](docs/TROUBLESHOOTING.md)

## Responsible Use

Use this tool **only for your own GLaDOS account**. Do not use another person's Cookie, account, or login state with this tool.

## Features

- Browser automation based on `Python + Playwright`
- Daily schedule window with random execution inside the window
- Default schedule window: `12:00-16:00`
- Two authentication modes:
  - Browser login once
  - Paste an existing Cookie request header
- Optional SMTP email alerts on failure
- Cross-platform scheduler support:
  - Linux: `systemd`
  - macOS: `launchd`
  - Windows: Task Scheduler

## Quick Install

### 1. Install Python

Use **Python 3.10+**.

### 2. Install the package

Run this in the project directory:

```bash
pip install .
```

### 3. Run the interactive wizard

```bash
glados-auto-checkin init
```

### 4. Validate your environment

```bash
glados-auto-checkin validate
```

### 5. Sign in once

Recommended for beginners:

```bash
glados-auto-checkin bootstrap-login
```

### 6. Test a manual run

```bash
glados-auto-checkin checkin
```

### 7. Install the daily scheduler

```bash
glados-auto-checkin install-schedule
```

## Main Commands

```bash
glados-auto-checkin init
glados-auto-checkin validate
glados-auto-checkin bootstrap-login
glados-auto-checkin status
glados-auto-checkin checkin
glados-auto-checkin install-schedule
glados-auto-checkin uninstall-schedule
glados-auto-checkin test-email
glados-auto-checkin clear-browser-state
```

## Authentication Modes

### Option A: Browser Login Once

Best for beginners.

- Run `glados-auto-checkin bootstrap-login`.
- A visible browser opens.
- Log in manually.
- The tool saves a dedicated browser profile for future runs.

### Option B: Paste Cookie

Use this mode if you already know how to copy an authenticated browser Cookie, or if browser-login mode is not convenient on your machine.

#### How to get the Cookie from Chrome or Edge

1. Open Chrome or Edge and log in to your own GLaDOS account.

2. Go to the signed-in GLaDOS page, for example:

   ```text
   https://glados.rocks/console/checkin
   ```

3. Open Developer Tools:

   - Windows / Linux: press `F12` or `Ctrl+Shift+I`
   - macOS: press `Option+Command+I`

4. Switch to the `Network` tab.

5. Refresh the page, or click the check-in/status button once so the browser creates network requests.

6. Click a request sent to `glados.rocks`, such as a request containing `status`, `checkin`, `user`, or `console`.

7. In the request details, open `Headers`, then find `Request Headers`.

8. Find the `Cookie` header and copy its value.

   Copy the value after `Cookie:`, not the whole request headers. It should look similar to this placeholder example:

   ```text
   koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE
   ```

   A valid GLaDOS login Cookie normally contains both `koa:sess` and `koa:sess.sig`. If you cannot find them, make sure you are logged in and that you selected a request to `glados.rocks`.

#### Configure the tool with the Cookie

Recommended method:

```bash
glados-auto-checkin init
```

Choose Cookie mode, then paste the Cookie request header value when prompted.

You can also configure it manually in your local config file:

```json
{
  "browser": {
    "seed_cookie_header": "koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE"
  }
}
```

Only paste the full `Cookie` request header value for your own account. Keep it as one line. Do not add `Cookie:` at the beginning.

#### Cookie Safety

Your Cookie is equivalent to a temporary login credential.

- Do not commit your real Cookie to this repository.
- Do not paste it into GitHub issues, chat messages, screenshots, or logs.
- Do not share it with other people.
- If it leaks, log out of GLaDOS in your browser and change your password if needed.

If the Cookie expires, paste a fresh one or switch back to browser-login mode:

```bash
glados-auto-checkin bootstrap-login
```

## Email Alerts

Email alerts are optional. If enabled, the tool only sends mail when a run fails.

## Personal Data Policy

The published source code should not contain:

- Your email address
- Your Cookie
- Your hostname
- Your personal absolute paths
- Your screenshots or runtime logs

Runtime data is stored outside the source tree by default, and local runtime folders are ignored by `.gitignore`.

## Project Structure

```text
glados-auto-checkin/
├── src/glados_auto_checkin/
├── tests/
├── docs/
├── config.example.json
├── README.md
└── README_EN.md
```
