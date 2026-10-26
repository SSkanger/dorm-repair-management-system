# 最终验收记录（含历史证据）

## 2026-10-26收尾版本：当前结论优先

后续文案精简补测：全量84 passed in 334.90s、独立HTTP退出0；代理浏览器实际检查1440和390px两图绘制、筛选/组合/清空、列表统计展开与收起。此前A26图表修复后的待验已在这些具体范围补证，其他待验和本人验收未冒称完成。见ai_evidence/ui_copy_cleanup.md。文案和CSS变更尚未Git保存，旧阶段输出保持历史原样。

以下是UI升级和16类报修扩展后的当前结论；后文2026-10-23的71/72项和旧图表截图是历史证据，不能覆盖本节或代替新版视觉复查。完整过程见`ai_evidence/finalization.md`。

| 项目 | 当前结论与证据 |
|---|---|
| 运行数据库升级 | PASS：真实默认库1→2，先备份；4账号及旧工单字段逐项核对，原库0单；integrity_check和foreign_key_check通过。finalization/runtime_migration.json |
| 自动化及干净环境 | PASS：全新目录/venv、无缓存安装、pip check、重复init/seed；84 passed in 218.18s，三套真实HTTP退出0，source_runtime_database_unchanged=true；见finalization/clean/pytest.txt、reproduction.json。首次旧HTTP五类断言失败保留在first_attempt/ |
| A03/A04/A08/A09及新类型 | PASS（代理浏览器实际操作）：其他展开且聚焦，空其他拒绝，填写家具损坏创建；切回空调类隐藏禁用旧文字，长描述成功；接单→开始→完成→学生确认→手机5分评价，SQLite字段核对 |
| A05/A19及授权统计 | PASS（真实HTTP重登录）：学生甲2单、学生乙0单、维修甲2单、维修乙1单；学生乙及维修乙对已由甲接走的详情404。finalization/browser_data_restart.json |
| A10/A11/A12 | 后端筛选和统计由完整pytest和三套HTTP独立核对；自定义文字统一归其他；数字表总和一致。新版筛选控件完整浏览器交互未补完 |
| A13持久化 | PASS：真实浏览器创建的两单停进程后启动新进程，重新HTTP登录四账号，工单全字段SHA256一致，家具损坏和5分仍在；不冒充重启后的浏览器手动重新登录 |
| A26新版UI | PARTIAL / NOT_VERIFIED：1440px首页、其他表单、维修概览/本人列表和390px详情/评价/菜单有截图；390/768/1366/1440长描述详情DOM宽度无溢出，菜单Escape/遮罩/Tab循环实际通过。16类图表实际发现绘制和拥挤问题，已改横向/禁动画并通过配置回归，但修复后浏览器再次禁用，最终图表绘制、列表展开图表、平板/1366视觉及离线重载仍待本人检查 |
| A25/A27材料 | 原始完整AI对话、本人真实视频仍缺失；没有报告全部交付完成。候选包仅代码和文档，见FINAL_HANDOFF.md |

业务状态仍四种、确认评价仍字段表达；没有为兼容新类别降低原权限/旧类别计数断言。本人/教师最终验收尚未发生。

## 以下为2026-10-23历史验收

核验日期：2026-10-23。正式依据：老师原始Word正文及内嵌九项评分表，本轮重新读取；与开发机整理资料交叉核对一致。A/E编号属于项目工程验收，不是老师发布的测试程序。阶段审核记录只是历史依据，下面结论来自本轮实际执行。

**判定口径**：PASS表示所列方法与范围实际通过；FAIL表示已知不满足；NOT_VERIFIED表示未执行或证据不足。代理浏览器操作不冒充本人现场验收；代码通过不等于五类材料全部交齐。

## 第8题正式功能及统一要求

