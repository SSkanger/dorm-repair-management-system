# Phase5：最终交付准备与独立验收

日期：2026-10-23。真实授权来源是本聊天用户消息“Phase4已完成并经过阶段审核，现正式批准进入Phase5：最终交付准备与独立验收”。本阶段不扩展业务功能，不提交作业、发邮件、创建Git提交或推送。最终人工审核待进行。

## 1. 本轮Prompt忠实摘要

用户要求重新读取原始Word及规则/设计/矩阵；全新目录和venv安装、真实HTTP闭环/异常/筛选/统计/进程重启；真实浏览器可用则检查；完善README和设计；整理真实AI材料、中文录制脚本及最终五类交付清单；缺对话/视频不能称全部完成；逐项PASS/FAIL/NOT_VERIFIED，不凭前轮报告自动通过。

本记录不是原始完整AI对话导出。项目内未发现用户已提供的完整原始导出或视频，不凭记忆补造。本人需按docs/AI_PROCESS_INDEX.md和DEMO_SCRIPT.md补充材料。

## 2. 起点、来源核对和计划

开始目录为项目根，main，工作区干净；HEAD为87ef8398a9feb33d229700a6cc47c0927909d197，本地缓存origin/main为aa24e76，ahead2。上一轮推送失败是已发生事实，本轮没有联网Git写操作。

重新读AGENTS、PLANS、DESIGN、初始化专项需求、状态权限、验收矩阵、AI规范、交付及课堂说明，查app/db/schema/auth/tickets/services/queries和测试。重新提取Word通用条款/第8题正文，评分图片先透明背景不可读，白底渲染后真实查看九项40/10/10/10/10/5/5/5/5=100，与整理表一致。原图片/正文不公开复制进交付包。

计划改README、DESIGN、PLANS，新增docs中的验收/AI索引/录制脚本/交付清单和实际文件清单；新增仅供验收的复现与独立HTTP脚本、phase5证据。不更换架构、不改状态/权限、不重置原库。

## 3. 实际实施及工具错误

`scripts/phase5_reproduce.py`以允许目录复制源码到系统临时新目录，使用基础Python创建新venv（没有system-site-packages），无缓存pip安装。环境移除继承的DORM_REPAIR配置，避免指向原运行数据库。执行pip check、版本记录、CLI init/seed各两次、全量pytest、原Phase4 HTTP和新独立HTTP；输出去掉用户路径、随机密码，不传Cookie/密钥到记录。

真实问题1：第一次隐藏密码管道输入在Windows等待。核对仅本轮seed-demo子进程身份后停止；子进程退出4294967295，复现工具退出1。保留first_attempt.txt，改为已有DORM_REPAIR_DEMO_PASSWORD随机密码入口，并加子进程超时。没有改密码散列、CSRF或业务接口。人工终端隐藏输入与无人值守管道不能混称。

真实问题2：独立HTTP第一轮业务断言已经完成，但sqlite3连接的with只提交/回滚、不自动close，导致Windows临时目录清理WinError32退出1。保留http_independent_first_failure.txt，即使它包含先前打印的JSON PASS也不掩盖退出失败；使用contextlib.closing后独立HTTP实际退出0。日志路径脱敏规则扩展到反斜杠转义形式，保留失败原因和调用位置。

另一次README编辑工具调用被拒，原因是单次patch同时删除和新增同一路径；没有应用该patch，改用文本写入完成。这是编辑工具错误，不伪装业务Bug。

没有删测试、降低断言、关闭CSRF或修改既定状态/隐私规则。业务代码本轮保持不变；真实修复限于新增验收工具的输入和连接生命周期。

## 4. 独立验收内容和证据

新独立HTTP脚本只导入requests和标准库，不调用app服务函数决定预期。使用新文件SQLite、四账号、随机密码、真实Flask子进程；按固定照明/网络两单验证完整流程，并直接sqlite3比较失败前后全部业务行。19次非法动作包括错角色、同Token改内容、过早/重复确认评价、学生维修动作、他人/本人重复接单、跳级完成、终态再接/开始、他人确认及空/0/6/1.5/文字评分，预期400/403/404/409预先固定。另核对GET写405、非法CSRF400、匿名401、筛选400、资源200和真实重启全字段一致。

第二次干净环境全量pytest为71 passed in 188.22s，原HTTP退出0；工具清理失败后独立重跑退出0。又从新的全新目录/venv运行整条修复后复现，最终结果见phase5/pytest.txt和reproduction.json；前一pytest输出保留为pytest_before_tool_fix.txt，不用前轮Phase4结果冒充本轮。

环境Python3.12.14、SQLite3.53.1，直接依赖与requirements一致，完整实际包版本见versions.txt；pip check无冲突。install.txt记录实际无缓存下载；CLI init/seed重复成功，已有数据不被自动清空。所有正式业务数据库均留在原处。

浏览器本轮工具库存恢复可用，先阅读computer-use技能与本地Web检查说明，再在第二个干净环境的独立browser.sqlite3上操作localhost:5001，未使用原端口5000的数据。实际点击学生登录/两类创建、维修员登录/接单/开始/完成、原学生确认/5分评价、AND筛选/清空/无结果、非法状态400及学生乙404/零统计。不是声称用户亲自操作。

截图为实际页面：browser_dashboard_desktop.jpg（请求1366×1000）、browser_dashboard_mobile_top.jpg、browser_dashboard_mobile_chart.jpg、browser_review_mobile.jpg等（请求390×844；含滚动条时内容宽375）。统计和详情DOM页面宽等于内容宽，没有整页横向溢出；长描述正常换行。首轮正常统计页读取浏览器error日志为空。测试后恢复临时视口；历史阶段的浏览器未验证记录保留为历史，不倒填。

