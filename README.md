# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践 **第8题**。让宿舍故障从学生提交、维修接单和处理，到学生确认和评价形成可持久化的闭环。

系统支持学生和维修人员两种身份：学生提交报修、跟踪进度、确认并评价；维修人员接单并推进维修流程。工单保存在SQLite中，重启后可以继续查询。

## 核心功能

|角色或功能|支持内容|
|---|---|
|学生|提交报修、查看本人列表和详情、确认维修结果、提交一次性评价|
|维修人员|查看待接工单、接单、开始维修、完成维修、查看本人负责的工单|
|查询与统计|按故障类型和状态单独或组合筛选、分页、故障类型数量柱状图、工单状态环形图|
|业务保护|空内容及非法输入提示、权限隔离、重复提交保护、禁止重复接单和非法状态流转、评分范围检查|

## 项目材料

|材料|位置与用途|
|---|---|
|正式开发设计文档|[开发设计文档.pdf](开发设计文档.pdf)|
|AI辅助开发过程说明|[AI辅助开发过程说明.pdf](AI辅助开发过程说明.pdf)，介绍关键Prompt、修改与验证|
|原始开发对话导出|[AI开发对话记录.md](AI开发对话记录.md)，与过程总结分开提供|
|当前代码的测试与页面检查记录|[文案精简与浏览器检查](ai_evidence/ui_copy_cleanup.md)|
|2026年10月28日独立审核|[README提交前审核报告](docs/README_提交前审核报告.md)，以及[实际命令与退出码](ai_evidence/readme_audit_20261028/commands.json)|
|运行演示视频|[视频演示.mp4](视频演示.mp4)，展示系统实际操作，时长约6分42秒|

PDF、对话导出及演示视频目前位于本地课程提交目录，未包含在已核对的GitHub main提交中。仅下载仓库源码时，需要同时取得课程提交包中的对应材料，并保留上述相对路径。对话导出的完整性、附件及脱敏情况应在最终提交前检查。阶段历史和旧交付清单保留作过程证据，其中的材料状态可能早于当前PDF、对话导出及视频，不作为当前材料是否存在的判断依据。

## 技术栈与环境

- Python 3.10+；2026年10月28日隔离审核使用Python 3.12.14。早期独立环境的Python、SQLite及间接依赖版本见 `ai_evidence/finalization/clean/versions.txt`；本次安装解析结果见 `ai_evidence/readme_audit_20261028/install.txt`。最低版本兼容性未做完整多版本矩阵测试。
- Flask 3.1.3、Flask-Session 0.8.0、Flask-WTF 1.3.0、CacheLib 0.14.0、WTForms 3.2.2；SQLite使用标准库sqlite3。
- Jinja2、自有响应式CSS、本地Chart.js 4.5.1。实际没有使用Bootstrap，无React/Vue构建流程。
- pytest 8.4.2、requests 2.32.5用于验证。直接依赖按requirements锁定；间接依赖的本轮解析版本另存证据，不宣称已全量锁定。

## Windows安装、初始化与启动

下载并解压项目，在包含 `run.py` 和 `requirements-dev.txt` 的项目根目录打开PowerShell。已有源码时不需要重新下载。安装需要连接Python包源；安装后运行应用和图表不需要外网。不需要Git、Node.js或大模型API密钥。