| 正式要求 | 判定 | 实现与独立证据 |
|---|---|---|
| 学生提交报修 | PASS | app/tickets.py:new_ticket、services.py:create_ticket；test_student_creates_normalized_pending_ticket；本轮独立HTTP及浏览器实际提交两类工单，检查SQLite记录 |
| 列表和详情 | PASS | tickets.ticket_list/ticket_detail、queries.get_visible_ticket；test_student_list_and_detail_are_private_and_match_database；HTTP字段核对、浏览器实际详情 |
| 维修人员接单 | PASS | services.apply_ticket_action条件UPDATE；test_concurrent_actions_use_same_file_independent_connections；HTTP、浏览器接单，负责人为维修员甲 |
| 维修状态更新 | PASS | accept/start/complete路由及同一服务层；test_web_full_workflow_fields_and_buttons；HTTP/浏览器依次ACCEPTED→IN_PROGRESS→COMPLETED |
| 完成确认和评价 | PASS | confirm/review路由；test_early_and_repeated_confirmation_and_review、test_strict_rating_and_review_text_boundaries；HTTP与浏览器确认并保存5分短评 |
| 按类型/状态查询 | PASS | queries.parse_filters/ticket_overview；test_single_combined_clear_and_zero_filters；HTTP组合查询、浏览器照明+COMPLETED只剩1条，清空恢复2条 |
| 合理顺序及完成保护 | PASS | 服务层前置条件+条件UPDATE、schema跨字段CHECK；test_all_invalid_transitions_and_permission_boundaries_leave_full_row_unchanged；独立HTTP跳级/再次接单/再开始拒绝且全行不变 |
| 至少一种真实统计 | PASS | queries同快照GROUP BY；test_student_and_repairer_scope_aggregates_are_private、test_pagination_keeps_filters_but_not_statistical_limit；独立HTTP固定两单对照，浏览器柱状/环形图真实绘制 |
| 空报修、重复接单、非法跳转、无效评分提示 | PASS | 服务端400/404/409及字段错误；test_invalid_ticket_fields_are_rejected、test_strict_rating_and_review_text_boundaries；独立HTTP19次拒绝且业务行不变 |
| 持久化和真实闭环 | PASS | SQLite提交、固定文件路径；http_restart.txt、http_independent.txt；停止/新进程重启后重新登录，负责人/状态/确认/评分全字段一致 |
| 可正常安装启动 | PASS | 新目录、新venv、无缓存安装、pip check、重复init/seed；真实服务器健康200。详细命令和输出见phase5日志 |
| README含目标、栈、启动、功能、AI说明 | PASS | README已按实际实现整理；安装/初始化/CLI入口真实复现，互动密码自动化限制单列说明 |
| 真实演示视频 | FAIL | 项目内没有已提供的视频；docs/DEMO_SCRIPT.md只是录制脚本，需本人实际录制并播放检查 |
| 现场教师/本人独立操作 | NOT_VERIFIED | 不能用代理测试代替尚未发生的教师现场验收；需本人依脚本操作并确认 |

原Word只要求至少一种统计；本项目两图是批准的工程选择。不做平均维修时长或可选AI扩展，不构成遗漏必做功能。

## A01–A27工程验收映射

