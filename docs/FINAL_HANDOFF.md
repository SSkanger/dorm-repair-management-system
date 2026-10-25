# 最终收尾与本人交付步骤

本文件针对2026-10-26收尾版本。代码候选包不等于完整课程作业；原始AI对话与真实视频仍需本人提供，禁止以阶段摘要或代理截图代替。

## 已完成的本机准备

默认运行库已显式备份并升级至版本2，4个账号保留，原库当时0条工单。备份在instance中，不能提交Git或给公开源码包。用户名仍是student_a/b、repairer_a/b；密码不变，无管理员账号。浏览器与自动化验收使用单独数据库，不向默认库灌入演示工单。

以后直接启动：

```powershell
.\.venv\Scripts\python.exe -m flask --app run:app run --host 127.0.0.1 --port 5001 --no-reload
```

打开 http://127.0.0.1:5001/ ，Ctrl+F5刷新。停止服务用Ctrl+C；不要删除instance更新UI。已有其他版本1数据库仍需停止相应服务并在相同配置下执行README中的migrate-db。新目录用init-db直接建版本2。

## 本人还需完成

1. **实际视觉复查。** 按UI_MANUAL_CHECKLIST补充本轮未完成项，尤其更新后横向16类别柱状图、状态环形图、列表内统计展开/收起、390px表单和真实触控。浏览器工具中途再次禁用，不能把旧截图当新版图表修复通过。检查两表合计和图表都等于真实匹配数；断外网强刷也需本人实际执行。
2. **导出真实对话。** 从本项目真实聊天复制或使用你客户端提供的导出方式，保留需求、阶段审核、修复和测试上下文及实际顺序。放入被Git忽略的AI对话/目录；标明起止范围和缺失，不补造对话。脱敏口令、Cookie、密钥、无关个人信息，并注明脱敏。ai_evidence和AI_PROCESS_INDEX只是摘要/索引。
3. **亲自录制视频。** 按DEMO_SCRIPT操作，展示当前侧栏、其他自定义类型、完整维修闭环、异常、筛选和真实统计，再停止重启核对。不要录下口令或凭据。录好后实际播放检查音画、完整流程、文件可打开，再放演示视频/目录；脚本不是视频。
4. **组合最终五类材料。** 源代码、README、DESIGN、真实对话、本人视频齐全后，用老师要求的学号姓名命名目录，排除.git/.venv/instance/数据库/Session/.env/缓存/秘密和教师原始参考资料。解压到另一目录按README复现，确认文档、对话和视频均可读。
5. **核实老师最终通知。** 课堂整理提到2026-10-30之前提交；准确时刻、邮箱、文件格式和命名仍以正式通知为准，由本人最终确认并提交。本工具不会发送邮件或上传作业。

## 候选包与再次验证

维护者使用Git库存清单生成安全的代码/文档候选包（不含视频、对话）：

```powershell
.\.venv\Scripts\python.exe scripts/prepare_delivery.py
```

输出在instance/delivery/source-docs-candidate.zip，打包后逐个核对SHA256；修改代码或证据后应重新生成。docs/DELIVERY_MANIFEST.txt包含新增UI、类型扩展、测试和证据，排除清单自身的循环哈希。不能把候选包改名后就宣称五类材料齐全。

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/phase4_http_smoke.py
.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py
.\.venv\Scripts\python.exe scripts/category_http_smoke.py
```

若需要再次全新目录、全新venv及无缓存安装复现，可用`python scripts/phase5_reproduce.py --evidence-dir ai_evidence/new_reproduction`，使用新的目录保留旧证据。维护用Node配置检查`node scripts/check_chart_config.cjs`只验证图表配置和取值，不冒充实际渲染；应用运行不需要Node。
