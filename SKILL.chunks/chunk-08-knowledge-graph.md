# Chunk 08: 知识图谱构建流水线（Knowledge Graph Pipeline）

> **加载时机**：GRAPH_BUILD 阶段
> **执行Agent**：GraphBuilder-Agent（7步流水线） + EntityAligner-Agent（Step3实体对齐）
> **全自主**：7步全自动跑完，不打断用户，中间结果立即落盘。

---

## Step 1: 节点归一化（Normalize）

### 输入
`_kb/L0_skeleton.json` + `_kb/L1_modules/*.json` + `_kb/L2_regions/*.json` + `_kb/L3_functions/*.json` + `_kb/L4_operations/*.json` + `_kb/L5_details/*.json`

### 执行
| 规则 | 处理 |
|------|------|
| ID规范化 | 扫描所有节点，按 MOD_xxx / PAGE_xxx / REG_xxx / FN_xxx / ENT_xxx / ROLE_xxx / ELM_xxxx / STEP_xxxxx 重新分配**全局唯一ID**，写映射表 `id_remap: {old->new}` |
| layer归属补齐 | MODULE/ROLE → L0；PAGE/ENTITY→L1；REGION→L2；FUNCTION/ELEMENT→L3；STEP→L4；FIELD/EVENT→L5 |
| display_name补齐 | 中文label优先，无则用name |
| module_id追溯 | REGION/FUNCTION/STEP/ELEMENT 缺module_id → 向上查 PAGE→module_id 传播 |
| 脏节点标记 | dirty=true 的节点单独放 dirty_nodes 数组，Step2/6/7 只处理它 + 新节点 |

### 输出
`graph/_nodes.json`（增量写入：保留已归一化且非dirty的节点，重算 dirty + 新节点）

```json
{
  "normalized_at": "...",
  "id_remap_count": 12,
  "dirty_nodes_processed": 5,
  "new_nodes_added": 18,
  "nodes": [ /* NODE v6 schema 见 knowledge-base/04-graph-schema-v6.md */ ]
}
```

---

## Step 2: 三元组生成（Triplify）

### 执行
先从各Lx文件直接生成显式三元组（4类），再跑规则引擎生成隐式三元组（4条传播规则）。

### 显式
```
MODULE.page_ids          → HAS_PAGE  → PAGE
PAGE.regions[].region_id → HAS_REGION → REGION
REGION.functions[].fn_id → HAS_FUNCTION → FUNCTION
FUNCTION.steps[].step_id → HAS_STEP → STEP
FUNCTION.target_entity_id → OPERATES_ON → ENTITY
FUNCTION.trigger_element.element_id → TRIGGERED_BY → ELEMENT
FUNCTION.preconditions.roles → ROLE.CAN_EXECUTE {level} → FUNCTION
STEP.next_steps[] → NEXT_STEP → STEP（带branch条件）
MODULE.entities[].entity_id → MANAGES → ENTITY
```

### 隐式规则引擎（Graph-only，不用LLM）
| # | 规则 | 谓词 |
|---|------|------|
| R1 | A-HAS_PAGE→B-HAS_REGION→C ⇒ A-CONTAINS{indirect:true}→C | 间接归属 |
| R2 | ROLE-CAN_EXECUTE→FUNCTION-HAS_STEP→STEP ⇒ ROLE-CAN_PERFORM{src:inherit}→STEP | 权限传播 |
| R3 | FUNCTION-OPERATES_ON→ENTITY 且 MODULE-MANAGES→ENTITY ⇒ MODULE-PROVIDES_CONTEXT_FOR{count:n}→FUNCTION | 实体传播聚类（Snake发现同实体功能聚类） |
| R4 | FUNCTION-OPERATES_ON→ENTITY←MANAGES←MODULE ≠ FUNCTION.module ⇒ MODULE-DEPENDS_ON{data:true}→MODULE | 模块依赖发现 |
| R5 | ENTITY被M个MODULE操作(非管理) ⇒ 标记 ENTITY.meta.cross_module=true，作为Snake种子 | 跨模块实体标记 |

