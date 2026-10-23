# Phase 4：工单筛选、统计、异常回归与界面

日期：2026-10-23。状态：已获本阶段开发授权；代码、自动化和真实 HTTP 验证已完成，等待用户审核。真实浏览器视觉检查未验证。没有创建本阶段 Git Commit、推送或执行 Phase 5。

## 1. 真实任务来源与依据

来源为本聊天用户消息“我已经手动推送，进行下一步工作”，随后明确批准 Phase 4。关键 Prompt 忠实摘录：

> 在已有学生工单列表及维修人员工作台中实现故障类型与工单状态筛选。
> 列表、总数和两种图表应复用同一套授权与过滤条件。
> 优先使用 DESIGN.md 约定的同一数据库读快照。
> Chart.js 优先使用项目本地静态资源。
> 不得使用“pytest 通过”替代真实图表渲染验证。
> 未经我确认，不创建 Git Commit，不推送远程仓库。

这是来源明确的摘录，不是完整原始 AI 对话导出，不包含私人账号密码或 Cookie。原始对话及最终视频尚未作为交付文件提供。

读取根目录规则、计划与批准设计；核对资料包正式 Word 的通用要求和第8题正文，及专项需求、权限、验收矩阵、AI过程要求。正式要求为按类型/状态查询和至少一种真实统计；两图、同一读快照、20条分页和本地 Chart.js 是批准的工程实现方案，不冒称老师额外规定。

Git 检查：本地 main 的 Phase 3 HEAD 为 `d4a45b16bce4838f9bd4ab7acfb03edfe8d808cb`，开始时工作区干净。origin 为项目既有 GitHub 仓库。虽然用户说明手动推送，实际 `git ls-remote origin refs/heads/main` 当次返回 `aa24e768f91aed112fc9de447b6b9f866b737b66`，与本地 HEAD 不同；如实报告此差异，不宣称同步，也不在本阶段代为提交或推送。

## 2. 实际文件修改

- `app/constants.py`：统一五种故障类型和四种状态；services/tickets 复用，原业务规则不变。
- `app/queries.py`：参数白名单、授权谓词、AND 条件、稳定分页、同快照聚合及补零。
- `app/tickets.py`：学生列表及维修工作台共用筛选视图上下文，分页保留条件。
- `app/dashboard.py`、`app/__init__.py`：受登录保护的统计页和查询错误400提示。
- `app/templates/tickets/filters.html`、`statistics.html`、`dashboard.html`：筛选、两种统计、可读数字表及空状态。
- 既有列表、工作台、分页、base、index 模板：复用组件、导航、授权范围和当前功能提示。
- `app/static/css/app.css`、`app/static/js/charts.js`：响应式筛选/图表布局、柱状/环形图初始化和降级提示。
- `app/static/vendor/`：Chart.js 4.5.1 UMD、source map、MIT许可证及来源说明。
- `tests/test_queries_stats.py`：9项专项用例，含参数化错误输入、独立固定数据和并发读快照。
- `tests/test_tickets.py`：旧阶段将 status 查询视为不支持；本阶段按已批准新增功能改为显式验证合法 status=200，其他非法参数断言保留，不降低权限或业务断言。
- `scripts/phase3_http_smoke.py`：保留默认原行为，可选增加筛选统计断言；`scripts/phase4_http_smoke.py` 调用扩展验证。
- README、DESIGN、PLANS、本记录及 `phase4/` 实际输出：更新阶段进度、复现方式及验证边界。

## 3. 查询与统计实现及取舍

`parse_filters` 只允许 category、status、page，各参数只出现一次。类型/状态为空表示全部，否则严格属于批准枚举。页码要求正整数且限制文本长度和 SQLite OFFSET 范围，拒绝未知/重复/注入式输入、超长整数和非ASCII数字，返回400明确提示。

`visible_scope` 对学生返回 student_id 条件；维修员返回带括号的“无人负责的 PENDING 或本人负责”条件，之后 AND 类型/状态。用户ID来自 g.user，值使用SQL参数绑定，不从查询参数接受身份。详情也复用同一可见范围。

`ticket_overview` 在同一连接显式 BEGIN，依次读取 COUNT、当前页、按类别分组、按状态分组，完成后 COMMIT，异常 ROLLBACK。两组聚合没有 LIMIT/OFFSET；枚举预置0，只有查询到的计数覆盖它。因此总数等于两表各自的和。

