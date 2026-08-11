# ManualGen 阶段执行规范 v6

> 每个阶段必须通过检查点才能进入下一阶段。本文件是阶段执行的**唯一详细来源**（SKILL.md只列总览，不重复描述）。
> v6 变化：13阶段 → 18阶段，废弃CONFIRM，新增六层 + GRAPH + AUTO_REVIEW，全流程AI自主。

---

## 0. 18 阶段路由总表

| # | 阶段 | 负责人 | 前置产物 | 阶段产物（最少） | 检查点（阻断条件） |
|---|------|--------|---------|----------------|------------------|
| 0 | START | 主控 | 无 | baton(START) | project_root 存在 |
| 1 | L0_SKELETON | Skeleton + NodeWeaver | baton | `_kb/L0_skeleton.json` | modules + roles 都≥1，data_creation_chain 给出 |
| 2 | L1_MODULE | Skeleton + NodeWeaver | L0_skeleton | `_kb/L1_modules/*.json` + `L1_INDEX.json` | 批数完成率 100%（`batches_done==batches_total`），每页都有 module_id |
| 3 | L2_REGION | Skeleton + NodeWeaver | L1_INDEX | `_kb/L2_regions/*.json` | **全部页面**每PAGE至少3个REGION（含分页/操作栏/表格区常见）+ 批数完成率100% |
| 4 | L3_FUNCTION | Skeleton + NodeWeaver | L2 regions | `_kb/L3_functions/*.json` | **全部区域** ≥90% FUNCTION 带 trigger_element + OPERATES_ON + 批数完成率100% |
| 5 | L4_OPERATION | Skeleton + NodeWeaver | L3 functions | `_kb/L4_operations/*.json` | **全部** FN 拆≥5个 STEP，STEP next_steps 完整 + 批数完成率100% |
| 6 | L5_DETAIL | Skeleton + NodeWeaver | L4 operations | `_kb/L5_details/{ENTITY,ROLE,ELEMENT,VALIDATION,AGGREGATE}/*.json` | **全部 ENTITY** fields ≥ 5 且 validation ≥ 2 条每模块 + 批数完成率100% |
| 7 | GRAPH_BUILD | GraphBuilder + EntityAligner | 六层 | `graph/_nodes/_triples/_evidence/_snakes/_layer_index/_quality.json` （6个全） | 6个JSON都存在 + nodes ≥ MODULE数+PAGE数+FN数 |
| 8 | GAP_ANALYSIS | 主控（含可选回灌） | graph_quality.json | `_gap_analysis.md` + `_auto_decisions.md` 回灌决策段 | 缺口分级完整（P0/P1/P2/P3都写） |
| 9 | AUTO_REVIEW | 主控 AI 自审 | gap_analysis.md + graph | `_auto_decisions.md` 低置信裁决段 | low_confidence_nodes 占比 ≤ 15% 或已被AI处理 |
| 10 | RESOLVE | Resolver v6 | auto_review + graph | `_resolution.md` + 各 resolution 写回 graph | HIGH 冲突 100% 有决策（不论保守解或标记⚠️） |
| 11 | WRITE | 主控（调度 Module-Writer 子Agent） | resolution + graph | `output_user_manual/_modules/*.md` | 模块文档数=MODULE数；每个≥4KB且结构齐备（见 agent04 §自检） |
| 12 | REFINE | 主控（调度 Refiner 子Agent） | `output_user_manual/_modules/*.md` | `_refine_log.md` | 各模块 REFINE 清单 ≥8/10（不合格自主修复后达标） |
| 13 | REFERENCE_CHECK | 主控 Graph 反向查询 | modules + triples | `_reference_check.md` | 术语一致率 & 引用有效率 ≥ 95% |
| 14 | INTEGRATE | Integrator v6 | `output_user_manual/_modules/` + graph + snakes | `output_user_manual/_appendix/B~F.md` + `{项目名称} 用户操作手册.md` + `_integration.md` | 主手册不含 _modules 外链；**5 大附录 B/C/D/E/F 都产出**（附录F=未覆盖清单） |
| 15 | AUDIT | 主控（10维度，含2个新增图谱） | _integration.md + graph_quality | `_audit.md` + _audit-summary.md | 10 维 ≥ 60；新增2个图谱维度权重20% |
| 16 | TODO_RESOLVE | 主控 AI 逐条解决 | audit.md | `_todo_resolution.md` + updated todo_list | P0 TODO 100% RESOLVED 或 BLOCKER 评估完成 |
| 17 | JUDGE | 子 Agent 盲审（模块级打回） | _judgment.md | `_judgment.md`（含 per_module_scores） | ≥70%模块 PASS；不合格且≤2次重试返回 WRITE；≥3次 DONE+⚠️ |
| 18 | DONE | 主控 | judgment PASS | 最终交付物（项目根） + 最终报告 | 最终文件存在于项目根；无未标记 BLOCKER |

