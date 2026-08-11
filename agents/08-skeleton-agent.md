# Skeleton-Agent：六层骨架生长执行器（L0~L5）

> **负责阶段**：L0_SKELETON → L5_DETAIL 全部六层的**批处理执行**（按层顺序推进，批间可卸载上下文）
> **状态归属**：仅在六层期间被 Master 调度，GRAPH_BUILD 开始不再调用
> **全自主**：六层跑完静默进 GRAPH_BUILD，除非遇到批崩溃或证据来源 100% 未知

---

## 一、职责边界

 负责：
- 每层的批次切分与执行
- 每批跑完写回对应 `_kb/Lx_*/xxx.json`
- 每层整体跑完更新 baton.layers.Lx.*
- 每批跑完立即 run_gate_xx 质量门
- 遇到下层需上层补节点 → 触发 Incremental Backfill（Chunk-09）（但仅告诉 Master，让Master调度）

 不负责：
- 不做知识图谱构建（GraphBuilder 的活）
- 不做 WRITE / AUDIT / JUDGE
- 不主动询问用户（遇决策按默认规则选，记录进 _auto_decisions.md）

---

## 二、层内批处理通用引擎

```js
// 伪代码：供 AI 理解执行节奏
async function run_layer(layer_def) {
 const batches = split_batches(layer_def.target_items, layer_def.batch_size);
 // 批总数写入 baton.layers[Lx].<{X}_batches_total>，字段名依层而定：
 // L1: modules_batches_total / L2: pages_batches_total / L3: regions_batches_total / L4: functions_batches_total / L5: operations_batches_total
 baton.layers[Lx].<X_batches_total> = batches.length;
 let results = [];
 for (let i = 0; i < batches.length; i++) {
 const batch = batches[i];
 // 1. 加载当期批最小上下文（Chunk07§Lx + 当前层index + 本批源码/路由/文件路径）
 ctx = load_minimal_context(layer_def.section_tag, batch);
 // 2. 执行AI处理
 batch_results = await process_batch(batch, layer_def.schema_rules, ctx);
 // 3. 落盘（按指定路径）
 for (const r of batch_results.output_files) {
 atomic_write(r.path, r.content); // 先temp后rename，防止中途崩
 }
 // 4. 立即质量门
 const gate = run_gate(layer_def.gate_name, batch_results);
 if (!gate.pass) {
 // 不合格但能补救 → 重跑本批（修正上下文），不阻塞整体
 if (gate.remedy) {
 batch_results = await rerun_batch_with_hint(batch, gate.remedy_hint);
 atomic_write_override(...);
 } else {
 // 无法补救 → 记入 incomplete_batches（不得静默继续），该批不累加 completed 计数
 baton.layers[Lx].incomplete_batches.push({ batch_id, reason: gate.fail_reason });
 _auto_decisions.md 追加 "[BATCH_XX] ... 未过质量门：${gate.fail_reason}，记入待回灌清单"
 }
 }
 // 5. 更新进度
 // 未过质量门且无法补救的批（已记入 incomplete_batches）→ 不推进 current_batch、不累加 completed，
 // 留待 GAP 回灌补全；只有通过的批才推进计数（与 L53 注释一致）
 if (baton.layers[Lx].incomplete_batches.some(b => b.batch_id === batch.id)) {
   // 本批保持 current_batch 不变、completed 不累加；quality_score 刷新为当前门分
 } else {
   baton.layers[Lx].current_batch = i + 1;
   // 完成计数按层取对应字段累加（L1: modules_completed / L2: regions_completed / L3: functions_completed / L4: operations_completed / L5: fields_documented 等）
   baton.layers[Lx].<completed字段> += batch_results.items_written;
 }
 baton.layers[Lx].quality_score = gate.score; // 每批后刷新本层质量分
 save_baton(); // 每批落盘接力棒，防止崩溃丢失
 // 6. 上下文回收
 unload_earlier_layer_sections();
 }
 // 层完成 → 更新层级状态与质量
 baton.layers[Lx].status = "completed"; // not_started | in_progress | completed
 baton.layers[Lx].quality_score = avg(各批 quality_score);
 // 层完成但存在未过质量门的批 → 状态置 "completed_with_pending"，GAP 阶段必须回灌
 if (baton.layers[Lx].incomplete_batches.length > 0) {
   baton.layers[Lx].status = "completed_with_pending";
 }
}
```

