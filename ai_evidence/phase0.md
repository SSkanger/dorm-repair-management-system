# Phase 0 真实开发证据

- 日期：2026-10-23（Asia/Shanghai）。
- 状态：user_approved。用户于 2026-10-23 明确回复“Phase 0 通过，批准进入 Phase 1”，并提出三项设计修订；修订已写入 DESIGN.md 第13节。
- 关键 Prompt 来源：本次 Codex 对话用户消息，忠实摘录：“本轮只允许完成 Phase 0，不要开始编写应用业务代码，不要直接执行 Phase 1–5。”“请将完整的技术设计方案写入项目根目录的 DESIGN.md。”用户还要求完整阅读初始化资料、对照正式 Word、设计权限/状态/数据/验收/后续计划。此处为摘录与摘要，不是完整原始对话导出。
- 原始对话导出：尚未提供/保存；本文件不能替代。人工审核结论：2026-10-23 用户明确通过 Phase 0 并授权 Phase 1。

## 实际完成的动作

1. 用 Get-Location、rg --files 检查目录，发现只有嵌套初始化资料包，无应用。通过 Get-Content 完整读取指定 Markdown/fixture，并补充读取初始化说明、演示脚本、证据模板及各阶段提示词。原文件未修改。
2. 读取 documents 技能及工作区依赖路径，使用内置 Python zipfile/ElementTree 提取 Word 全文和唯一内嵌 PNG。没有安装软件、修改 Word 或创建应用数据库。
3. 首次 Python 标准输出中文出现编码乱码；随后设置 PYTHONIOENCODING=utf-8 重新提取并成功读取全部正文，保存 official_word_text.txt。首次内嵌透明图片显示为黑底难以识别，使用 Pillow 白底合成后，通过 view_image 成功查看九项评分。白底预览仅用于原图阅读，没有改写评分内容。
4. 核验原文第8题、统一要求与 docs/00 整理稿一致；内嵌图中评分为40、10、10、10、10、5、5、5、5，合计100。未发现需求冲突；未核验课堂原始录音、邮箱或准确截止时刻。
5. 用 apply_patch 写入根目录 DESIGN.md。明确真正服务端 Session、两业务表、四状态、确认后评价、原子更新、统计范围、输入边界和未实现状态。保留原 fixture 的期望，明确 assigned_to/assignee_id 映射、S16→S17清空筛选及补零项口径。
6. 编写并实际运行仅检查设计资料的 verify_design.py，输出保存 verification.txt。12项文档检查通过，进程退出码0；这不是应用测试。

## 实际文件产物

- DESIGN.md：完整技术设计、需求与评分映射、验收和阶段计划、待确认问题。
- ai_evidence/phase0.md：本记录。
- ai_evidence/phase0/official_word_text.txt：原 Word 正文提取。
- ai_evidence/phase0/source_media/image1.png：原 Word 内嵌评分图片副本。
- ai_evidence/phase0/source_media/scoring_on_white.png：便于阅读的白底预览。
- ai_evidence/phase0/verify_design.py：资料/文档核验脚本，不是业务代码。
- ai_evidence/phase0/verification.txt：该脚本真实输出，含原 Word 和 fixture 当前 SHA256。

## 实际验证命令与结果

在项目根目录 PowerShell 执行：

```powershell
$env:PYTHONIOENCODING='utf-8'
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" 'ai_evidence\phase0\verify_design.py'
```

实际结果：`Result: 12/12 document checks passed`，退出码0。完整输出见 phase0/verification.txt。该脚本检查资料存在、fixture保持NOT_RUN/场景编号/类别状态、需求和验收条目、阶段计划标题、评分分值求和、提取文件、无app/instance及人工审核门槛；不证明设计没有缺陷或业务通过验收。评分图片内容对照由本轮视觉读取完成，不由该脚本自动识别。

## AI 建议与人工决定

建议采用现有初始化包的轻量单体方向，补上真正服务端Session和PRG不足以防双击的幂等约束；统计随权限范围及筛选，所有动作由服务端条件更新。建议待用户整体审核，无任何决定已被人工批准。

## 尚未执行和下一阶段门槛

未创建 Flask 应用、schema.sql 或数据库，未安装应用依赖，未运行 pytest/HTTP/浏览器业务测试，未执行 Git 初始化/提交，未录屏、未导出完整对话、未向任何人发送材料。A01–A27、S01–S18业务场景全部未执行。等待用户审核 DESIGN.md 并明确授权 Phase 1 后继续。
