# Chunk 09: 增量回灌 & 局部重做（Incremental Backfill）

> **加载时机**：GAP_ANALYSIS 发现严重P0缺口、AUTO_REVIEW 发现某模块整体低置信、JUDGE 打回某模块、或上层（L3/L4/L5）执行过程中意外发现下层（L0/L1/L2）缺节点时。
> **执行Agent**：主控（调度Skeleton/NodeWeaver局部批次）。
> **核心原则**：**永远不全量重来**。哪里缺补哪里，只标记dirty节点，不影响不相关模块的已完成产物。

---

## 一、增量回灌触发场景 & 处理模式

| 触发点 | 检测条件 | 回灌范围 | 处理模式 |
|-------|---------|---------|---------|
| **L3处理途中发现L1缺了一个PAGE**（最常见） | NodeWeaver读某模块路由时发现一个不在L1_index的页面 | 只补对应模块：L1追加该PAGE → L2跑这一页 → 加入当前L3批次末尾 | 局部串行补 L1→L2→L3 |
| **L4发现某FUNCTION缺ENTITY字段** | 从图谱查 OPERATES_ON 时 ENTITY.fields 为空或<3个字段 | 只补该ENTITY：跳回 L5_DETAIL 对应实体的字段详情，不影响其他FUNCTION | 单点补 L5 |
| **GAP_ANALYSIS 发现某模块全是低置信（证据<0.5的节点>30%）** | GAP报告中某模块 P0=FUNCTION缺失过多 | 回到 L2 该模块的所有PAGE → 补读 template 的 methods 片段 → 补 L3 → 再向下传播 | 模块级补 L2→L3→L4 |
| **GAP_ANALYSIS 发现 Snake 数量=0** | `snakes_discovered==0` | 运行 Step 5 Snake 发现的加强版：放宽 TF-IDF 相似度阈值（0.65→0.55），把 FUNCTION.description 里关键词重合的跨模块功能强行组蛇 | GRAPH Step 5 加强重跑 |
| **AUDIT/JUDGE 打回某模块文档** | REFINE/JUDGE 说「客户管理模块写得太概括，缺少字段表」 | 不跑 L0~L3，直接补 L5_DETAIL 对应模块的字段 → 重建该模块文档的 WRITE子Agent（只重写 _modules/客户管理.md，其他模块文件不动） | 补 L5 → 模块级重写 |
| **用户下次激活，发现有新文件/改了代码** | `_kb/Lx_*/*.json` vs 源码文件的 last_modified 对比差异>阈值 | 按差异文件定位到对应模块/页面，标记 dirty，从该层开始按批补跑 | 差异驱动增量补跑 |

### 禁止触发
- 「我感觉整体都写得不好，从头来」→ **永远不做全量重来**（即使判 FAILED，下次激活也从 FAILED 记录的 last_blocker 那批开始局部重做）
- 某节点缺1个字段就补整个模块的 L5 → 只补那个FIELD所在的ENTITY的json文件追加字段

---

## 二、回灌执行算法（Incremental Backfill Algorithm v6）

