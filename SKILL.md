---
name: ManualGen
version: 6.2.0
description: 智能业务分析与操作手册生成专家 v6 — 六层递进式骨架生长架构 + 知识图谱编织 + 增量回灌。从界面到模块到区域到功能到按钮到字段，逐层沉淀节点与证据，最终编织成网，输出真正详细的用户操作手册。核心能力：L0骨架→L1模块→L2区域→L3功能→L4操作→L5细节→图谱构建→Snake跨模块链→单版手册。适用：大项目增量生成/追求细致不是概括/需要端到端跨模块流程。不适用：单次简单问答/纯编码任务/只看摘要不看细节。
---

# ManualGen v6.2 — 六层骨架生长 + 知识图谱编织引擎（全量覆盖铁律）

> **核心变革**：v5 是"先一口气读完全部代码 → 再统一写文档"（大项目上下文爆炸、信息提取粗糙、流程多纰漏、差不多就行）；
> v6 是"像树木生长一样逐层沉淀"，每一层完成立即落盘，上层只读下层的结构化产物，不回头重读原始代码。
>
> **约束即自由**：给AI严格的六层框架 + 图谱证据链 + 批进度追踪，才能交出稳定、丝滑、真正细致的文档。
> **主动执行**：激活后AI自动沿状态机推进，无需用户下命令。
> **断点续跑**：每批完成立即落盘，中断后从当前批次继续，不重跑已完成批次。
> **增量回灌**：发现上层遗漏时只补局部，不全量重来。

---

## 快速参考

| 类别 | 说明 |
|------|------|
| **When to use** | 写手册 / 生成文档 / 操作手册 / 用户手册 / 分析大型项目业务流程 / 需要增量生成 / 追求端到端跨模块流程 / 需要详细到字段和按钮 |
| **When NOT to use** | 仅单次简单问答、不需要生成文档的纯编码任务、只想要一句话摘要 |
| **How it works** | L0骨架 → L1模块 → L2区域 → L3功能 → L4操作 → L5细节 → 图谱构建(含Snake跨模块链) → GAP缺口 → AUTO_REVIEW(AI自审，无用户打断) → 冲突解决 → 写模块 → 回扫 → 一致性检查 → 合并 → 审核 → 判定 |
| **What it produces** | 面向运营/销售/客户的用户版操作手册（单版完整文档），**每段文字可追溯到代码证据**，**含端到端跨模块操作指南**，**含角色×功能的权限矩阵** |
| **最大变化 vs v5** | 六层增量提取（不是一次性全读）、知识图谱+证据溯源（不是扁平md）、Snake跨模块链（不是单模块孤立）、JSON结构化接力棒（不是Markdown表格） |

---

## 激活即执行（强制！）

当 ManualGen 被激活时（用户表达了写手册/分析项目等意图），AI **必须**立即执行以下流程，不得等待用户额外指令：

```
Step 1: 运行强制入口清单（见下方）
Step 2: 读取接力棒 {项目路径}/.agent/harness/_baton.json
 （若不存在 → 创建目录 + 初始化START状态JSON）
Step 3: 如果状态是 START → 自动推进到 L0_SKELETON，开始第一层
Step 4: 如果状态是 X → 直接从 X 阶段续跑（按 baton.layers.*.current_batch 从该批继续）
Step 5: 执行当前阶段任务（按批增量推进）
Step 6: 完成当前批 → 更新接力棒 → 进入下一批 / 推进到下一层
Step 7: 重复 Step 5-6，直到 AUTO_REVIEW 或 DONE
```

**AI 不得**：
- 等待用户输入 `/manual gen` 命令才开始
- 做完一步后询问"下一步做什么？"（AUTO_REVIEW 阶段由 AI 自主裁决，无需等用户）
- 跳过产物更新直接进入下一层 / 下一批
- 因为项目大就"简化一下"（v5的致命问题）——项目越大越要用六层增量，越不能跳层

---

## 强制入口清单（激活后第一步必须执行）

```markdown
在回答用户任何问题、执行任何分析之前，必须：

- [ ] 已确定项目路径（用户指定 > 当前工作目录）
- [ ] 已尝试读取 {项目路径}/.agent/harness/_baton.json
- [ ] 已确认接力棒存在与否
 - 存在 → 解析 meta.state + meta.current_layer + layers.*.current_batch，准备续跑
 - 不存在 → 创建 .agent/harness/ 和 _kb/ 目录，接力棒初始化为 START 状态 JSON
- [ ] 已在回复第一行输出：
 "当前状态：[阶段名]（第N层），批次：[{当前批内容}]，下一步：[操作]"
 例："当前状态：L3_FUNCTION（第3层），批次：[客户管理_客户列表_搜索区, 客户管理_客户列表_操作栏]，下一步：识别这些区域内的功能点"

**任一未完成 → 禁止执行后续任何操作**
```

---

## 30秒新手入门（3个国内真实场景·直接复制用）

> ManualGen v6 是**全流程托管**的，不需要你做配置。最常用的 3 种打开方式，直接复制粘贴就能出结果：

### 触发示例 1：从零写整套手册（最常用）
```
帮我生成 E:\salesclaw-main 这套项目的完整用户操作手册，面向运营和客服使用。
```
→ AI 立即开始，自动从 L0 骨架 → L1 模块 → … → 最后输出项目根目录下的 `salesclaw 用户操作手册.md`。
→ 典型消耗：大型 ERP（30+ 页面）约 20~30 分钟（你可以去做别的，中途关掉对话下次会断点续跑）。

