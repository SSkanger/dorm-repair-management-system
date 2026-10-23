# AI辅助开发真实材料索引

这是一份证据索引及解释材料，**不是原始全量对话**。来源为本聊天实际用户消息、已存在阶段记录、真实命令输出和本地Git历史；不根据推测补造未发生的人工操作。

## 阶段证据

| 阶段 | 真实Prompt主题/AI参与 | 证据 | 人工决定或边界 |
|---|---|---|---|
| 0 | “现在只执行Phase0”，核对Word、需求映射、角色、状态、数据库和分阶段计划 | ai_evidence/phase0.md、DESIGN变更记录 | 用户独立审核通过，要求根规则位置、CSRF优先级、404/409隐私边界先修订 |
| 1 | 真实Flask/SQLite/服务端Session/CSRF基础，四演示账号，显式初始化 | ai_evidence/phase1.md、phase1/test_runs.txt | 用户批准基础阶段；要求核实实际依赖API，不硬编码演示密码 |
| 2 | 学生创建→SQLite→列表→详情、幂等、跨学生隔离 | ai_evidence/phase2.md、tests/test_tickets.py | 用户审核并授权版本保存，不提前维修动作 |
| 3 | 原子接单、四状态、本人确认与一次性评价、真实并发 | ai_evidence/phase3.md及phase3/输出 | 用户明确确认四状态，confirmed_at表达确认，不新增CONFIRMED；失败不得改数据 |
| 4 | 共享权限/AND筛选、同读快照、全部分页两种聚合、本地图表 | ai_evidence/phase4.md及phase4/输出 | 用户批准两图但仍区分老师“至少一种”；禁止跨阶段扩展 |
| 5 | “目标不是继续增加新功能”，新环境复现、独立验收、最终文档与材料 | ai_evidence/phase5.md、phase5/、docs/ | 用户批准本轮准备；未授权最终提交、邮件、推送；最终人工审核仍待进行 |

旧阶段记录中的awaiting_user_review等文字描述当时历史，不静默回填。后续聊天中的明确阶段通过是新的事实；“代理运行浏览器”不等于用户本人手动验收。

## 可以解释的真实问题

1. Phase1首次pytest曾为7 failed、9 passed：CSRF时限传timedelta，实际依赖按秒比较触发TypeError。改为7200整数秒，保留正确CSRF断言并回归。原阶段日志已记录，不能声称本轮再现过该缺陷。
2. Phase1审查发现测试配置应用前就写默认instance文件，调整配置顺序并增加隔离测试。目标是避免测试触碰正式存储，不靠清空数据库解决。
3. Phase2审查发现WTForms校验会重建错误列表，业务Token错误应在validate后追加。这是代码审查中发现并处理，不能编成一次未发生的pytest失败。
4. Phase4审查补充超长页码检查、图表枚举顺序，修正首页遗留功能说明；当轮没有失败pytest，不故意制造Bug。
5. Phase5复现工具在Windows隐藏密码输入等待，改用已有环境变量入口；独立HTTP脚本未关闭sqlite连接导致临时目录清理WinError32，显式closing修复。保留首次失败与修复后输出，业务规则未修改。
6. Phase5后续版本保存复测真实发现测试辅助工单使用时间戳作唯一提交标识，密集插入碰撞。数据库约束正确拒绝；测试辅助标识改UUID，新增冻结时钟下25条标识仍唯一的回归，不降低原统计/权限断言。失败和复测输出见phase5/precommit相关记录。

## 核心代码讲解

- 为什么原子接单：两名维修员可能同时看见PENDING。只有事务内条件UPDATE及rowcount=1能决定赢家，先查后无条件更新会覆盖负责人。
- 为什么前端隐藏按钮不够：请求可被自行构造。auth/服务层必须独立核验角色、可见范围、状态和负责人。
- 为什么确认评价不是新状态：维修工单已经COMPLETED，学生认可和反馈用时间/评分字段表示，避免统计分布被无必要状态拆分。
- 为什么失败不改数据：同一事务保存状态及相关时间，所有异常回滚，只有COMMIT成功才303。
- 为什么列表统计共享范围：否则会泄露他人数量或出现表格和图表矛盾；分页只是一段展示窗口，不改变全部匹配聚合。

## Git辅助证据

| 本地真实Hash | 内容 |
|---|---|
| 8c4b718cacd33917da3125c447f29d4f73a2725d | Phase1 foundation and authentication，含设计成果 |
| aa24e768f91aed112fc9de447b6b9f866b737b66 | Phase2 student repair requests and ticket management |
| d4a45b16bce4838f9bd4ab7acfb03edfe8d808cb | Phase3 repair workflow and student reviews |
| 87ef8398a9feb33d229700a6cc47c0927909d197 | Phase4 ticket filtering and analytics dashboard |

本轮开始main在87ef839，本地缓存origin/main仍aa24e76。上一轮fetch/push因github443失败，但API确认当时远程为祖先；本轮不推送、不重写历史，不声称远程已同步。Git只证明版本节点，不能替代真实对话、人工验收和视频。

## 原始对话材料现状与本人补充步骤

项目内未发现已提供的原始完整对话导出；阶段Markdown只是摘要。没有从未提供的文件或隐藏产品存储中提取聊天，也不凭记忆生成“原始消息”。

请本人从当前聊天实际可用的复制/导出界面保存原始消息，保留用户Prompt、Codex回复、实际错误/测试及人工批准。若界面无法一次导出，按Phase0–5分段复制，分别标起止消息和缺失范围；保持真实顺序。这里不承诺某产品版本必有特定导出按钮。

建议放在仅用于课程提交的 `AI对话/` 或被Git忽略的 `ai_evidence/conversation_export/`；附一页说明覆盖范围、脱敏和缺失。脱敏密码、Cookie、密钥、个人路径及无关个人信息时标注“已脱敏”，不要改测试结果。当前GitHub是Public，原始对话不默认推送。

请另行本人录制视频、完成最终现场复核和确认交付清单。没有这些真实材料，不勾选AI对话/视频齐全，不承诺具体成绩。