先确认Python命令可用，版本为3.10或以上。以下命令无需激活虚拟环境：

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir --disable-pip-version-check -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m flask --app run:app init-db
.\.venv\Scripts\python.exe -m flask --app run:app seed-demo
.\.venv\Scripts\python.exe -m flask --app run:app run --host 127.0.0.1 --port 5001 --no-reload
```

`seed-demo`要求输入并确认一个不少于8字符的密码，输入不回显。四个账号共用该初始密码，源码不保存实际密码：

| 账号 | 身份 |
|---|---|
| student_a / student_b | 学生甲 / 学生乙 |
| repairer_a / repairer_b | 维修员甲 / 维修员乙 |

访问 [本机首页](http://127.0.0.1:5001/)，健康检查为 `/health`。保持终端运行，Ctrl+C停止，再执行启动命令即可重启。`run.py`提供app入口，上述命令加载application factory生成的应用。开发服务器仅用于本机课程演示。

### 无交互环境准备账号

自动化运行时，隐藏密码提示可能一直等待输入。可以改用已支持的环境变量入口；以下示例生成随机演示密码，不在源码中固定密码：

```powershell
$demoPassword = [guid]::NewGuid().ToString('N')
$env:DORM_REPAIR_DEMO_PASSWORD = $demoPassword
try {
    .\.venv\Scripts\python.exe -m flask --app run:app seed-demo
    if ($LASTEXITCODE -ne 0) { throw '演示账号准备失败，请检查命令输出。' }
} finally {
    Remove-Item Env:DORM_REPAIR_DEMO_PASSWORD -ErrorAction SilentlyContinue
}
```

本次新建账号的密码保存在当前PowerShell变量 `$demoPassword` 中，使用者应通过本机安全方式取用并妥善记录，不要录入公开视频或日志。完成登录并记录后，执行 `Remove-Variable demoPassword` 清除变量。已有账号的密码不会改变；如果已有账号，应使用原密码。该步骤在初始化数据库之后、启动服务之前执行，可替代交互式 `seed-demo`。

### 数据保存与配置

重复init-db不会清空数据；未知版本会明确拒绝，需先备份并显式迁移。seed-demo仅补缺失账号，不重置已有密码、不创建业务工单。忘记旧密码时重新seed不能重置它；请使用自己记录的密码，或选择全新数据库准备演示，不删除旧数据假装修复。

默认数据库为 `instance/dorm_repair.sqlite3`，Session位于 `instance/sessions/`。没有外部密钥时在 `instance/secret_key`生成随机密钥。这些均排除Git和交付包。

| 可选环境变量 | 用途 |
|---|---|
| DORM_REPAIR_DATABASE | SQLite文件路径 |
| DORM_REPAIR_SESSION_DIR | 服务端Session目录 |
| DORM_REPAIR_SECRET_KEY | 外部签名密钥，不公开实际值 |
| DORM_REPAIR_COOKIE_SECURE | HTTPS设1；本机HTTP保持0 |
| DORM_REPAIR_DEMO_PASSWORD | 非交互种子密码，用后清除，不写日志 |

默认无需额外配置。应用不会自动加载.env；设置应在初始化、种子和启动所用的同一PowerShell中保持一致。`.env.example`只有配置占位符。

## 完整使用方法

切换角色时先退出登录再登录其他账号，或使用不同浏览器/独立隐私窗口。普通浏览器的不同标签页通常共享登录状态。

1. student_a登录，提交楼栋、宿舍号、类型及描述，成功后跳到真实工单详情。
2. `/tickets`每页20条，按创建时间倒序、ID倒序；学生只看到本人记录。student_b不能查看甲的详情。
3. repairer_a登录，侧栏“待接工单”查看待处理工单；打开详情后点击“接单”，再依次点击“开始维修”“完成维修”。仅点击“查看详情”不会接单。“我负责的工单”用于查看本人已接工单；直接访问 `/work-queue` 可以查看待接及本人负责的工单。
4. repairer_b看不到甲已接走的工单，不能覆盖负责人；已接单不能跳级完成。
5. 原学生重新登录，确认维修完成后提交1–5整数评分和可选短评；评分不能覆盖。
6. 在列表和“工单统计”中按故障类型、状态筛选，也可以组合筛选或清空条件，检查列表与图表数量。
7. 停止重启服务后重新登录，核对工单、负责人、时间、确认和评分仍在。

楼栋trim后1–30字符，宿舍号1–20字符，描述5–1000字符，短评最多500字符。类型包括原有照明、水管、门锁、网络，以及本体类、电类、电梯类、道路景观类、给排水类、空调类、开水饮水类、门窗五金类、暖气类、洗浴热水类、消防设施类、其他。选择“其他”后显示文字输入框，具体类型去掉首尾空白后必填1–50字符；列表和详情显示具体文字，筛选和统计统一计入“其他”。

### 已有数据库升级（报修类型扩展）

当前数据库版本为2。若你之前已经运行过系统，请先在原服务终端Ctrl+C停止，再在原来的项目目录和数据库环境配置下执行：

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app migrate-db
.\.venv\Scripts\python.exe -m flask --app run:app run --host 127.0.0.1 --port 5001 --no-reload
```