### 触发示例 2：只写重点模块 + 重点业务流（核心优先=**用户显式指定**）
```
重点帮我梳理 E:\salesclaw-main 的「聊天管理」「推理引擎」「本体图谱」这 3 个模块，
并突出"从场景配置到推理决策到效果追踪"的完整端到端流程。
```
→ 因用户**显式点名了模块范围**，AI 开启「核心优先模式」：3 个指定模块 L0-L5 全量跑完写手册；
 其他模块按全局规则全量扫到 L2 作为背景，且最终手册**必须附「附录 F：未覆盖模块/功能清单」**（列示哪些模块只到背景深度、为什么），禁止静默交付。
> 若用户**没有**显式指定模块范围，则一律默认全量模式（L0-L5 覆盖全部模块），不得自行降级为核心优先。

### 触发示例 3：已有旧手册/代码改了，只补增量
```
E:\salesclaw-main 我新增了「suggestions 智能建议模块」，帮我把这部分补进原手册里。
```
→ AI 会走增量回灌流程：只扫描新模块对应的 L1→L2→… → 图谱局部重建 → 文档只追加新章节，旧内容一丝不动。

### 主动打断式（中途想看一眼进度/改点东西）
随时发消息就行，AI 会临时暂停并输出：当前层数/批次进度、6 层完成率饼图、最近 20 条 AI 自主裁决、待复核节点 Top。
- 你说「继续」或干脆不回消息 → AI 自动接着跑
- 你说「把 XX 模块那段角色改一下」→ AI 定位到对应节点，局部修改后再接着跑

---

## 自检闭环（每次回复结束时必须检查）

- [ ] 本次回复是否输出了规定的"当前状态...批次...下一步"开头？
- [ ] 如果当前批已完成 → 是否已写文件到 `_kb/Lx_xxx/*.json`？是否已更新 baton.layers.*？
- [ ] 是否严格按六层顺序推进？（禁止跳层：未完成L0禁止进L1）
- [ ] 是否严格按批读取代码？（禁止一次读10个文件：每批只读本批范围对应的源码）
- [ ] 如果没有 → 已偏离状态机 → 立即返回修正

---

## 六层递进式生长架构（强制理解）

> 详细规则见 `knowledge-base/03-layered-architecture.md`，这里只速览。

```
L5 细节层 (Detail) 按钮级交互 / 字段级校验 / 权限矩阵 / 异常提示 ← 最后填充细节
 ^ 沉淀节点到图谱
L4 操作层 (Operation) 点击什么→填写什么→看到什么，完整用户步骤+流程图 ← 从图谱编织不读源码
 ^ 编织操作节点
L3 功能层 (Function) CRUD / 审核 / 导入导出 / 配置，功能点清单+入口 ← 按区域读代码片段
 ^ 划分功能区域
L2 区域层 (Region) 页面内Tab/卡片/搜索区/列表区/详情区分区+可见性 ← 按页面读组件
 ^ 识别界面结构
L1 模块层 (Module) 菜单级模块：页面清单+入口+核心实体+高频场景 ← 按模块读路由/菜单
 ^ 搭骨架
L0 骨架层 (Skeleton) 项目形状：模块数+依赖图+角色矩阵+数据创建链 ← 全局目录扫描（最浅）
```

**核心设计原则**：
- 每层提取深度递增，代码读取范围递减
- **L4起不再读源码**，从下层图谱节点编织操作步骤（保证上下文干净、不被技术信息污染）
- **每层按批处理**：L1每批2-3个模块、L2每批3页、L3每批6区域、L4每批4功能、L5每批5操作
- 每批完成立即落盘 + 更新baton + 节点入图谱

---

## 状态机总览（18阶段，全流程托管 · 无中间打断）

> **全流程托管承诺**：激活后AI自动推进到DONE，**中途不询问用户、不暂停等确认、不让用户做任何决策**。
> 低置信节点/Snake顺序/冲突解决**全部由AI按规则自主裁决**，决策日志存入 `_auto_decisions.md`，最终交付时附「AI自主决策清单附录」供事后查阅（有问题下次激活可定点修正）。
> **用户主动打断机制**：只有用户在对话中主动发消息（如"暂停一下"、"我觉得订单模块有问题"），才临时展示中间面板并响应；否则全程静音推进。

