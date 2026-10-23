# Phase 3 AI 辅助开发证据

日期：2026-10-23（Asia/Shanghai）。状态：代理实现与验证完成，阶段报告已通过用户初步审核，本轮已明确获准复测后 Git 提交与推送。真实浏览器人工检查仍为未验证。

## 1. 真实任务来源及阅读

来源为本聊天中用户的 Phase 3 完整请求，忠实摘录：

> 现在我正式批准进入 Phase 3：维修接单、状态流转、学生确认与评价。
> 本阶段必须让这些操作通过真实 Web 页面和服务端业务逻辑执行。
> 并发测试使用同一个临时 SQLite 文件及独立数据库连接。
> Phase 3 结束后停止，等待我审核。不要自行进入 Phase 4，也不要未经我确认创建 Git Commit 或推送远程仓库。

这是关键 Prompt 摘录及来源说明，不是完整原始对话导出。用户仍需保留实际聊天导出及自行录制演示视频。

实际读取根目录 AGENTS.md、PLANS.md、DESIGN.md，资料包 docs/01–05、fixture、原 Word 正文和第 8 题要求，复核已提取的评分图；读取现有 auth/db/tickets/services/queries 和模板及相关测试。原 Word 首次终端输出编码乱码，使用 PYTHONIOENCODING=utf-8 重新提取可读正文；未更改 Word。正式要求、课堂补充及工程决定仍按 DESIGN 分类。

Git 开发前检查：main 工作区干净，与 origin/main 同步；基线 `aa24e768f91aed112fc9de447b6b9f866b737b66`。

## 2. 预先固定的验收与隐私规则

A06–A09：接单、按序开始/完成、学生确认、确认后一次性评价真实落库。A15–A21：禁止重复接单、跳级、回退、越权、非法评分、过早或重复确认评价；E07：并发确认/评价只一次成功；E08：锁超时或事务故障503、业务全字段不变。

资料包 A15 笼统要求“业务冲突提示”，批准后的 DESIGN 3.3 已明确：别人接走后无权查看为404，本人重复接单为409。fixture S05/S09 只要求拒绝和业务数据不变，没有规定409。因此实施前固定并发接单一个303、另一个404；确认/评价并发一个303、另一个409。保留资料包原件，不根据实现结果修改正确断言。

## 3. 文件与关键实现

- app/services.py：新增 apply_ticket_action；服务层验证角色、可见性、前置状态和输入；BEGIN IMMEDIATE、条件 UPDATE、rowcount、COMMIT/rollback。
- app/tickets.py：五个 POST 动作，303 PRG，友好400/403/404/409/503；评分错误保留短评；北京时间显示过滤器。
- app/queries.py：在授权查询中附加负责人展示名，不展示登录名或密码信息。
- 工单详情/表格/维修列表、portal/base 和 CSS：真实接单、开始、完成、确认、评分表单，显示时间与负责人及评价；依赖服务端独立验证。
- tests/test_workflow.py：完整 Web 闭环、独立历史时间 fixture、全字段不变、合法/非法评分、CSRF和权限、事务故障与锁超时。
- tests/test_concurrency.py：ThreadPoolExecutor + Barrier，同一临时文件库、独立连接和已认证客户端；验证唯一赢家和最终负责人/确认/评分，失败操作无额外字段变化。
- scripts/phase3_http_smoke.py：随机凭据与临时存储，真实 Flask 子进程及 HTTP 闭环，停止再以新进程、新 Session 目录/密钥重启，对比全部业务字段。
- README/DESIGN/PLANS：同步本阶段功能和审核门槛；本文件和 phase3/ 存储真实验证证据。

## 4. 帮助课程讲解的技术说明

接单必须原子：两名维修员可能同时看到 PENDING。先查后无条件更新会造成后者覆盖前者。BEGIN IMMEDIATE 串行化 SQLite 写入，条件 UPDATE 再要求 PENDING 且无负责人，只有更新一行且提交成功才算接单成功。后来的竞争者重新读取时已无权查看，返回404。

按钮控制只是体验：用户可以手动构造 POST 或使用旧页面。后端从 Session 加载用户，每次验证角色、归属/负责人和当前状态；SQL 再次带同样前置条件。

确认和评价是完成后的学生反馈：维修员的 COMPLETED 表示维修完成，学生确认写 confirmed_at，评价写 rating/review_text/reviewed_at；状态始终是 COMPLETED，不添加额外状态，也不开放回退或重开。

