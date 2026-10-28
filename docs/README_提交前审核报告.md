# README 提交前审核报告

审核日期：2026年10月28日。审核对象：项目根目录 `README.md`（143行），本地分支 `main`，提交 `2eb319651204ebcb37a6f592dab05be8d18ce69a`。本轮只新增本报告和 `ai_evidence/readme_audit_20261028/` 核查记录，未修改README、应用、Schema或测试，未提交或推送Git。

## 1 总体审核结论

**PASS_WITH_ISSUES：README基本满足正式内容要求，安装启动和业务说明总体真实，但存在提交材料索引缺失、旧阶段结果被称为最新、视觉检查状态过时等问题，应修订后再作为最终提交入口。**

未发现可直接认定为P0的命令或功能错误。交互式密码输入在本轮无人值守环境中超时，不能据此认定普通PowerShell人工输入也失败；README已有环境变量入口，补充可直接操作的说明有助于自动化评审。自动化结果与浏览器人工验收严格区分。

本地HEAD与本轮 `git ls-remote origin refs/heads/main`返回均为上述提交；仅说明远程main节点一致，不代表本地未跟踪PDF和对话材料已在GitHub。没有进行远程克隆后独立验收，远程压缩包或实际课程交付包的完整性为NOT_VERIFIED。

### 1.1 正式要求与工程建议分开判断

已读取原始 `宿舍保修管理系统工作说明/sources/综合实践项目选题与验收标准.docx` 的正文，完整提取保存至本轮证据目录，并实际查看内嵌评分图片。Word明确要求README说明项目目标、技术栈、启动方法、核心功能及AI使用情况。评分表中README/项目说明占5分，重点为“启动、功能、技术栈和使用说明是否清楚”。

第8题规定学生报修、列表详情、接单、维修状态、完成确认评价、类型/状态查询；至少一种统计；空报修、非法状态、重复接单、无效评分处理。可选AI扩展不属于必做。

课堂补充只核对了资料包 `docs/06_TEACHING_GUIDANCE.md`、`docs/05_DELIVERY_CHECKLIST.md`等二手整理，没有取得或重新听取原始录音。项目名称简介、安装使用、功能、结构、AI使用等与现有整理方向一致；用户所述课堂十项逐字原话及完整录音一致性为NOT_VERIFIED，不能冒称已核实原始课堂通知。

Python版本检查、无交互密码示例、当前证据入口、可点击交付索引、强刷说明和干净环境复现属于增强可用性的工程建议，并非Word规定的额外强制评分子项。视频及真实对话是交付材料，不等于要求README本身包含全部内容。

## 2 逐项审核表

PASS表示该项存在且与检查证据基本一致；FAIL表示该项存在明确遗漏或错误；NOT_VERIFIED表示没有足够执行或来源证据。单项FAIL不自动等同总体项目不可运行。

