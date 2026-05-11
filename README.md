# 444 调试入口

这个目录包含注册、支付 replay、Web UI 和排障辅助脚本。工作时优先使用离线
或本地验证命令，避免直接触发真实注册、支付或外部副作用。

## 目录

- `CTF-reg/`：注册与 auth 辅助代码。
- `CTF-pay/`：支付 replay、hCaptcha、PayPal 相关工具。
- `webui/`：Web UI 后端和测试。
- `docs/debugging.md`：常见失败、截图查看和排障 runbook。
- `.codex/overnight-log.md`：Codex unattended 工作日志和验证证据。

## 安全验证命令

```bash
# 注册侧单元测试
cd /opt/444/CTF-reg && ../.venv/bin/pytest -q

# Web UI 单元测试
cd /opt/444/webui && ../.venv/bin/pytest -q

# 验证 WebUI 运行在 Tailscale 地址且无凭证 API 被 auth 拦住
cd /opt/444 && ./.venv/bin/python scripts/verify_webui_runtime.py

# 汇总 WebUI access log 里的最近 run/start、run/status、401 auth gate
cd /opt/444 && ./.venv/bin/python scripts/summarize_webui_access_log.py --tail 300

# 一次性汇总注册失败日志、注册截图时间线和 WebUI access log 证据
cd /opt/444 && ./.venv/bin/python scripts/diagnose_registration_failure.py --failure-log logs/failure_2.log

# 最近一次注册截图时间线
cd /opt/444 && ./.venv/bin/python CTF-reg/registration_evidence.py --dir /tmp

# 验证 screenshot viewer 白名单已写进调试手册
cd /opt/444 && ./.venv/bin/python scripts/verify_screenshot_viewer_docs.py
```

## 截图查看

注册和支付流程的截图通过 Tailscale 内网 viewer 查看：

```text
http://100.89.13.34:18080/
```

健康检查：

```bash
curl -fsS http://100.89.13.34:18080/healthz
```

viewer 只展示 systemd `SHOT_VIEW_GLOBS` 白名单中的截图路径；白名单和文档一致性
可以用 `scripts/verify_screenshot_viewer_docs.py` 检查。

## WebUI / Dashboard

当前 WebUI 预期绑定到 Tailscale 地址 `100.89.13.34:8765`。`444-webui.service`
可能不是 active；判断 dashboard 是否可用时，以端口连通、`/api/healthz` 返回
`200`、无凭证访问 `/webui/api/run/status` 返回 `401` 为准。只读检查：

```bash
cd /opt/444 && ./.venv/bin/python scripts/verify_webui_runtime.py
```

排查“用户点了 start、后续注册失败、dashboard 仍在轮询”的情况时，用 access
log 摘要确认最近 run API 活动：

```bash
cd /opt/444 && ./.venv/bin/python scripts/summarize_webui_access_log.py --tail 300
```

如果要把注册失败根因、截图路径和 dashboard 访问证据放在同一份输出里：

```bash
cd /opt/444 && ./.venv/bin/python scripts/diagnose_registration_failure.py --failure-log logs/failure_2.log
```

诊断报告会给失败截图和最近逐步截图生成 viewer 直达 URL，默认使用
`http://100.89.13.34:18080`；如果 viewer 地址变化，可传
`--viewer-base-url http://100.x.x.x:18080`。

更多排障步骤见 [docs/debugging.md](docs/debugging.md)。