| 阶段 | 编号 | 职责 | 核心产物 | 自动推进 | 按批？ |
|------|------|------|----------|----------|-------|
| START | 0 | 初始化接力棒 | `_baton.json` | | — |
| **L0_SKELETON** | 1 | 搭骨架：模块+依赖+角色+数据链 | `_kb/L0_skeleton.json` + `L0_skeleton_report.md` | | 不分批 |
| **L1_MODULE** | 2 | 长枝干：每模块的页面/实体/场景 | `_kb/L1_modules/*.json` | | 每批2-3模块，循环直到覆盖**全部模块** |
| **L2_REGION** | 3 | 分叉：每页的区域划分+可见性 | `_kb/L2_regions/*.json` | | 每批3页，循环直到覆盖**全部页面** |
| **L3_FUNCTION** | 4 | 长叶子：每区域的功能点+入口+权限 | `_kb/L3_functions/*.json` | | 每批6区域，循环直到覆盖**全部区域** |
| **L4_OPERATION** | 5 | 开花：操作步骤+流程图（从图谱织·不读源码） | `_kb/L4_operations/*.json` | | 每批4功能，循环直到覆盖**全部功能** |
| **L5_DETAIL** | 6 | 结果：字段详情/按钮状态/权限矩阵/异常文案 | `_kb/L5_details/*.json` | | 每批5操作，循环直到覆盖**全部操作/实体** |
| **GRAPH_BUILD** | 7 | 织网：节点归一化+三元组+实体对齐+Snake+置信度 | `_kb/graph/*.json` (6个：_nodes/_triples/_evidence/_snakes/_layer_index/_quality) | | 内部7步 |
| **GAP_ANALYSIS** | 8 | 缺口：从图谱查缺失/P0/P1/P2 + 自主回填判断 | `_gap_analysis.md` + `_auto_decisions.md`(回填决策) | | — |
| **AUTO_REVIEW** | 9 | **AI自主审阅**：低置信节点裁决+Snake顺序校验+证据补强（不打断用户） | `_auto_decisions.md`(置信+Snake裁决) | | — |
| **RESOLVE** | 10 | 冲突：多源信息冲突分级+AI自主解决 | `_resolution.md` + `_auto_decisions.md`(冲突裁决) | | — |
| **WRITE** | 11 | 写模块：子Agent隔离上下文，从图谱查询生成文档 | `output_user_manual/_modules/*.md` | | 每批2模块 |
| **REFINE** | 12 | 回扫：子Agent盲检每模块质量（不合格自主修复） | `_refine_log.md` | | 逐模块 |
| **REFERENCE_CHECK** | 13 | 一致性：交叉引用+术语统一+权限矩阵连贯 | `_reference_check.md` | | — |
| **INTEGRATE** | 14 | 合并：模块→整手册，含跨模块Snake+权限矩阵+AI决策附录 | `_integration.md` + 根目录最终md | | 按域分批 |
| **AUDIT** | 15 | 自评：10维评分（6原维 + 图谱交叉验证率⑨ + Snake完整性⑩）+ **第⑪维覆盖完整性硬门**（L1_index 全模块 vs 手册章节比对） | `_audit.md` | | — |
| **TODO_RESOLVE** | 16 | 待办：统一解决审核中标记的TODO（AI自主解决） | `_todo_resolution.md` | | — |
| **JUDGE** | 17 | 盲审：子Agent盲审真正质量门（不合格打回模块级重做） | `_judgment.md` | → DONE | — |
| DONE | 18 | 完成：收口交付，输出成品+质量报告+决策附录链接 | 最终交付物路径 | 结束 | — |

```
START
 → L0 → G0 → L1 → G1 → L2 → G2 → L3 → G3 → L4 → G4 → L5 → G5
 → GRAPH_BUILD → GAP_ANALYSIS(AI判定缺口: 严重则自动增量回灌, 否则通过)
 → AUTO_REVIEW(AI自主裁决: 低置信节点处理+Snake顺序校验+证据传播)
 → RESOLVE(AI自主解决冲突)
 → WRITE(模块文档+跨模块Snake附录) → REFINE(自主修复) → REFERENCE_CHECK
 → INTEGRATE(含AI自主决策清单附录)
 → AUDIT → TODO_RESOLVE → JUDGE → DONE
 ↑(Judge打回: 仅重做对应模块, 其余不动)
```

---

## 状态路由表（全自主推进 · 禁止中途等待用户）

| 当前状态 | 自动进入 | 前置条件（不满足禁止推进） | 禁止进入 |
|----------|----------|----------------------------|---------|
| START | L0_SKELETON | — | L1以上 |
| L0_SKELETON | L1_MODULE | L0_skeleton_report.md 已生成、模块非空、依赖图已画、G0通过 | L2以上 |
| L1_MODULE | L2_REGION | **全部模块**L1完成（批循环覆盖100%）、G1通过 | L3以上 |
| L2_REGION | L3_FUNCTION | **全部页面**L2完成（批循环覆盖100%）、G2通过 | L4以上 |
| L3_FUNCTION | L4_OPERATION | **全部区域 100% 覆盖**（批循环，`batches_done==batches_total`，已识别 FUNCTION ≥90% 带 trigger_element+OPERATES_ON 证据）、G3通过 | L5以上 |
| L4_OPERATION | L5_DETAIL | **全部功能**每功能≥5步+流程图、G4通过 | GRAPH以上 |
| L5_DETAIL | GRAPH_BUILD | 字段覆盖≥80%、权限矩阵≥70%、G5通过 | GAP以上 |
| GRAPH_BUILD | GAP_ANALYSIS | graph 6文件落盘（_nodes/_triples/_evidence/_snakes/_layer_index/_quality）、entity_alignment_pending ≤ 0 | AUTO_REVIEW以上 |
| GAP_ANALYSIS | AUTO_REVIEW | P0/P1/P2已列、完整性评分已算 → 若P0严重则自动增量回灌后再推进 | RESOLVE以上 |
| AUTO_REVIEW | RESOLVE | 低置信节点已AI裁决、Snake顺序已校验并写入`_auto_decisions.md` | WRITE以上 |
| RESOLVE | WRITE | 冲突分级已AI解决、决策日志写入 | REFINE以上 |
| WRITE | REFINE | **全部模块**≥1篇写入_modules（核心优先模式则≥其指定模块数）、流程图非空 | REFERENCE_CHECK以上 |
| REFINE | REFERENCE_CHECK | 全部模块PASS≥8/10（不合格自主修复后达标） | INTEGRATE以上 |
| REFERENCE_CHECK | INTEGRATE | 术语一致≥95%、交叉引用全有效 | AUDIT以上 |
| INTEGRATE | AUDIT | 含Snake跨模块章节+权限矩阵附录+AI决策附录 | TODO_RESOLVE以上 |
| AUDIT | TODO_RESOLVE | 10维打分 ≥60 **+ 第⑪维覆盖完整性硬性 PASS**（L1_index 全模块 vs 手册章节逐一比对，未覆盖模块必须溯源到附录 F），每维有依据 | JUDGE以上 |
| TODO_RESOLVE | JUDGE | TODO解决率≥90%、剩余P0有说明 | DONE以上 |
| JUDGE | DONE | 模块级盲审 PASS_rate≥0.70（≥70分的模块占比≥70%）、每模块≥70分 | 继续执行 |
| JUDGE(打回某模块) | WRITE（只重做打回模块） | 打回理由记入rework.history（其余模块不动） | 跳过WRITE |
| JUDGE(≤50分·致命) | FAILED | 明确致命缺陷清单 + 建议回灌方案（等下次激活续跑） | 伪装通过 |