实际断外网后浏览器重载、用户本人手机触控/其他浏览器、教师现场验收仍未验证；只以本地资源源码检查/HTTP200和本轮截图证明已执行部分。截图、摘要和脚本不充当演示视频。

## 5. 文档、AI过程与材料边界

README按真实自有CSS而非Bootstrap写技术栈、命令、账号、角色完整使用、测试、目录、限制和错误处理。DESIGN按实际ER/字段、状态、接口、事务及查询重写，保留第13节历史变更，修正过度宣称的配置文件加载/完整表签名校验/额外时间CHECK/直接读取原fixture等。没有为迎合文档额外加功能。

docs/ACCEPTANCE_RESULTS.md给正式要求和A01–A27逐项结论及九项评分风险；docs/AI_PROCESS_INDEX.md索引Phase0–5和真实Bug/人工决定/本地Git哈希；docs/DEMO_SCRIPT.md提供中文逐步录制讲解；docs/DELIVERY_CHECKLIST.md说明五类材料、排除项及本人待办。最终未提供原始对话和视频，材料齐全项为FAIL/NOT_VERIFIED，不自评具体成绩。

当前原始对话须本人从真实聊天导出或复制，说明范围与脱敏；不读取隐藏产品存储或伪造聊天。不自行录制、包装假视频；视频需本人实际录制播放。准确截止时刻/邮箱与格式以老师正式通知为准，课堂日期摘要不冒充最新通知。

## 6. 最终状态

本轮修改保留工作区，等待最终人工审核。没有Git提交、push、邮件、云发布或最终作业提交。没有生成声称五类材料齐全的最终压缩包。收尾实际命令和结果追加于下，不预填未发生的测试或人工结论。

修复后的第三次全新目录/venv复现已完整退出0：最终全量 **71 passed in 214.80s (0:03:34)**，两个HTTP脚本退出0，pip check无损坏依赖，init/seed及重复执行均退出0。reproduction.json确认原项目运行SQLite文件哈希未变。此前188.22秒记录和两个真实工具失败保留，不以最终成功覆盖历史失败。

另对独立浏览器演示服务实际停止/新进程启动，退出并以学生甲重新登录，页面显示原负责人、全部时间和5分短评，dashboard仍照明1/网络1、PENDING1/COMPLETED1；业务SQLite哈希重启前后完全相同。本轮已关闭代理创建的验收标签，恢复视口；没有关闭用户原有5000端口页面或重置其数据库。

收尾补充.gitignore排除SQLite伴随journal/wal/shm文件及课堂私有对话/视频目录，避免后续误推Public仓库。交付目录清单只列安全源码/文档/实际证据，不含原始课程资料、运行instance或虚拟环境；原始对话和视频仍需本人另加进课堂提交包。

收尾实际执行 `python -m compileall -q app scripts tests` 和 `git diff --check`，均退出0（后者仅Windows换行提示）；全部Git候选文件路径/凭据格式及Markdown链接检查无问题。`git diff --exit-code HEAD -- app tests requirements.txt requirements-dev.txt run.py`退出0，确认本轮未改业务实现或降低旧测试断言。第三方资源来源/许可证核查见docs/THIRD_PARTY_NOTICES.md，干净环境Python包元数据原样记录，未把缺失许可证字段伪称已核实。

## 7. 后续用户授权版本保存

用户在本聊天随后明确要求“将当前版本提交到github仓库并推送”。此前“不提交/推送”描述的是Phase5准备时的授权边界；本次仅授权版本保存，不把它解释为本人手动验收、最终作业提交或视频/原始对话已齐全。

提交前main为87ef8398a9feb33d229700a6cc47c0927909d197，工作区为Phase5文档、验收脚本和真实证据。origin为用户指定仓库。本次 `git fetch origin` 实际退出0；远程main仍aa24e768f91aed112fc9de447b6b9f866b737b66，`git merge-base --is-ancestor origin/main main`退出0，差异为远程0/本地2提交，没有分叉。GitHub CLI核实仓库PUBLIC。普通推送会连同未推送的Phase3、Phase4一并快进同步，不使用force/reset/rebase。

按本次实际状态重新执行完整pytest，输出另存phase5/precommit_tests.txt，不以先前214.80秒结果替代本次结果。暂存前检查全部候选文件，真实运行数据库、Session、秘密、私人对话及教师原件不得进入提交；已有浏览器截图仅是独立虚构账号验收数据，不含真实用户身份。最终哈希、推送结果及同步状态以本次工具输出和最终报告为准，不预填未来成功。

本次首轮提交前测试真实失败：`1 failed, 69 passed, 1 error in 147.03s`，退出1，保留phase5/precommit_first_failure.txt。两处均在tests/test_workflow.py的prepared_ticket数据准备函数，使用utc_now作为submission_token，密集创建时当前时钟值重复，触发数据库UNIQUE(student_id,submission_token)。这不是业务幂等约束错误；应用创建仍使用随机Session请求标识。

最小修复：仅将测试辅助函数的请求标识换成uuid4.hex，保留显式固定业务时间和所有正确断言；新增冻结app.db时钟后创建25条记录仍各有独立标识的回归测试。新用例与两个原失败用例专项为`3 passed in 8.01s`、退出0，见precommit_targeted_tests.txt。随后重跑完整测试，不删除用例或降低唯一性/统计断言。

修复后本次完整回归实际为 **72 passed in 152.16s (0:02:32)**，退出0，完整输出保存在phase5/precommit_tests.txt。业务代码/依赖/schema均未修改；只有测试辅助标识与新增回归用例改变。版本提交消息为 `chore: prepare phase 5 delivery and independent acceptance`。暂存内容安全扫描及diff检查通过后才创建提交；提交自身不预填其Hash或推送成功状态，真实结果由本次工具输出和最终报告记录。
