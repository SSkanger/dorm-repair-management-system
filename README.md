# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践第 8 题。Phase 0–3 已通过阶段审核；Phase 4 已实现类型/状态筛选和真实统计，自动化与 HTTP 验证通过，等待用户审核。桌面和手机浏览器视觉检查尚未验证；Phase 5 未开始。

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

Phase 4 开始基线为 `62 passed`，Phase 1–4 当前全量回归结果为 `71 passed`；保留三种真实并发竞争、锁超时、五种动作的事务故障回滚，新增权限范围内组合筛选、分页统计、状态分布及并发读快照验证。详细记录见 `ai_evidence/phase4.md`。

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

## Phase 4 筛选与统计验收

学生在 `/tickets`、维修员在 `/work-queue` 使用类型和状态筛选；`/dashboard` 为相同权限范围的统计页。两个条件同时选择采用 AND；“应用筛选”回到第一页，“清空筛选”恢复授权范围内全部工单，分页链接保留条件。

统计柱状图按类型计数，环形图按状态计数。Chart.js 4.5.1 及许可证保存在 `app/static/vendor/`，无需课堂联网或前端构建。数字表始终可读；无数据时各项为 0。图表实际绘制尚需本机浏览器核验。

1. 按 Phase 3 步骤准备至少两种类型、不同状态的真实工单。
2. 学生分别选择类型、状态及组合条件，核对列表、匹配总数和两张数字表；两表合计应均等于匹配总数。
3. 切换 `student_b`，确认只显示其本人数据；维修员仅能看到待接和本人负责工单及其统计。
4. 在维修员页面接单、开始、完成后刷新统计，核对状态数量；学生确认与评价后数量不变。
5. 选择无匹配条件，核对空提示及全零统计；访问 `/tickets?page=0` 或非法类型应返回 400。
6. 超过 20 条匹配记录时翻页，统计总数应不变。更换条件后应回到第一页。
7. 停止再启动服务，重新登录核对同一批数据；断开外网，验证两图仍可绘制。
8. 在桌面及开发者工具约 390px 宽度检查筛选、长描述、表格、按钮和图例；这些视觉项目当前均为未验证。

真实 HTTP 自检会启动、停止并重启独立应用进程，使用临时数据库和随机密码，不污染运行库：

```powershell
.\.venv\Scripts\python.exe scripts\phase4_http_smoke.py
```

每次页面请求在同一 SQLite 读事务中取得列表、总数及两组聚合。统计覆盖全部匹配记录，而不是当前 20 条；刷新页面后读取最新已提交数据，不使用浏览器缓存数字。

## 当前范围

- 已实现：首页、登录、退出、身份读取、学生/维修员角色入口、健康检查。
- 已实现：非破坏初始化、显式幂等种子、外键与 CHECK/UNIQUE 约束、数据库版本拒绝策略。
- 已实现：学生真实报修、创建请求幂等、本人列表、稳定分页及详情权限隔离。
- 已实现：原子接单、负责人按序维修、学生确认和一次性评价、真实状态时间展示。
- 已实现：类型/状态 AND 筛选、权限范围内两种真实统计、本地图表资源和数字降级表。
- 尚未验证：真实浏览器图表绘制、桌面/手机视觉和人工完整操作；最终交付整理留待获批的 Phase 5。

详细设计和阶段门槛见 `DESIGN.md`、`AGENTS.md` 和 `PLANS.md`。老师原始要求位于 `宿舍保修管理系统工作说明/`。
