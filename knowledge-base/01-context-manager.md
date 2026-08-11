# Context Manager v6 — 六层分块 + 按需加载

> v6 的核心变化：
> - 新增**按阶段卸载 Chunk**机制（六层走完前一层就卸载它的 §节）
> - **Graph 优先，不直接堆 _extraction**：WRITE/RESOLVE/AUDIT 时读 graph JSON，不把六批产物塞上下文
> - **子Agent上下文隔离**：Module-Writer / Refiner / Judge 子 Agent 启动时只取自己模块的节点

---

## 0. 核心预算 & 加载/卸载顺序

### 0.1 上下文预算（参考值，按实际 LLM max_context 调整）
- 总预算：~128K tokens
- 固定开销（SKILL 框架 + 接力棒）：~25K
- 可变：
  - 阶段专用 Chunk（Chunk 07§Lx / 08 / 09 等）：~8-15K
  - 当前批源码 / 路由 / SQL / 模块节点：~30-60K
  - 其他（系统提示 + 历史对话残留）：~10K

### 0.2 强制卸载顺序（先卸的先不相关）
```
SKELETON 六层内部：
  L0 → 进L1后卸载 Chunk07§L0
  L1 → 进L2后卸载 Chunk07§L1 + L1_modules/*（但保留 L1_INDEX.json）
  L2 → 进L3后卸载 Chunk07§L2 + L2_regions/* 中已处理完的前几批
  L3 → 进L4后卸载 Chunk07§L3 + L3_functions/* 中已处理完的模块
  L4 → 进L5后卸载 Chunk07§L4
  L5 → 进GRAPH后卸载 全部 Chunk07（§L5 也卸）+ 清空所有 Lx 路径的记忆
GRAPH 之后：
  GRAPH Step7 完成 → 卸载 Chunk08（graph协议）
  WRITE 阶段结束 → 卸载 Chunk04§WRITE + flowchart-spec
  REFINE → 只加载 Chunk04§REFINE（§WRITE 可以卸）
  INTEGRATE 结束 → 卸载 Chunk04
  AUDIT → 只加载 Chunk05§AUDIT
  JUDGE → 只加载 Chunk05§JUDGE
  → 到 DONE 时只剩 Chunk-01 + 06 + baton（合计 ≤5K）
```

---

## 1. 六层骨架生长阶段的"最小上下文加载"

