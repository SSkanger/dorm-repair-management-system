# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践第 8 题。当前完成 Phase 1：Flask 基础应用、SQLite 数据结构、服务端 Session、CSRF、演示账号登录/退出和角色入口。报修、接单、状态流转、评价、筛选和统计尚未实现。

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

Phase 1 最终回归结果为 `17 passed`；真实进程 HTTP 检查覆盖首页、健康检查、登录、角色入口、退出和退出后访问保护。详细记录见 `ai_evidence/phase1.md`。

## 当前范围

- 已实现：首页、登录、退出、身份读取、学生/维修员角色入口、健康检查。
- 已实现：非破坏初始化、显式幂等种子、外键与 CHECK/UNIQUE 约束、数据库版本拒绝策略。
- 尚未实现：正式业务闭环及统计功能。界面不会显示假工单或假统计。

详细设计和阶段门槛见 `DESIGN.md`、`AGENTS.md` 和 `PLANS.md`。老师原始要求位于 `宿舍保修管理系统工作说明/`。