|审核项目|要求来源|README位置|实际证据|结论|问题及建议|
|---|---|---|---|---|---|---|
|名称、课程、题号、目标|Word及课堂整理|1–3行|正式Word第8题|PASS|目标清楚，角色在使用流程可识别；开头阶段历史偏长，建议后移|
|必做功能|Word|52–61、75–90行|tickets、services、queries、dashboard及模板|PASS|核心闭环、两种筛选和真实统计均有说明，建议改为角色功能列表以便扫描|
|最终新增功能|实现一致性|61、82行|category_detail、category迁移、my-work路由|PASS|16类、其他输入、本人负责列表均提及，没有将扩展当官方必做|
|技术栈与依赖版本|Word|11–14行|requirements两文件；Chart.js文件头；app初始化|PASS|实际为自有CSS、原生JS，无Bootstrap；Python最低3.10未在本轮多版本矩阵验证|
|初次安装步骤|Word|18–26行|venv、pip安装与pip check本轮记录|PASS|文件名和PowerShell相对路径正确；建议加python --version以及解压后进入根目录的明确步骤|
|数据库初始化与迁移|启动及工程建议|24、38、63–72行|db.py的三条CLI、schema.sql版本2及迁移测试|PASS|非破坏初始化、显式备份迁移描述真实；本轮新库为2，迁移见自动化测试|
|演示账号及密码机制|使用说明|25、29–38、48行|db.py:seed_demo_command、DEMO_USERS|PASS|四账号真实、密码至少8字符，重复seed不改旧密码；无真实密码硬编码|
|人工隐藏密码输入|实际操作|25、29行|seed_interactive.txt|NOT_VERIFIED|无人值守执行12秒超时；不能等同人工交互失败，也不能写人工输入已通过|
|自动评审密码入口可操作性|工程建议|48行|seed_env.txt|FAIL|只列变量名，缺完整安全设置及清除步骤；补示例，勿硬编码密码|
|Flask入口、端口和页面|Word|26、36行|run.py、启动记录startup.json|PASS|CLI显式5001与URL一致；run.py直启为5000，README未列其作为第二启动方式，故不是当前自相矛盾|
|完整业务操作|Word|54–59、84–86行|本轮隔离HTTP及服务代码|PASS|完整路径已说明；建议明确退出换账号或独立隐私窗口，并把筛选统计并入编号步骤|
|业务规则与异常|Word|57–61、75–78、139–142行|services.py:_action_target/apply_ticket_action、schema约束|PASS|终态、顺序、评分、权限都正确；重复接单和空内容提示说明分散，建议集中列出|
|目录结构|课堂整理及建议|112–124行|实际app/tests/scripts/docs等|PASS|主要目录真实，无缓存堆砌；可选细化核心Python模块，不强制逐文件罗列|
|测试命令与安装依赖|工程建议，支撑正确性|22、95–97行|requirements-dev与两脚本|PASS|能安装pytest和requests；脚本使用临时存储，包含业务、异常、重启|
|当前测试证据指向|真实性|7、82、100行|ui_copy_cleanup/pytest.txt；phase5/precommit_tests.txt|FAIL|100行把72项阶段记录称为最新，82行“本轮80项”易当当前全量；应分历史与当前|
|当前图表验收范围|真实性|7、88–90行|ui_copy_cleanup.md:26–32及1440/390截图；设计文档593行|FAIL|已存在后续代理图表检查，但README仍只指向旧待验；更新具体范围，不能由代理检查推导本人全部验收|
|持久化与重启|Word|36、59、100行|HTTP检查与数据库测试|PASS|保存机制和手动复查步骤明确|
|Codex实际参与|Word|130行|阶段记录、AI_PROCESS_INDEX、真实导出文件|PASS|需求、设计、实现、调试、测试有概述；可补一句AGENTS/PLANS约束及本人审核后推进|
|AI说明及原始对话索引|用户审核要求及交付可定位性|5、130行|根目录两PDF、AI开发对话记录.md；旧索引50行|FAIL|现有正式材料未索引，旧索引仍称未发现对话导出；更新入口，不把总结当完整对话|
|设计文档入口|交付建议|121行|DESIGN.md和开发设计文档.pdf|FAIL|旧DESIGN存在但未指向用户指定最终PDF；应明确主交付版本，保留早期设计为辅助|
|视频材料|Word交付要求|5行间接指向清单|本轮项目范围未检出视频文件|NOT_VERIFIED|没有证据认定已录制或已交付；若视频存别处，待用户提供实际文件位置|
|故障排查与配置|工程建议|38–50、134–143行|环境变量读取、CLI和错误处理|PASS|大部分真实；缺页面缓存刷新提示、新库路径示例，可小范围补充|
|现有Markdown链接|可定位性|5、7、82行|本轮本地链接存在性检查|PASS|6个Markdown相对链接均存在，问题是内容老旧而非链接404|
|真实浏览器和本人验收|验证边界|88–90行|历史截图、用户关于审核的陈述|NOT_VERIFIED|本轮未操作浏览器；用户已明确说明逐阶段人工审核，但具体设备、离线、触控及视频不能据此推断|

## 3 独立可复现性检查

### 3.1 方法与限制

只从README确定正常启动顺序、依赖和测试命令。复制app/tests/scripts与README、run.py及两份依赖到系统临时目录，不复制.venv、运行库、Session或密钥。全新venv安装依赖。额外的临时复制和日志采集属于隔离审核手段，不是补齐缺失业务步骤。

未直接执行 `scripts/phase5_reproduce.py`：它会向源项目 `instance/phase5_workspace.txt`写入路径，超出本轮只新增报告及验证记录的边界；本轮由独立临时驱动执行README中的命令，未改该脚本。该复现工具的整套一键执行在本轮为NOT_VERIFIED，不能用分步通过冒充该工具执行通过。

README第21行的 `python -m venv .venv`，实际使用已存在解释器的绝对路径加 `-m venv <临时项目>/.venv`。`python --version`也单独检查。该变化是明确选择解释器和临时工作目录，不是业务修复；仍建议README加版本检查。本轮并未实际安装一个Python3.10或3.11来验证全部最低版本组合。

README安装、pip check、init-db、seed-demo、启动、pytest及两套HTTP命令都从临时项目执行。绝对命令和退出码保存在 `../ai_evidence/readme_audit_20261028/commands.json`；真实5001启动及首页、登录、health保存在 `startup.json`和`server_startup.txt`。临时工作目录最终以summary.json为准。

