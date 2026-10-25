# 报修类型及“其他”自定义输入扩展

日期：2026-10-23。来源：本聊天用户提供类别截图，并要求“报修类型中能包括图片中的这些报修类型，并且选择其他选项后可以弹出一个文字输入框让用户文字输入类型”。这是原始请求的关键摘录，本记录不是完整聊天导出。不声称已获本轮人工验收，不创建Git提交或推送。

## 实际改动

本体类、电类、电梯类、道路景观类、给排水类、空调类、开水饮水类、门窗五金类、暖气类、洗浴热水类、消防设施类和其他均有对应选项。原照明、水管、门锁、网络保留，避免改变旧工单含义。没有实现图片中的搜索弹层或字母索引，用户要求的重点是选项及其他文字输入；仍使用原表单原生下拉框。

- constants.py统一16项白名单；schema.sql扩展CHECK并增加category_detail；数据库版本2。
- tickets.py增加字段白名单和条件验证：其他必须trim后1–50字符，非其他不允许提交具体类型。
- services.py随工单INSERT保存具体类型，并把该字段纳入幂等比较；修改文字后重发相同Token冲突409。
- queries.py读取附加文字；new.html及ticket-form.js实现选择其他后就地展开、聚焦输入，切走禁用字段；模板转义后在列表、详情、概览显示。
- db.py提供显式migrate-db，先备份、事务复制核对并替换工单表，恢复索引和外键检查，失败回滚；原业务数据字段不变。新库直接版本2，未知库不自动迁移；备份位于原库旁，受.gitignore的sqlite3规则保护。
- tests/fixtures/schema_v1.sql取自本地HEAD原始schema，作为独立真实旧结构夹具；新增test_category_extension.py四项测试。
- 旧test_queries_stats.py及phase5_http_acceptance.py只为新枚举补十一项明确零值预期；原五类和全部权限/总数断言保留，不把业务输出反过来当预期，不降低断言。
- README、DESIGN、PLANS记录当前字段和升级步骤；scripts/category_http_smoke.py提供独立真实HTTP验收，使用临时数据库、随机密码和服务端Session，不写默认运行数据。

## 实际验证

上一轮同工作区完成的全量为80 passed。新增专项命令为：

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_category_extension.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/phase5_http_acceptance.py
.\.venv\Scripts\python.exe scripts/category_http_smoke.py
node --check app/static/js/ticket-form.js
.\.venv\Scripts\python.exe -m compileall -q app scripts/category_http_smoke.py
git diff --check
```

专项首次4 passed in 6.00s；备份连接改为显式closing后又重跑专项，4 passed in 10.00s，退出0，最终输出见category_extension/focused.txt。全量84 passed in 308.95s，退出0，见category_extension/regression.txt。独立既有HTTP完整闭环退出0，19次拒绝检查全行不变，真实停止/重启持久化PASS，新增类别在旧固定数据中均为0，见category_extension/http.txt。JS语法、Python编译及git diff --check均退出0。

新增真实HTTP验证空其他400→同Token补文字303→原样重发303→换文字409；核对数据库仅一条其他/家具损坏/PENDING，过滤统计其他1，静态脚本200。最终退出0，见category_extension/new_http.txt。

## 真实问题与修复

新HTTP脚本首次所有业务断言已通过并输出PASS，但清理临时目录时报WinError32，整体退出1，不能把该次称为成功。原因是sqlite3连接的with上下文只提交/回滚，并不自动close，脚本仍持有打开连接。改用contextlib.closing后重新执行，整体退出0；数据库备份连接也显式closing。首轮失败保留在first_http_failure.txt，仅对本机用户目录做脱敏，并在文件头说明；没有删除业务断言或忽略清理异常。

## 仍待本人执行

本轮未对用户正式运行库自动执行迁移；请停止原服务后按README运行migrate-db再重启，不能删除旧库。迁移在独立版本1临时库验证了备份内容、原ID和全字段、外键、重复执行、非法约束及故障回滚，不冒充正式库已升级。

浏览器此前被Work设置禁用，本轮其他输入框真实展开/焦点/手机布局未验证；JS语法和真实HTTP不冒充视觉检查。人工检查：选择其他→出现输入框→空白提交有字段提示→填家具损坏提交→列表详情可见且统计计入其他；切回空调类隐藏输入框，合法提交不携带旧其他文字。重启后具体类型仍可见。已有旧其他工单不强制补写文字。旧UI阶段的人工待验项继续保留。