升级会先生成同目录`.v1-backup-随机标识.sqlite3`备份，再在一个事务中保留原字段和ID、扩展类别约束并增加category_detail字段，核对旧行一致后提交；失败回滚。旧“其他”工单不强制补文字。重复升级不修改数据，未知版本、未知字段或自定义触发器/索引拒绝自动处理。请保管备份，禁止公开上传；不要删除旧数据库，也不需要重新seed。全新安装继续使用init-db，直接创建版本2。

```text
PENDING 待处理 → ACCEPTED 已接单 → IN_PROGRESS 维修中 → COMPLETED 已完成
```

确认完成由原学生执行，工单仍保持“已完成”，单独保存确认时间。确认后才能提交1–5整数评分和可选文字评价；已确认或已评价不能重复操作、覆盖结果。

- 接单要求维修人员已登录，工单仍为待处理且没有负责人；同一工单只能有一个有效接单者。
- 只有该工单的维修负责人可以开始和完成维修，不能跳级或回退；已完成不能再次接单。
- 学生只能查看、确认和评价自己的工单。空内容、非法评分、无效筛选及越权请求均有提示或错误响应。
- 相同提交标识与相同内容重复发送会打开原工单，不重复创建；同标识更改内容则拒绝。

当前没有编辑、删除、取消和返修功能。

## 筛选、统计与页面验收

界面包含侧栏、真实数据工作概览、本人负责列表、表单和详情时间线。维修员侧栏“待接工单”默认筛选PENDING，“我负责的工单”使用只读 `/my-work`。

列表、维修工作台和`/dashboard`支持类型、状态单条件及AND组合。“应用筛选”回到第一页，分页保留条件，“清空筛选”恢复当前授权范围的全部记录。

故障类型柱状图、状态环形图及数字表来自SQLite全部匹配记录，分页不截断统计。缺失枚举补0；两表合计均等于匹配总数。维修推进后刷新读取最新状态，确认评价不改变COMPLETED分布。Chart.js及MIT许可证在`app/static/vendor/`，无CDN；图表失败时数字表仍可读。

16类采用横向柱状图并自动增加图表高度，状态仍环形图；关闭绘制动画以直接显示最终几何位置。后续Codex代理浏览器检查已覆盖1440px和390px下的两图、筛选及部分列表交互，见 [页面检查记录](ai_evidence/ui_copy_cleanup.md)及对应截图。

本人对各阶段成果进行了人工审核。代理浏览器检查、自动化测试和本人人工审核是不同的验证方式；上述截图只证明对应页面和视口，实体手机触控、离线强刷等具体检查按实际执行情况记录，不由pytest结果推导通过。2026年10月28日README审核没有重新操作浏览器。