### 3.2 README原文与实际执行映射

|README原文|实际执行方式|额外操作与边界|
|---|---|---|
|`python -m venv .venv`|源环境Python的绝对路径，创建临时项目/.venv|不复制已有venv；先执行python --version|
|`.\.venv\Scripts\python.exe -m pip install --no-cache-dir --disable-pip-version-check -r requirements-dev.txt`|临时venv解释器执行相同参数|联网全新解析，原依赖未改|
|`.\.venv\Scripts\python.exe -m pip check`|同命令|无补充依赖|
|`.\.venv\Scripts\python.exe -m flask --app run:app init-db`|同命令|生成临时目录下版本2库|
|`.\.venv\Scripts\python.exe -m flask --app run:app seed-demo`|先无交互尝试，超时后用DORM_REPAIR_DEMO_PASSWORD|变量名和用途已在README第48行列出，但设置示例缺失；随机密码不入日志|
|`.\.venv\Scripts\python.exe -m flask --app run:app run --host 127.0.0.1 --port 5001 --no-reload`|同命令|独立进程，检查三页面后主动停止，未停止原服务|
|`.\.venv\Scripts\python.exe -m pytest -q`|同命令|临时SQLite和Session，原断言未改|
|`.\.venv\Scripts\python.exe scripts/phase4_http_smoke.py`|同命令|HTTP完整闭环、筛选及重启|
|`.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py`|同命令|四账号、闭环、19次拒绝、统计和重启；不是浏览器人工操作|

人工输入seed密码、本人浏览器验收、触控和断网渲染、正式压缩包独立解压、视频播放与完整原始对话逐条一致性，本轮均NOT_VERIFIED。现有对话导出文件存在且开头包含真实阶段任务，未逐条对照其约5MB全文与原应用聊天，也未宣称已完整脱敏。

## 4 问题分级与影响

### P0

本轮尚未发现证据支持P0。无人值守密码超时是验证阻碍，正常交互式输入未验证，不将其虚报为系统无法登录。

### P1 必须在最终README中修订

1. **正式材料无法从README直接定位**：README:5、121、130；`docs/DELIVERY_CHECKLIST.md`:14仍称对话缺失，`docs/AI_PROCESS_INDEX.md`:50称未发现导出，但本地已有 `AI开发对话记录.md`（5,120,022字节）和两份用户指定PDF。缺失的是更新后的索引与导出完整性复核，不应继续笼统说对话文件不存在。材料均为未跟踪文件，不在当前远程main提交内。影响AI过程及开发设计材料验收，尤其仅看GitHub时。
2. **“最新测试”误指旧72项**：README:100指 `ai_evidence/phase5/precommit_tests.txt`，实际末行为72 passed in 152.16s。已有后续 `ai_evidence/ui_copy_cleanup/pytest.txt`为84 passed in 334.90s。README:7的84 passed in 218.18s是真实历史复现，不是造假，但应标注日期与批次，不能和最新提交检查混写。影响正确性证据可信度。

### P2 应改进

3. README:88和旧收尾记录没有接续10月26日文案精简阶段的1440/390代理图表检查；与最终设计文档:593及`ai_evidence/ui_copy_cleanup.md`:26–32不一致。只更新已验证具体范围，不抹除尚未进行的本人触控或离线检查。
4. README:25、48缺非交互密码设置示例，AI评审可能卡在隐藏输入。现有入口已经可用，无需改业务代码。
5. README:82把80项称“本轮”，且首页堆叠Phase0–5信息，容易让评审不清楚当前版本；历史移至证据索引。
6. README:54–59在换角色前未明确退出/独立隐私窗口；同浏览器直接访问登录页会因已登录而跳回工作台。补操作提示，减少误判。
7. README:11引用早期versions文件，建议改为当前或本轮新环境版本证据；未发现当前直接依赖版本错误。Python最低3.10的全面兼容未实测。

### P3 可选优化

8. 安装前补Python版本检查、取得源码并进入根目录的步骤；目录树细化auth/services/queries/db；异常规则集中列出；补Ctrl+F5刷新静态资源。
9. `python run.py`的5000在最终设计文档:677已有说明。README只提供CLI5001本身正确；若今后添加直接运行方式，必须同步说明访问5000。

## 5 可直接采用的修改建议

以下仅为建议文本，本轮未应用。材料链接使用当前真实文件名；视频未定位，不编造链接。若未来源码仓库不存私人对话，应注明它仅在课程提交包中提供，并让源码包与外层交付目录位置一致。

### 5.1 增加正式材料索引并精简开头

