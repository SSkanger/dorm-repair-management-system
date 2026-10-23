# 宿舍报修管理系统

《企业级 AI 软件设计与开发》综合实践 **第8题**。让宿舍故障从学生提交、维修接单和处理，到学生确认和评价形成可持久化的闭环。

Phase0–4已经用户阶段审核；Phase5最终结果见 [验收记录](docs/ACCEPTANCE_RESULTS.md)。原始AI对话、真实视频及人工待验项见 [交付清单](docs/DELIVERY_CHECKLIST.md)，不宣称五类材料已全部齐全。

## 技术栈与环境

- Python 3.10+；本轮实际Python、SQLite及完整包版本保存在 `ai_evidence/phase5/versions.txt`。
- Flask 3.1.3、Flask-Session 0.8.0、Flask-WTF 1.3.0、CacheLib 0.14.0；SQLite使用标准库sqlite3。
- Jinja2、自有响应式CSS、本地Chart.js 4.5.1。实际没有使用Bootstrap，无React/Vue构建流程。
- pytest 8.4.2、requests 2.32.5用于验证。直接依赖按requirements锁定；间接依赖的本轮解析版本另存证据，不宣称已全量锁定。

## Windows安装、初始化与启动

在解压后的项目根目录打开PowerShell。安装需要连接Python包源；安装后运行应用和图表不需要外网。不需要Git、Node.js或大模型API密钥。

```powershell
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

1. student_a登录，提交楼栋、宿舍号、类型及描述，成功后跳到真实工单详情。
2. `/tickets`每页20条，按创建时间倒序、ID倒序；学生只看到本人记录。student_b不能查看甲的详情。
3. repairer_a登录，进入`/work-queue`，查看无人接单工单及本人负责工单；接单后在详情依次“开始维修”“完成维修”。
4. repairer_b看不到甲已接走的工单，不能覆盖负责人；已接单不能跳级完成。
5. 原学生重新登录，确认维修完成后提交1–5整数评分和可选短评；评分不能覆盖。
6. 停止重启服务后重新登录，核对工单、负责人、时间、确认和评分仍在。

楼栋trim后1–30字符，宿舍号1–20字符，描述5–1000字符，短评最多500字符。类型固定为照明、水管、门锁、网络、其他。

```text
PENDING 待处理 → ACCEPTED 已接单 → IN_PROGRESS 维修中 → COMPLETED 已完成
```

确认只写confirmed_at，评价写rating/reviewed_at，不增加CONFIRMED状态；完成后不能再接单或回退。没有编辑、删除、取消和返修功能。

## 筛选、统计与页面验收

列表、维修工作台和`/dashboard`支持类型、状态单条件及AND组合。“应用筛选”回到第一页，分页保留条件，“清空筛选”恢复当前授权范围的全部记录。

故障类型柱状图、状态环形图及数字表来自SQLite全部匹配记录，分页不截断统计。缺失枚举补0；两表合计均等于匹配总数。维修推进后刷新读取最新状态，确认评价不改变COMPLETED分布。Chart.js及MIT许可证在`app/static/vendor/`，无CDN；图表失败时数字表仍可读。

本机需检查桌面和约390px宽度、长描述、筛选切换、空态、图例和触控按钮；断开外网后确认两图仍绘制。实际已验证范围以本轮验收记录为准，不以pytest代替真实视觉检查。

## 自动化测试与独立复现

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/phase4_http_smoke.py
.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py
```

pytest用临时数据库和Session，CSRF保持开启。HTTP脚本用独立临时存储、随机密码和真实Flask子进程，包含停止重启，不写默认运行数据库。Phase5独立环境曾实际运行71项，记录在`ai_evidence/phase5/pytest.txt`；后续版本保存发现测试标识时钟碰撞，增加冻结时钟回归并修复测试辅助数据，最新结果见`ai_evidence/phase5/precommit_tests.txt`，历史失败也保留。

维护者可自动复制到系统临时目录，创建全新虚拟环境、无缓存安装、初始化和运行独立验收：

```powershell
.\.venv\Scripts\python.exe scripts/phase5_reproduce.py
```

该命令联网下载依赖，保留临时工作目录供浏览器检查；位置仅写入忽略的`instance/phase5_workspace.txt`。日志去除私人路径和随机密码，不生成最终压缩包。

## 目录

```text
app/                  Flask应用、schema、业务服务、查询、模板和静态资源
  static/vendor/      Chart.js与MIT许可证
tests/                认证、数据库、工单、并发和筛选统计测试
scripts/              HTTP验收与干净环境复现工具
docs/                 验收矩阵、演示脚本、AI索引和交付清单
ai_evidence/          Phase0–5真实阶段记录和测试输出
run.py                应用入口
requirements*.txt     直接依赖
README.md / DESIGN.md 使用说明 / 实际设计
AGENTS.md / PLANS.md   开发规则 / 阶段门槛
instance/             本地生成，不属于源码或交付包
```

开发机的老师原始资料包仅供核对，不是应用运行依赖，不默认公开分发。

## AI开发、限制与常见错误

Codex参与需求映射、架构、分阶段生成、审查、调试和实际测试；开发者在聊天中审核阶段并确认关键决定。案例和Git历史见`docs/AI_PROCESS_INDEX.md`；阶段总结不冒充原始完整对话。软件不接入LLM，不实现智能派单、多智能体、注册、管理员、找回密码或生产部署。SQLite面向单机课程演示，没有完整审计历史。

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