---

## 一、条件性跳过（保留旧协议，增加新跳层场景）

### 跳过条件表（v6 更新）

| 阶段 | 跳过条件 | 跳过处理 | 跳过产物 |
|------|----------|----------|----------|
| L1~L5 任一层 | baton.layers[Lx].status == "completed"（激活恢复） | 直接推进下层 | 标记复用 |
| GRAPH_BUILD | graph/.graph_build_complete 存在时间 > 六层最晚 updated_at | 读已有 graph，不重建 | baton.graph.graph_builds 不增 |
| AUTO_REVIEW | `_auto_review_complete` 标记存在（激活恢复） | 直接推进 RESOLVE | 复用已有裁决 |
| RESOLVE | `_resolution.md` 已存在且 HIGH 冲突 0（产物判断） | 直接推进 WRITE | 标记复用 |
| WRITE（全部） | `output_user_manual/_modules/*.md` 全部存在（产物判断） | 直接推进 REFINE | 标记复用 |
| WRITE（模块级重写模式） | baton.rework.write_rerun_modules 非空 | **只重写指定模块**，其他跳过 | 单独模块追加写 |
| TODO_RESOLVE | `_todo_list.md` 为空或全 RESOLVED | 写"无待办" |  |

### 新跳层（S1 超小项目·允许合并 6 层为 EXPLORE/EXTRACT 旧流程）
仅限：MODULE < 3 且 PAGE < 10 的小型后台。
```
Master 在 L0 完成后判断：
  if modules < 3 && pages < 10:
    → 允许按 chunk-02 + chunk-03 的 v5 EXPLORE/EXTRACT/ANALYZE 走
    → 完成后直接从 EXPLORE→EXTRACT→ANALYZE→（跳过 6 层直接）→ GRAPH_BUILD
    → baton.meta.small_project_fastpath = true
  else:
    → 按 6 层正规流程，不允许跳层
```
**原因**：6 层流程虽完整，但小型项目开 6 层成本高。v5 流程对小项目足够。

### 跳过限制（与 v5 相同·更严格）
- 同一阶段最多连续跳过 2 次（防止激活死循环）
- 用户明确要求不跳过 → 禁止跳过
- **首次运行 START 时**：所有跳过条件禁用；但 GRAPH/AUTO_REVIEW 的激活恢复标记除外（激活恢复=非首次）

---

## 二、通用执行流程（继承 v5 · 新增「批级」自检）

