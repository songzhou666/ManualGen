# EntityAligner-Agent：跨层实体对齐 & 歧义消解

> **被调用时机**：GraphBuilder-Agent Step3（一次构建调用一次；若增量时 Entity 有新增/改dirty也会调用）
> **核心工作**：识别"看起来是同一实体的多个 ENTITY 节点（如「用户User」和「用户」）"，自主决策合并或保留，不询问用户。

---

## 一、候选对发现算法

```
ENTITY 总集合 E （n 个，按 n*n 两两配对，但用倒排索引加速）
对所有 (eA, eB), eA.id < eB.id：
 1. name_sim = 中文名称相似度（字重叠+拼音相似度 + alias 重合）
 2. fields_jaccard =
 len(eA.fields∩eB.fields) / len(eA.fields∪eB.fields)
 若 eA.fields 或 eB.fields 未填 → 设为 0.2（降权）
 3. common_neighbors =
 同时 (eA,eB) 被 MODULE/MANAGES 共同引用的模块数 / max(1, 被各自引用数)
 + 同时 (eA,eB) 被 FUNCTION/OPERATES_ON 共同引用的函数重合比
 4. type_match = (eA.type == eB.type) ? 1.0 : (eA.type ∈ {table,dto} 且 eB.type ∈ {table,dto}) ? 0.6 : 0.0

overall_score = 0.40*name_sim + 0.35*fields_jaccard + 0.15*common_neighbors + 0.10*type_match
```

候选分类：
| overall_score | 分类 | 处理 |
|---------------|------|------|
| ≥ 0.80 | AUTO_MERGE | 直接合并，不进 AI 判 |
| 0.60 ~ 0.80 | NEED_AI_REVIEW | 由本 Agent 基于上下文再判（自主，不询用户） |
| < 0.60 | NO_MERGE | 不合并 |

---

## 二、AI 复核裁决规则（对 0.6~0.8 的 NEED_AI_REVIEW 候选对）

AI 自主按以下规则优先顺序判，**不询问用户**：

| 规则 | 判定 | 原因举例 |
|------|------|---------|
| 字段名重合 ≥ 6 个（非id类字段） | MERGE | 「订单主表」和「订单DTO」都有 orderNo/customerId/totalAmount/status/createTime/paymentTime → 判定同一 |
| 完全不同 source_type 但 fields_jaccard ≥ 0.65 | MERGE | 「用户」backend.entity vs 「User」前端 dto，但字段高度重合 → 对齐为同一（跨端同义词） |
| 模块不同 + fields 重合<3 + name 仅部分字相同 | NO_MERGE（标记 uncertain=true） | 「日志审计」系统管理模块 vs 「日志」运维模块 → 虽都含"日志"但实体不同 |
| 模块同一 + fields 重合 3~5 + name_similarity>0.7 | MERGE | 「客户主档」和「客户」同一 MOD_客户管理 → 判定都是 ENT_客户 |
| 无法归入以上任何一条 | MERGE（但 ENTITY.meta.alignment_merged_with_uncertainty=true） | 先合并，后续若产生问题 WRITE 阶段加标注或 AUDIT 扣分 |

### 裁决记录
所有 NEED_AI_REVIEW 的决策都追加写 `_auto_decisions.md`：
```
[ENTITY_ALIGN] 候选对 #12 (ENT_049=客户主档, ENT_011=客户)
 相似度：name=0.82 fields_jaccard=0.57 common_neighbors=0.50 type_match=1.0 → overall=0.71
 AI 裁决：MERGE（规则：模块同一 + fields 重合 3~5 + name_similarity>0.7）
 主实体：ENT_011「客户」，从实体别名「客户主档」追加到 ENT_011.aliases[]
```

---

## 三、合并后状态更新 & 下游传播

```
对每个 MERGE(e_master, e_slave)：
 1. e_master.aliases.push(e_slave.name);
 if e_slave.aliases not empty → 都合并进 e_master.aliases
 2. e_master.fields = union(e_master.fields, e_slave.fields)
 （按 field.name 去重；两边都有定义但 validation 不同 → 都保留，标记冲突=conflict_in_fields_merge 交给 L5_DETAIL 回灌时再 AI 裁决）
 3. 合并证据：e_master.evidence_ids = union(e_master.evidence_ids, e_slave.evidence_ids)
 4. 更新三元组 object_id / subject_id 中 e_slave.id → e_master.id（全部重定向）
 5. 受影响传播：所有引用 e_slave 的 FUNCTION / STEP / MODULE.MANAGES 节点标记 dirty_by_entity_merge=true
 → GraphBuilder Step6 会对这些节点重算 confidence + 下游 Snake 若包含这些节点会重新校正顺序
 6. GraphBuilder 将 e_slave 标记「merged_into: e_master.id」，在 _nodes.json 列表里保留但置 disabled=true（供追溯，不参与后续写入）
```

---

## 四、跨层"FUNCTION.target_entity_id"的二次对齐（辅助功能）

Graph Step2 三元组生成前，EntityAligner 还需做一轮扫尾：
```
对所有 FUNCTION 节点 fn：
 若 fn.target_entity_id 为空但 fn.description/steps 明确提到"操作X实体"：
 - 用语义匹配 ENTITY 的 name + aliases
 - 找到 ≥1 个候选 ENT_xxx：
 confidence < 0.70 → 不自动填，fn.meta.uncertain_target_entity=true（后续 AUTO_REVIEW 裁决）
 confidence ≥ 0.70 → 直接填 fn.target_entity_id + 写入 OPERATES_ON 三元组 + 写 AI 决策
```

---

## 五、防止"过度合并"（合并的边界）

以下**严禁合并**（即使 name_sim=0.99 也不行）：
1. eA / eB 其中之一是 type=「config」（配置表），另一是 type=「business」（业务实体）
2. eA / eB 的 module_id 相同，但在 state_machine 中分别出现却没有 transition 关联到彼此
3. eA.name 包含「历史/日志/版本」关键字，eB 不含 → 「订单历史」和「订单」不应合并
4. eA 的 fields 中有 eB 完全不存在的 ≥ 8 个独特字段 → 判定为两个不同的东西，即使名字像

→ 这些规则放在 Step2 的"候选对发现"之前先剪枝，避免 AI 复核时错判。

---

**版本**: 6.2.0-agent11
**最后更新**: 2026-08-11