| ID | 判定与本轮证据 |
|---|---|
| A01 | PASS：全新环境安装、init/seed、首页/登录/health正常，非静态启动 |
| A02 | PASS：tests/test_auth.py全量；真实HTTP四账号登录、退出；浏览器学生/维修员登录切换 |
| A03 | PASS：规范化学生创建、服务端归属/PENDING和时间；独立HTTP及浏览器创建 |
| A04 | PASS：列表/详情查询与DB一致，浏览器实际查看 |
| A05 | PASS：学生乙详情404，HTTP/pytest/浏览器均验证，统计为0 |
| A06 | PASS：接单状态/负责人/时间；并发和真实HTTP通过 |
| A07 | PASS：按序开始完成，HTTP与页面操作均通过 |
| A08 | PASS：仅本人完成后确认，状态仍COMPLETED |
| A09 | PASS：确认后5分短评，保存/展示/重启一致 |
| A10 | PASS：单条件、AND、清空；非法枚举明确400 |
| A11 | PASS：固定两单类型照明1/网络1/其余0，DB及图表数字一致 |
| A12 | PASS：四状态随动作变化；学生确认评价不改变COMPLETED |
| A13 | PASS：两个真实HTTP脚本停止并启动新进程，重新登录比较全字段 |
| A14 | PASS：空/空白/4/1001描述拒绝，5/1000接受，缺位置/非法类别拒绝；全量pytest及独立HTTP |
| A15 | PASS：他人接走后404，本人重复409；负责人不覆盖，失败全行不变 |
| A16 | PASS：跳级/回退/非法动作拒绝；参数化各状态测试与独立HTTP |
| A17 | PASS：原负责人对已完成单再接/开始409；他人不可见404，数据不变 |
| A18 | PASS：合法前置工单上0/6/1.5/空/文本均400；独立工单1和5有效 |
| A19 | PASS：学生/维修员/负责人服务端隔离，HTTP和pytest核对全行 |
| A20 | PASS：过早/重复确认评价拒绝，原评分不覆盖 |
| A21 | PASS：同一临时文件SQLite、独立连接/客户端、Barrier竞争；唯一303及404，负责人对应赢家 |
| A22 | PASS：非法类型/状态/重复和未知参数/超长或负页码400，无效ID404 |
| A23 | PASS：CSRF开启、认证优先级、GET写405、URL越权、绑定SQL及XSS转义测试 |
| A24 | PASS：全新目录venv、无缓存安装，重复init/seed不破坏记录；真实启动及全量测试 |
| A25 | NOT_VERIFIED：Phase0–5摘要/实测/真实Git节点已整理；原始完整对话未提供，不能判材料齐全 |
| A26 | PASS（代理浏览器范围）：1366px桌面、请求390px手机视口、两图绘制、长描述/筛选/空态、真实完整流程；本人设备与实际断外网待验 |
| A27 | FAIL：源代码/README/设计已准备；真实原始对话与演示视频缺失，最终包未定稿/未提交 |

A15隐私策略已在Phase0人工审核固定；原资料“业务冲突提示”不能解释成必须向无权用户泄露409。无权404、可见冲突409，各测试预期未根据错误实现事后改低。

## 本轮命令与证据

| 执行 | 结果/证据文件 |
|---|---|
| 全新venv + pip install --no-cache-dir | 安装成功，phase5/install.txt；Python3.12.14、SQLite3.53.1及包版本见versions.txt |
| pip check | 退出0，No broken requirements found，pip_check.txt |
| flask --app run:app init-db / seed-demo，各重复一次 | 均退出0，init/seed/init_repeat/seed_repeat.txt；自动化种子使用环境变量随机密码 |
| 全量pytest | 首次本轮71 passed in 188.22s；工具修复后重新全新目录/venv运行最终71 passed in 214.80s，退出0；phase5/pytest.txt |
| phase4_http_smoke.py | 退出0，筛选统计、业务闭环、真实进程重启；http_restart.txt |
| phase5_http_acceptance.py | 修复工具连接未关闭后退出0；19个非法动作全行未变，固定两类/两状态计数；http_independent.txt |
| 浏览器实际操作 | browser_dashboard_desktop.jpg、browser_dashboard_mobile_top.jpg、browser_dashboard_mobile_chart.jpg、browser_review_mobile.jpg等；不生成假截图 |
| 第三方静态资源 | 本地Chart.js 4.5.1、MIT、SHA256、同源引用及实际绘制已查；未使用Bootstrap；详THIRD_PARTY_NOTICES.md |

所有测试和页面演示使用独立存储；原运行数据库不重置。两个真实HTTP脚本使用随机临时密码，日志不含密码/Cookie/密钥。自动化不是教师现场通过证明。