```
每阶段 Master Step 流程：
Step 1: 读取接力棒（必做，即使刚写也要重读确认）
Step 2: 输出进度栏（按 progress-protocol.md 格式）
Step 3: 检查跳过条件 → 满足→跳过
Step 4: 按 chunk-index.yaml 加载该阶段 Chunk
Step 5: 阶段任务执行（六层/WRITE/JUDGE 是"批循环"，其他阶段是单次执行）

----- 如果是批循环阶段（L0~L5, WRITE, JUDGE模块级打回）
  for 每一批:
    5a. 加载该批最小上下文（严禁加载其他批/其他模块源码）
    5b. 调子 Agent（Skeleton / Module-Writer）执行该批
    5c. 批原子落盘（先 .tmp 后 rename，见 baton-protocol §写操作协议）
    5d. 批级质量门 run_gate_Lx / 批级文档长度检查
    5e. 更新 baton.layers[Lx] 或 baton.rework.xxx
    5f. 卸载该批上下文（释放字符串）
  → 全部批完成后，层级/模块级汇总
----- 否则（单次执行阶段：GRAPH/GAP/AUTO_REVIEW/RESOLVE/INTEGRATE/AUDIT 等）
  5a. 调该阶段 Agent，一次性跑完
  5b. 产物落盘

Step 6: 扫描产物中 TODO: 标记 → 更新 _todo_list.md
Step 7: 阶段自检清单（按各阶段检查点）
Step 7.5: 验证链检查（计数+列表+确认+Mermaid图）
Step 8: 强制更新接力棒 + save_baton
Step 9: 输出阶段完成提示
Step 10: → 进入下一阶段
```

---

## 三、各阶段检查点详解（v6 新增/变化的部分，其余继承 v5）

### 7. GRAPH_BUILD 检查点
```
阻断条件：
  - graph/_nodes.json / _triples.json / _evidence.json / _snakes.json / _layer_index.json / _quality.json 任一缺失 → 阻断
  - nodes 总数 < MODULE数 × 3（6层不可能只输出这么少·必有 Step1 归一化失败）→ 阻断 → 重跑 Step1
  - snakes_discovered==0 且 scale_target_snakes≥2 且 实体数≥5 → 不阻断，但必须在 GAP 触发"GRAPH Step5 加强版"回灌
  - entity_alignment_pending ≥ 1（Step3 合并没跑完）→ 阻断 → 返回 Step3 再跑
```

### 9. AUTO_REVIEW 检查点
```
必做事项（不作为阻断，但必须写入 _auto_decisions.md）：
  1. 每个 confidence<0.7 节点必须经过至少 1 条自主裁决规则处理
  2. incomplete_snake=true 的蛇至少过一次 §Snake审阅
  3. 权限覆盖率<60% 的模块必须尝试过"基于注解聚合+推断"补全
  4. ENTITY.fields 缺失≥40% 的模块至少尝试"基于 JPA/MyBatis mapper XML 扫字段"补全
阻断：
  以上 4 类都未处理而直接推进 → 阻断
注意：low_confidence 即使仍残留也不阻断（文档加 ⚠️ 就行），关键是 AI 必须"处理过"而非"放过"。
```

### 14. INTEGRATE（变化大）
```
继承 v5 检查项 + 新增 v6 附录要求：
阻断：
  - 主手册中出现指向 _modules/ 的链接 → 阻断（必须全文内联）
  - _appendix/ 中 B、C、D、E 四个附录任意缺失 → 阻断
  - 附录 C 不包含「仍需人工复核清单」或该清单节点数 < 实际 requires_human_review=true 节点数 → 阻断
  - 附录 E 证据索引覆盖的证据数 < 证据总数的 80% → 阻断（其余 20% 可写"未覆盖的证据列表"作为说明）
```

### 15. AUDIT（维度从 6 → 10）
```
原 6 维度（权重合计 80%）：
  1. 手册结构完整性  25%
  2. 流程图质量     20%
  3. 去技术化合规性  15%
  4. 操作可执行性   15%
  5. 角色隔离与权限  15%
  6. 异常覆盖完整度  10%
→ 按比例缩减到 80%（即 1→20, 2→16, 3→12, 4→12, 5→12, 6→8，合计 80）

v6 新增 2 维度（+2 共 10 维度，合计 20%）：
  9. 图谱交叉验证率（=cross_verified_nodes_pct × 10）→ 权重 10%
  10. Snake 完整性 & 覆盖率 = min(snakes_discovered/max(2,scale_target_snakes),1.0)
                                     ×10 - incomplete_count×0.5   → 权重 10%

原 7/8 号保留为「快速入门可用性」「术语风格统一性」引用 2 维度（合计 0%→不影响评分，只作为 REFERENCE_CHECK 审计时的 PASS/FAIL 条件）
```

