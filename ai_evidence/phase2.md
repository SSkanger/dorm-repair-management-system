# Phase 2 AI 辅助开发记录

日期：2026-10-23（Asia/Shanghai）  
阶段状态：代理实现及验证完成；用户已审阅报告并原则上批准 Git 提交与推送。浏览器视觉检查仍为未验证。

## 1. 任务与 Prompt 来源

用户明确批准进入 Phase 2，并要求只实现“学生提交报修 → SQLite 存储 → 本人列表 → 权限隔离详情”。用户给出的关键要求包括：

- `GET/POST /tickets/new`，字段和长度遵循已批准的 `DESIGN.md`；成功后 HTTP 303 到详情。
- `student_id` 从当前 Session 读取，状态和负责人等受信任字段不能由客户端决定。
- CSRF Token 与业务 `submission_token` 分离；同 Token 同规范化内容重传返回原工单，不同内容返回 409；非法表单不消耗 Token。
- `GET /tickets` 仅显示当前学生数据，每页 20 条，按 `created_at DESC, id DESC` 排序。
- 学生越权和不存在详情均返回 404；维修人员仅可读取批准的可见范围，本阶段不允许接单或推进状态。
- 执行 Phase 1 回归、本阶段 pytest、真实服务和重启持久化验证；浏览器受限时必须标明未验证。

实现前实际阅读了根目录 `AGENTS.md`、`PLANS.md`、`DESIGN.md`，资料包 `docs/01_TOPIC8_PRODUCT_SPEC.md`、`02_STATE_AND_PERMISSIONS.md`、`03_ACCEPTANCE_MATRIX.md`、`04_AI_DEVELOPMENT_EVIDENCE.md`、`fixtures/acceptance_cases.json`，以及现有 `app/`、`tests/`。未发现需要推翻 Phase 1 架构的冲突。

## 2. 实际修改与作用

- `app/tickets.py`：表单、会话绑定的 submission_token、学生创建/列表/详情、维修人员只读列表、页码校验及角色权限。
- `app/services.py`：规范化工单输入；使用 `BEGIN IMMEDIATE`、唯一键和内容比对完成创建事务与幂等重放；SQLite 失败统一回滚并转为友好错误。
- `app/queries.py`：学生和维修人员可见范围、稳定分页、权限条件内的详情查询。
- `app/__init__.py`：注册 tickets 蓝图，补充 409、503 错误处理。
- `app/templates/tickets/`：新增创建表单、学生列表、维修只读列表、分页、详情页面。
- `app/templates/base.html`、`portal.html`、`app/static/css/app.css`：按角色显示真实导航，增加表单、表格、状态标签、详情和移动宽度样式。
- `tests/test_tickets.py`：覆盖创建、归属、字段边界、CSRF/认证/角色优先级、幂等、越权、XSS 转义、分页、持久化和数据库错误展示。
- `scripts/phase2_http_smoke.py`：通过真实 HTTP 服务验证创建、列表、详情、学生隔离和进程重启后的持久化。
- `README.md`、`DESIGN.md`、`PLANS.md`：同步实际范围、路由、验证结果和审核门槛。

## 3. 关键实现选择

1. 创建表单每次 GET 生成随机 submission_token，Session 仅保留最近 10 个标识。标识在字段校验失败后仍可使用；成功重传通过数据库行内容判断是安全重放还是冲突。
2. 创建事务先执行 `BEGIN IMMEDIATE`，在同一事务检查 `(student_id, submission_token)`，再插入固定 `PENDING` 工单。事务失败调用 rollback，页面返回 503，不显示未处理的 500。
3. 客户端若附加 `student_id`、`status`、`assignee_id` 等未允许字段，请求直接返回 400。真正的归属、初始状态、负责人及时间仍完全由服务端产生。
4. 学生详情 SQL 同时限制 `id` 和当前 `student_id`，因此他人数据和不存在资源统一为 404。维修人员范围使用完整括号：无人负责的 PENDING，或本人负责的工单。
5. Phase 2 实现只读 `/work-queue` 以验证维修人员可见范围，没有添加接单、开始或完成写接口。

## 4. 实际命令与结果

开发前仓库检查：