修复后第三次全新目录复现从建venv到最后一个HTTP脚本完整退出0，见reproduction.json，原项目运行数据库SHA256在流程前后相同。另真实停止浏览器演示服务、启动新进程、退出重新登录，浏览器看到相同负责人/时间/5分短评；浏览器独立业务数据库SHA256在重启前后也相同，证据browser_restart_ax.txt和browser_checks.json。

## 真实失败、修复与限制

- 首次复现工具向隐藏密码提示管道输入，在Windows等待，核对并终止仅该子进程后记录退出1；改为项目已有环境变量入口，加超时。见first_attempt.txt。
- 新独立HTTP脚本的业务断言已完成，但SQLite连接上下文不自动close，Windows清理临时目录WinError32导致退出1；保留http_independent_first_failure.txt，改contextlib.closing后重跑退出0。不能把首次JSON中的PASS遮盖其退出失败。
- README/设计早期写Bootstrap、本地配置加载、完整结构校验及直接读取fixture等规划与实现不一致，本轮按代码修正文档，没有擅自加框架或改业务规则。
- 真正断开外网后浏览器重载未执行；已检查本地资源HTTP200和无外部引用。实际触控设备、其他浏览器兼容性、教师现场验收未验证。
- 本轮未发现需要修改业务状态或降低测试断言的缺陷；新增脚本缺陷已修复并保留原失败记录。

## 九项评分风险（不预测成绩）

| 维度/官方分值 | 已有依据 | 剩余风险与本人动作 |
|---|---|---|
| 核心功能40 | 六类必做、筛选、两图均有测试和真实操作 | 本人应独立演练全部按钮，准备现场新工单，不只播放固定数据 |
| 正确性与数据闭环10 | DB全字段比较、统计对照、真实进程重启 | 使用自己的最终运行目录再重启确认；勿误用不同环境变量指向不同库 |
| 业务规则与异常10 | 并发、非法跳转/评分、权限、CSRF、回滚 | 解释404/409隐私边界和评分合法前置；不要靠隐藏按钮作证明 |
| 代码结构与质量10 | 两表/四状态、参数绑定、服务端校验、清晰模块 | 非生产认证平台；无迁移框架、审计历史或多节点支持，应能说明取舍 |
| AI辅助开发10 | 真实Phase记录、Prompt摘要、失败修复和Git | 原始完整对话缺失是主要材料风险，需本人导出/复制和标明范围 |
| 界面美观5 | 桌面/手机代理截图、实际图表绘制 | 本人屏幕/触控与离线图表仍需检查；代理检查不替代主观评分 |
| 演示视频5 | 中文录制脚本已准备 | 视频尚未录制提供，须本人录制、播放及查音画 |
| README5 | 命令已在独立环境执行，说明完整 | 本人解压路径/包源/端口可能不同，最终包再按README复现 |
| 设计文档5 | 对应实际模块、ER/状态/接口/事务 | 本人需读懂并现场解释，格式要求如有新增通知需核对 |

不自行承诺具体成绩。准确截止时刻、邮箱与压缩包规范需本人按老师正式通知确认。

## 后续版本保存复测补充

用户随后授权提交并推送当前版本。本次首轮提交前回归为1 failed、69 passed、1 error，原因是测试辅助函数用时间戳当submission_token，密集插入可能重值。数据库唯一约束正确拒绝；未修改业务代码。辅助函数改用UUID请求标识，并增加冻结时钟25条记录仍唯一的回归测试；专项3 passed，完整复测结果见ai_evidence/phase5/precommit_tests.txt。上文71项是Phase5独立环境的真实历史结果，不用它覆盖这次失败或冒充最新复测。

修复后最新全量为 **72 passed in 152.16s**，退出0，新增1项用于锁定时钟碰撞问题，未减少旧断言。
