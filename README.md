# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践第 8 题。当前已完成 Phase 2 的代理开发与验证，等待人工审核：系统包含 Flask 基础应用、SQLite 数据结构、服务端 Session、CSRF、演示账号登录/退出，以及学生提交报修、本人列表和权限隔离详情。维修接单、状态流转、确认评价、筛选和统计尚未实现。

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

Phase 2 当前全量回归结果为 `42 passed`；真实进程 HTTP 检查覆盖学生登录、创建工单、列表、详情、另一学生数据隔离，以及停止并重启应用后的工单持久化。详细记录见 `ai_evidence/phase2.md`。

## Phase 2 操作

学生登录后可使用以下页面：

- `/tickets/new`：提交楼栋、宿舍号、故障类型和 5–1000 字符的故障描述。
- `/tickets`：按创建时间倒序查看本人报修，每页 20 条。
- `/tickets/<id>`：查看授权范围内的真实工单详情。

维修人员可访问 `/work-queue` 查看无人接单的待处理工单及本人负责工单。该页面在 Phase 2 中为只读；接单和维修状态按钮将在对应阶段通过审核后实现。

## 当前范围

- 已实现：首页、登录、退出、身份读取、学生/维修员角色入口、健康检查。
- 已实现：非破坏初始化、显式幂等种子、外键与 CHECK/UNIQUE 约束、数据库版本拒绝策略。
- 已实现：学生真实报修、创建请求幂等、本人列表、稳定分页、详情权限隔离和只读维修工单视图。
- 尚未实现：维修接单及状态推进、学生确认和评价、筛选及统计图表。界面不会显示这些功能的虚假按钮或假数据。

详细设计和阶段门槛见 `DESIGN.md`、`AGENTS.md` 和 `PLANS.md`。老师原始要求位于 `宿舍保修管理系统工作说明/`。
