# 论文与提交验收计划

## 1. 失败关闭原则

本计划定义未来验收动作，不是验收报告。当前总状态为 `BLOCKED`：工作流仍处于 `INIT`；官方模板和提交要求已核验，但题面输入来源仍未验证，2023 生成式 AI 专项条款未找到，模型结果未冻结，论文尚未生成。任何强制项为 `FAIL`、`BLOCKED`、`NOT_RUN`、`UNKNOWN` 或阻断性 `WARN` 时，总状态必须为 `FAIL`，不得声称“验收通过”“提交就绪”。

验收只审查同一组已冻结输入和同一个最终 PDF。论文或上游结果发生实质修改后，必须重新冻结并重跑受影响检查；不得沿用旧 PASS。

## 2. 当前门禁快照

已执行：

```text
python -X utf8 <1start-mathmodel>/scripts/workflow_guard.py check --workspace . --gate model-results
```

本轮重新执行的退出码为 1，状态为 `FAIL`。官方模板和提交要求不再是错误项；当前阻断项包括：`rules` 总状态与 AI policy 非 PASS、题面输入来源未核验、problem/tournament protocol/model results 冻结缺失，以及检索、协议、指标与对擂结果未通过或无正式记录。因此当前不运行论文编译、逐页检查或最终硬验收，也不创建伪造的 PASS 记录。

### 2.1 官方材料哈希与视觉复核

| 文件 | SHA-256 | 本轮核验 |
| --- | --- | --- |
| `paper_format.doc` | `9d277f47898ca7a009dfedef2a407a9e6af560532a7b3e5e70312a561f3d9f04` | Microsoft Word 16.0 只读导出，3/3 页经 Poppler 渲染并实际查看 |
| `paper_template.doc` | `64ad3f75fc490b880034f9583e44232b3820cc87b4c303fda43da42021d52f06` | Microsoft Word 16.0 只读导出，4/4 页经 Poppler 渲染并实际查看 |
| `submission_manual.pdf` | `a5d723706e27f05a0676cd49dabf4bc1bebb2a9a9e14c04ecfce3169b1aa7dba` | PDF 共 16 页，16/16 页经 Poppler 渲染并实际查看 |
| `submission_manual.txt` | `b2d911b24fc73cb53a05f4a1c04e0a62733397b5e2cbd642bb1ec2d30ee3e0cc` | 仅作机械检索副本；不替代 PDF 视觉证据 |

本环境存在可用的 Microsoft Word 16.0 和 Poppler，因此本轮官方 `.doc` 源文件视觉复核不是 `NOT_RUN`。这不代表尚未生成的最终论文已完成视觉核验；最终论文的 `visual_qa.json` 仍为 `NOT_RUN`。模板复核另发现：格式规范要求摘要页从 `1` 编号，而 Word 导出的模板封面显示 `0`；在总控确认 LaTeX 实现并完成最终对照之前，该差异不得静默判 PASS。

## 3. 验收阶段与机器记录

| 顺序 | 检查 | 主要输出 | PASS 条件 | 当前状态 |
| --- | --- | --- | --- | --- |
| 1 | 上游与冻结一致性 | 读取 gates/freezes | `model-results` 门禁 PASS，冻结清单无漂移 | `BLOCKED` |
| 2 | 官方规则与输入来源 | 规则/输入核验记录 | 当届模板、AI、提交规则和正式输入来源均 PASS | `BLOCKED`：模板/提交已 PASS，AI/题面仍阻断 |
| 3 | 数值谱系 | `numeric_claims.json` | 每个关键数字能到达冻结 JSON Pointer 与 run manifest，舍入一致 | `NOT_RUN` |
| 4 | 引用真实性 | `text_gate.json` 及人工记录 | 引用键闭合、来源可核验、无虚假/未读引用 | `NOT_RUN` |
| 5 | 关键复现 | `reproducibility.json` | 在规定环境重跑成功且与冻结指标一致 | `NOT_RUN` |
| 6 | 干净编译 | `compile.json` | 真实目标引擎退出码 0，无缺图/缺字形/未定义引用，PDF 非空 | `NOT_RUN` |
| 7 | 文本门禁 | `text_gate.json` | 无占位符、内部路径、Agent 指令、非法身份信息和结构错误 | `NOT_RUN` |
| 8 | 逐页视觉检查 | `visual_qa.json` | 最终 PDF 每一页均实际查看且 PASS | `NOT_RUN` |
| 9 | 提交包回读 | `submission_manifest.json` | 文件名/格式/大小/内容/哈希符合当届规则并完成双签 | `NOT_RUN` |
| 10 | paper 冻结与硬验收 | paper freeze、`ACCEPTANCE.json`、`VERIFY_REPORT.md` | 冻结无漂移，`hard_accept.py` 退出码 0 且状态 PASS | `NOT_RUN` |

