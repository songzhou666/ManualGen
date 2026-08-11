# 知识图谱构建管道协议 v6

> 参考：Wiki-Graph 三元组 + 证据链 + SpineDigest 分阶段管道 + NovelGraph 实体对齐
> 执行Agent：GraphBuilder-Agent + EntityAligner-Agent

---

## 管道总览（7步，增量执行，不一次性全图构建）

```
Step 1: 节点归一化       Step 2: 三元组生成      Step 3: 实体对齐
    ↓                       ↓                       ↓
  各层Lx节点 → ID规范    节点间关系推导       同实体多名称合并
    ↓                       ↓                       ↓
Step 4: 证据回链聚合     Step 5: Snake概念链发现  Step 6: 置信度传播
    ↓                       ↓                       ↓
  每个节点溯源证据      跨模块语义聚类       高置信节点推低置信
    ↓                       ↓                       ↓
              Step 7: 质量评估 + 落盘
                    ↓
               graph/* 6个JSON（含 _quality.json）
```

---

## Step 1: 节点归一化（Normalize）

### 目的
L0-L5 各层分别产生节点，命名风格不一致（有的用中文名、有的用英文、有的带模块前缀、有的不带）。先统一成规范的 ID 体系。

### 规则
```
MODULE:  MOD_{序号3位}  如 MOD_001
PAGE:    PAGE_{序号3位} 如 PAGE_015
REGION:  REG_{序号3位}  如 REG_042
FUNCTION:FN_{序号3位}   如 FN_078
ENTITY:  ENT_{序号3位}  如 ENT_012
ROLE:    ROLE_{序号3位} 如 ROLE_003
ELEMENT: ELM_{序号4位}  如 ELM_0156
STEP:    STEP_{序号5位} 如 STEP_00234
```

### 归一化检查项
| 项 | 检查方式 | 不通过处理 |
|----|---------|-----------|
| ID 唯一性 | 在 graph._nodes.json 中查重 | 重复ID追加后缀 _dup1/_dup2 |
| name 非空 | 所有节点必须有 display_name | 空则从 label/filename 推断并标记待确认 |
| layer 归属 | 节点.layer 必须在L0-L5之间 | 缺失则从所在目录推断 |
| module_id 归属 | PAGE/REGION/FUNCTION 必须能追溯到 MODULE | 缺失则从文件路径推断并标记 dirty |

### 产物
追加写入 `graph/_nodes.json`（已存在则只写新节点 + 更新归一化标记）

---

## Step 2: 三元组生成（Triplify）

### 目的
各层Lx文件中只显式写了一部分关系，大量关系是隐式的（如"REGION属于PAGE属于MODULE"是层级蕴含的）。本步显式生成所有谓词的三元组。

### 显式关系（从Lx文件直接读）
```
- MODULE.id = PAGE.module_id → 生成 (MODULE)-[HAS_PAGE]->(PAGE)
- PAGE.id = REGION.page_id   → 生成 (PAGE)-[HAS_REGION]->(REGION)
- REGION.id = FUNCTION.region_id → 生成 (REGION)-[HAS_FUNCTION]->(FUNCTION)
- FUNCTION.target_entity_id  → 生成 (FUNCTION)-[OPERATES_ON]->(ENTITY)
- FUNCTION.preconditions.role_required → 生成 (ROLE)-[CAN_EXECUTE {level:rw}]->(FUNCTION)
- FUNCTION.steps → 生成 (FUNCTION)-[HAS_STEP]->(STEP) + (STEP)-[NEXT_STEP]->(STEP)
```

### 隐式关系推导（规则引擎，不是LLM）
```
规则 1: 传递闭包
  如果 A-HAS_PAGE→B 且 B-HAS_REGION→C
  则推导出 A-[CONTAINS {indirect:true}]->C
  用途：快速查询"某模块下所有区域"不用 JOIN 3次

规则 2: 反向权限传播
  如果 ROLE-CAN_EXECUTE→FUNCTION 且 FUNCTION-HAS_STEP→STEP
  则推导出 ROLE-[CAN_PERFORM {source:inherit}]->STEP
  用途：WRITE阶段查询"某角色对某步操作有没有权限"

规则 3: 实体传播
  如果 FUNCTION-OPERATES_ON→ENTITY 且 MODULE-MANAGES→ENTITY
  则推导出 MODULE-[PROVIDES_CONTEXT_FOR {count:n}]->FUNCTION
  用途：Snake发现时把同实体的功能聚类

规则 4: 模块依赖推导
  如果 ENTITY 被 MOD_A MANAGES 同时被 MOD_B OPERATES_ON(非MANAGES)
  则推导出 MOD_B-[DEPENDS_ON {data:true}]->MOD_A
  用途：数据依赖链自动发现

规则 5: 跨模块实体标记（Snake 种子）
  如果 ENTITY 被 ≥2 个 MODULE 的 FUNCTION OPERATES_ON（其中 ≥1 个非 MANAGER）
  则标记 ENTITY.meta.cross_module = true
  用途：Snake 发现时把这些实体作为跨模块链的锚点
```