### 17. JUDGE（变化大·模块级打回替代全量打回）
```
盲审输入：只传最终手册 MD 正文（不传 graph / 不传 6 层产物）
盲审按「模块级」评分（每模块 70 分合格，不看综合分）：
  - per_module_scores 中 ≥70% 的模块 score ≥ 70 → 全局 PASS
  - 某模块 < 70 & 重试 ≤2 → 写 baton.rework.write_rerun_modules=[该模块id]
      → meta.state = WRITE（按 SKILL.chunk04 §5.3 只重写该模块）
  - 某模块 < 70 & 重试 ≥ 3 → 不再重写，最终文档该模块末尾加 ⚠️ 提示 + 附录 C 列成 Top 未决项
全局综合分：模块级平均分 ×0.7 + 附录质量分 ×0.2 + 概述/通用章节分 ×0.1
→ 不再出现 v5 的 "<75% 全量回 WRITE" 的情况，最多影响单个不合格模块
```

---

## 四、产物依赖关系图 v6

```
START
  ↓
_kb/L0_skeleton.json (L0)
  ↓
_kb/L1_modules/*.json + L1_INDEX.json (L1)
  ↓
_kb/L2_regions/*.json (L2)
  ↓
_kb/L3_functions/*.json (L3)
  ↓
_kb/L4_operations/*.json (L4)
  ↓
_kb/L5_details/*/*.json (L5)
  ↓
graph/_nodes/_triples/_evidence/_snakes/_layer_index/_quality.json (GRAPH)
  ↓
_gap_analysis.md (GAP) → 可能触发 增量 BACKFILL → 回到对应 Lx → GRAPH(增量) → 再 GAP
  ↓
_auto_decisions.md + 写入 graph 不确定标记 (AUTO_REVIEW)
  ↓
_resolution.md + graph 修改 (RESOLVE)
  ↓
output_user_manual/_modules/*.md (WRITE · 子Agent按模块并行)
  ↓
_refine_log.md (REFINE)
  ↓
_reference_check.md (REFERENCE_CHECK)
  ↓
_integration.md + _appendix/B~E.md + {项目名称} 用户操作手册.md (INTEGRATE)
  ↓
_audit.md + _audit-summary.md (AUDIT · 10维)
  ↓
_todo_list.md + _todo_resolution.md (TODO_RESOLVE)
  ↓
_judgment.md (JUDGE · 模块级打回 → WRITE重写单个模块·最多3次)
  ↓
DONE → 最终交付
```

---

## 五、异常中断 & 激活恢复（全流程托管必备）

```
若激活恢复时 baton.meta.state ∈ {L0..L5}:
  if baton.layers[Lx].current_batch == baton.layers[Lx].*_batches_total:
    → 层已完成，推进下层
  else:
    → 从 current_batch + 1 开始跑下一批（不重跑已完成的批）

若 baton.meta.state == GRAPH_BUILD:
  if graph/.graph_build_complete 不存在 → 从 Step1 重跑（幂等）
  else → 直接推进 GAP

若 baton.meta.state == WRITE & baton.meta.sub_state=="RERUN_MODULES":
  → 只重跑 baton.rework.write_rerun_modules 中列出的模块
  → 跑完后把 sub_state 置为 null，继续 REFINE

若 baton.meta.state == FAILED:
  读 baton.rework.last_blocker.stage
  → 从 last_blocker.stage 的前一个阶段重新开始（不从头 START）
  → baton.rework.global_retries += 1（≥3 就真的 DONE_FAIL，写说明让用户处理）
```

---

**版本**: 6.2.0
**最后更新**: 2026-08-11