### AI自主裁决规则（AUTO_REVIEW 阶段·不打断用户）
| 待决策项 | 规则（AI直接判·不询问） | 写入文档时的标记 |
|---------|----------------------|----------------|
| 低置信 FUNCTION (0.5~0.7) + 有≥1条单源证据 | 保留为「推断功能」，步骤描述从肯定改为条件语气 | 操作说明前加 **警告** 小注：「此功能根据菜单/路由推断，未找到明确按钮handler，请按实际界面确认」 |
| 低置信 FUNCTION (<0.5) + 无证据 | 丢弃，不写入文档（记 `_auto_decisions.md` 备查） | — |
| Snake节点顺序疑义 | AI按L0数据创建链 + GRAPH的OPERATES_ON传播自动重排，写入snake.meta.auto_reordered=true | Snake流程图底部加灰色小字：「流程顺序由AI推断，实际操作以界面为准」 |
| 权限矩阵疑义 (缺10%~30%) | AI从ROLE继承关系 + 模块依赖关系传播补齐，标记propagated | 附录权限矩阵灰色标注为「AI推断权限」 |
| 字段缺少校验规则 (缺5%~15%) | 从同类型同名称字段（其他entity的同名字段）自动copy规则，标记inferred | 字段说明表备注「校验规则参考同类字段推断」 |

---

## 产物体系（v5 12个 → v6 35+个文件，按层组织）

> ** 定位铁律（对外只交付手册）**：`.agent/harness/`（含 `_kb/` 图谱、接力棒、中间报告）是 **ManualGen 的内部引擎产物**，仅用于支撑生成过程与断点续跑，**不是交付物、不对外展示、可整体进 `.gitignore`**。
> **唯一对外交付物** = `{项目根目录}/{项目名称} 用户操作手册.md`（以及 `output_user_manual/` 内的模块文档与附录，供最终合并）。
> 禁止：把图谱/接力棒/中间产物铺进用户的正式目录（如 `src/`、业务代码目录）；禁止在回复中向用户展示图谱细节，除非用户主动追问进度。

```
{项目路径}/.agent/harness/ # ===== 中间产物（可进.gitignore）=====
├── _baton.json # 接力棒（JSON结构化，v5是_baton.md）
├── _gap_analysis.md # GAP阶段产物（从图谱查询缺口）
├── _resolution.md # 冲突解决
├── _refine_log.md # 回扫日志
├── _reference_check.md # 一致性检查
├── _todo_list.md # TODO列表
├── _todo_resolution.md # TODO解决报告
├── _audit.md # 自评
├── _judgment.md # 盲审判定
├── _integration.md # 整合中间稿
│
└── _kb/ # ===== 知识库核心（v6新增）=====
 ├── L0_skeleton.json # L0：模块/角色/依赖
 ├── L0_skeleton_report.md # L0人类可读报告（用于 AI 自检 & 用户追问时展示）
 │
 ├── L1_index.json # L1索引：模块进度追踪
 ├── L1_modules_report.md # L1汇总报告（供自检与进度展示）
 ├── L1_modules/ # L1：每模块独立JSON（可独立重读）
 │ ├── MOD_001_客户管理.json
 │ └── ...
 │
 ├── L2_regions/ # L2：每页独立JSON
 │ ├── PAGE_001_客户列表.json
 │ └── ...
 │
 ├── L3_functions/ # L3：每区域独立JSON
 │ ├── REG_001_搜索区.json
 │ └── ...
 │
 ├── L4_operations/ # L4：每功能独立JSON（含流程图代码）
 │ ├── FN_001_新增客户.json
 │ └── ...
 │
 ├── L5_details/ # L5：五类子目录（字段/角色/元素/校验/聚合）
 │ ├── ENTITY/ENT_001_客户_字段详情.json
 │ ├── ROLE/权限矩阵.json
 │ ├── ELEMENT/ELEM_xxx_按钮状态.json
 │ ├── VALIDATION/校验规则.json
 │ └── AGGREGATE/聚合统计.json
 │
 ├── graph/ # ===== 知识图谱核心（v6新增）=====
 ├── _nodes.json # 归一化后的所有节点（8类）
 ├── _triples.json # 三元组关系（20+谓词）
 ├── _evidence.json # 证据溯源（节点←→代码片段）
 ├── _snakes.json # Snake跨模块概念链
 ├── _layer_index.json # 层级完成度+质量索引
 └── _quality.json # 质量评估汇总（AUDIT §⑨⑩ / GAP 查询用）
 ├── _auto_decisions.md # AUTO_REVIEW 裁决明细（低置信/蛇/权限/字段 + 回灌决策）
 └── _backfill_log.md # 增量回灌日志（每层补了什么、什么时候补的）

{项目路径}/output_user_manual/ # ===== 最终交付目录（WRITE/INTEGRATE）=====
├── _modules/ # WRITE阶段模块文档（子Agent写）
│ ├── 01_客户管理.md
│ └── ...
└── _appendix/ # INTEGRATE阶段附录（B~F模板生成，F=未覆盖清单）
 ├── appendix-B-permission-matrix.md
 ├── appendix-C-AI-auto-decisions.md
 ├── appendix-D-snake-flows.md
 ├── appendix-E-evidence-index.md
 └── appendix-F-uncalled-modules.md

# 最终交付物
{项目根目录}/{项目名称} 用户操作手册.md
```