建议将README第5–7行的多轮状态说明后移，增加：

```markdown
## 项目材料

- [开发设计文档](开发设计文档.pdf)
- [AI辅助开发过程说明](AI辅助开发过程说明.pdf)
- [AI开发对话记录](AI开发对话记录.md)
- [当前版本测试与浏览器检查记录](ai_evidence/ui_copy_cleanup.md)

上述PDF和对话记录当前位于本地提交目录；若仅下载GitHub源码，需同时取得课程交付包中的对应材料。演示视频请按最终实际文件位置补充，不以口播稿或截图代替。
```

原文依据：正式Word要求README/视频及AI过程说明；课堂整理要求真实对话；当前文件存在性。原始对话的完整性、隐私和媒体附件可用性应在提交前另行核对。不得为了让链接有效而未经用户批准将私人对话推送公共仓库。

### 5.2 纠正历史与当前证据

建议替换第100行中“最新结果”表述：

```markdown
测试证据按版本保留：Phase5早期为71项，补充冻结时钟用例后为72项，UI升级后为80项，类型扩展后为84项。当前文案精简版本的完整保存输出见 ai_evidence/ui_copy_cleanup/pytest.txt（84 passed in 334.90s）；早期干净环境复现见 ai_evidence/finalization/clean/（84 passed in 218.18s及三套HTTP记录）。这些是各自批次的历史结果，不表示本次阅读README时自动重新执行。
```

本轮审核新执行结果见下一节，不直接用来改写历史输出。若将本轮记录加入README，应注明2026-10-28审核批次和路径。

### 5.3 更新浏览器检查范围

建议替换88–90行中的过时状态：

```markdown
后续代理浏览器检查已记录1440px和390px下的统计图表、筛选及部分列表交互，见 ai_evidence/ui_copy_cleanup.md 和对应截图。该检查只覆盖记录中的版本、页面与视口，不等于本人在所有设备完成独立验收。实体手机触控、离线强刷等检查按实际执行情况记录。
```

依据：后续记录与最终开发设计文档，不凭pytest推导视觉通过。本人已向本聊天说明逐阶段人工审核，但不将这一总体陈述扩大为未记录的具体设备测试。

### 5.4 补充无人值守账号准备方法

常规人工录制继续使用交互式seed-demo。自动化环境可以使用下面的PowerShell步骤，随机生成仅本机演示用密码；使用者自行妥善记录变量值，不要把它录屏、写入公开日志或提交Git。

```powershell
$demoPassword = [guid]::NewGuid().ToString('N')
$env:DORM_REPAIR_DEMO_PASSWORD = $demoPassword
.\.venv\Scripts\python.exe -m flask --app run:app seed-demo
Remove-Item Env:DORM_REPAIR_DEMO_PASSWORD
# 本次新建的四个演示账号共用 $demoPassword，已有账号密码保持不变。
# 本机登录完成并妥善记录后，清除变量：
Remove-Variable demoPassword
```

必须说明已有账号不会重置密码。随机值和命令结构是推荐说明，不是声称本轮实际执行过这段PowerShell；本轮执行的是Python进程环境中设置同名变量。

### 5.5 补充使用路径与AI概述

```markdown
切换身份时先退出登录，或使用独立浏览器/隐私窗口。维修人员在“待接工单”打开详情后点击“接单”；仅查看详情不会自动接单。随后依次开始维修、完成维修，原学生再确认并评价。在“工单统计”按类型和状态筛选，列表分页不会截断统计总量。

Codex参与需求分析、架构设计、代码生成、调试、测试与界面优化。项目通过 AGENTS.md 固定业务约束，通过 PLANS.md 和分阶段Prompt控制范围；阶段成果经本人审核并结合实际测试后继续推进。详细案例与原始对话见项目材料索引。
```

### 5.6 常见问题补充

建议安装前增加 `python --version`，确认3.10及以上；若Windows没有python命令，先安装并确认命令可用。页面旧样式可先Ctrl+F5强刷，避免把缓存当数据库损坏；禁止用删除数据库或关闭CSRF作为排错捷径。

## 6 最终验收判断

