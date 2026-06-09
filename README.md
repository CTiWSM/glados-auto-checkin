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

Use this mode if you already know how to copy an authenticated browser Cookie, or if browser-login mode is not convenient on your machine.

如果你已经会从浏览器复制登录后的 Cookie，或者你的机器不方便使用浏览器登录模式，可以使用这个方式。

#### How to get the Cookie from Chrome or Edge / 如何从 Chrome 或 Edge 获取 Cookie

1. Open Chrome or Edge and log in to your own GLaDOS account.

   打开 Chrome 或 Edge，登录你自己的 GLaDOS 账号。

2. Go to the signed-in GLaDOS page, for example:

   进入已登录状态下的 GLaDOS 页面，例如：

   ```text
   https://glados.rocks/console/checkin
   ```

3. Open Developer Tools.

   打开开发者工具：

   - Windows / Linux: press `F12` or `Ctrl+Shift+I`
   - macOS: press `Option+Command+I`

4. Switch to the `Network` tab.

   切换到 `Network` 网络面板。

5. Refresh the page, or click the check-in/status button once.

   刷新页面，或者点击一次签到/状态按钮，让浏览器产生网络请求。

6. Click a request sent to `glados.rocks`, such as a request containing `status`, `checkin`, `user`, or `console`.

   在请求列表中点击一个发往 `glados.rocks` 的请求，比如 URL 中包含 `status`、`checkin`、`user` 或 `console` 的请求。

7. In the request details, open `Headers`, then find `Request Headers`.

   在请求详情中打开 `Headers`，找到 `Request Headers`。

8. Find the `Cookie` header and copy its value.

   找到 `Cookie` 请求头，复制它后面的值。

   Copy the value after `Cookie:`, not the whole request headers. It should look similar to this placeholder example:

   只复制 `Cookie:` 后面的值，不要复制整段请求头。它大概会像下面这个占位示例：

   ```text
   koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE
   ```

   A valid GLaDOS login Cookie normally contains both `koa:sess` and `koa:sess.sig`. If you cannot find them, make sure you are logged in and that you selected a request to `glados.rocks`.

   有效的 GLaDOS 登录 Cookie 通常同时包含 `koa:sess` 和 `koa:sess.sig`。如果找不到它们，请确认你已经登录，并且选中的是发往 `glados.rocks` 的请求。

#### Configure the tool with the Cookie / 将 Cookie 配置到工具中

Recommended method:

推荐方式：

- Run `glados-auto-checkin init`
- Choose Cookie mode
- Paste the Cookie header when asked

运行：

```bash
glados-auto-checkin init
```

然后选择 Cookie 模式，并在提示时粘贴刚才复制的 Cookie header。

You can also configure it manually in your local config file:

也可以手动写入你的本地配置文件：

```json
{
  "browser": {
    "seed_cookie_header": "koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE"
  }
}
```

Only paste the full `Cookie` request header for your own account. Keep it as one line. Do not add `Cookie:` at the beginning.

只粘贴你自己账号的完整 `Cookie` 请求头值，并尽量保持为一行。不要在开头额外加 `Cookie:`。

#### Cookie safety / Cookie 安全提醒

Your Cookie is equivalent to a temporary login credential.

Cookie 相当于临时登录凭据。

- Do not commit your real Cookie to this repository.
- Do not paste it into GitHub issues, chat messages, screenshots, or logs.
- Do not share it with other people.
- If it leaks, log out of GLaDOS in your browser and change your password if needed.

如果 Cookie 过期，可以重新复制一个新的 Cookie，或者切回浏览器登录模式：

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