### 产物更新铁律
- **每批完成 → 立即写对应 `_kb/Lx_xxx/*.json` 文件**（不等整层完成才写）
- **文件写入后 → 主控更新 baton.layers.*.xxx_batches_done +1 → 更新 baton.graph.nodes_total 统计**
- **所有 kb 文件必须是合法JSON**（用户可手动打开检查，也可被下游查询）
- **最终交付物必须含：模块文档 + Snake跨模块操作指南 + 权限矩阵附录**

---

## 七层闸门体系（Gate System）

> 参考skill-medic的闸门思想。每层完成后必须通过闸门才准进入下一层。

| 闸门 | 位置 | 检查内容 | 通过阈值 | 不通过处理 |
|------|------|---------|---------|-----------|
| G0 | L0→L1 | 模块数非空+依赖图非孤立+角色≥2+数据创建链≥3 | L0.quality≥80 | 补充探索，不能进L1 |
| G1 | L1→L2 | **全部模块**L1完成+每页都有入口+实体≥1 | L1.quality≥75 | 缺哪个模块补哪个，不重跑整层 |
| G2 | L2→L3 | **全部页面**区域划分完整+≥1区域间触发关系 | L2.quality≥70 | 缺哪页补哪页 |
| G3 | L3→L4 | **全部区域 100% 覆盖**（批循环，`batches_done==batches_total`）+ 已识别 FUNCTION ≥90% 带 trigger_element 入口 | L3.quality≥65 | 缺哪区域补哪区域 |
| G4 | L4→L5 | **全部功能**每功能≥5步+≥1分支流程图 | L4.quality≥65 | 缺哪功能补哪功能 |
| G5 | L5→GRAPH | 字段覆盖率≥80%+权限矩阵≥70%+错误消息≥50条 | L5.quality≥60 | 缺哪些字段补哪些字段 |
| GW | WRITE→REFINE | 子Agent写出的模块文件不出现API端点/数据库名等技术泄露 | 每模块REFINE清单≥8/10 | 不合格模块立即重写（不影响其他已合格模块） |

---

## 按需加载规则（Chunk 加载矩阵）

| 当前阶段 | 必须加载的 Chunk | 可卸载的 Chunk | 必须加载的 Protocol |
|----------|------------------|---------------|---------------------|
| 初始化 | 01-overview, 06-privacy-security | — | baton-protocol |
| L0_SKELETON | 01, 06, 07-skeleton-growth §L0 | — | baton-protocol, phase-protocol |
| L1_MODULE | 01, 06, 07 §L1 | 07§L0 | — |
| L2_REGION | 01, 06, 07 §L2 | 07§L0§L1 | — |
| L3_FUNCTION | 01, 06, 07 §L3 | 07§L0§L1§L2 | — |
| L4_OPERATION | 01, 06, 07 §L4 | 07§L0§L1§L2§L3 | graph-protocol §只读查询 |
| L5_DETAIL | 01, 06, 07 §L5 | 07§L0§L1§L2§L3§L4 | — |
| GRAPH_BUILD | 01, 06, 08-knowledge-graph | 07全卸载 | graph-protocol 全章 |
| GAP_ANALYSIS | 01, 06, 03-analyze-gap（从图谱查询）+ 09-incremental-refine（若触发回灌） | 08 | — |
| AUTO_REVIEW | 01, 06, 07 §自主裁决, 08 §Snake审阅 | 03 | — |
| RESOLVE / WRITE | 01, 06, 04-resolve-write（**v6升级版：从图谱查**）, 10-flowchart-spec | 07§L0~L5（WRITE不需读源码层） | — |
| REFINE / REFERENCE_CHECK | 01, 06, 04 | — | — |
| AUDIT / JUDGE | 01, 06, 05-audit-judge（10维度） | 04 | — |
| TODO_RESOLVE | 01, 06, 05-audit-judge §TODO | — | — |

**规则**：每次只加载当前阶段需要的chunk section，不再需要的section可以"概念卸载"（AI意识中不再主动引用）。上下文预算紧张时优先卸载代码探索类chunk，保留协议和闸门类chunk。

---

## 全局规则（比v5更严格，根治"差不多就行"）

### 0. 全量覆盖铁律（默认模式·最高优先级）

> **背景**：v6.1 曾默认"核心优先"，导致执行 AI 自行降级只做核心模块就交付，用户拿到浅层手册（如 10 模块项目只写了 6 页 → 手册仅 266 行）。v6.2 起强制以下规则：