## 自动化测试与独立复现

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/phase4_http_smoke.py
.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py
```

pytest使用临时数据库和Session，CSRF保持开启。HTTP脚本使用独立临时存储、随机密码和真实Flask子进程，包含停止重启，不写默认运行数据库。

|验证批次|实际保存结果|证据|
|---|---|---|
|2026-10-28 README独立审核|全新venv安装成功；84 passed in 287.80s；上述两套HTTP脚本均退出0，业务闭环与重启通过|[pytest输出](ai_evidence/readme_audit_20261028/pytest.txt)、[HTTP闭环与19次拒绝检查](ai_evidence/readme_audit_20261028/http_independent.txt)、[筛选与重启检查](ai_evidence/readme_audit_20261028/http_phase4.txt)|
|2026-10-26 文案精简|84 passed in 334.90s|[保存的完整输出](ai_evidence/ui_copy_cleanup/pytest.txt)|
|2026-10-26 收尾干净环境复现|84 passed in 218.18s，三套HTTP退出0|[pytest输出](ai_evidence/finalization/clean/pytest.txt)、[复现结论](ai_evidence/finalization/clean/reproduction.json)|

早期Phase5为71项，补充冻结时钟用例后为72项，UI升级后为80项，类型扩展后为84项；这些记录对应不同阶段，不能把早期数量当作当前全量结果。表中是实际保存的执行记录，阅读README不会自动重新运行测试。HTTP验证不等于浏览器人工验收。

维护者可自动复制到系统临时目录，创建全新虚拟环境、无缓存安装、初始化和运行独立验收：

```powershell
.\.venv\Scripts\python.exe scripts/phase5_reproduce.py
```

该命令联网下载依赖，保留临时工作目录供浏览器检查；位置仅写入忽略的`instance/phase5_workspace.txt`。日志去除私人路径和随机密码，不生成最终压缩包。

## 目录

```text
app/                  Flask应用
  __init__.py         应用工厂、扩展与蓝图注册
  auth.py             登录、退出及角色校验
  tickets.py          报修、列表详情及业务操作路由
  services.py         创建、接单、状态推进、确认评价
  queries.py          权限范围、筛选、分页与统计
  dashboard.py        统计页面
  db.py / schema.sql  数据库连接、初始化、迁移和表约束
  templates/          Jinja2页面模板
  static/             自有CSS、原生JavaScript与图标
    vendor/           Chart.js与MIT许可证
tests/                认证、数据库、工单、并发和筛选统计测试
scripts/              HTTP验收与干净环境复现工具
docs/                 验收矩阵、演示脚本、AI索引和交付清单
ai_evidence/          Phase0–5真实阶段记录和测试输出
run.py                应用入口
requirements*.txt     直接依赖
README.md             安装、操作与材料入口
DESIGN.md             开发阶段设计记录（最终提交设计见上方PDF）
AGENTS.md / PLANS.md   开发规则 / 阶段门槛
instance/             本地生成，不属于源码或交付包
```

开发机的老师原始资料包仅供核对，不是应用运行依赖，不默认公开分发。

## AI开发、限制与常见错误

Codex参与需求分析、架构设计、代码生成、调试、测试和界面优化。通过 `AGENTS.md`固定业务约束，通过 `PLANS.md` 和分阶段Prompt控制范围；阶段成果经本人审核并结合实际测试后继续推进。关键Prompt、修改和验证见上方AI辅助开发过程说明，原始消息见独立对话导出。`docs/AI_PROCESS_INDEX.md`保留早期阶段案例与Git记录，不作为当前材料清单。软件不接入LLM，不实现智能派单、多智能体、注册、管理员、找回密码或生产部署。SQLite面向单机课程演示，没有完整审计历史。

| 现象 | 处理 |
|---|---|
| Python/pip不可用 | 安装Python，使用虚拟环境python路径；无需激活PowerShell脚本 |
| 安装失败 | 检查包源联网，保留真实错误，恢复网络后重试，勿跳过依赖 |
| 端口占用 | 选空闲端口替换5001并修改URL；不停止无关进程 |
| health503/no such table | 核对数据库配置并执行init-db；未知版本先备份迁移 |
| 登录失败 | 使用seed时设置的密码；重复seed不重置旧密码 |
| 请求验证400 | 重新打开表单获取新CSRF；不能关闭防护 |
| 403/404 | 检查角色和工单归属；他人已接工单不泄露存在性 |
| 409 | 动作顺序不符或已经执行，刷新后按状态操作 |
| 写入503 | 数据库繁忙/存储失败，稍后重试，勿删库；失败不提交半条业务修改 |
| 图表不可用 | 核对数字表、本地JS和控制台；无需CDN |

| 页面显示旧样式 | 先按Ctrl+F5强刷，检查本地静态资源是否加载；不要删除数据库 |