### 输出
`graph/_triples.json`（dirty涉及的子图全量重建 + 不变部分保留 + R4/R5 触发的自动回灌标记）

---

## Step 3: 实体对齐（Entity Alignment · EntityAligner-Agent）

### 候选对发现
```
对所有 ENTITY 两两配对：
  score = 0.4*名称相似度 + 0.35*字段Jaccard + 0.15*共同邻居(FUNCTION/MODULE数) + 0.10*类型匹配
```
- ≥0.80 → 自动合并
- 0.60~0.80 → 标记 `pending_auto_review=true`，由 EntityAligner 基于上下文再判（仍AI自主，不询用户），若仍不确定则合并但保留 `meta.alignment_merged_with_uncertainty=true`
- <0.60 → 不合并

### 合并后动作
- 节点保留主节点，从节点写入主节点.aliases
- 三元组 object_id/subject_id 全部重定向
- 证据合并，confidence重新算
- 下游节点（FUNCTION/STEP 等）标记 `dirty_by_entity_merge=true`，Step 6 置信度传播会刷新它们

### 输出
`graph/_nodes.json`（合并后实体） + `graph/_triples.json`（重定向后） + baton.graph.entity_alignment_pending 重置为0

---

## Step 4: 证据聚合（Evidence Aggregation）

### 规则
每个NODE：
1. 收集所有引用它的EVIDENCE（各Lx节点的evidence字段合并）
2. 按 source_type 分组：frontend / backend / db_schema / doc / user_confirmed
3. ≥2个不同source_type → cross_verified
4. 只有1组 → single_source
5. 0组 → unsupported，confidence强制≤0.5
6. 按公式聚合计信度：`0.6*max(各证据置信度) + 0.3*(cross_verified?1:单源) + 0.1*(manual?1:0.5)`

### unsupported节点处理
- **不是丢弃**！而是标记 meta.needs_strong_evidence=true，并在 Step 6 尝试置信度传播拉到≥0.4

### 输出
`graph/_evidence.json`（含反向索引：evidence_id → supporting_node_ids[]）

---

## Step 5: Snake概念链发现（Snake Discovery）

### 目标
自动发现端到端跨模块业务流，AI自主排序，**不询问用户**。

### 流水线
```
Step A 种子生成
  1. ENTITY.meta.cross_module=true（R5规则标记）的实体 → 每个生成1条 end_to_end_flow 蛇的种子
  2. 每个核心 ROLE → 生成1条 user_journey 蛇的种子
  3. 跨 MODULE 的 FUNCTION.preconditions.REQUIRES(其他FUNCTION.output) → 生成1条 rule_chain 蛇的种子

Step B 节点扩展（对每个种子snake）
  对蛇头FN_A：
    查 TRIPLE (FN_A)-[:OPERATES_ON]->(ENT_x)-[:OPERATES_ON]<-(FN_B)，且FN_B.module≠FN_A.module
    若 ENT_x.state_machine 中有状态流转 FN_A→state→FN_B，把 FN_B 追加到 snake.node_ids
  递归直到找不到新的跨模块节点

Step C 顺序校正（AI自主·不询用户）
  1. 按 L0.data_creation_chain 的 ENTITY 顺序给每个 FUNCTION 打位置分
  2. 按 FUNCTION.preconditions.REQUIRES 拓扑排序
  3. 取两者加权平均后的顺序作为最终 snake.node_ids 顺序
  4. 记录 snake.meta.auto_reordered = true / false

Step D 合理性回环检查
  蛇必须：第一个是 initiator（如"新建""发起"类），最后一个是 terminator（如"结算""归档""完成"类）
  否则补头尾节点或标记 snake.meta.incomplete_snake=true（WRITE阶段只展示完整的snake，不完整的写入AI决策附录）
```

### 输出
`graph/_snakes.json`（每条蛇都有 category + node_ids + link_to_next + auto_reordered 标记 + needs_review=false（因为AI已自主审））

---

## Step 6: 置信度传播（Confidence Propagation）

