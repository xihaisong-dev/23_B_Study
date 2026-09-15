# 论文验收 Agent 官方格式复核交接

- 角色：W（论文与验收规划）。
- 状态：2023 官方模板和提交规范复核已完成；正式论文写作与最终验收仍为 `BLOCKED`。
- 工作树与分支：`worktrees/paper`，`agent/paper`。
- 输入版本：本轮同步基线提交 `542427ab5de6799783d891d53f2a9ebfd2d4c418`；已包含主分支 `92d12dcc52325f43989984ea19574c0caa5e2405` 的 D-005、官方格式和来源证据。
- 治理输入哈希：`workflow.json` SHA-256 `486ba2eaa9b2e48a294735e77ea2fa77d4509406e3054e5558970d666d1ea672`；`rules.json` `326070b77e521d7f65f073a6347701cc97d50b2830d9d0c0c5e0fb34d78b8f15`；`semantic_contract.json` `bdbe1b5a454e1ba56d47201ff942f94844165e5550755cc4195af50da6f0cb62`；`input_manifest.json` `61502af16786cc5ae07448a23f8fb0b236ea3f798d5a9f613cf2b9b6cf4f7209`；`DECISIONS.md` `a78411b1b9bd7f60217157a23a726338df6a2a5d723d0004f65c457d178ae174`；`official/2023/SOURCES.md` `6deafa13bfc4210e3aa54fe21f30593a4ca06955632bb7c652079ca4cd259364`。
- 官方文件哈希：`paper_format.doc` SHA-256 `9d277f47898ca7a009dfedef2a407a9e6af560532a7b3e5e70312a561f3d9f04`；`paper_template.doc` `64ad3f75fc490b880034f9583e44232b3820cc87b4c303fda43da42021d52f06`；`submission_manual.pdf` `a5d723706e27f05a0676cd49dabf4bc1bebb2a9a9e14c04ecfce3169b1aa7dba`；机械提取稿 `submission_manual.txt` `b2d911b24fc73cb53a05f4a1c04e0a62733397b5e2cbd642bb1ec2d30ee3e0cc`。
- 内容提交哈希：`4da8104df771cde7d826ad9a2329159680d0d895`。
- 命令与 run-id：用 `Get-FileHash -Algorithm SHA256` 复算文件哈希；通过 Microsoft Word 16.0 COM 只读打开两份 `.doc` 并 `ExportAsFixedFormat` 到临时 PDF；用 Poppler `pdftoppm -png -r 110` 渲染；逐页查看格式规范 3/3 页、模板 4/4 页、提交手册 16/16 页；重新执行 `workflow_guard.py check --workspace . --gate model-results`，退出码 1。未运行模型或论文实验，run-id 为 `N/A`。
- 产物路径：更新 `06_paper/PAPER_PLAN.md`、`07_review/VERIFICATION_PLAN.md`；更新本交接文件。
- 已核验提交约束：成品为问题编号加队伍号命名的 PDF，即本题 `B<队伍编号>.pdf`；封面、摘要页、正文依次排列；摘要页从 `1` 起在页脚中部连续编号且全文无页眉；首页外不得出现学校、姓名、队号等身份信息；最终 PDF 生成并提交 MD5 后不得再改，上传文件必须与识别码对应文件完全一致；附件是可选项，允许 `zip`/`rar`、最多 1 个且不大于 50 MB，论文 PDF 也最多 1 个且不大于 50 MB。
- 测试与门禁：官方二进制哈希与 `SOURCES.md`/`rules.json` 一致；Word 与 Poppler 均实际可用，官方源文件视觉复核已执行；`git diff --check` 无报错。`model-results` 门禁仍为 `FAIL`，最终论文的数值谱系、编译、逐页视觉检查、复现、paper freeze、提交包回读和硬验收均为 `NOT_RUN`。
- 已知限制：官方题面 ZIP/MD5 仍未取得，本地题面为未核验第三方副本；2023 官方材料中未找到生成式 AI 专项条款，不能将后续年份政策倒推，也不能把“未找到禁止条款”解释成官方明确允许。官方格式文字要求摘要页从 `1` 编号，但 Word 16.0 导出的官方模板封面显示 `0`，正式 LaTeX 重建需以文字规则为硬约束并由总控确认该显示差异。
- 数值边界：已把论文计划同步到 D-005（所有问题 `beta=1`；问题 5 按 `(C,K,RMSE)` 字典序；`q=1` 不宣称唯一最优），但没有写入任何未冻结模型数值或优胜结论。
- 接口影响：论文和验收计划新增官方模板/提交证据、匿名、MD5、附件与 AI 条款边界；没有修改上游模型、结果或共享机器状态。总控若要把封面页码显示差异写入共享决策，应在集成时处理。
- 下一步与接收人：交给总控/集成者审阅并合并内容提交与本交接提交。待题面来源、上游协议/结果冻结和 `model-results` 门禁全部 PASS 后，W Agent 才能同步最新 `main` 建立 LaTeX 正式稿并执行最终论文验收。
