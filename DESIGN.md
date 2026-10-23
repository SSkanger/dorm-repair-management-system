# 宿舍报修管理系统开发设计

《企业级 AI 软件设计与开发》综合实践第8题；Phase5交付复核版，2026-10-23。Phase0–4已获用户阶段审核，Phase5验收和材料准备等待最终人工审核。原始对话、真实视频未齐全前，不称全部交付完成。

## 1. 需求依据与范围

正式依据是开发机 `宿舍保修管理系统工作说明/sources/综合实践项目选题与验收标准.docx`。本轮重新提取正文并读取内嵌评分图片，与整理表九项合计100分一致。原始教师材料保留本地，不是应用运行或默认公开分发的依赖。

| 来源 | 内容与边界 |
|---|---|
| 老师正式Word | 报修、列表详情、接单、状态更新、确认评价、类型/状态查询；合理流转及终态保护；至少一种真实统计；空报修/重复接单/非法跳转/无效评分提示；可运行、持久化、README和视频 |
| 课堂整理，未重新取得录音 | 五类材料、独立完成、学号+姓名压缩包、2026-10-30之前、邮箱提交；准确邮箱与截止时刻待正式通知 |
| 用户批准的工程选择 | Flask/SQLite单体、两角色四账号、四状态、确认后1–5整数评价、两张统计图、分页20条、CSRF、幂等Token和隐私404 |

可选AI扩展不是必做，不实现LLM、智能派单、多智能体、注册、管理员后台、图片上传、通知或支付。实际功能验收与代码证据见 `docs/ACCEPTANCE_RESULTS.md`；A编号为工程验收编号，不冒充教师原始测试集。

## 2. 实际架构与职责

```mermaid
flowchart LR
    Browser[浏览器] --> Routes[Flask路由 / Jinja2]
    Routes --> Auth[Session身份 / CSRF / 角色]
    Routes --> Services[services 写事务]
    Routes --> Queries[queries 授权查询及统计]
    Services --> SQLite[(SQLite两业务表)]
    Queries --> SQLite
    Routes --> Charts[本地Chart.js与数字表]
```

| 实际文件 | 职责 |
|---|---|
| run.py、app/__init__.py | Application Factory、环境配置、扩展和错误处理 |
| app/db.py、schema.sql | 每请求连接/关闭、外键、版本检查、建库与种子CLI、两表约束 |
| app/auth.py | 登录、密码散列验证、Session ID轮换、退出失效、角色装饰器 |
| app/tickets.py | 报修表单、列表详情、五种POST动作、北京时间显示 |
| app/services.py | 创建幂等、动作权限/前置状态、原子更新及事务回滚 |
| app/queries.py、constants.py | 统一枚举、授权范围、参数解析、分页及同快照统计 |
| app/dashboard.py | 登录保护统计页，复用列表筛选上下文 |
| templates/、static/ | Jinja转义、角色导航、状态提示、自有CSS、Chart.js本地资源 |
| tests/、scripts/ | 独立期望测试、真实HTTP和进程重启、全新环境复现 |
| docs/、ai_evidence/ | 实际验收、交付缺项、演示脚本和真实过程记录 |

没有ORM、Redis、消息队列或前端构建系统。实际使用自有响应式CSS，没有引入Bootstrap；早期设计中的Bootstrap建议已按实现校正。

## 3. 数据库ER和字段

```mermaid
erDiagram
    users ||--o{ repair_tickets : student_id
    users o|--o{ repair_tickets : assignee_id
    users {
        INTEGER id PK
        TEXT username UK
        TEXT password_hash
        TEXT display_name
        TEXT role
        TEXT created_at
    }
    repair_tickets {
        INTEGER id PK
        INTEGER student_id FK
        INTEGER assignee_id FK
        TEXT building
        TEXT room_number
        TEXT category
        TEXT description
        TEXT status
        TEXT created_at
        TEXT updated_at
        TEXT assigned_at
        TEXT started_at
        TEXT completed_at
        TEXT confirmed_at
        INTEGER rating
        TEXT review_text
        TEXT reviewed_at
        TEXT submission_token
    }
```

一个学生有多单，一单必须有一个学生；维修员可负责多单，一单至多一个负责人。Session存在服务器文件，不新增业务表。评价直接存工单表，一单一次，不新增评价表。

