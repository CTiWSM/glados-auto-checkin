# Quick Start / 快速上手

This guide is written for users who are not comfortable with code.

这份文档面向不太熟悉代码和命令行的用户。

## Step 1: Install Python / 安装 Python

You need Python 3.10 or newer.

你需要安装 Python 3.10 或更高版本。

- Windows: install from python.org and check "Add Python to PATH".
- macOS: use the python.org installer or Homebrew.
- Linux: use your package manager or a Python distribution you trust.

## Step 2: Install this project / 安装项目

Open a terminal in this project folder, then run:

在项目目录打开终端，然后运行：

```bash
pip install .
```

If that fails, try:

如果失败，可以试试：

```bash
python -m pip install .
```

## Step 3: Run the setup wizard / 运行初始化向导

```bash
glados-auto-checkin init
```

The wizard will ask:

向导会询问：

- How you want to log in
- What daily time window you want
- Whether you want email alerts

## Step 4: Validate the environment / 验证环境

```bash
glados-auto-checkin validate
```

This checks:

- Your config file
- Playwright installation
- Whether a supported browser can be launched

## Step 5: Choose your login method / 选择登录方式

### Recommended: browser login once / 推荐：浏览器登录一次

```bash
glados-auto-checkin bootstrap-login
```

What happens:

1. The tool opens a browser window.
2. You log in manually.
3. The tool saves a dedicated browser profile.
4. Future runs reuse that login state automatically.

### Advanced: Cookie mode / 进阶：Cookie 模式

If you selected Cookie mode in `init`, the tool will use the Cookie header you pasted.

如果你在 `init` 中选择 Cookie 模式，工具会使用你粘贴的 Cookie header。

## Step 6: Test a real run / 测试一次真实运行

```bash
glados-auto-checkin checkin
```

If today was already signed in, a duplicate-check-in result is still a good sign.

如果今天已经签到过，返回“已签到”或类似结果也说明工具可以正常访问账号状态。

## Step 7: Install the scheduler / 安装定时任务

```bash
glados-auto-checkin install-schedule
```

The tool will install the correct scheduler for your system:

- Linux: user-level systemd timer
- macOS: launchd agent
- Windows: Task Scheduler task

## Step 8: Optional email test / 可选：测试邮件告警

If you enabled email alerts:

如果你开启了邮件告警：

```bash
glados-auto-checkin test-email
```

## Daily Behavior / 每日运行逻辑

The scheduler triggers the tool at the **start** of your time window.

定时器会在你设置的时间窗口起点触发程序。

Then the tool picks a **random time inside the window** and waits until that time before checking in.

随后工具会在窗口内随机选择一个时间点，并等到该时间再执行签到。