> 目的：减少 low_confidence 节点数，降低 AUTO_REVIEW 阶段需要处理的量。

### 3轮迭代（内存算，图≤1000节点毫秒级）
对所有 NODE：
```
high_conf_neighbors = 直接相连三元组对方的 confidence≥0.85 的节点数
if len(high_conf_neighbors) ≥ 2 且 NODE.confidence ∈ [0.4, 0.7):
  delta = 0.1 * (avg(high_conf_neighbors).confidence - 0.7)
  NODE.confidence = clamp(NODE.confidence + delta, 0.4, 0.75)
  NODE.meta.propagated_confidence = true
  NODE.meta.original_confidence = 原值
```
- 传播后仍<0.7 → AUTO_REVIEW阶段处理
- 传播后≥0.7 → 视为可信，WRITE阶段正常引用（但标记propagated备查）

### 输出
`graph/_nodes.json`（confidence刷新 + propagated标记）

---

## Step 7: 质量评估 + 顺序落盘

### 质量指标计算
```
completeness = L0*0.1 + L1*0.15 + L2*0.15 + L3*0.20 + L4*0.20 + L5*0.20
quality =
    graph.evidence_cross_verified_rate * 0.35
  + (1 - low_confidence_nodes/total_nodes) * 0.25
  + min(snakes_discovered / max(2, scale_target_snakes), 1.0) * 0.20
  + (entity_alignment_pending == 0 ? 1.0 : 0.5) * 0.20
```

### 顺序落盘（强制！防止写入中间崩溃只写了一半）
```
1. graph/_nodes.json        → 先原子写 temp，fsync 后 rename
2. graph/_triples.json      → 同上
3. graph/_evidence.json     → 同上
4. graph/_snakes.json       → 同上
5. graph/_layer_index.json  → 同上（每层 quality_score / completeness_score / progress）
6. graph/_quality.json      → 同上（质量评估汇总，供 AUDIT §⑨⑩ 维度与 GAP 查询）
7. graph/.graph_build_complete ← 最后写当前时间戳（唯一"完成标记"；任一步写失败→下次激活发现标记缺失→从第1步幂等重跑）
8. baton.graph.* 字段同步更新（由 master 单点写）
```

---

## §Snake审阅（AUTO_REVIEW阶段自调用）

AI自主检查所有 snake：
1. **完整性**：initiator + terminator 是否齐全 → 缺则补虚拟节点（标记auto_added）或标记 incomplete 不入附录
2. **顺序正确性**：是否符合 data_creation_chain → 若冲突则按 R4 数据链重排
3. **描述合理性**：link_to_next.description 是否跟 FUNCTION.name 语义合 → 不合则 AI 自写一句更合理的 description
4. 全部裁决结果写 `_auto_decisions.md`，形如：
   ```
   [SNAKE_001] 订单全生命周期链
     - 原序列缺「财务对账」terminator → 已自动追加 FN_056 财务对账作为 terminator（依据：ENTITY_订单.state_machine 终态为「已结算」）
     - link(创建订单→扣库存) 描述原写「自动」→ 已改写「订单审核通过后自动触发」
   ```

---

## 增量构建（断点续跑规则）

若 `graph/_nodes.json` 已存在且 baton.graph 非空：
1. 扫描各 Lx 文件的 updated_at vs `_nodes.json` 的 `last_graph_build_at`
2. 只把"新文件/更新过的文件"中的节点标记为 dirty
3. Step 1-7 只处理 dirty 节点 + 它们的 2 跳邻居（防止传播遗漏）
4. **禁止删除任何以下节点**：
   - snake.meta.manual_confirmed = true 的 Snake（AUTO_REVIEW 阶段已裁决的蛇）
   - `evidence[].verification_status == auto_reviewed` 或 `user_confirmed` 的节点（AUTO_REVIEW 已裁决）
   - 附录 C 中标记为 HUMAN_REVIEW_REQUIRED 但尚未复核的节点（保留待人工确认）

---

**版本**: 6.2.0-chunk08
**最后更新**: 2026-08-11
