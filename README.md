# ManualGen v6.2.0 · 智能业务分析与操作手册生成专家
## 六层递进式骨架生长架构 + 知识图谱编织 + 增量回灌

**定位**：不是"把代码翻译成文档"，而是像产品经理一样理解业务→像用户一样梳理流程→像运维一样沉淀细节，最终输出真正详细、可追溯到代码行的**用户操作手册**。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **六层递进提取** | L0骨架 → L1模块 → L2区域 → L3功能 → L4操作 → L5细节，逐层生长，不跳层 |
| **知识图谱驱动** | 8 种节点（MODULE/PAGE/REGION/FUNCTION/ENTITY/ROLE/ELEMENT/STEP）+ 20+ 关系谓词，构建业务语义网 |
| **Snake 跨模块链** | 独立章节+Mermaid流程图输出端到端业务流，不用跨 4 个模块翻手册 |
| **证据溯源 & 置信度** | 每段文字≥3条源码证据（路径+行号+代码片段），低置信节点自动标⚠️不虚假输出 |
| **增量回灌** | 新模块/代码变更只做局部补正，不从头重跑整个项目 |
| **断点续跑** | 每批写完立即落盘+更新JSON接力棒，关掉对话下次接着跑 |
| **全流程托管** | 18 阶段状态机全自主推进 + AI 自审无用户打断，零配置也能出文档 |

---

## 架构亮点（v6 vs v5）

| 维度 | ManualGen v6 | ManualGen v5（旧版） |
|------|-------------|-------------------|
| 信息架构 | 六层增量 + 知识图谱（非扁平md） | 一次全读 + 扁平md |
| 阶段数 | 18 阶段（含 AUTO_REVIEW 自审） | 13 阶段（含 CONFIRM 需用户确认） |
| Agent 数量 | 11 个专职 Agent 分工协作 | 7 个 Agent |
| 跨模块流程 | Snake 概念链独立章节 + 端到端 Mermaid | 各模块独立无联系 |
| 证据机制 | 每节点≥3条证据 + 反向索引可定位到源码行 | 只输出文本，不保存证据 |
| 低置信处理 | AI 自主裁决 + 警告语（不写虚假操作） | 要求用户一个个确认 |
| 上下文优化 | 按阶段+批+section 按需加载 chunks | 一次读所有 chunk |
| 断点粒度 | 每批原子写，随时停随时续 | 每阶段写，停在中间会丢 |
| 项目规模上限 | 无限（批处理分治 + 增量回灌） | 中大型项目上下文溢出 |
| 全流程托管 | ✅（激活后自动跑到 DONE） | ❌（中间频繁问用户） |

---

## 快速开始（30秒入门）

ManualGen v6 是**全流程托管**的，无需配置。以下 3 种是最常用的打开方式，直接复制粘贴就能出结果。

### ✅ 触发示例 1：从零写整套手册（最常用）

```
帮我生成 E:\my-erp 这套项目的完整用户操作手册，面向运营和客服使用。
```

→ AI 立即启动 L0 骨架 → … → 项目根目录生成 `my-erp 用户操作手册.md`。大型 ERP（30+ 页面）典型耗时 20~30 分钟（中途关对话断点续跑）。

### ✅ 触发示例 2：只写重点模块 + 重点业务流

```
重点帮我梳理 E:\my-erp 的「客户管理」「订单管理」「财务收款」这 3 个模块，
并突出"从客户下单→财务收款→发货跟踪"的完整端到端流程。
```

→ 因用户**显式点名了模块范围**，AI 开启「核心优先模式」（默认全量关闭）：指定模块 L0-L5 全量写完手册，其余模块扫到 L2 作背景并列入附录 F 未覆盖清单。若用户未点名模块范围，则默认全量模式覆盖全部模块。

### ✅ 触发示例 3：代码改了只补增量

```
E:\my-erp 我新增了「智能建议 suggestions 模块」，帮我把这部分补进原手册里。
```

→ AI 走增量回灌：只扫描新模块对应 L1→L2→… → 图谱局部重建 → 只追加新章节，旧内容一丝不动。

> 中途想看进度 → 发一句「进度」或「暂停」即可；不想看了发「继续」或不理它 → 自动接着跑。

---

## 适用场景 vs 不适用场景

| ✅ 适用 | ❌ 不适用 |
|--------|---------|
| 大型项目从零写操作手册（推荐） | 单次简单问答（直接问 AI 即可） |
| 代码量大、需要增量式提取 | 纯编码任务（写代码/改bug） |
| 需要端到端跨模块流程梳理（Snake） | 只要一句话摘要/一句话总结 |
| 需要字段、按钮、权限级别的详细手册（L5） | — |
| 追求细致不是概括、希望有证据追溯 | — |
| 需要 0 人配置全托管生成（18阶段AI自主） | — |

---

## 目录结构