## 4. 数值谱系检查

对 `06_paper/PAPER_PLAN.md` 定义的每个 claim id 执行以下检查：

1. `result_file` 在 `00_admin/freezes/model_results.json` 中且当前 SHA-256 匹配。
2. `json_pointer` 存在并指向数值型精确值；对应 run manifest 的配置、代码与输入哈希完整。
3. `exact_value` 与冻结 JSON 完全一致，`display_value` 严格按记录的 `rounding_rule` 生成。
4. 正文、表格、图注和摘要的同一 claim 使用同一生成源。
5. RMSE 可行性用未舍入值判断；`C=qL` 重新独立计算并与冻结记录核对。
6. 问题 4 的 `F_4 tensor F_8` 与问题 3 的 32 点 DFT 分开追踪，禁止串用。

任何缺少 JSON Pointer、run manifest 或冻结哈希的关键数值均判 `FAIL`。`numeric_claims.json` 只有逐项人工复核后才能把相应 `manual_check` 标为 `PASS`。

## 5. 引用与文本检查

- 核验正文每个引用键均可解析，参考文献每个条目均被正文实际引用；修复未定义、重复和孤立引用。
- DOI 优先通过出版方或 DOI 注册信息核验；网页核验权威性、发布日期与访问日期。
- 区分题面事实、作者假设、知识库启发与本文贡献；检索材料只能支撑适用范围内的陈述。
- 扫描正文和 PDF 文本，禁止未替换占位符、`02_retrieval/`、run-id、内部绝对路径、Agent 指令、调试文本和未解释工程标识。
- 核验题号、公式号、图表号、交叉引用、符号定义、单位以及摘要和正文结论一致。
- 核验身份、队号、匿名要求和 AI 使用披露，具体口径必须来自当届官方规则。
- 核验官方格式：封面、摘要页、正文顺序；摘要页起连续阿拉伯页码且页码位于页脚中部；无页眉；标题/一级标题/正文的字号字体与行距符合规范；摘要一般不超过两页且无英文译文。
- 核验匿名性：首页以外不得出现高校、参赛人员姓名、队伍编号等身份信息；PDF 元数据、批注、附件内容和文件名也要扫描潜在身份泄露。
- 核验官方引用格式：按正文出现顺序编号并使用方括号，书籍引用给出页码，期刊条目包含卷期与页码，网页包含访问日期，程序来源明确。

前提满足后执行：

```text
python -X utf8 <6verity>/scripts/paper_check.py text --workspace .
```

记录真实命令、工具版本、时间、退出码、检查目标 PDF 的 SHA-256 和发现项到 `07_review/text_gate.json`；临时搜索不能替代该记录。

## 6. 可复现检查

`07_review/reproducibility.json` 至少记录：

- 操作系统、Python/依赖版本、CPU/GPU（如使用）、随机种子与配置文件哈希；
- 从干净输入开始的轻量测试和每问关键复现命令、开始/结束时间、退出码；
- 新生成指标与冻结 `metrics.json` 的字段级比较及允许容差；
- 图表源数据再生成与哈希比对；
- 失败候选、超时、不可行解和非确定性来源是否如实保留。

正式复现不得覆盖既有 run；使用新 run-id。若资源不足只能记 `NOT_RUN`，不得用历史日志替代。任何超过冻结协议容差或口径不一致的结果均判 `FAIL` 并返回计算阶段处理。

## 7. 编译门禁

1. 在上游与数值谱系通过后，从清理临时缓存的论文源执行真实 LaTeX 编译；引擎以官方模板和 `workflow.json.paper.engine` 为准。
2. 通常至少运行 XeLaTeX 两遍；如使用 BibTeX/Biber，按实际引用链完整运行，记录每一步命令、版本和退出码。
3. 检查日志中的 fatal error、未定义引用、缺图、缺字形、overfull/underfull 风险和字体替代；阻断问题必须修复并重编译。
4. 确认 `06_paper/main.pdf` 非空、可解析，并计算 SHA-256。

