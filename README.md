# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践第 8 题。Phase 0–2 已通过审核；Phase 3 已完成代理实现与验证，等待人工审核：学生报修、维修接单、开始和完成维修、学生确认与一次性评价。筛选和统计留待 Phase 4。

## 环境与安装

需要 Python 3.10 或更高版本；Phase 1 已在 Python 3.12.14 上验证。以下命令在 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

依赖锁定为 Flask 3.1.3、Flask-Session 0.8.0、Flask-WTF 1.3.0 和 CacheLib 0.14.0。Session 数据保存在服务器文件目录中，浏览器 Cookie 只保存随机 Session ID。

## 初始化与演示账号

首次运行前：

```powershell
$env:FLASK_APP = "run:app"
.\.venv\Scripts\flask.exe init-db
.\.venv\Scripts\flask.exe seed-demo
```

`seed-demo` 会安全提示输入一个不少于 8 位的演示密码，并创建 student_a、student_b、repairer_a、repairer_b。密码只以 Werkzeug 散列保存。重复执行不会改已有匹配账号的密码，也不会创建业务工单。

数据库默认位于 `instance/dorm_repair.sqlite3`。可通过 `DORM_REPAIR_DATABASE` 指定其他路径；Session 目录可通过 `DORM_REPAIR_SESSION_DIR` 指定。`instance/`、`.env`、数据库、Session 和密钥均被 Git 忽略。

## 启动

```powershell
.\.venv\Scripts\python.exe run.py
```

浏览器访问 `http://127.0.0.1:5000/`，健康检查为 `http://127.0.0.1:5000/health`。本地 HTTP 演示默认不设置 Secure Cookie；部署到 HTTPS 时设置 `DORM_REPAIR_COOKIE_SECURE=1`。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

测试使用 pytest 提供的临时目录作为数据库和 Session 存储，不接触默认运行数据库。CSRF 在测试中保持开启。

Phase 1–3 当前全量回归结果为 `62 passed`；覆盖三种真实并发竞争、锁超时、全部五种动作的事务故障回滚，以及已有身份/报修回归。真实 HTTP 脚本已验证完整闭环和进程重启后的全字段持久化。详细记录见 `ai_evidence/phase3.md`。

## Phase 2 操作

学生登录后可使用以下页面：

- `/tickets/new`：提交楼栋、宿舍号、故障类型和 5–1000 字符的故障描述。
- `/tickets`：按创建时间倒序查看本人报修，每页 20 条。
- `/tickets/<id>`：查看授权范围内的真实工单详情。

维修人员可访问 `/work-queue` 查看无人接单的待处理工单及本人负责工单。可在列表或详情接单，在本人详情中点击“开始维修”“完成维修”。其他维修员已接走的工单不可见。

## Phase 3 操作与验收

1. `student_a` 登录，提交一张报修，记下工单编号。
2. 退出后以 `repairer_a` 登录，从“维修工单”接单，在详情依次开始、完成维修。
3. `repairer_b` 访问该单应为 404，不能覆盖负责人。
4. `student_a` 重新登录，检查负责人、维修时间，点击“确认完成”，再提交 1–5 分及可选短评。
5. 评价后为只读结果；`student_b` 不可查看、确认或评价该工单。
6. 停止服务后重新运行，重新登录检查原工单、负责人、确认时间、评分和短评仍存在。

所有动作只接受带合法 CSRF 的 POST。本人可见资源的状态冲突返回 409；不存在或无权访问返回 404；合法 CSRF 后未登录返回 401、角色不符403；无效 CSRF 优先返回400。确认和评价不新增工单状态，工单仍为 COMPLETED。

真实进程闭环及重启自检（使用随机密码、独立临时数据库和 Session，不修改运行库）：

```powershell
.\.venv\Scripts\python.exe scripts\phase3_http_smoke.py
```

桌面和约 390px 手机宽度的真实浏览器检查尚未验证；当前 Work 设置禁用了本地浏览器工具，需要本机按以上步骤检查按钮、错误反馈和页面布局。

## 当前范围

- 已实现：首页、登录、退出、身份读取、学生/维修员角色入口、健康检查。
- 已实现：非破坏初始化、显式幂等种子、外键与 CHECK/UNIQUE 约束、数据库版本拒绝策略。
- 已实现：学生真实报修、创建请求幂等、本人列表、稳定分页及详情权限隔离。
- 已实现：原子接单、负责人按序维修、学生确认和一次性评价、真实状态时间展示。
- 尚未实现：类型/状态筛选及统计图表。

详细设计和阶段门槛见 `DESIGN.md`、`AGENTS.md` 和 `PLANS.md`。老师原始要求位于 `宿舍保修管理系统工作说明/`。