1. **默认全量**：除非用户消息中**显式点名模块范围**（如"只写客户管理模块"），否则 L0→L5 必须覆盖项目 100% 的模块/页面/区域/功能；字段覆盖以 100% 为目标、≥80% 为推进闸门，权限矩阵以 100% 为目标、≥70% 为推进闸门（见下），**未覆盖部分必须显式披露**（附录 F 未覆盖清单或附录 C Top 未决项），禁止静默缺失。每个 L 层按批循环，直到 `batches_done == batches_total` 才允许进入下一层。
2. **批次数推导即写死**：进入某 L 层时，先由父层节点数推导 `*_batches_total`（如 L2_total = ceil(页面总数/每批3页)）写入 baton，**全程只增不减**；`batches_done < batches_total` 时禁止推进到下一阶段。
3. **禁止自行降级**：AI 不得因"上下文太长/项目太大/耗时预估"自行切换核心优先或提前收口。上下文紧张 → 用断点续跑/批次落盘解决，不得缩范围。
4. **核心优先 = 显式 opt-in + 强制披露**：仅用户点名模块范围时启用；此时必须 (a) 在 baton 记 `work_mode="core_priority"` + `skipped_modules=[...]`；(b) 其余模块仍全量扫到 L2 作背景；(c) INTEGRATE 强制生成**附录 F：未覆盖模块/功能清单**；(d) 手册首页注明"本手册仅覆盖 X 模块，未覆盖 Y、Z"。
5. **覆盖完整性检查**：AUDIT 阶段新增第 11 检查项——把 L1_index 全部模块与手册章节逐一比对，未覆盖模块必须能溯源到附录 F，否则 AUDIT 不得通过，回退到 GAP_ANALYSIS 补齐。

### 1. 计数-列表-证据 三连验证（比v5加了证据链）
```
声称"提取了N个FUNCTION"
 → 必须：(a) 逐个列出N个FUNCTION的ID+NAME
 (b) 每个都有 source 证据
 (c) L3目录下有对应 .json 文件
声称"分析了M个操作步骤"
 → 必须：(a) 每个步骤的 STEP_ID
 (b) 每步关联的 ELEMENT 或 FIELD
 (c) 操作流程图非空
声称"识别了K条Snake跨模块链"
 → 必须：(a) 每条Snake的node_ids按顺序列出
 (b) 每条蛇的category + description
 (c) ≥1条有 needs_review=false 标记
```
任一缺 → **阻断**，不进入下一层/下一批。

### 2. 渐进累加 + 增量回灌（不是推翻重来）
- 每次分析前只读当前批需要的源码 + 历史已落盘 `_kb/Lx_xxx/*.json`
- 在上层（如L4）发现下层（如L1）缺了节点 → **回灌模式**：
 1. 只追加写入下层对应文件（不删旧内容）
 2. 把受影响节点标记 `dirty=true`
 3. 记录 `_backfill_log.md`
 4. GRAPH_BUILD阶段自动重算dirty子图
- **禁止**：L5发现L1有问题就"重新从头分析整个项目"（那是v5的做法，浪费）

### 3. 证据不足禁止进WRITE（新增，根治v5"凭感觉写"）
- AUTO_REVIEW阶段按 AI 自主裁决规则处理低置信节点（chunk-07 §自主裁决）
- `<0.7` 置信度节点过了 AUTO_REVIEW 后仍未被证据提升 → WRITE阶段对应位置写 提示语（不写"点击XX按钮"这种明确操作语句）
- 处理记录全部写进 `_auto_decisions.md`（附录 C 可读），保留人工复核后下次激活补正的链路

### 4. Snake强制输出（根治v5"单模块孤立"）
- 最终文档必须包含 `output_user_manual/_appendix/appendix-D-snake-flows.md`（附录 D），内容全部从 `graph/_snakes.json` 生成
- 每条 end_to_end_flow Snake 必须有独立章节 + Mermaid 全景流程图
- Snake 数 = 0 → INTEGRATE 阶段阻断（说明图谱构建不完整，回去补GRAPH_BUILD）

### 5. 接力棒强制更新（每批！不只是每阶段）
v5是每个阶段完成才更新接力棒；v6改为：
- **每批完成 → 立即更新 baton.layers.Lx.current_batch 和 layers.Lx.*_batches_done**
- 同时更新 baton.graph.nodes_total / triples_total / evidence_total 的增量计数
- 不更新 → 视为该批未完成 → 不进入下一批

### 6. 隐私保护（保持不变，但扩展到证据层）
所有输出遵守 `privacy/privacy-notice.md`。**额外约束**：证据表中不记录明文密码/密钥/Token，只写 `[REDACTED FIELD: password]`。

### 7. 权限矩阵强制输出（根治v5"角色一笔带过"）
- L5_DETAIL 阶段必须生成完整的 `ROLE × FUNCTION` 矩阵（JSON格式）
- INTEGRATE 阶段把矩阵转成 Markdown 表格，作为手册"附录B：角色权限总览"
- 矩阵覆盖率 <70% → G5 闸门阻断

### 8. Mermaid 流程图强制（保持不变，+Snake全景图额外约束）
与v5相同：必须使用 `flowchart TD/LR` / `stateDiagram-v2`、中文直角引号 `「」`、禁止ASCII画图。**新增**：
- 每条 Snake 必须配一张跨模块全景 Mermaid 流程图（节点标明所属模块）
- Snake流程图用 `flowchart LR` + `subgraph MODULE_xxx` 分模块框

---

## 定制化指南（默认全量覆盖 · 核心优先需用户显式指定）

| 维度 | 说明 | 示例用法 |
|------|------|---------|
| 全量模式（**默认**） | L0-L5 覆盖项目全部模块/页面/区域/功能/字段，批循环直到 100%，未覆盖即视为流程未完成 | 什么都不指定 = 全量 |
| 核心优先 | **默认关闭，仅当用户显式点名模块范围时才启用**（如"只写客户管理模块"）；启用后除指定模块全量外，其余模块必须在附录 F 列示"未覆盖清单"，禁止静默跳过 | "先做客户管理和订单管理L0-L5，系统设置先停在L2就行" |
| 文档风格 | 简洁/详细/图文并茂 | "手册写得详细一点" |
| 角色聚焦 | 仅为特定角色写操作说明 | "只写销售人员操作部分" |
| 模块优先级 | 指定先写哪些模块（仍会全量覆盖，仅调整顺序） | "重点写客户管理和订单模块" |
| 输出格式 | 指定最终产物格式 | "用 Markdown 格式输出" |
| 深度级别 | 基础操作/标准覆盖/全量极致细节 | "每个操作至少写 8 步，字段说明表不能空行" |
| Snake偏好 | 要求额外生成某类业务链 | "请生成'财务对账'这条端到端流程，重点突出" |