1. 列表与统计必须共享权限和筛选，否则会出现列表不可见但统计泄露数量，或选中类型后图仍显示别的类型的矛盾。
2. 分页是显示窗口；25条匹配记录即使第2页只显示5条，匹配总数和图表仍为25。
3. 维修员只统计可见范围。他人接走后该工单从其列表和统计同时消失，不能通过图表侧推无权访问数据。
4. 页面刷新会建立新的读快照，读取已提交状态。PENDING→ACCEPTED→IN_PROGRESS→COMPLETED改变分布；确认和评价只写时间/评分，不改变COMPLETED统计。

不引入新表、缓存统计、管理员、SPA、预测或AI API。生产仍使用原数据库日志模式；只有隔离测试切换WAL以允许在一次读请求的多个SELECT之间提交并发写入，验证统计与列表共享旧快照。

图表使用本地 Chart.js 4.5.1，官方 npm 元数据中的 SHA-512 integrity 与下载tarball核对后提取分发文件。UMD文件 SHA-256：`48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a`。保留许可证和source map。参考官方文档：

- https://www.chartjs.org/docs/latest/charts/bar.html
- https://www.chartjs.org/docs/latest/charts/doughnut.html
- https://www.chartjs.org/docs/latest/configuration/responsive.html

数字表始终显示，不依赖JS；零数据不创建误导性空图。使用独立容器和固定高度以适应响应式图表，桌面两列、窄屏单列。显式序列数组保证Jinja JSON键排序不会改变枚举展示顺序。

## 4. 实际命令与结果

以下均实际执行，退出码0；测试临时数据库和Session与运行库隔离，CSRF未关闭。

| 命令 | 实际结果 | 原始输出 |
|---|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q`（开始基线） | 62 passed in 125.46s | 本次工具输出；未另存基线文件 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_queries_stats.py` | 9 passed in 22.60s | `phase4/first_tests.txt` |
| `.\.venv\Scripts\python.exe scripts/phase4_http_smoke.py` | 筛选/授权统计/本地资源/闭环/重启通过 | `phase4/http_restart.txt` |
| `.\.venv\Scripts\python.exe -m pytest -q`（全量回归） | 71 passed in 158.10s (0:02:38) | `phase4/regression_tests.txt` |
| `.\.venv\Scripts\python.exe -m compileall -q app scripts tests` | 无输出 | 本次工具输出 |
| `node --check app/static/js/charts.js` 及本地vendor JS | 两个均无输出 | 本次工具输出 |

全量输出通过 PowerShell `Tee-Object` 保存，pytest最终退出码为0。实际结果：

```text
.......................................................................  [100%]
71 passed in 158.10s (0:02:38)
```

真实进程HTTP输出：

```text
Phase 4 filters, scoped statistics, local assets and restart passed
{"workflow": "passed", "atomic_fields": "passed", "private_rejections": [404, 404], "illegal_transition": 409, "duplicate_review": 409, "restart_new_process": true, "restart_all_fields_equal": true, "rating": 5}
Phase 3 real HTTP and process restart passed
```

HTTP脚本实际启动临时服务，学生创建两类工单、维修接单/推进、他人不可见、原学生确认5分评价；逐次检查独立确定的类型/状态计数；校验组合/无匹配/非法参数/本地JS的HTTP响应，停止并以新进程启动后再次核对同一数据及统计。不将这些请求称为浏览器人工操作。

## 5. 发现与修复

- 查询设计审查发现大数字页码可能触发 Python int 转换长度限制；转换前限制长度，再校验OFFSET，专项覆盖5000位输入。属于审查中防范，未编造一次实际失败测试。
- JSON序列化可能排序键，因此给图表额外提供明确类别/状态顺序。
- 首页还保留早期“业务尚未开放”说明，按已经实现的真实功能更正。
- 专项和全量本次均通过，没有失败pytest记录；不为制造Bug证据而伪造失败，不删除或降低正确断言。
- 既有事务、角色、CSRF、并发接单、非法流转、评分和持久化回归全部保留。

## 6. 覆盖与未验证项

| 验收项 | 本阶段证据与状态 |
|---|---|
| A10 | 单条件、AND、清空、分页保留、无匹配，pytest及HTTP通过 |
| A11 | 故障类型真实聚合、零补齐、全部分页、独立固定期望通过 |
| A12 | 四状态逐次分布、确认/评价不变、接单后的授权范围变化通过 |
| A22 | 非法类型/状态/页码、重复及未知参数、注入式输入400通过 |
| A23 | 跨学生/维修员数量和详情隔离、已有全部安全回归通过 |
| A26 | 页面组件/本地资源及HTTP已检查；真实视觉、桌面/390px、图表绘制和人工交互未验证 |
| E06 | 25条分页不截断统计通过；额外同一次请求并发读快照通过 |
| E10 | 无数据全零、本地静态资源HTTP200通过；断网后浏览器图表实际绘制未验证 |

