# Phase 1 真实开发证据

- 日期：2026-10-23（Asia/Shanghai）。
- 状态：awaiting_user_review。Phase 1 实现和代理验证已完成，尚未获得用户人工验收；Phase 2 未获授权。
- Prompt 来源：本次 Codex 对话用户消息。用户明确批准 Phase 1，要求先修订根规则路径、CSRF/认证错误顺序和接单隐私边界，再实现 Flask 工程、完整 schema、两角色认证、服务端 Session、CSRF、基础页面及实际测试。本文件是忠实阶段记录，不替代完整原始对话导出。

## 设计修订

1. 从资料包复制 AGENTS.md、PLANS.md 到项目根目录，保留原件；根文件中的资料路径改成实际存在的嵌套路径。
2. DESIGN.md 更新为 Phase 0 已批准，固定 CSRF 缺失/无效400、合法Token后未登录401、错角色403。
3. 接单隐私固定为：不可见或被他人接走后不可见返回404，当前仍可见资源的业务冲突返回409；A15/A17/A21预期同步修订并留有第13节变更记录。

## 技术选择与实际版本

- Flask 3.1.3、Flask-Session 0.8.0、Flask-WTF 1.3.0、CacheLib 0.14.0。
- Flask-Session 使用 `SESSION_TYPE=cachelib` 和 CacheLib FileSystemCache；序列化显式选择 JSON。登录调用公开的 `app.session_interface.regenerate(session)` 轮换 Session ID。
- Flask-WTF CSRFProtect 全局启用，测试也不关闭。依赖 API 先对照 Flask-Session 0.8.0、Flask-WTF 1.3.x 官方文档及 PyPI 发布信息核实，再在本地安装验证。
- SQLite 业务库采用 `PRAGMA user_version=1`，外键/忙等待每连接开启；已有未知表或不兼容版本会拒绝初始化，不执行 DROP。

## 创建和修改的文件

- 根目录规则和文档：AGENTS.md、PLANS.md、DESIGN.md、README.md、.gitignore、.env.example、requirements.txt、requirements-dev.txt。
- 应用：run.py，app/__init__.py、db.py、schema.sql、auth.py、pages.py，四个页面模板及 static/css/app.css。
- 测试：tests/conftest.py、test_app.py、test_auth.py、test_database.py、test_cli.py、tests/__init__.py。
- 验证：scripts/http_smoke.py、ai_evidence/phase1.md、ai_evidence/phase1/test_runs.txt。

本阶段没有创建报修、接单、状态推进、确认评价、筛选或统计路由；没有生成虚假业务工单。浏览器页面明确标注这些功能尚未开放。

## 真实错误与修复

1. 首次 pytest：`7 failed, 9 passed in 22.08s`。所有失败发生在合法 CSRF 请求。根因是将 `WTF_CSRF_TIME_LIMIT` 配成 `timedelta(hours=2)`；Flask-WTF 1.3.0 将其直接交给 itsdangerous 的 `max_age`，后者用整数秒比较，产生 TypeError。改为整数 `7200` 后回归为 `16 passed in 24.47s`。
2. 后续隔离审查发现应用工厂在测试配置覆盖前创建默认 instance 密钥/Session 文件。没有业务数据被污染，但违背完全隔离目标。调整配置顺序：先应用 test_config，再创建指定的数据库、Session 和必要密钥；增加隔离测试。最终回归时默认 instance 文件在测试前后名称、大小和时间状态一致，证明测试未再触碰默认存储。
3. 初始 schema/认证/CLI/HTTP 测试没有发现需降低断言的失败；所有修复均保持既定预期。

## 实际测试和结果

完整摘要见 `ai_evidence/phase1/test_runs.txt`。

- `.venv\Scripts\python.exe -m pytest -q`：最终 `17 passed in 66.74s`，退出码0。
- `.venv\Scripts\python.exe -m compileall -q app tests scripts`：无输出，退出码0。
- 隔离临时目录真实运行 `flask init-db`：输出“数据库初始化完成（版本 1）”。
- 同一临时目录真实运行 `flask seed-demo`：输出“演示账号准备完成；已有匹配账号保持不变”。
- 启动 `python run.py` 后运行 HTTP smoke：主页200、health200、登录页200、维修员登录303、portal200、退出303、退出后portal302；输出 `HTTP smoke passed`，退出码0。
- 使用真实浏览器查看默认桌面宽度：首页、登录页、学生入口布局正常；用 student_a 实际登录后显示“学生甲 · 学生”和学生入口。临时设置390×844视口检查，导航与入口内容可读且无水平溢出，随后恢复默认视口。

## 已验证范围

应用工厂和启动、首页/登录/health、两种账号、错误密码、密码散列、GET登录保护、错角色403、CSRF错误顺序、Session ID轮换、旧ID重放无效、退出后旧会话无效、服务端Session文件、SQLite外键/CHECK/UNIQUE、非破坏初始化、不兼容版本拒绝、种子幂等且不覆盖密码/数据、重新连接持久化、两个测试库和Session目录隔离。

## 尚未完成与风险

- Phase 2–5 所有业务功能未实现，A03–A23中涉及工单的场景仍为NOT_RUN。
- 浏览器实际操作覆盖了学生登录及响应式显示；维修员登录通过真实HTTP和pytest验证，但未再做一套重复的浏览器截图流程。
- 本地 HTTP 使用 `SESSION_COOKIE_SECURE=False`；只有部署 HTTPS 并设置 `DORM_REPAIR_COOKIE_SECURE=1` 才启用 Secure Cookie。
- CacheLib 文件存储适合本课程单机演示，不声称适合多实例生产部署。
- 最早一次测试在配置顺序修复前生成了 gitignored 的 `instance/secret_key` 和匿名Session缓存；最终回归证明测试已不再触碰它们。该目录本来也是正常本地运行目录，不含业务数据库或演示密码。
- 未创建 Git 提交、未推送远程、未导出完整对话、未录制视频；不声称这些事项完成。

## 人工审核门槛

用户可按 README 在 Windows 本机新环境安装，运行 init-db、交互式 seed-demo、启动、分别登录学生/维修员并运行 pytest。收到用户明确通过 Phase 1 前，不进入 Phase 2。