### 产物
全量写入 `graph/_triples.json`（每次增量重建，因为规则可能变）

---

## Step 3: 实体对齐（Entity Alignment）

### 目的
不同代码里对同一个东西可能有不同叫法（前端叫 Customer / 后端叫 Client / 数据库表叫 t_customer），不合并的话图谱是碎片化的。

### 候选对发现（相似度判定，非LLM）
| 维度 | 计算方式 | 权重 |
|------|---------|------|
| 名称相似度 | 拼音编辑距离 + Jaccard字符合集 | 0.4 |
| 字段重合度 | ENTITY.fields.name 的交集/并集 | 0.35 |
| 上下文关联度 | 共同的 FUNCTION / MODULE 数量 | 0.15 |
| 类型匹配度 | type/enum_values 是否兼容 | 0.10 |

相似度 ≥ 0.80 → **自动合并**（置信度高）
相似度 0.60~0.80 → **标记待 AI 裁决**（写入 graph/_nodes.json 的该节点 meta.pending_auto_review=true）
相似度 < 0.60 → **不同实体**

### 合并执行
```
如果 ENT_001(Customer) ≈ ENT_008(Client):
  1. 保留主节点 ENT_001，标记 ENT_008.status = merged_into
  2. 把 ENT_008 的 fields 合并进 ENT_001（字段名冲突时，保留主节点属性，另一个字段写入 ENT_001.aliases）
  3. 把所有指向 ENT_008 的 triples 改为指向 ENT_001
  4. 把 ENT_008 的 evidence 全部加到 ENT_001 下（证据合并）
  5. 把 ENT_001.meta.confidence 重新按证据聚合
  6. 记录到 graph.entity_alignment_pending 减 1
```

### 产物
- 更新 `graph/_nodes.json`（合并实体 + 标记别名）
- 更新 `graph/_triples.json`（修改目标节点）
- 合并记录写入 `graph/_evidence.json`

---

## Step 4: 证据回链聚合（Evidence Aggregation）

### 目的
每个节点在提取时写了若干 evidence_id，本步把它们聚合成一个"证据质量分"，并标记 cross_verified。

### 算法
```
对每个 NODE：
  1. 收集所有引用该 NODE 的 EVIDENCE
  2. 按 source_type 分组（frontend/backend/db_schema/doc）
  3. 如果存在 ≥2 个不同 source_type 组 → evidence_status = cross_verified
  4. 如果只有 1 个 source_type 组 → evidence_status = single_source
  5. 如果 0 个 → evidence_status = unsupported（节点置信度强制≤0.5）
  6. 计算 NODE.meta.confidence 最终值：
       0.6 * max(各证据.raw_extraction.confidence_per_field均值)
     + 0.3 * (cross_verified ? 1.0 : 单源置信度)
     + 0.1 * (auto_review_accepted ? 1.0 : 0.5)
```

### 证据不足标记
对 `NODE.meta.confidence < 0.7` 的节点：
- 在 NODE.meta 里写 `needs_review: true` + `pending_auto_review: true`
- AUTO_REVIEW 阶段逐条裁决（chunk-07 §自主裁决），结论写回 `NODE.meta.auto_decision`
- 该节点在后续 WRITE 阶段：auto_decision=HUMAN_REVIEW_REQUIRED → 默认不引用（仅附录 C 列示）；其他结论按需使用或加 ⚠️

### 产物
更新 `graph/_evidence.json`（把节点→证据的反向索引写好）

---

## Step 5: Snake 概念链发现（Snake Discovery）

### 目的
v5最大的问题：只写单个模块的文档，**没有跨模块业务流**。用户拿到手册后不知道"从客户下单到最终收款整个怎么走"。Snake 就是补这个的。

### Snake 类别
| 类别 | 说明 | 数量目标 |
|------|------|---------|
| end_to_end_flow | 端到端业务流（如订单全链路） | 核心业务×1-2条 |
| user_journey | 关键角色操作旅程（如"销售新人第一天"） | 每个核心角色×1条 |
| data_propagation | 数据跨模块传播链（如"商品价格变更"的影响） | 核心实体×1条 |
| rule_chain | 业务规则传递链（如"审批流条件组合"） | 复杂流程×1条 |