| 表/字段 | SQLite类型与实际限制 |
|---|---|
| users.id | INTEGER PRIMARY KEY |
| username | TEXT NOT NULL UNIQUE，trim长度1–50 |
| password_hash | TEXT NOT NULL，长度>20，应用生成Werkzeug散列 |
| display_name、role、created_at | TEXT NOT NULL；展示名trim长度1–50；role为student/repairer；创建时间长度>=20 |
| repair_tickets.id、student_id | INTEGER主键；学生ID非空外键users(id)，删除RESTRICT |
| assignee_id | 可空INTEGER外键，非空时不能等于student_id，删除RESTRICT |
| building、room_number、description | TEXT NOT NULL，数据库trim长度1–30/1–20/5–1000；请求层strip处理Unicode空白 |
| category、status | TEXT NOT NULL；类别照明/水管/门锁/网络/其他；状态四枚举，默认PENDING |
| created_at、updated_at | TEXT NOT NULL；其余assigned/started/completed/confirmed/reviewed时间可空 |
| rating | 可空INTEGER，非空时typeof为integer且1–5 |
| review_text | 可空TEXT；非空须已评分且trim后1–500字符；请求空短评存NULL |
| submission_token | TEXT NOT NULL，UNIQUE(student_id,submission_token) |

跨字段CHECK要求：PENDING无负责人及维修时间；ACCEPTED有负责人/接单时间且无开始完成时间；IN_PROGRESS已有开始时间但无完成时间；COMPLETED拥有所有维修时间。确认必须COMPLETED，评分必须已确认；评分与reviewed_at同空或同非空。updated_at>=created_at；已有阶段时间满足创建≤接单≤开始≤完成≤确认≤评价。schema未额外约束每个节点<=updated_at，应用在同一次更新保证更新时刻；不夸大数据库CHECK能力。

数据库外键只验证用户存在，角色、历史流转与权限由服务端检查。当前没有用户角色修改接口。固定UTC ISO格式含微秒/Z，展示转UTC+8，不能信任前端时间。

索引为username唯一、学生+创建时间+ID、负责人+创建时间+ID、状态+创建时间+ID以及提交标识组合唯一。版本为PRAGMA user_version=1，每连接外键ON、busy_timeout=5000。未知版本或已有未知结构拒绝初始化；相同版本检查必要表是否存在，但不做完整列签名校验或自动迁移。重复初始化/种子保持历史；种子不重置已有密码或灌入工单。

## 4. 身份、权限与安全

Flask-Session 0.8.0通过CacheLib文件存储保存服务端会话；Cookie仅携带随机Session ID。每请求从users读取角色，登录成功regenerate，退出删除服务器会话。会话有效2小时；HttpOnly、SameSite=Lax，本机HTTP不设Secure，HTTPS需显式开启。

SECRET_KEY优先从环境取，否则在instance生成并复用随机值；数据库与Session路径可配置，测试覆盖默认路径隔离。应用不自动读.env，不把配置建议写成已实现配置文件加载器。

| 主体 | 查询范围 | 合法写操作 |
|---|---|---|
| 学生 | student_id=本人，所有状态 | 创建本人单；完成后本人确认，再一次性评价 |
| 维修员 | (PENDING且无人负责) OR assignee_id=本人 | 接单；本人负责且状态符合时开始/完成 |
| 未登录 | 首页、登录、health | 登录；业务写操作不允许 |

角色、归属、状态检查都在后端。前端按钮仅改善体验。任何student_id/assignee_id/status/时间伪造字段均不作为可信身份来源；非预期字段拒绝。

CSRFProtect覆盖全部POST：缺失/无效优先400；合法CSRF后未登录业务POST401，错角色403。未登录受保护GET302登录；不存在/无权访问工单404；仍可见的业务状态冲突409；非法输入400；写存储失败503并回滚。已被他人接走从当前范围消失返回404，避免泄露负责人；本人重复接自己的单返回409。所有写路径GET405，成功提交后303。

SQL用户值均绑定参数；动态列名只取代码常量；Jinja自动转义，统计用tojson，不把描述当HTML。没有向客户端公开数据库路径、密钥或密码。

## 5. 状态机、确认和评价

```mermaid
stateDiagram-v2
    [*] --> PENDING: 学生提交
    PENDING --> ACCEPTED: 维修员接单
    ACCEPTED --> IN_PROGRESS: 负责人开始
    IN_PROGRESS --> COMPLETED: 负责人完成
```