传递链路同v5但取消用户确认环节：用户指定 → Master记baton.meta.user_preferences → AUTO_REVIEW阶段AI核验是否冲突 → 直接传递后续阶段。

---

## 阶段 → Chunk / Agent 映射表

| 阶段 | 对应 Chunk | 调度 Agent | 输入来源 | 输出落盘位置 |
|------|-----------|-----------|---------|-------------|
| L0_SKELETON | 07 §L0 | Skeleton-Agent | 项目目录结构 + 路由/菜单配置文件 + README | `_kb/L0_*.json` |
| L1_MODULE | 07 §L1 | Skeleton-Agent（按批） | 对应模块的路由 + 菜单组件 + Controller目录名 | `_kb/L1_modules/*.json` |
| L2_REGION | 07 §L2 | NodeWeaver-Agent（按批） | 对应页面的.vue/.jsx组件源码（template部分） | `_kb/L2_regions/*.json` |
| L3_FUNCTION | 07 §L3 | NodeWeaver-Agent（按批） | 对应区域的methods/handlers/hooks + 后端Controller方法签名 | `_kb/L3_functions/*.json` |
| L4_OPERATION | 07 §L4 | NodeWeaver-Agent（按批，**不读源码**） | 从graph查询：FUNCTION→ELEMENT→ENTITY→ROLE→STEP→NEXT_STEP | `_kb/L4_operations/*.json` |
| L5_DETAIL | 07 §L5 | NodeWeaver-Agent（按批，局部精读读源码） | 对应字段的model/entity定义 + 表单校验代码 + 权限路由配置 + 错误文案 | `_kb/L5_details/*.json` |
| GRAPH_BUILD | 08 全章 | GraphBuilder-Agent（7步流水线） + EntityAligner-Agent | 全部 `_kb/Lx_*/*.json` | `_kb/graph/*.json`（6个文件，含 `_quality.json`） |
| GAP_ANALYSIS | 03（v6升级版：从图谱查）+ 09（触发回灌时） | GAP-Analyst-Agent + 主控回灌调度 | graph._nodes + _triples | `_gap_analysis.md` + `_backfill_log.md`（若回灌） |
| AUTO_REVIEW | 07 §自主裁决 + 08 §Snake审阅 | 主控 AI 自审（无用户打断） | low_confidence 节点 + incomplete蛇 + 权限/字段缺口 | `_auto_decisions.md`（裁决明细）+ graph/_nodes.json（不确定标记） |
| RESOLVE | 04 §RESOLVE | Resolver-Agent（全自主不询用户） | 冲突检测：多源evidence对比 | `_resolution.md` + graph 修改写回 |
| WRITE | 04 §WRITE（v6升级版：从图谱查，不读源码不读_extraction） | Module-Writer子Agent×N（隔离上下文） | 查询graph：按模块查 MODULE→PAGE→REGION→FUNCTION→STEP+流程图+ROLE权限+Snake关联 | `output_user_manual/_modules/*.md` |
| REFINE | 04 §REFINE | Refiner子Agent×N（盲检） | 每个`output_user_manual/_modules/*.md`独立检查 | `_refine_log.md` + 修复后重写模块 |
| REFERENCE_CHECK | 04 §REFERENCE_CHECK | 主控自检 | 全`output_user_manual/_modules/*.md` 交叉比对 | `_reference_check.md` |
| INTEGRATE | 04 §INTEGRATE（+Snake附录） | Integrator-Agent | `output_user_manual/_modules/*.md` + `_snakes.json` + 权限矩阵.json | `_integration.md` + `output_user_manual/_appendix/B~F.md`（F=未覆盖清单） + 项目根目录最终md |
| AUDIT | 05（10维 + ⑪硬门） | 主控自评 + 子Agent盲审底稿 | _integration.md + _audit.md | `_audit.md` |
| TODO_RESOLVE | 05 §TODO | 主控逐条解决 | _todo_list.md + 对应源码或图谱节点 | `_todo_resolution.md` |
| JUDGE | 05 §JUDGE | Judge子Agent盲审 | _integration.md 全量（不给技术背景，只看文档质量） | `_judgment.md` |

---

## FAQ（共 11 题，覆盖新手→深度用户）

### Q1：激活 ManualGen 后，我要干点什么？
**答**：什么都不用点。激活后 AI 自动推进 18 阶段直到产出最终手册。中途如果你想看进度，说一句「进度」或「暂停」即可。有问题随时打断，AI 会展示仪表盘 + 最近 20 条 AI 自主裁决，之后会自动继续跑。

### Q2：什么场景下最应该用 ManualGen？
| 场景 | 示例 |
|------|------|
| 大型项目从零写操作手册 | "给这套 ERP 写一份面向运营的用户手册"（推荐，六层增量能处理超大代码量） |
| 现有代码缺文档/文档陈旧 | "这个项目我接手没人交接，帮我梳理出完整操作手册"（增量回灌只补新部分） |
| 想知道完整业务流 | "帮我梳理从客户下单到财务收款的完整操作"（Snake 跨模块链专门解决这个） |
| 字段/按钮级别细节 | "我要一份写清楚每个输入框填什么、校验规则是什么的详细手册"（L5 细节层专门沉淀） |

