# FAQ / 常见问题

## Do I need to copy Cookie every day? / 需要每天复制 Cookie 吗？

No.

不需要。

If you use browser-login mode, you usually only need to log in once. The tool then reuses the dedicated browser profile.

如果你使用“浏览器登录一次”模式，通常只需要首次手动登录一次。之后工具会复用专用浏览器配置。

## What if the login state expires? / 登录状态过期怎么办？

Run:

```bash
glados-auto-checkin bootstrap-login
```

Then log in again manually.

然后在打开的浏览器里重新手动登录。

## Do I have to enable email? / 必须开启邮件告警吗？

No. Email alerts are optional.

不需要。邮件告警是可选功能。

## Does this support Windows? / 支持 Windows 吗？

Yes. The scheduler supports Windows Task Scheduler.

支持。Windows 下会使用任务计划程序。

## Does this move my real mouse? / 会移动真实鼠标吗？

No. It uses browser automation, not desktop mouse automation.

不会。它使用浏览器自动化，不会控制你的真实鼠标。

## Where are logs stored? / 日志保存在哪里？

Logs are stored in the path defined by `runtime.log_file` in your config.

日志位置由配置文件中的 `runtime.log_file` 决定。

## Can I change the daily time window later? / 以后可以修改每日时间窗口吗？

Yes. Edit the config file, then reinstall the scheduler:

可以。修改配置文件后，重新安装定时任务：

```bash
glados-auto-checkin uninstall-schedule
glados-auto-checkin install-schedule
```
