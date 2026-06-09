# GLaDOS Auto Check-in

Cross-platform browser automation for **GLaDOS daily check-in**.

跨平台的 GLaDOS 自动签到工具，面向个人自用部署，兼容 **Windows / macOS / Linux**。

## What This Project Does / 项目功能

- Opens the GLaDOS check-in page with Playwright.
- Reuses a dedicated browser profile or a pasted Cookie.
- Clicks the daily check-in button automatically.
- Installs a daily scheduled task for your operating system.
- Optionally sends failure notification emails.

这个项目只专注一件事：为你自己的 GLaDOS 账号执行每日自动签到。

## Beginner-Friendly Setup / 新手友好

This project includes:

- Interactive setup wizard: `glados-auto-checkin init`
- Two authentication modes: browser login or pasted Cookie
- Daily scheduler installation
- Optional email alerts
- Detailed docs for setup and troubleshooting

If you are new to JSON, SMTP, Playwright, or system schedulers, start here:

1. [Quick Start](docs/QUICK_START.md)
2. [FAQ](docs/FAQ.md)
3. [Troubleshooting](docs/TROUBLESHOOTING.md)

## Responsible Use / 使用边界

Use this tool **only for your own GLaDOS account**.

请只把它用于你自己的 GLaDOS 账号。不要把他人的 Cookie、账号或登录状态交给本工具使用。

## Features / 功能

- Browser automation based on `Python + Playwright`
- Daily schedule window with random execution inside the window
- Default schedule window: `12:00-16:00`
- Two authentication modes:
  - Browser login once
  - Paste an existing Cookie header
- Optional SMTP email alerts on failure
- Cross-platform scheduler support:
  - Linux: `systemd`
  - macOS: `launchd`
  - Windows: Task Scheduler

## Quick Install / 快速安装

### 1. Install Python / 安装 Python

Use **Python 3.10+**.

### 2. Install the package / 安装项目

```bash
pip install .
```

### 3. Run the interactive wizard / 运行初始化向导

```bash
glados-auto-checkin init
```

### 4. Validate your environment / 检查环境

```bash
glados-auto-checkin validate
```

### 5. Sign in once / 首次登录

Recommended for beginners:

```bash
glados-auto-checkin bootstrap-login
```

### 6. Test a manual run / 手动测试一次

```bash
glados-auto-checkin checkin
```

### 7. Install the daily scheduler / 安装每日定时任务

```bash
glados-auto-checkin install-schedule
```

## Main Commands / 主要命令

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

## Authentication Modes / 登录方式

### Option A: Browser Login Once

Best for beginners.

- Run `glados-auto-checkin bootstrap-login`
- A visible browser opens
- Log in manually
- The tool saves a dedicated browser profile for future runs

### Option B: Paste Cookie

Best if you already know how to copy authenticated cookies.

- Run `glados-auto-checkin init`
- Choose Cookie mode
- Paste the Cookie header when asked

You can also configure it manually in your local config file:

```json
{
  "browser": {
    "seed_cookie_header": "koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE"
  }
}
```

Only paste the full `Cookie` request header for your own account. Do not commit your real Cookie to this repository, do not paste it into issues, and do not share it with other people. If the Cookie expires, paste a fresh one or switch back to browser-login mode:

```bash
glados-auto-checkin bootstrap-login
```

## Email Alerts / 邮件告警

Email alerts are optional. If enabled, the tool only sends mail when a run fails.

邮件告警是可选功能。开启后，程序只会在运行失败时发送通知邮件。

## Personal Data Policy / 个人信息处理

The published source code should not contain:

- Your email address
- Your Cookie
- Your hostname
- Your personal absolute paths
- Your screenshots or runtime logs

Runtime data is stored outside the source tree by default, and local runtime folders are ignored by `.gitignore`.

## Project Structure / 项目结构

```text
glados-auto-checkin/
├── src/glados_auto_checkin/
├── tests/
├── docs/
├── config.example.json
└── README.md
```