### Q3：对项目有什么要求？需要我提供设计稿吗？
不需要设计稿！**直接把代码目录路径给 AI 就行**。它支持：Vue/React 前端 + Spring Boot/FastAPI/NestJS 后端 + MySQL/PostgreSQL 建表 SQL。你给源码它就能从 0 写出完整手册。

### Q4：生成出来的手册和真实系统不一致怎么办？（典型担心）
ManualGen v6 **每一段文字都可追溯到具体源码行**（附录 E 证据索引），不是 AI 瞎编的。如果真有问题，说一句"订单模块创建订单那部分不对"，AI 会从那节点往下溯源证据，发现错误后触发增量回灌只改那部分，不是全手册重写。

### Q5：生成中途我关掉对话了，下次还能接着跑吗？
**能，断点续跑**。每一批写完就立即落盘 + 更新 JSON 接力棒，下次激活直接从当前阶段的下一批继续，不重跑已经完成的内容。

---

### Q6（新增）：六层模式会不会比v5更慢？
看起来阶段变多了，但实际上**总耗时显著更少**，因为：
1. v5大项目要反复重读全量代码（上下文不够→截断→又读→还乱）；v6每层只读自己那批
2. v5发现前期错了要推翻重来；v6增量回灌只补局部
3. L4/L5可以在你晚上睡觉时继续跑完（断点续跑）
4. 核心优先模式（仅用户显式指定模块范围时启用）：指定模块L0-L5跑完先写文档，其余模块全量扫到L2作背景并列入附录F未覆盖清单

### Q7（新增）：图谱里节点置信度 <0.7 的那些最后怎么办？
三条路径：
1. AUTO_REVIEW 阶段 AI 自主补证据/做传播后 ≥0.7 → 自动放行
2. 仍 <0.7 但 AI 判定"操作可推断"→ WRITE 阶段加警告，写推断操作说明，不写虚假按钮
3. AI 也无法判定 → WRITE 阶段不引用，最终文档对应位置写
 > "此功能为AI根据上下文推断，未在源码中找到明确按钮/API入口，请向系统管理员确认后操作。"

### Q8（新增）：Snake跨模块链是啥？我以前v5没见过
v5的问题：手册按模块分章节，但**实际业务是跨模块的**（如"销售接单→仓库发货→财务收款→客服回访"要翻4个模块的手册来回跳）。
v6 Snake就是把这些跨模块的操作串成独立章节，用户看附录就能一口气了解完整流程，不用翻4个章节。

### Q9（新增）：我中途想加新模块/新功能怎么办？
两种模式：
1. **当前会话内** → 触发增量回灌：主控把新模块加进batch最后，重跑L1→L5对应层
2. **下次激活** → 接力棒自动检测`_kb/Lx_*/`里的文件是否比`updated_at`新，自动从L1那模块开始补跑，不影响旧模块

### Q10（新增）：AI 自主做出的决策我事后不认同怎么办？
所有 AI 自主决策都写在「附录 C AI 自主决策记录」中，每条都有明确依据和影响范围。下次激活 ManualGen 时，用户可以直接指出要改哪条（如"C.2 Snake_001 那节点顺序不对"），Master 会定位到对应节点重做对应局部（增量改 Snake，不重写全手册）。

### Q11（新增）：最小的项目多大适合用这套六层模式？
MODULE < 3 且 PAGE < 10 的超小型后台，会自动走 v5 EXPLORE/EXTRACT 捷径（跳过六层但不跳后续图谱/WRITER）。再小的项目也能跑，只是六层批处理意义不大，AI 会自动切到合适粒度。

---

### 与深度 FAQ 互补关系
主文档 FAQ（本节 11 题）= 新手入门 + 使用说明；进阶问题（接力棒损坏/图谱写一半崩/证据链缺失/多次激活冲突 等 15 题）见 `references/faq-deep.md`。

---

## 关键参考文档（执行时按需加载，不一次塞）

| 文件 | 何时加载 | 内容 |
|------|---------|------|
| `knowledge-base/03-layered-architecture.md` | L0~L5每层开始时 | 六层每层的提取目标/内容/完成标准/分批规则 |
| `knowledge-base/04-graph-schema-v6.md` | GRAPH_BUILD 开始时 | 节点/三元组/Snake/证据的完整JSON schema |
| `protocols/baton-protocol.md` | 全程（主控每次读写baton前） | JSON接力棒字段含义 + 7条控制规则 |
| `protocols/graph-protocol.md` | GRAPH_BUILD 全程 | 7步图谱构建流水线 + 增量构建规则 |
| `protocols/phase-protocol.md` | 每次阶段切换前 | 各阶段闸门/产物验证/异常处理细则 |
| `SKILL.chunks/chunk-07-skeleton-growth.md` | L0~L5每层 | 每层执行细则 + Agent输入输出模板 |
| `SKILL.chunks/chunk-08-knowledge-graph.md` | GRAPH_BUILD | 图谱构建7步的具体执行代码/查询模板 |
| `SKILL.chunks/chunk-09-incremental-refine.md` | 回灌/打回重做时 | 增量回灌算法 + 局部重做规则 |
| `templates/user-manual.md` | WRITE阶段前 | 模块文档写作模板（v6新增：Snake章节模板+权限矩阵模板） |
| `references/anti-patterns.md` | 全程（自检时） | 10类经典错误 + v6新增"跳层/跳批/证据不足硬写"反模式 |
| `references/faq-deep.md` | 遇到疑难时 | 15个深度问答（新增v6专属5题） |

---

**版本**: 6.2.0
**最后更新**: 2026-08-11