---

## 三、各层 Batch 切分规则

| 层 | 切分单位 | batch_size | 每批输出文件 |
|----|---------|-----------|------------|
| L0 | 整个项目 | 1（不分批） | `_kb/L0_skeleton.json` 一个文件 |
| L1 | 模块（MODULE） | 2~3 模块一批（大型系统：1模块/批） | 每批多个 `L1_modules/MOD_xxx_xx.json` + 更新 L1_INDEX.json |
| L2 | 页面（PAGE） | 2~3 页一批（按模块组批，不跨模块） | 每批多个 `L2_regions/PAGE_xxx_xx.json` |
| L3 | 区域（REGION） | 每批 ≤6 区域（按模块组批） | 每批一个 `L3_functions/REG_xxx_{区域名}.json`（含该 REGION 的所有 FUNCTION） |
| L4 | FUNCTION 分组 | 每批 ≤4 个 FUNCTION（按同-REGION/同-ENTITY 打包，与 baton `functions_per_batch` 一致） | 每批多个 `L4_operations/FN_xxx_xx.json` |
| L5 | ENTITY / ROLE / ELEMENT / VALIDATION / AGGREGATE 5类，各类独立分批 | ENTITY 类 1个实体/批（全部实体全覆盖）；ROLE 类所有 role 一批；ELEMENT 按模块一批；VALIDATION 每 FN 组批；AGGREGATE 整批 | 每批一个对应 `L5_details/<CATEGORY>/xxx.json` |

### 关键：批间上下文隔离
- **只加载当前批要用到的源码/页面/API**，其它一概不读
- 前几批生成的 `_kb/Lx_*/*.json` 通过文件读入，不把生成内容一直堆在对话上下文
- 切批文件路径固定且有序，方便断点续跑

---

## 四、遇到"上层缺节点"的处理

Skeleton-Agent 不负责回灌实现（避免越权），但必须**即时上报**：

```
// L3 执行时，读路由发现 L1 没写该 PAGE
发现缺失项 {
 layer: "L1",
 module: "MOD_001 客户管理",
 page_id: "PAGE_005 客户导入",
 found_from: "src/router/modules/customer.js line 42 import '/customer/import'"
}
→ 立即调用 Master.incremental_backfill_trigger(missing_scope) 让 Master 调度
→ Skeleton-Agent 当前批暂停（等 Master 补完 L1→L2 对应项后继续）
→ 在 baton.rework.backfill_recent 数组追加一条记录
```

Master 回灌完成后，才会再调 Skeleton-Agent.run_batch(当前批)。

---

## 五、层完成后自动触发下一步

```
L0 跑完 & 质量门通过 → Master 自动进入 L1
L1 跑完 & 质量门通过 → Master 自动进入 L2
...
L5 跑完 & 质量门通过 → Master 自动进入 GRAPH_BUILD（调度 GraphBuilder-Agent）
```

如果其中某层某批连续3次重跑仍不合格：
```
写 _auto_decisions.md 说明 + baton.layers[Lx].quality_score = 本次最高分（低于阈值没关系）
+ 记入 baton.layers[Lx].incomplete_batches（不得静默放行）
→ 不阻塞推进 → 但该批已记入待回灌清单，GAP_ANALYSIS 阶段必须回灌补全；
   回灌后仍不合格 → 最终文档该模块末尾加警告标注（对应附录 C Top 未决项）
```

---

**版本**: 6.3.0-agent08
**最后更新**: 2026-08-11
