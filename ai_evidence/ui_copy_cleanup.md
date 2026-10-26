# 界面文案精简

日期：2026-10-26。真实Prompt来源：用户提供首页/表单/统计三张截图，指出“真实工单记录 · 角色权限保护 · 处理进度可查”“筛选与统计仍归入其他”“仅统计我的报修 · 全部匹配结果，含所有分页”等解释过多，要求审视项目、减少无用信息、保证UI简洁。本记录是摘要，不冒充完整对话或本人审核。

## 改动

- base：首页/各页侧栏底部技术说明删除，页脚只保留系统名。
- index：删除技术保证口号、流程免责声明和重复特色区；主说明缩为“提交报修，随时查看维修进度”。
- login：删除权限宣传及初始化命令/管理员说明，保留账号密码和错误。
- portal：删除范围/快照说明、最近5条排序说明、底部两个解释卡；保留身份、指标、列表和快捷操作。
- new：删除页头重复说明、右侧帮助卡及幂等解释；其他只提示必填与50字符上限，描述保留5–1000限制，原aria关联和字段错误不变；CSS去掉第二列布局。
- list/work_queue/filters/detail/dashboard/statistics：删除重复权限、数据口径、刷新时间和冗长引导；保留总数、筛选、分页、状态、数字表及必要反馈，空状态缩短。
- charts.js：正常及零数据时不显示解释；仅失败时取消hidden并提示查看数据。图表算法和数据未改。check_chart_config.cjs改为严格断言正常反馈为空且隐藏，原图表数据断言保留。

未改后端Python业务文件、数据库、认证、角色、状态机、CSRF或幂等。未修改已有pytest。只调整显示文案和必要布局，没有仅用CSS隐藏技术文字冒充删减。

## 实际验证

| 命令/方法 | 实际结果 |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | 退出0，84 passed in 334.90s；ui_copy_cleanup/pytest.txt |
| `.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py` | 退出0，完整闭环、19次拒绝全行不变、筛选统计及重启持久化PASS；ui_copy_cleanup/http.txt |
| `node scripts/check_chart_config.cjs`、`node --check app/static/js/charts.js` | 退出0；配置数值保留，正常反馈为空 |
| `git diff --check` | 退出0 |

浏览器工具本轮可用；使用独立instance/finalization-browser.sqlite3既有两张真实验收单，只读访问和登录，不修改用户运行库。实际浏览1440首页/登录/概览/其他表单/统计，保存home_1440.png、form_1440.png、stats_1440.png；390px统计截图stats_390.png。其他输入框正常显示，已不含技术说明。两图实际绘制：空调1、其他1；待处理1、已完成1，合计2，与表一致。

浏览器实际选择其他→匹配1，叠加PENDING→0，清空→2；进入列表，展开/折叠/再展开，均执行并保存list_expanded_390.png。初次用Playwright按钮角色找summary未匹配（原生AX呈按钮，DOM呈generic），读取DOM重新按实际文字定位成功；这是工具定位问题，没有改应用冒充修复。

## 实际发现及修复

手机列表首次完整截图宽575px，DOM确认scrollWidth=575>innerWidth=390。宽表格中的绝对定位sr-only表头跑出滚动容器的裁切范围；为table-wrap增加position:relative，使其成为定位容器。重新加载后文档宽390，展开统计后文档宽375，表格640在341px容器内部滚动。原始图保存list_expanded_390_before_fix.png，不抹去失败证据；修复后图是同一文件夹的list_expanded_390.png。该单行CSS修复后直接用真实浏览器验证，不把Python测试当布局证明，也未为此重复无关全量测试。

临时视口已reset，验收标签已关闭。5003独立验收服务结束后停止；用户原5001进程未擅自终止，可能仍缓存旧Jinja模板，需停止重启并Ctrl+F5后查看本轮更新。

本人或教师仍未审核本轮文案，真实触控/断外网及其余视口未全面检查。旧截图是旧版本证据，不覆盖。本轮不自动Git提交/推送；交付候选清单按最新工作区重新生成，视频和原始对话仍缺。

## 后续用户授权版本保存（2026-10-26）

用户明确要求“将当前版本项目提交并推送到仓库”。本次重新执行`python -m pytest -q`，实际退出0，**84 passed in 231.03s**（终端真实输出，未用前轮结果代替）；`node scripts/check_chart_config.cjs`退出0。`git fetch origin`成功，远程main是本地HEAD祖先，原有50ba4d2尚未推送，无历史分叉。检查改动、.gitignore和待提交文本，未发现运行库/Session/凭据/教师原始资料；学生甲6条用户要求的演示报修仅在被忽略的instance数据库，不进入提交。创建本轮界面精简提交并普通推送，不force、不覆盖历史；实际Hash及推送结果以最终报告和Git记录为准。原视觉待验和材料缺失不因版本保存改成通过。