```
输入：
 missing_scope: {
 layer: "L1",
 module_ids: ["MOD_001"], // 只涉及客户管理
 page_ids: ["PAGE_005"], // 只缺客户导入页
 reason: "L3时发现路由里有/import页，但L1没写"
 }
 current_baton: 当前接力棒

Step 1: 局部状态重置
 1.1 将对应层的该模块/页面节点标记 dirty=true
 - L1_INDEX.json 中 MOD_001.pages_completed -= 1
 - baton.layers.L1.pages_completed -= 1
 1.2 将下游依赖该 PAGE 的所有节点也标记 dirty=true（影响传播）
 - graph 中所有路径 PAGE_005 -HAS_REGION→ REGION -HAS_FUNCTION→ FUNCTION
 的 REGION/FUNCTION/STEP 标记 dirty=true
 1.3 估算需要重跑的 Lx 层集合：layers_to_backfill = [L1, L2, L3, L4, L5]
 （PAGE 是 L1 的东西，但下游都要重跑对应节点）

Step 2: 将补跑批次插入当前执行计划
 2.1 若当前正在跑 layers_to_backfill[0] 层之后的层：
 → 暂停当前层后续批次（写回 baton.current_batch 保存进度）
 → 在 layers_to_backfill[0] 层的 current_batch 末尾插入补跑批次
 → 标记 meta.sub_state = "BACKFILLING"，便于后续区分正常推进
 2.2 若还没跑到之后的层 → 简单追加到对应层最后一批即可

Step 3: 执行补跑批次（和正常流程完全一致）
 3.1 按批读取缺失范围对应的源码（只读本模块/本页的代码，其他模块一概不碰）
 3.2 追加写入 L1_modules/MOD_001_客户管理.json 的 pages[] 尾部
 （覆盖写整个文件，但旧 pages[] 内容原样保留，只追加新的）
 3.3 新建 L2_regions/PAGE_005_客户导入.json
 3.4 ... 依次 L2/L3/L4/L5，和正常流程一样
 3.5 每批完更新 baton.layers.*.current_batch / quality_score / <X_batches_done>（schema 实际字段，按层对应累加）
 3.6 标记 Graph 中对应 dirty=true 节点 → false（刚补完就是 fresh）

Step 4: 下游修复（传播到图谱）
 4.1 如果已经过了 GRAPH 阶段 → 追加运行一次 GRAPH_BUILD 的增量模式（只处理 dirty=true）
 4.2 如果已经到 WRITE 阶段但还没写对应模块文档 → 正常，写的时候会用新的图谱节点
 4.3 如果 WRITE 阶段已写过对应模块文档 → 安排 JUDGE 打回"重新生成客户管理.md"
 （注意：是单模块重写，不是全量重写）

Step 5: 记录回灌日志
 追加写 `.agent/harness/_kb/_backfill_log.md`：
 ```
 ## 回灌记录 #23 2026-08-11T17:20:00+08:00
 - 触发点：L3_FUNCTION 处理 REG_044 时
 - 原因：发现 /customer/import 路由存在但 L1 未登记 PAGE_005
 - 回灌范围：L1(新增PAGE_005) → L2(3个REGION) → L3(2个FUNCTION) → L4(2组STEP) → L5(8个FIELD)
 - 受影响节点数：15 个 dirty，传播标记 23 个下游
 - 模块级重做：无
 - 图谱重建：仅增量（耗时约2s，未重建全图）
 - 最终补写文档：_modules/客户管理.md 追加「3.8 客户批量导入」一节
 ```

Step 6: 恢复（取消暂停）
 把 meta.sub_state 从 BACKFILLING 恢复为 null，
 按 Step 2.1 保存的进度继续跑原来的层/批。
```

---

## 三、局部重做（GAP/AUDIT/JUDGE 打回处理）

和增量回灌类似，但触发是"AI自我判断某模块质量不达标"。

### JUDGE 打回决策树（AI自主判·不询问用户）
```
JUDGE 盲审返回:
{
 overall_score: 62,
 per_module_scores: {
 "MOD_001 客户管理": 85,
 "MOD_002 订单管理": 48, // ← 低分
 "MOD_003 库存管理": 76
 },
 per_module_fail_reasons: {
 "MOD_002 订单管理": [
 "缺少字段说明表（FAIL_字段说明: 0/15项）",
 "跨模块引用「库存扣减」位置不正确（实际在订单审核通过后而非订单创建时）"
 ]
 }
}

AI 自主处理：
 1. MOD_001 / MOD_003 PASS → 写入 REFINE_PASS，不动
 2. MOD_002 FAIL
 a. 原因1「缺字段」→ 回灌 L5: ENT_订单 字段详情.json
 b. 原因2「位置不正确」→ 定位 Snake: 订单全生命周期链的 link(1→2) 顺序错
 → 直接修改 graph/_snakes.json 的 node_ids 顺序
 → 写入 _auto_decisions.md: "[Snake_001] 节点1-2顺序由创建就扣库存改为审核后扣库存"
 c. 只重跑 WRITE 阶段的 MOD_002 订单管理.md + 附录跨模块操作指南.md 的对应蛇
 → 不重写 MOD_001 / MOD_003！
 3. 把 REFINE/JUDGE 重跑次数 +1 → 记入 baton.rework.stage_retries["WRITE:MOD_002"] = 1
 4. 单模块重写后再跑一次盲审（只审 MOD_002，不审其他）
 5. ≥3次仍不合格 → 最终文档该处写提示：「本章质量未过盲审，请人工复核」
 → 不阻塞全局 DONE
```