失败不影响旧数据：状态和对应时间在同一 UPDATE、同一事务写入。校验或状态冲突直接 rollback；数据库异常也 rollback，直到 COMMIT 成功才反馈成功。测试注入真实 UPDATE 后失败与提交失败，逐字段检查回滚结果。

越权隔离：学生只有本人 student_id；维修员仅看待处理无人负责单和本人 assignee_id。开始/完成还必须是负责人。跨学生、他人已接单统一404；角色错误403；无效 CSRF400优先；合法 CSRF 后未登录401。错误页面不泄露另一个负责人的身份。

## 5. 真实命令与结果

开发前：`.\.venv\Scripts\python.exe -m pytest -q`，退出码0，`42 passed in 77.18s (0:01:17)`。

首轮专项：`.\.venv\Scripts\python.exe -m pytest -q tests/test_workflow.py tests/test_concurrency.py`，退出码0，`11 passed in 30.82s`。原始输出见 phase3/first_tests.txt。

真实 HTTP：`.\.venv\Scripts\python.exe scripts/phase3_http_smoke.py`，退出码0：

```json
{"workflow": "passed", "atomic_fields": "passed", "private_rejections": [404, 404], "illegal_transition": 409, "duplicate_review": 409, "restart_new_process": true, "restart_all_fields_equal": true, "rating": 5}
```

`Phase 3 real HTTP and process restart passed`。原始输出见 phase3/http_restart.txt。隔离数据库在临时目录，结束后清理；实际运行数据库未被重置。

首轮全量：`.\.venv\Scripts\python.exe -m pytest -q`，退出码0，`53 passed in 108.05s (0:01:48)`；原始输出见 phase3/regression_tests.txt。

扩展五种动作各自的 UPDATE 后失败/COMMIT 失败，以及缺少/重复评分、短评脚本转义后最终全量回归：

```text
.\.venv\Scripts\python.exe -m pytest -q
..............................................................           [100%]
62 passed in 126.34s (0:02:06)
```

退出码0，原始输出见 phase3/final_tests.txt。没有失败测试，不删除用例、不降低断言。

`.\.venv\Scripts\python.exe -m compileall -q app scripts tests` 退出码0，无输出。`flask --app run:app routes` 退出码0，确认五个新动作只允许POST，没有任意状态写接口。`git diff --check` 退出码0，只有本地LF/CRLF转换提示。敏感密钥格式和个人绝对路径扫描无匹配（rg退出码1表示未发现匹配）；数据库、Session及原始课程资料仍按 .gitignore 排除。

## 6. 真实问题、修复及未验证

- 当前专项测试没有失败，未删除测试或降低断言；进一步扩展所有五种动作的 UPDATE 后失败和 COMMIT 失败场景。
- 现有 Phase 2 详情只有“已有负责人”的笼统提示，Phase 3 增加授权范围内的维修员展示名和时间节点；保持两张业务表，无数据库迁移。
- 浏览器工具实际返回 `Browsers: Error: Local browser use is disabled in Work settings`。桌面/390px 真实视觉、触控及人工按钮操作继续标为 **未验证**；HTTP/模板断言不能替代此检查。
- 开发结束时未创建本阶段 Commit、未推送；用户随后授权本轮版本保存，见下节。未进入 Phase 4，筛选/图表未实现。
- 最终真实 AI 对话导出、用户演示视频尚未交付；阶段总结不冒充这两项材料。

## 7. 用户授权版本保存

用户在本聊天中明确说明 Phase 3 报告通过初步审核，要求重新运行完整 pytest，通过后以 `feat: implement repair workflow and student reviews` 提交并普通推送至 origin/main，不得 force push，浏览器未验证状态保持不变。

提交前本地位于项目根目录，分支 main，基线为 `aa24e768f91aed112fc9de447b6b9f866b737b66`；origin fetch/push 均为 `https://github.com/SSkanger/dorm-repair-management-system.git`。检查差异未发现删除前两阶段功能、修改其已批准业务规则或修改数据库结构。忽略规则排除运行库、Session、密钥、虚拟环境、缓存、原始课程资料及原始对话导出。初次远程查询遇到 github.com:443 连接失败，将在本地复测和提交后重试正常推送。

本轮提交前完整回归：`.\.venv\Scripts\python.exe -m pytest -q`，退出码0，`62 passed in 130.40s (0:02:10)`；原始输出保存在 phase3/precommit_tests.txt。暂存差异检查及高风险密钥格式/个人绝对路径扫描未发现问题；浏览器人工视觉检查继续为 **未验证**。
