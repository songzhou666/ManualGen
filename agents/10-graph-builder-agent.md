# GraphBuilder-Agent：7步知识图谱构建流水线

> **调度阶段**：GRAPH_BUILD（Master 调度 Skeleton 跑完 L5 后调用一次，增量模式可被回灌调度触发多次）
> **输入**：`_kb/L0_skeleton.json` + `_kb/L1_modules/*.json` + `_kb/L2_regions/*.json` + `_kb/L3_functions/*.json` + `_kb/L4_operations/*.json` + `_kb/L5_details/*.json`
> **输出**：`graph/_nodes.json` / `_triples.json` / `_evidence.json` / `_snakes.json` / `_layer_index.json` / `_quality.json`（共 6 个，含质量评估汇总）
> **全自主**：7 步全跑完自动推进，除非 Step4 证据聚合后 total_evidence < 10（真的没任何来源，说明项目太小/读失败）→ 记录+不阻塞。

---

## 一、调用约定

Master 只需要发：
```
GraphBuilder-Agent.run(
  mode: "FULL" | "INCREMENTAL",  // 首次=FULL，增量回灌=INCREMENTAL
  dirty_node_ids: [ /* INCREMENTAL 模式传 */ ],
  dirty_file_globs: [ /* 或者传脏文件列表也行，AI 内部解析 */ ]
)
```

不管模式，GraphBuilder 内部都按 Chunk-08 定义的 7 步：
1. **Normalize**（ID归一化 + dirty 标记）
2. **Triplify**（4类显式 + 4类隐式传播规则）
3. **Entity Alignment**（AI 调 EntityAligner-Agent，自主完成合并）
4. **Evidence Aggregation**（按 4 种 source_type 聚合计信度 + cross_verified 判定）
5. **Snake Discovery**（4 类种子 + 扩展 + 顺序校正 + 回环检查，AI自主）
6. **Confidence Propagation**（3轮迭代拉齐置信度，避免全是 low_confidence）
7. **Quality Eval + 顺序落盘**（6层质量分算出 + 原子文件写 temp→rename）

### 禁止
- 不允许跳过其中任何一步（哪怕是 tiny 项目，Step5 Snake 找不到也必须跑完至少产出空 snakes 数组 + log）
- 不允许把 `graph/_nodes.json` 直接写 JSON（必须先写 `_nodes.json.tmp`，`fsync` 后 rename，防止写一半崩溃留半截文件）

---

## 二、子 Agent 协同

### GraphBuilder ↔ EntityAligner
Step 3 触发：
```
GraphBuilder（Step2 后状态）：
  - 产生 136 ENTITY
  - 初步相似度扫描 → 38 对 0.6~0.8 需复审（其他≥0.8自动合并，<0.6不合并）

→ 调 EntityAligner-Agent.resolve(candidate_pairs: 38对)
→ EntityAligner 按 Chunk-08 Step3 规则 + 上下文自主判
→ 返回 38 对的 merge_list（[主实体ID, 从实体ID][]） + uncertainty_list（12 对不确定但仍合并）
→ GraphBuilder 执行合并 + 三元组重定向 + 写 uncertainty 标记到 ENTITY.meta
```

### GraphBuilder ↔ 主控（Master）增量回灌
若 Graph Step5 跑完：
- snakes_discovered = 0
- 或 low_confidence_nodes / total_nodes > 35%

→ GraphBuilder 不自己回灌，但在 GRAPH_BUILD 结果报告中明确标记：
```
{
  "graph_quality_flags": ["NO_SNAKES", "HIGH_LOW_CONFIDENCE_RATE"],
  "suggested_backfill_scopes": [
    { layer: "L5", category: "FIELD", entities: ["ENT_订单"] },
    { layer: "L5", category: "VALIDATION", functions: ["FN_014"] },
    { layer: "GRAPH", mode: "RERUN_STEP5_STRONG" }
  ]
}
```
→ 由 Master 在 GAP_ANALYSIS 阶段基于 Chunk-09 触发增量回灌。

---

## 三、顺序落盘原子操作约定（7步内第7步的子规范）

```
写文件顺序（必须严格递增，前面的 fsync 成功才写下一个）：
  1. graph/_nodes.json.tmp       → fsync → rename → _nodes.json
  2. graph/_triples.json.tmp     → fsync → rename → _triples.json
  3. graph/_evidence.json.tmp    → fsync → rename → _evidence.json
  4. graph/_snakes.json.tmp      → fsync → rename → _snakes.json
  5. graph/_layer_index.json.tmp → fsync → rename → _layer_index.json
  6. graph/_quality.json.tmp     → fsync → rename → _quality.json
  7. graph/.graph_build_complete ← 最后写当前 timestamp（空文件也行，作为唯一"完成标记"）
写失败恢复：
  - 任一步写失败：下次激活看到第7个完成标记文件不存在 → 从第1步重跑（节点三元组都是幂等的，重复生成不影响）
  - 增量模式 dirty 节点：即使写一半，下一次也会重新被识别为 dirty（因为 .graph_build_complete 的时间比他们 updated_at 早）
```

---

## 四、图谱质量指标计算（作为 AUDIT & JUDGE 的输入）

写完 6 个 JSON（_nodes/_triples/_evidence/_snakes/_layer_index/_quality）后最后写 `.graph_build_complete` 完成标记：

```json
{
  "completeness_by_layer": {
    "L0": 100, "L1": 100, "L2": 97.8, "L3": 95.2, "L4": 92.0, "L5": 88.0
  },
  "graph_counts": {
    "nodes": 482, "triples": 2103, "evidences": 1644, "snakes": 7
  },
  "quality_rates": {
    "cross_verified_nodes_pct": 64.2,
    "low_confidence_nodes_pct": 11.8,
    "propagated_confidence_pct": 5.3,
    "entity_merged_pairs": 27,
    "entity_alignment_uncertainty_pct": 8.2
  },
  "snake_breakdown": {
    "end_to_end_flow": 3, "user_journey": 2, "rule_chain": 2,
    "incomplete_count": 1,
    "auto_reordered_count": 4
  },
  "graph_quality_flags": [],   // ["NO_SNAKES", "HIGH_LOW_CONFIDENCE_RATE"] 等
  "overall_quality_score": 87.6
}
```

- **AUDIT 阶段新增的 2 个维度**（参考 Chunk-05 §AUDIT 10 维，其中 2 个为图谱新增）：
  - 维度9「图谱交叉验证率」权重 10% → cross_verified_nodes_pct
  - 维度10「Snake 完整性 & 覆盖率」权重 10% → snake_breakdown.incomplete_count 和 snakes/scale_target_snakes

---

## 五、增量构建（Chunk-08 §增量构建 的实际执行规范）

INCREMENTAL 模式启动时：
1. GraphBuilder 先读已有的 `_nodes.json`，把所有节点 loaded_from_existing=true
2. 扫描 `_kb/Lx_*/*.json` 中 updated_at 大于 `_nodes.json` 里 normalized_at 的文件 → 其内部节点标 dirty
3. 再加上传入的 dirty_node_ids（回灌时 Master 传入）
4. 7 步流水线只处理 dirty=true 节点，但：
   - **Step 3 实体对齐**：所有 ENTITY 都参与（因为可能新节点和旧实体是同义词）
   - **Step 6 置信度传播**：dirty 的 + 2 跳邻居参与，其他保持原值
5. Step 7 落盘时：旧节点（非dirty/未动）直接写回，dirty 的节点用计算后的新值覆盖
6. Step 7 写 `_nodes.json.normalized_at` = 当前时间

---

**版本**: 6.2.0-agent10
**最后更新**: 2026-08-11
