# Troubleshooting / 故障排查

## `validate` says no browser can be launched / `validate` 提示无法启动浏览器

Try one of these:

可以尝试：

1. Install Google Chrome or Chromium.
2. Set `browser.executable_path` in the config file.
3. Run `glados-auto-checkin validate` again.

## `bootstrap-login` opens but does not finish / `bootstrap-login` 打开后无法完成

Possible reasons:

可能原因：

- You did not complete login in time.
- The page layout changed.
- The site redirected to another login step.

Try running it again and watch the browser more carefully.

可以重新运行一次，并留意浏览器中的登录流程。

## The scheduler was installed but nothing happened / 已安装定时任务但没有运行

Check:

请检查：

1. Your config file path is correct.
2. Logs exist in `runtime.log_file`.
3. Your operating system scheduler is active.

## Linux: scheduler does not run after reboot / Linux 重启后定时任务不运行

This is often because the user service is not allowed to run before login.

这通常是因为用户级服务不允许在登录前运行。

Try:

```bash
loginctl enable-linger "$USER"
```

## Email alerts do not arrive / 收不到邮件告警

Check:

请检查：

1. SMTP host and port
2. App password or SMTP password
3. `use_ssl` and `use_starttls`
4. Spam folder

## Cookie mode stopped working / Cookie 模式失效

Your Cookie probably expired.

大概率是 Cookie 已经过期。

Either:

可以选择：

1. Paste a fresh Cookie.
2. Switch to browser-login mode and run:

```bash
glados-auto-checkin bootstrap-login
```