| 层 | 必须加载的东西 | **严禁加载**（避免撑爆） |
|----|--------------|------------------------|
| L0 | project config + package.json / pom.xml / routes index + Chunk07§L0 | 任何业务代码文件 |
| L1 每批（2~3模块） | `_kb/L0_skeleton.json` + 该模块的 `router/modules/xxx.js`（或路由树分支）+ Chunk07§L1 | 其它模块路由、页面 template、后端代码 |
| L2 每批（2~3页面·组自同一模块） | `L1_INDEX.json` + 对应 PAGE 的 Vue/React 文件 + 组件（页面内引用的子组件）+ Chunk07§L2 | 同模块的其他 PAGE 文件、后端 service |
| L3 每批（≤6 REGION·按模块组批） | 该模块的所有 PAGE 区域索引（`L2_regions/PAGE_*.json` 只读 metadata，不读 evidences 明细）+ Chunk07§L3 + 对应 pages 的 template/methods（只读 FN 相关的 methods） | 其他模块的任何东西 |
| L4 每批（≤4 FUNCTION） | `L3_functions/REG_xxx.json` 里的 FN 列表（metadata）+ 对应 template methods 行 + 对应 api/*.js + Chunk07§L4 | **不带源码正文**（只带 file_path + line_numbers，需要看时再局部读） |
| L5 各类分批 | 对应 ENTITY/FN 的 ID 列表 + 关联的 schema/route 路径 + Chunk07§L5 | 其他类别 L5 的内容（例如处理字段时不读 ELEMENT） |

### 1.1 切批文件路径规范（避免"同文件反复读"）
Skeleton-Agent 每批的输入是**路径列表**，不是全文：
```
L3 批次 MOD_002：
  source_assets: [
    "src/views/order/List.vue",
    "src/views/order/Detail.vue",
    "src/api/order.js",
    ...（只列路径，不读内容）
  ]
```
→ NodeWeaver 内部"用哪读哪"，读完的字符串立即释放。

---

## 2. 子 Agent 上下文隔离

### 2.1 Module-Writer-Agent 启动上下文（每启动一个只给这些）
```
（启动头）+ 
graph/_nodes.json: {
  filter: node.module_id == MOD_xxx || 
          (node.type in {ENTITY, ROLE} && node 通过三元组能到达 MOD_xxx 的 FUNCTION)
}（≈200-500 nodes 不是全图4000 nodes）
graph/_triples.json: { filter: 上述 node_ids 相关 }
graph/_snakes.json: { filter: snake.node_ids ∩ MOD_xxx ≠ ∅ }
相关附录模板片段（只 flowchart-spec 一段）
```
→ **其他模块的 nodes/triples/snakes 绝对不出现在子Agent上下文里**。避免 MOD_订单管理 写的时候还塞一堆 MOD_库存管理 的节点在上下文里干扰。

### 2.2 Refiner/Judge 子Agent 盲审隔离
- 启动头 + **只传对应模块 MD 内容**，不传 graph、不传 node、不传 evidences
- 原因：盲审要模拟"最终用户读这一章"，不给 AI 背后的结构化数据，防止它"偷看到节点名就给高分"。

---

## 3. 数据文件管理：_kb/ 与 graph/ 的"先写后删引用"

```
_kb/ 是"生产车间"（六层骨架时写入，GRAPH后变只读）
  L0_skeleton.json           ← Master：永远保留
  L1_modules/*.json          ← Skeleton-Agent 批写
  L1_INDEX.json              ← 层完成后汇总
  L2_regions/*.json          ← 同上
  L3_functions/*.json        ← 同上
  L4_operations/*.json       ← 同上
  L5_details/ENTITY/*.json   ← 同上
  L5_details/ROLE/*.json     ← 同上
  L5_details/ELEMENT/*.json  ← 同上
  L5_details/VALIDATION/*.json ←同上
  L5_details/AGGREGATE/permissions.json ← 同上

graph/ 是"成品仓库"（GRAPH 阶段首次构建，后续增量构建）
  _nodes.json / _triples.json / _evidence.json / _snakes.json / _layer_index.json / _quality.json

上下文引用规则：
  - GRAPH 阶段及之前（L0~GRAPH）：AI 需要 Lx 明细 → 从 _kb/Lx_*/ 按需局部读
  - GRAPH 阶段之后（GAP→DONE）：**AI 一律从 graph/ 读**，不再引用 _kb/Lx_*/*.json 的内容
    （除了增量回灌或 JUDGE 打回模块级重写时需回到 _kb 补对应 dirty 节点）
```

---

## 4. 旧 Context-Manager v5 内容保留（仍然有效·和v6不冲突）

以下原则在 v6 **继续生效**，优先级不变：
1. **内容完整性永远优先于上下文优化**（不能因为 token 不够就简化模块文档）
2. **拆分是为了结构，不是为了截断**（单模块 4KB 最低门槛）
3. **大型项目分模块逐步生成**（Module-Writer 子Agent隔离 = 拆分落地）
4. **代码输入按文件/模块读，不必一次性整库读**（Skeleton-Agent 每批最小上下文 = 落地）

---

## 5. 紧急方案：上下文预算不够

若某批处理过程中检测到 LLM "context window exceeded" 或明显推理速度变慢：

```
策略 A（优先）：切更细的批
  - L4 每批 4 FUNCTION → 改为每批 2 个
  - L3 每批 6 REGION → 改为每批 3 个
  - L5 ENTITY 类 1 实体/批 → 改为按字段组批（先基础字段再扩展字段）

策略 B（A 不行再用）：降精度读取
  - 读取源码时只保留方法签名 + 首 8 行代码，不是完整方法
  - evidence.snippet 只保留 100 字符，不是 200
  - 记录 precision_degraded=true + 附在 _auto_decisions.md，WRITE 阶段加 ⚠️

策略 C（B 还不行）：启用多轮对话续跑
  - 当前批不 finish（不写 baton.layers[Lx].quality_score）
  - 输出临时结果，等激活续跑时再 finish
  - **注意**：这是用户激活模式下的终极方案，全托管模式尽量不用
```

---

**版本**: 6.2.0-kb01-context-manager
**最后更新**: 2026-08-11