```text
git status --short --branch
## main...origin/main

git log -1 --oneline --decorate
8c4b718 (HEAD -> main, origin/main) feat: complete phase 1 foundation and authentication
```

Phase 1 基线：

```text
.\.venv\Scripts\python.exe -m pytest -q
17 passed in 53.61s
```

首次 Phase 1+2 全量回归：

```text
.\.venv\Scripts\python.exe -m pytest -q
38 passed in 70.48s (0:01:10)
```

补充楼栋/宿舍号上限、非法业务 Token、越界分页和超大整数参数后最终回归：

```text
.\.venv\Scripts\python.exe -m pytest -q
42 passed in 95.19s (0:01:35)

.\.venv\Scripts\python.exe -m compileall -q app scripts tests
退出码 0，无输出
```

真实进程首次创建验证：

```text
.\.venv\Scripts\python.exe scripts\phase2_http_smoke.py --password <测试密码>
{'mode': 'create', 'ticket_id': 1, 'student_a_detail': 200, 'student_b_detail': 404, 'isolation': 'passed'}
Phase 2 HTTP smoke passed
```

停止 Flask 进程后，使用同一 SQLite 文件和新的 Session 目录重新启动，再次验证：

```text
.\.venv\Scripts\python.exe scripts\phase2_http_smoke.py --password <测试密码> --verify-ticket 1
{'mode': 'restart-verification', 'ticket_id': 1, 'student_a_detail': 200, 'student_b_detail': 404, 'isolation': 'passed'}
Phase 2 HTTP smoke passed
```

两次服务均通过 Ctrl+C 主动停止，因此服务进程退出码为 1；这是人工停止开发服务器的结果，不是 HTTP 验证失败。隔离运行库位于被 `.gitignore` 排除的 `instance/`，未写入默认课程演示数据库。

## 5. 真实问题和处理

- 没有出现 pytest 失败，未删除测试或降低断言。
- 首次代码审查发现若在 `form.validate()` 前手动追加 submission_token 错误，WTForms 校验过程会重建错误列表。实现调整为先执行字段校验、再追加会话 Token 错误，并增加缺失/伪造业务 Token 的回归测试。
- 分页自查发现超出末页时原模板会显示成“从未有工单”的空态。现区分总数为 0 和页码超范围，并提供返回最后一页的链接；同时限制超大页码和工单 ID，避免 SQLite 整数绑定溢出成为 500。
- Flask CLI 初始化中文输出在当前 PTY 中出现编码乱码，但命令退出码为 0，随后健康检查、登录和数据库操作均通过；未把乱码文本作为功能断言。
- 尝试使用 computer-use 打开 `http://127.0.0.1:5000/login` 时，工具返回 `Local browser use is disabled in Work settings`。因此未声称完成真实浏览器视觉验收。

## 6. 尚未验证与当前边界

- 桌面约 1366px、手机约 390px 的真实浏览器视觉和触控操作：**未验证**，需要用户本机检查。
- Phase 3 的接单、状态推进、学生确认和评价：未实现。
- Phase 4 的故障类型/状态筛选和统计图表：未实现。
- 开发结束时尚未创建 Commit、未推送；随后用户明确授权本轮复测后提交并推送，见下节。Phase 3 未获执行授权。

## 7. 版本提交授权与检查

用户在本聊天中明确要求：重新执行 Phase 1+2 全部自动化测试，通过后以 `feat: implement student repair requests and ticket management` 创建提交并普通推送至已有 `origin/main`；不得 force push，浏览器未验证状态必须保留。

提交前确认项目根目录正确，当前分支为 main，本地与远程基线均为 `8c4b718cacd33917da3125c447f29d4f73a2725d`。`.gitignore` 已排除虚拟环境、运行数据库、Session、缓存、原始课程资料和含隐私风险的原始对话导出。待提交文件检查未发现实际密码、密钥、Cookie 或运行数据；自动化测试专用值不用于实际运行配置。

本轮提交前真实复测命令：`.\.venv\Scripts\python.exe -m pytest -q`，退出码 0，输出：`42 passed in 125.98s (0:02:05)`。暂存文件共 19 个，仅含代码、模板、样式、测试、HTTP 验证脚本和开发文档。浏览器视觉检查继续保留“未验证”，本轮未重新执行浏览器验证。