1. **是否符合原始Word？** 基本符合，五项README明确内容均存在；主要问题是当前证据及正式材料入口未更新，结论PASS_WITH_ISSUES。
2. **是否符合课堂补充？** 按现有二手整理基本覆盖名称、简介、安装、功能、结构与AI概述；原始课堂录音未核实，逐字一致性NOT_VERIFIED。
3. **是否反映最终代码？** 技术栈、16类、schema v2、账号、四状态、两图和端口说明基本准确；测试“最新”和视觉验收状态存在上述明确时序错误。
4. **陌生评审能否启动？** 分步隔离安装启动可执行；需具备Python、联网安装和交互输入能力。无人值守代理应使用已有环境变量入口，建议补完整示例。
5. **是否适合AI Agent验收？** 能提供基本命令和脚本，但密码交互及过时材料入口会增加误判风险。先修订P1及密码说明，再开展自动评审；不得加入任何操控评分的特殊指令。
6. **必须改什么？** 修正最新测试证据、添加最终PDF与现有对话材料入口，并避免引用链继续误报对话不存在。同步更新图表已验范围，明确本地材料与GitHub源码范围。
7. **修订后重验什么？** 核对相对链接和实际课程包；用新目录按最终README从安装到登录走完；验证交互/非交互seed、完整业务链、pytest及两套HTTP和重启；若只改链接，可只重查链接与材料范围，不机械重复无关业务测试。新增材料、变更命令或依赖后，应重做相应独立复现。

### 6.1 非正式模拟评分

建议当前README约 **4/5分**，仅为审核者判断，不是官方评分或自动评分算法。目标、技术栈、启动、功能和AI使用具备，安装说明可执行；扣分风险在材料索引落后、最新结果含混、无交互操作不够明确。老师没有公布内部小项权重，不据此编造固定扣分公式。最终分数还取决于实际提交包和评审操作。

影响其他评分维度的风险：旧对话缺失说法及入口缺失影响AI过程10分材料定位；设计PDF无索引影响设计文档5分可访问性；历史结果混写影响正确性与闭环证据判断；视频未定位属于交付5分材料问题，不能当README无法运行来扣同一性质分数。

## 7 本轮执行结果

本轮实际在全新临时目录执行，工作目录为 `C:/Users/刘新康/AppData/Local/Temp/dorm-readme-audit-zb64efna`。此路径仅用于追溯本次审核，不是运行项目所需路径。

|步骤|退出码或状态|实际结果|证据文件（均在ai_evidence/readme_audit_20261028/）|
|---|---|---|---|
|Python命令检查|0|Python 3.12.14|python_launcher.txt|
|创建全新venv|0|成功创建，未复制原venv|venv.txt、commands.json|
|无缓存安装requirements-dev|0|安装成功，包含直接依赖、pytest及requests|install.txt|
|pip check|0|No broken requirements found.|pip_check.txt|
|init-db|0|新库初始化为版本2|init.txt|
|交互式seed-demo|NOT_VERIFIED|12秒等待超时，无人值守没有完成隐藏密码输入；非正常进程退出码|seed_interactive.txt|
|环境变量seed-demo|0|演示账号准备成功，随机密码未写日志|seed_env.txt|
|README显式5001启动|PASS|首页200、登录200、health200；仅本轮服务被停止|startup.json、server_startup.txt|
|pytest -q|0|84 passed in 287.80s (0:04:47)|pytest.txt|
|phase4_http_smoke.py|0|筛选统计、本地资源、业务闭环及重启字段一致|http_phase4.txt|
|phase5_http_acceptance.py|0|result=PASS，19条拒绝记录均all_rows_unchanged=true，restart_persistence=PASS|http_independent.txt|
|源数据库及密钥指纹比较|PASS|本轮前后哈希一致|summary.json|
|源代码及README变更检查|PASS|git diff --exit-code -- README.md app tests requirements.txt requirements-dev.txt run.py退出0|本报告及reviewed_file_hashes.json|

HTTP验证使用真实子进程和独立临时SQLite，不调用应用业务函数来代替外部请求。验证包含学生创建、列表详情、维修接单、开始、完成、学生确认、评分、按类型和状态统计，再停止并启动新进程核对全部字段。独立脚本同时验证越权、重复接单、跳级、无效评分与重复评价拒绝后原行不变。

5001启动检查访问的是本轮seed后的新库，首页、登录和健康检查实际成功。完整业务链由README提供的HTTP脚本在另外的独立临时库中验证，不声称曾在5001浏览器人工点击完成该闭环。未执行浏览器操作，也未执行本轮人工输入密码和实体手机验证。

本轮未遇到需要修改依赖、源代码、测试断言或Schema才能继续的阻碍；唯一受限项是交互密码输入，采用README第48行已经列出的环境变量机制后继续。该选择及其缺少具体命令示例的问题已如实列入报告。

当前分支除原有未跟踪文件外，只新增本报告和本轮证据目录。两PDF及AI开发对话记录在本地存在，但不能仅由存在性推出导出完整、已脱敏、视频齐全或已交付。未经批准不修订关联旧文档，不创建Commit，不推送。

