# webui — 配置向导 + preflight 体检

## 快速开始

```bash
# 后端依赖
pip install -r webui/requirements.txt

# 前端构建（一次）
cd webui/frontend && pnpm i && pnpm build && cd ../..

# 启动
python -m webui.server
# 浏览器开 http://127.0.0.1:8765
```

首次访问会跳到 `/setup` 创建管理员账号。

## 15 步流程

详见 `docs/superpowers/specs/2026-04-28-webui-design.md`。

| Phase | 步骤 |
|---|---|
| 1 基础（6）| 模式选择 / 系统依赖 / Cloudflare / IMAP / 邮箱地址来源 / 代理 |
| 2 支付（2）| PayPal / 卡 + Billing |
| 3 验证码（2，可选）| 打码平台 / VLM endpoint |
| 4 下游（4）| Team plan / gpt-team / CPA / Daemon / Stripe runtime |
| 5 完成（1）| Review + 导出 |

每步右栏 `PreflightPanel` 实时显示已通过的 check。

## 固定邮箱池格式

Step 05 选择“固定邮箱池”时，默认读取：

- 邮箱池文件：`/opt/444/output/email_pool.txt`
- 取号状态：`/opt/444/output/email_pool_state.json`

`email_pool.txt` 是普通文本文件，一行一个已配置转发的邮箱地址：

```text
# 空行和 # 开头的注释会跳过
alias-001@example.net
alias-002@example.net
alias-003@example.net  # 行尾注释也可以
```

不要用逗号分隔，也不要写 JSON。系统会去重并按顺序取号；`email_pool_state.json` 会自动创建和更新，不需要手工编辑。

## 反向代理（公网访问）

webui 默认 bind `127.0.0.1`。要让其他机器访问，nginx 反代：

```nginx
location /webui/ {
    proxy_pass http://127.0.0.1:8765/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
}
```

## 开发

```bash
# 后端开发模式（auto-reload）
uvicorn webui.server:create_app --factory --reload --host 127.0.0.1 --port 8765

# 前端开发模式（Vite proxy 自动转 /api → 8765）
cd webui/frontend && pnpm dev
# 开 http://127.0.0.1:5173

# 跑测试
python -m pytest webui/tests/ -v       # 后端 47 测试
cd webui/frontend && pnpm test         # 前端 Vitest
```

## 架构

- 后端：FastAPI + SQLite (users + sessions) + JSON (wizard state) + bcrypt + sse-starlette
- 前端：Vue 3 + Vite + TypeScript + Naive UI + Pinia + Vue Router
- 鉴权：cookie session（httponly + SameSite=Lax）
- 启动：单进程 `python -m webui.server`，FastAPI 同时 serve API + 静态前端
