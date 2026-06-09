# GLaDOS 自动签到

英文版：[README_EN.md](README_EN.md)

这是一个基于 **Python + Playwright** 的跨平台 GLaDOS 每日自动签到工具，面向个人自用部署，兼容 **Windows / macOS / Linux**。

## 项目功能

- 打开 GLaDOS 签到页面
- 复用专用浏览器配置，或使用手动粘贴的 Cookie
- 自动点击每日签到按钮
- 为当前操作系统安装每日定时任务
- 可选：在运行失败时发送邮件告警

这个项目只专注一件事：为你自己的 GLaDOS 账号执行每日自动签到。

## 新手友好

项目包含：

- 交互式初始化向导：`glados-auto-checkin init`
- 两种登录方式：浏览器登录一次，或粘贴 Cookie
- 每日定时任务安装
- 可选邮件告警
- 安装、常见问题和故障排查文档

如果你不熟悉 JSON、SMTP、Playwright 或系统定时任务，建议先阅读：

1. [快速上手](docs/QUICK_START.md)
2. [常见问题](docs/FAQ.md)
3. [故障排查](docs/TROUBLESHOOTING.md)

## 使用边界

请只把它用于你自己的 GLaDOS 账号。不要把他人的 Cookie、账号或登录状态交给本工具使用。

## 功能特性

- 基于 `Python + Playwright` 的浏览器自动化
- 每日时间窗口内随机执行
- 默认执行窗口：`12:00-16:00`
- 两种认证方式：
  - 浏览器登录一次
  - 粘贴已有 Cookie 请求头
- 可选 SMTP 邮件失败告警
- 跨平台定时任务支持：
  - Linux：`systemd`
  - macOS：`launchd`
  - Windows：任务计划程序

## 快速安装

### 1. 安装 Python

需要 **Python 3.10+**。

### 2. 安装项目

在项目目录中运行：

```bash
pip install .
```

### 3. 运行初始化向导

```bash
glados-auto-checkin init
```

### 4. 检查运行环境

```bash
glados-auto-checkin validate
```

### 5. 首次登录

推荐新手使用浏览器登录模式：

```bash
glados-auto-checkin bootstrap-login
```

### 6. 手动测试一次

```bash
glados-auto-checkin checkin
```

### 7. 安装每日定时任务

```bash
glados-auto-checkin install-schedule
```

## 主要命令

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

## 登录方式

### 方式一：浏览器登录一次

最适合新手。

- 运行 `glados-auto-checkin bootstrap-login`
- 程序会打开一个可见浏览器窗口
- 你在浏览器中手动登录
- 工具会保存一个专用浏览器配置，后续运行会复用这个登录状态

### 方式二：粘贴 Cookie

如果你已经会从浏览器复制登录后的 Cookie，或者你的机器不方便使用浏览器登录模式，可以使用这个方式。

#### 如何从 Chrome 或 Edge 获取 Cookie

1. 打开 Chrome 或 Edge，登录你自己的 GLaDOS 账号。

2. 进入已登录状态下的 GLaDOS 页面，例如：

   ```text
   https://glados.rocks/console/checkin
   ```

3. 打开开发者工具：

   - Windows / Linux：按 `F12` 或 `Ctrl+Shift+I`
   - macOS：按 `Option+Command+I`

4. 切换到 `Network` 网络面板。

5. 刷新页面，或者点击一次签到/状态按钮，让浏览器产生网络请求。

6. 在请求列表中点击一个发往 `glados.rocks` 的请求，比如 URL 中包含 `status`、`checkin`、`user` 或 `console` 的请求。

7. 在请求详情中打开 `Headers`，找到 `Request Headers`。

8. 找到 `Cookie` 请求头，复制它后面的值。

   只复制 `Cookie:` 后面的值，不要复制整段请求头。它大概会像下面这个占位示例：

   ```text
   koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE
   ```

   有效的 GLaDOS 登录 Cookie 通常同时包含 `koa:sess` 和 `koa:sess.sig`。如果找不到它们，请确认你已经登录，并且选中的是发往 `glados.rocks` 的请求。

#### 将 Cookie 配置到工具中

推荐方式：

```bash
glados-auto-checkin init
```

然后选择 Cookie 模式，并在提示时粘贴刚才复制的 Cookie 请求头值。

也可以手动写入你的本地配置文件：

```json
{
  "browser": {
    "seed_cookie_header": "koa:sess=PASTE_YOUR_VALUE_HERE; koa:sess.sig=PASTE_YOUR_SIGNATURE_HERE"
  }
}
```

只粘贴你自己账号的完整 `Cookie` 请求头值，并尽量保持为一行。不要在开头额外加 `Cookie:`。

#### Cookie 安全提醒

Cookie 相当于临时登录凭据。

- 不要把真实 Cookie 提交到仓库
- 不要把真实 Cookie 粘贴到 GitHub issue、聊天消息、截图或日志里
- 不要与他人分享 Cookie
- 如果 Cookie 泄漏，请在浏览器中退出 GLaDOS；必要时修改密码

如果 Cookie 过期，可以重新复制一个新的 Cookie，或者切回浏览器登录模式：

```bash
glados-auto-checkin bootstrap-login
```

## 邮件告警

邮件告警是可选功能。开启后，程序只会在运行失败时发送通知邮件。

## 个人信息处理

公开源码不应包含：

- 你的邮箱地址
- 你的 Cookie
- 你的主机名
- 你的个人绝对路径
- 你的截图或运行日志

运行数据默认保存在源码目录之外，本地运行目录也已经被 `.gitignore` 忽略。

## 项目结构

```text
glados-auto-checkin/
├── src/glados_auto_checkin/
├── tests/
├── docs/
├── config.example.json
├── README.md
└── README_EN.md
```