| 当前状态/条件 | 操作者与动作 | 写入 |
|---|---|---|
| PENDING且无负责人 | 维修员accept | ACCEPTED、assignee_id、assigned_at、updated_at |
| ACCEPTED | 负责人start | IN_PROGRESS、started_at、updated_at |
| IN_PROGRESS | 负责人complete | COMPLETED、completed_at、updated_at |
| COMPLETED且未确认 | 原学生confirm | confirmed_at、updated_at，状态不变 |
| 已确认且未评价 | 原学生review | rating、可选review_text、reviewed_at、updated_at，状态不变 |
| 已评价 | 无业务写操作 | 只读 |

维修完成由维修员声明；学生确认表示认可完成；确认后评价反馈质量。确认/评价是完成后的字段，不是新状态，所以COMPLETED统计不被拆散。拒绝跳级、回退、再次接单、重复确认或覆盖评价。请求评分只接受原始字符串1至5，拒绝1.0、1.5、布尔、空值、文字及越界；短评strip后<=500。

## 6. 核心接口

| 方法与路径 | 用途/权限 |
|---|---|
| GET /、/health | 首页、数据库连接/版本健康 |
| GET/POST /login、POST /logout | 登录及退出，POST带CSRF |
| GET /portal | 登录身份入口 |
| GET/POST /tickets/new | 学生创建表单/提交 |
| GET /tickets | 学生本人列表及统计 |
| GET /work-queue | 维修员可见工单及统计 |
| GET /tickets/<id> | 授权详情 |
| POST /tickets/<id>/accept、/start、/complete | 维修角色，且满足归属和状态 |
| POST /tickets/<id>/confirm、/review | 原学生，且满足完成/确认前置 |
| GET /dashboard | 登录用户授权范围内统计 |

所有列表/统计只接受category/status/page三个白名单参数，重复、未知枚举或非法页码400。不存在任意status写入接口。

## 7. 事务、幂等与并发

创建GET签发与Session绑定的submission_token，保留最近10个。POST合法后在BEGIN IMMEDIATE事务中查询同学生+标识，存在且规范化内容相同则返回原单，内容不同409；不存在则插入PENDING后提交。唯一约束兜底。非法表单不消耗标识，成功303实现PRG；CSRF和submission_token分别防伪造与防重传，不混用。

状态动作在BEGIN IMMEDIATE内检查可见范围和前置条件，并执行条件UPDATE。例如接单WHERE id=? AND status='PENDING' AND assignee_id IS NULL，rowcount必须1；开始/完成另含assignee_id，确认/评价含student_id及未确认/未评价条件。SQLite同文件写锁和条件谓词保证竞争时只有一名有效接单者，不能SELECT后无条件覆盖。

所有相关字段用同一服务器时间、同一UPDATE写入，COMMIT成功才反馈成功；状态校验、约束或SQLite异常ROLLBACK，锁超时/写存储故障503。测试注入UPDATE后/提交失败验证全行不变。并发使用同一临时文件库、独立连接、屏障，不用两个不共享的内存库冒充竞争。

## 8. 筛选、分页和统计

visible_scope生成授权谓词，追加category/status绑定参数的AND条件。学生本人；维修员“待接或本人负责”用括号整体与筛选相交。固定类别/状态补零，不聚合无权限记录。

同一请求在同一显式SQLite读事务内执行COUNT、ORDER BY created_at DESC,id DESC的20条页、两组GROUP BY。统计不加LIMIT；总数等于所有类型数量之和，也等于所有状态数量之和。测试在隔离WAL库中于多次SELECT之间提交并发写，确认请求内部仍使用同一快照；生产日志模式不改为WAL。

分页保留条件，应用筛选不带旧page，清空条件恢复全部授权记录。无匹配是全零+空提示，超出最后页有返回导航。刷新创建/维修状态后看到新的已提交分布；确认/评价不改变COMPLETED；其他维修员接走后该记录和数量一起退出当前维修员范围。

本地Chart.js 4.5.1绘制类型柱状图和状态环形图，使用显式枚举顺序、同一服务端JSON，始终提供数字表。官方npm来源、SHA校验及MIT许可证在vendor README和Phase4记录，无CDN运行依赖。图表实际浏览器渲染的证据与HTTP/pytest分开记载。

## 9. 测试、交付与人工决定

本轮在全新目录、新虚拟环境、无缓存安装后运行Phase1–4全部pytest和两个真实HTTP脚本；最终实际输出以 `ai_evidence/phase5/` 和 `docs/ACCEPTANCE_RESULTS.md` 为准。独立HTTP不导入业务服务，使用固定输入、真实请求与sqlite3逐行核验；真实停止/重启进程后重新登录比较全字段。