`07_review/compile.json` 必须指向后续逐页检查与提交清单所使用的同一 PDF。编译器缺失或任一步非零退出均为 `NOT_RUN`/`FAIL`，不能解释为 PASS。

## 8. 逐页 PDF 检查

先用真实渲染器将最终 PDF 的每一页输出为图片；脚本生成的记录初始保持 `NOT_RUN`，必须实际查看后逐页填写。每页至少检查：

- 页面尺寸、方向、页边距、页码、页眉页脚、封面与模板保护元素；
- 第 1 页为含五个官方 Logo 与身份字段的封面，第 2 页为题目/摘要/关键词页，正文从摘要页下一页开始；
- 首页外没有学校、姓名、队号等身份信息，全文无页眉，摘要页从 `1` 起在页脚中部连续编号；
- 字体、中文、数学符号、上下标和特殊字符是否清晰且无乱码；
- 文字、公式、表格、图片和图注是否裁切、溢出、重叠、跨页断裂或过小；
- 图表颜色、图例、坐标轴、单位、线型和灰度可辨识性；
- 空白页、孤行寡行、异常留白、重复页或缺页；
- 本页显示数值与 `numeric_claims.json`、交叉引用与目录的一致性。

`07_review/visual_qa.json` 记录 PDF 路径、SHA-256、总页数、渲染器版本和每页 `page/status/checker/notes`。缺少任一页记录、渲染失败或未实际查看均为 `NOT_RUN`；任一页失败则总项 `FAIL`。

## 9. 提交清单与双签

`07_review/submission_manifest.json` 仅在当届提交要求核验后建立，至少包含：

- 竞赛年份、官方规则来源，以及问题 B 成品文件名 `B<队伍编号>.pdf`；文件名不得附加学校名、空格或其他前后缀；
- 最终论文只能上传 1 个 PDF，单个文件不大于 50 MB；首页外不得出现学校、参赛人员姓名、队伍编号等身份信息；
- 每个提交文件的相对路径、字节数、SHA-256、来源 paper freeze；
- 最终 PDF 的 MD5 论文识别码、计算命令和时间；提交 MD5 后 PDF 必须字节不变，上传前重算并逐字节/哈希确认与识别码对应文件一致；
- 归档命令、真实格式、解压/回读结果和回读后哈希；
- 论文写作审稿者签名、总控独立复核签名及时间；
- 与 `compile.json`、`visual_qa.json` 相同的最终 PDF SHA-256。

附件是非必要环节；没有论文附件时跳过。需要附件时仅按平台显示的 `zip` 或 `rar` 打包，最多 1 个文件且不大于 50 MB；官方手册未规定附件文件名，不自行创造命名要求。使用 RAR 时必须生成并回读真实 RAR，不能给 ZIP 改扩展名；工具缺失时只能标记候选包。人工最终上传、平台侧 MD5/哈希确认和官网回执由队长完成，不属于机器 PASS 的替代物。

## 9.1 2023 生成式 AI 条款限制

- 已核验材料要求遵守学术规范、不得抄袭或买卖论文，并注明引用文献与程序来源。
- 截至本轮复核，没有在 2023 官方材料中找到针对生成式 AI 的专项条款；`rules.json.ai_policy.status` 因此保持 `BLOCKED`。
- 不得引用后续年份规定并声称其适用于 2023。仓库 `AI_USE_LOG.md` 是审慎治理证据，不冒充 2023 官方专项格式。
- 若最终仍无法取得更明确的 2023 规则，应在验收报告中保留限制并由队长作人工合规判断；不得把“未找到禁止条款”解释成官方明确允许。

## 10. 最终执行顺序

1. 重新运行 `workflow_guard.py ... --gate model-results`，只有 PASS 才继续。
2. 完成数值谱系、引用/文本、关键复现、真实编译和逐页视觉检查。
3. 由有权限的总控执行 `workflow_guard.py freeze --stage paper`，随后确认冻结无漂移。
4. 完成提交清单及写作审稿者—总控双签。
5. 执行：

```text
python -X utf8 <6verity>/scripts/hard_accept.py --workspace .
```

只有退出码为 0 且 `07_review/ACCEPTANCE.json.status` 为 `PASS`，才可报告“机器硬验收通过”。本计划本身不产生 PASS，也不授权论文 Agent 为自己的论文单独签发最终验收。