### 关键：绝不重跑通过的模块
v5 的老问题：一个模块不合格就全文档重写，浪费90%时间。v6 严格按模块隔离，不合格的单独重跑。

---

## 四、GAP_ANALYSIS → AUTO_REVIEW 链路的自主回灌决策

GAP 报告出来后不直接进 AUTO_REVIEW，AI 先做一次回灌必要性判定：

| GAP 情况 | 阈值 | 决策 |
|---------|------|------|
| 模块 P0 功能缺失（应该有CRUD但缺U/D） | 模块 P0 ≥ 2个 | 触发「模块级回灌 L2→L3」对应模块（**全量模式所有模块一视同仁，不得因非核心而跳过**；core_priority 模式核心模块优先） |
| 模块 P1 缺口（功能部分实现 / 区域识别不全 / 操作缺失） | 存在 `incomplete_batches` 或 P1 ≥ 3 个 | 触发「模块级回灌 L2→L4」对应模块；回灌后仍不合格 → 该模块最终加警告标注 + 附录 C Top 清单 |
| 非核心模块 P0 较多 | 非核心 P0 ≥ 5 个 & 核心无P0 | 全量模式下必须回灌对应模块；仅 core_priority 模式（用户未点名该模块）才可标注「扩展功能」，且必须列入附录F未覆盖清单，禁止静默跳过 |
| 权限矩阵完整度 < 50% | coverage_percent < 50 | 回灌 L5 权限矩阵.json，从 role_check 注解 + 路由 meta.roles 聚合扫一遍 |
| Snake 数量 0 | snakes_discovered==0 | 回灌 GRAPH Step5 Snake 发现加强版（阈值0.65→0.55） |
| 字段覆盖 < 50%（全部 ENTITY，默认全量） | documented/fields_total < 50 | 回灌 L5 对应ENTITY的字段详情 |
| 以上都不严重 | completeness_score ≥ 70 **且无 `incomplete_batches`** | **不回灌**，直接推进 AUTO_REVIEW；若存在 `incomplete_batches` 则必须回灌，不得直接推进 |

### 决策结果写入
`_gap_analysis.md` 末尾追加：
```markdown
## 10. AI 自主回灌决策（无用户参与）
- 触发1次回灌：订单管理模块 缺 L2「订单详情页操作栏」区域 → L2→L3 补跑
- 触发1次回灌：权限矩阵覆盖43% → L5 权限聚合器重扫一遍注解
- 跳过（仅核心优先模式允许）：数据字典模块 P0=缺2个，用户本次未点名该模块，加警告标注并列入附录F未覆盖清单；全量模式下该模块必须回灌
预计新增节点 ~35 个，预计耗时 ~3 分钟
```

---

## 五、防止回灌死循环（熔断）

```
同一 LAYER+MODULE 组合的回灌次数 ≥ 3
 → 视为"这个模块就是缺代码/确实没实现"
 → 不再继续回灌，最终文档对应位置写
 → 写入 _auto_decisions.md：「MODULE_007 系统设置的「角色权限分配」页面，3次增量回灌仍未找到可点击按钮，判定该功能在当前版本未实现，已跳过并加提示」
```

---

**版本**: 6.3.0-chunk09
**最后更新**: 2026-08-11