人工选择与AI协作：用户分阶段批准；Phase0审核修订CSRF/身份优先级和404隐私边界；要求预置账号但真实服务端Session；批准四状态、两表、确认字段与两种统计。真实问题、Prompt、验证方法、已知历史哈希见 `docs/AI_PROCESS_INDEX.md`。阶段记录不是完整聊天导出，未收到用户记录不伪造人工操作或成绩。

保留两业务表、四状态和单机应用，避免为课程引入复杂管理后台。限制包括缺少返修/取消/用户注册/迁移平台/完整审计；SQLite不是多节点生产平台。代码可运行不代表视频、原始对话和最终提交已完成。

## 13. 变更记录

| 日期 | 来源 | 变更 |
|---|---|---|
| 2026-10-23 | 用户 Phase 0 独立审核 | Phase 0 通过并批准 Phase 1；根目录新增 AGENTS.md/PLANS.md，资料包原件保留，文档引用改为实际路径。 |
| 2026-10-23 | 用户 Phase 0 独立审核 | 固定 CSRF/认证顺序：无效 CSRF 400，合法 CSRF 后未登录401、错角色403；测试不得关闭 CSRF。 |
| 2026-10-23 | 用户 Phase 0 独立审核 | 收紧接单隐私：不可见或已被他人接走返回404；当前仍可见的业务冲突返回409；并发验收固定失败码且重点验证唯一成功与数据不变。 |
| 2026-10-23 | 用户批准 Phase 2 | 实现学生提交、幂等 Token、本人列表、20 条分页和权限隔离详情；维修人员可见范围提供只读 `/work-queue`，未加入任何接单或状态写操作。 |
| 2026-10-23 | Phase 2 实际验证 | 首轮 Phase 1+2 回归为 38 passed，补充边界后最终回归为 42 passed；真实进程 HTTP 创建、跨学生 404 和停止重启后持久化通过。浏览器自动化因 Work 设置禁用本地浏览器而未验证。 |
| 2026-10-23 | 用户批准 Phase 3 | 沿用四状态及现有两表，增加 accept/start/complete/confirm/review 五个 POST 动作和对应页面。所有更新带当前状态、负责人或学生归属前置条件，成功提交后才 303。 |
| 2026-10-23 | Phase 3 验收预期核对 | 资料包矩阵 A15 的“业务冲突提示”是笼统表述，按已批准 3.3 节固定为：他人接走/不可见404，本人可见重复动作409。fixture S05/S09 只要求拒绝及数据不变，并未指定冲突 HTTP 码，无需改动原件。 |
| 2026-10-23 | Phase 3 事务实施 | BEGIN IMMEDIATE 内检查可见性和状态，再执行条件 UPDATE，以 rowcount=1 与 COMMIT 成功判定成功；同一事务内生成服务器 UTC 时间，异常回滚。并发确认/评价同样条件更新。详情显示维修员展示名、北京时间、确认及评价。 |
| 2026-10-23 | Phase 3 实际验证 | 最终全量62 passed；三种真实双连接竞争及五种动作的事务故障回滚通过。隔离真实 HTTP 闭环、新进程重启后的全字段一致性通过。浏览器工具仍被设置禁用，桌面/手机人工检查未验证。 |
| 2026-10-23 | 用户批准 Phase 4 | 保留两表、四状态、已批准权限范围。学生列表、维修工作台及 `/dashboard` 共用授权和类型/状态 AND 条件、20 条分页、两种真实统计。未增加任何业务状态或管理角色。 |
| 2026-10-23 | Phase 4 查询实施 | `constants.py` 统一枚举，`parse_filters` 白名单校验参数；`ticket_overview` 同一显式 SQLite 读事务内完成总数、列表、两组 GROUP BY，统计不加分页 LIMIT。缺失类别/状态补零；数字表及本地 Chart.js 4.5.1 展示同一结果。 |
| 2026-10-23 | Phase 4 实际验证 | 基线62 passed，专项9 passed，最终71 passed；真实 HTTP 筛选、权限范围统计、状态分布及新进程重启通过。隔离 WAL 测试验证读快照一致性；不修改运行库日志模式。浏览器工具被 Work 设置禁用，实际图表绘制、桌面/390px视觉仍未验证。未提交或推送。 |

| 2026-10-23 | 用户批准Phase5及实际审查 | 按最终代码整理设计，校正未使用Bootstrap、版本检查范围、时间约束及fixture适配的规划措辞；保留历史记录。执行干净环境与独立HTTP验收，结果另见实际证据；不自动提交或推送。 |