真实浏览器工具调用返回 `Browsers: Error: Local browser use is disabled in Work settings`，没有可用浏览器面板。未绕过设置，未声称截图、图表渲染、人工操作通过。请用户按README的Phase4步骤在Windows本机补验桌面/手机、离线图表及完整流程。

Phase 4 实现等待用户审核。最终交付材料、完整对话导出及演示视频不在本轮整理；Git远程是否已包含Phase3需后续版本保存时重新核对，不在此轮修改历史或推送。

收尾检查：`git diff --check` 退出码0，仅Windows LF/CRLF转换提示；检查改动未删除既有业务动作或修改状态/权限规则。对本次应用、测试、脚本及文档扫描高风险凭据格式和个人绝对路径，无匹配；`git ls-files` 未发现运行数据库、`.env`、instance或虚拟环境文件。`.gitignore` 继续排除运行库、Session、虚拟环境、缓存、密钥、原始课程资料和原始对话导出；本次没有暂存或提交文件。

## 7. 用户授权的 Phase 4 版本保存

用户随后在本聊天明确说明“阶段报告通过初步审核”，授权重新核对历史、安全检查及全量pytest，通过后以 `feat: implement ticket filtering and analytics dashboard` 提交并在安全、历史确认条件满足时普通推送 main；不允许 force push、重置或自动变基，不执行Phase5。此前“未获提交授权”等内容是开发结束时的历史状态，以本节后续实测为准。浏览器视觉仍未验证。

项目根目录、分支 main、origin fetch/push地址与用户指定仓库一致。开始时本地HEAD为 `d4a45b16bce4838f9bd4ab7acfb03edfe8d808cb`，缓存origin/main为 `aa24e768f91aed112fc9de447b6b9f866b737b66`，`git rev-list --left-right --count origin/main...main` 为 `0 1`；包含Phase1、Phase2、Phase3完整历史。

本轮三次 `git fetch origin` 均退出1，报 `Failed to connect to github.com port 443`；一次GitHub API ref查询也发生TLS handshake timeout。随后 `gh api repos/SSkanger/dorm-repair-management-system/branches/main --jq .commit.sha` 实际成功，返回与缓存相同的 `aa24e768f91aed112fc9de447b6b9f866b737b66`。对该真实远程提交执行 `git merge-base --is-ancestor <sha> main` 退出0，确认截至API查询时远程为本地祖先，无分叉，未伪称fetch成功。

`gh repo view ... --json nameWithOwner,visibility,isPrivate,url,defaultBranchRef` 实际成功，确认仓库PUBLIC，默认main。检查全部67个当时Git候选文件，没有运行库、Session、.env、虚拟环境、缓存、原始Word/课程资料或私人对话导出；凭据格式/个人绝对路径扫描无匹配。测试代码中固定密码和test-secret仅用于临时测试库，不是运行账号密码或真实密钥；HTTP脚本使用随机临时密码。`.env.example` 仅为占位配置。Chart.js及source map为官方分发资源，保留MIT许可证；UMD的SHA256与前节记录一致。

`git diff --check` 本轮退出0，仅LF/CRLF提示；检查业务差异无误删，状态机/CSRF/权限没有改变，原schema无改动。合法status筛选对应旧阶段测试的调整已在第2节说明。接下来保存本次重新运行的测试结果和实际提交/推送结果，不沿用上次71项输出。

本轮重新执行 `.\.venv\Scripts\python.exe -m pytest -q`，退出码0，真实结果 `71 passed in 263.43s (0:04:23)`，通过Tee-Object保存在 `phase4/precommit_tests.txt`。覆盖Phase1–4全部用例，包含筛选/权限、两种统计、分页、同次读快照及原业务闭环。不是前轮158.10秒输出的复制。浏览器人工验收继续未验证。

本次提交使用用户指定消息；实际最终提交Hash、普通推送成败和最终工作区状态以本次工具输出及最终报告为准，不在提交自身内部预填Hash或预称推送成功。若连接仍失败，保留本地提交，不改写历史、不强制推送。