```
.trae/skills/ManualGen/
├── SKILL.md                              # 主入口（18阶段/FAQ/新手入门）
├── README.md                             # 本文件（产品介绍）
├── SKILL.chunks/                         # ===== 按阶段分节 01~09 =====
│   ├── chunk-index.yaml                  # 加载矩阵 + 路由表
│   ├── chunk-01-overview.md              # 强制入口清单 + 18阶段状态机
│   ├── chunk-02-explore-extract.md       # S1小项目捷径：探索/抽取（v5兼容）
│   ├── chunk-03-analyze-gap.md           # 缺口分级 P0~P3（从图谱查）
│   ├── chunk-04-resolve-write.md         # 6冲突解决 + WRITE 6件套
│   ├── chunk-05-audit-judge.md           # 10维度自评 + TODO + JUDGE 盲审
│   ├── chunk-06-privacy-security.md      # 隐私与安全约束
│   ├── chunk-07-skeleton-growth.md       # v6核心：L0-L5 六层批处理规则
│   ├── chunk-08-knowledge-graph.md       # v6核心：7步图谱 + Snake
│   └── chunk-09-incremental-refine.md    # v6核心：增量回灌 + 局部重做
│
├── agents/                               # ===== 15个 Agent 文件（11个专职 + 4个v5兼容/legacy）=====
│   ├── 00-master-controller.md           # 主控：18阶段编排+批调度+回灌
│   ├── 01-extractor-agent.md             # 抽取（L0辅助，v5 legacy）
│   ├── 02-analyzer-agent.md              # 分析（L4流程辅助，v5 legacy）
│   ├── 03-resolver-agent-enhanced.md     # 6类冲突全自主规则（v6主用）
│   ├── 03-resolver-agent-v2-legacy.md    # 旧版Resolver（v5保留，不参与v6流程）
│   ├── 04-module-writer-agent.md         # 按模块隔离上下文写 6 件套
│   ├── 05-integrator-agent.md            # 4附录B/C/D/E 整合
│   ├── 06-file-writer-agent.md           # 文件落盘控制（v5 legacy）
│   ├── 07-gap-analyst-agent.md           # 缺口分级 P0~P3（v6从图谱查）
│   ├── 08-skeleton-agent.md              # L0-L5 六层批处理引擎
│   ├── 09-node-weaver-agent.md           # 节点级 E/F/E/R/S + 证据
│   ├── 10-graph-builder-agent.md         # 7步图谱流水线（6个JSON）
│   ├── 11-entity-aligner-agent.md        # 实体对齐 + 置信传播
│   ├── 12-refiner-agent.md               # 盲检·模块级修复（v6新增）
│   └── 14-judge-agent.md                 # 盲审·模块级打回（v6新增）
│
├── protocols/                            # ===== 协议规范 =====
│   ├── baton-protocol.md                 # JSON 接力棒 v6 规范
│   ├── graph-protocol.md                 # 图谱 Schema + 7步流水线
│   ├── phase-protocol.md                 # 18 阶段检查点 + 跳过早停
│   ├── progress-protocol.md              # 18阶段进度可视化（批级）
│   └── todo-protocol.md                  # TODO 逐条解决 + 熔断
│
├── knowledge-base/                       # ===== 知识沉淀 =====
│   ├── 00-schema.md                      # 底层 schema（v5目录体系，legacy）
│   ├── 01-context-manager.md             # 阶段/批/section 三级上下文管理
│   ├── 02-knowledge-accumulation.md      # 知识累积（v5产物演进，legacy）
│   ├── 03-layered-architecture.md        # 六层批处理 + 质量闸
│   └── 04-graph-schema-v6.md             # 8节点/20+谓词/SnakeSchema
│
├── templates/                            # ===== 模板 =====
│   ├── user-manual.md                    # 最终手册结构模板
│   ├── flowchart-spec.md                 # 流程图规范（chunk 加载矩阵 ID=10）
│   ├── exploration-report.md             # S1 探索报告模板（v5兼容）
│   ├── appendix-B-permission-matrix.md   # 附录B权限矩阵模板
│   ├── appendix-C-AI-auto-decisions.md   # 附录C AI决策记录模板
│   ├── appendix-D-snake-flows.md         # 附录D Snake全景模板
│   └── appendix-E-evidence-index.md      # 附录E证据索引模板
│
├── references/                           # ===== 参考文档 =====
│   ├── anti-patterns.md                  # 反模式说明（含 v6 新增反模式）
│   └── faq-deep.md                       # 进阶 FAQ（深度问题）
│
├── artifacts/                            # ===== v5 产物模板（legacy）=====
│   └── template-artifacts.md             # 产物总览表（v5阶段）
├── quality-control/                      # ===== 质量标准 =====
│   └── 00-quality-system.md              # 质量体系（AUDIT 对齐）
├── privacy/privacy-notice.md             # 隐私承诺
├── 1-manifest/skill-manifest.yaml        # Skill 元数据（version 6.2.0）
└── CHANGELOG.md                          # 版本变更日志
```

---

## 版本记录

| 版本 | 日期 | 核心变化 |
|------|------|---------|
| v6.2.0 | 2026-08-11 | 全流程自主托管：AUTO_REVIEW 取代 CONFIRM、JUDGE 模块级打回、AUDIT 10 维度、产物路径统一、附录 B~E 模板、Refiner/Judge Agent 补齐 |
| v6.0.0 | 2026-08-10 | 六层增量 + 知识图谱 + Snake + 增量回灌，13→18 阶段 |

---

© ManualGen Team · Licensed under CC-BY-SA 4.0