### 发现算法
```
输入：全部 FUNCTION 节点 + 已建三元组

Step A: 数据驱动建链（实体传播）
  1. 找出"高频流转实体"（被≥3个MODULE操作的ENTITY）
  2. 对每个这样的 ENTITY：
     a. 收集所有 OPERATES_ON(ENTITY) 的 FUNCTION
     b. 按 ENTITY.state_machine 的状态流转顺序排列这些 FUNCTION
     c. 如果某个 FUNCTION 跨 MODULE → 这就是一条 end_to_end_flow
     d. 生成一条 SNAKE，node_ids 按此顺序写入

Step B: 角色驱动建链（操作旅程）
  1. 对每个 ROLE：
     a. 收集所有 CAN_EXECUTE(ROLE) 的 FUNCTION
     b. 按 module 顺序 + 用户场景常识排序（先查询→后操作→再查询）
     c. 生成一条 user_journey 类型 SNAKE

Step C: 规则驱动建链
  1. 找出 FUNCTION.preconditions 中依赖其他 FUNCTION 输出的节点
  2. FUNCTION_A.REQUIRES → FUNCTION_B.output
  3. 串成 rule_chain

Step D: 语义相似度聚类（可选，用于数据不完整时）
  1. 对 FUNCTION.description 做字面向量（不用embedding，用TF-IDF关键词重合度）
  2. 相似度 ≥ 0.65 的跨模块 FUNCTION 归为同一条 SNAKE 候选
  3. 标记为 auto_clustered（由 AUTO_REVIEW 阶段 AI 自主校验，不询用户）
```

### Snake 完整性检查
每条 SNAKE 自动检查：
- ✅ 首尾有没有 initiator/terminator（不能是中间状态）
- ✅ 中间每个 link_to_next 都有 description
- ✅ 每个 node 都有真实的节点ID（不是纯文字）
- ❌ 不合格的 SNAKE 标记为 `needs_review: true`，进入 AUTO_REVIEW 蛇审查

### 产物
写入 `graph/_snakes.json`

---

## Step 6: 置信度传播（Confidence Propagation）

### 目的
很多节点本身证据弱，但它的"邻居"证据强。通过图传播算法给它一个更合理的置信度，避免一刀切地全部标成待确认。

### 简化算法（不跑复杂PageRank，在内存中迭代3轮即可）
```
第 0 轮：各节点初始 meta.confidence = 已有的证据聚合值

第 1-3 轮迭代：
  对每个 NODE N：
    邻居集合 = 所有通过 TRIPLE 直接相连的节点
    高置信邻居 = 邻居中 confidence ≥ 0.85 的节点
    如果 len(高置信邻居) ≥ 2 且 N.confidence 在 [0.4, 0.7)：
      增量 = 0.1 * (高置信邻居平均置信度 - 0.7)
      N.confidence = clamp(N.confidence + 增量, 0.4, 0.75)
    （不能超过 0.75，邻居证据强不代表节点本身可靠，只是减少待 AI 核验的低置信项）

第 4 轮：收尾
  对 confidence 更新过的节点，在 meta 里写入：
    propagated_confidence: true
    original_confidence: 原来的值
  证据状态仍保持 single_source/unsupported（传播不改证据质量）
```

### 产物
更新 `graph/_nodes.json`（置信度字段）

---

## Step 7: 质量评估 + 落盘

### 指标计算
写入 `_baton.graph.graph_completeness_score` 和 `graph_quality_score`：
```
completeness = Σ(各层完成率 × 权重)
  L0×0.10 + L1×0.15 + L2×0.15 + L3×0.20 + L4×0.20 + L5×0.20

quality = Σ(质量项 × 权重)
  evidence_cross_verified_rate × 0.35
  (1 - low_confidence_nodes_count/total_nodes) × 0.25
  snakes_discovered / 目标Snake数 × 0.20
  entity_alignment_pending == 0 ? 1.0 : 0.5 × 0.20
```

### 落盘顺序（强制！）
```
1. graph/_nodes.json       → 节点归一化+置信度后的最终节点
2. graph/_triples.json     → 显式+隐式推导的全部三元组
3. graph/_evidence.json    → 证据+反向索引
4. graph/_snakes.json      → 概念链
5. graph/_layer_index.json → 各层进度+质量（给 AUTO_REVIEW/用户追问进度时展示用）
6. graph/_quality.json     → 质量评估汇总（cross_verified_nodes_pct / completeness / low_confidence / snake_breakdown / scale_target_snakes 等，供 AUDIT §⑨⑩ 维度与 GAP 查询）
7. graph/.graph_build_complete ← 最后写当前时间戳（唯一"完成标记"；任一步写失败→下次激活发现标记缺失→从第1步幂等重跑）
```

---

## 增量构建（续跑时的核心）

如果不是第一次跑 GRAPH_BUILD：
1. 只处理 `dirty=true` 的节点 + 新加入的节点（`created_at > last_graph_build_at`）
2. Step 1/2/4/6/7 只重算受影响的子图
3. Step 3（实体对齐）全部重跑（因为可能上次留下的待确认对这次有新证据）
4. Step 5（Snake发现）：只重算 `needs_review=true` 或 包含dirty节点的 Snake，其他不动
5. **禁止**删除已 AI 裁决通过（auto_decision ∈ accepted 集合）的 Snake 或 已裁决的节点

---

**版本**: 6.1.0-graph-pipeline
**最后更新**: 2026-08-11
