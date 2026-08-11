# 接力棒协议 v6 — 结构化 JSON 接力棒

> **文件位置**：`.agent/harness/_baton.json`（自动创建，目录不存在时自动建）
> **参考设计**：skill-medic 的单点写 + 断点续跑 + 批进度追踪
> **变更点**：v5 用 Markdown 表格接力棒（人类可读但机器难解析），v6 统一为 JSON（结构化工期管理）
> **v6.2 全量覆盖铁律**：默认 `meta.work_mode="full"`，各层 `*_batches_total` 在进入该层时按父层节点数推导（如 L2_total = ceil(页面总数/3)）并写入，**只增不减**；`*_batches_done < *_batches_total` 时禁止推进到下一阶段。仅当用户在对话中显式点名模块范围才可置 `work_mode="core_priority"`，此时 `batch.skipped_modules` 记录未覆盖模块，交付强制进附录 F。

---

## 一、接力棒完整结构

```json
{
  "meta": {
    "skill": "ManualGen",
    "version": "6.2.0",
    "state": "START|L0_SKELETON|L1_MODULE|L2_REGION|L3_FUNCTION|L4_OPERATION|L5_DETAIL|GRAPH_BUILD|GAP_ANALYSIS|AUTO_REVIEW|RESOLVE|WRITE|REFINE|REFERENCE_CHECK|INTEGRATE|AUDIT|TODO_RESOLVE|JUDGE|DONE|FAILED",
    "sub_state": null, // 阶段内子状态，如 "PROCESSING_BATCH_2"；各阶段主控统一读写 meta.state，不得使用其他别名
    "session_id": "manual_20260811_143000",
    "project_path": "E:/projects/my-crm-system",
    "project_name": "诊所CRM管理系统",
    "project_shape": "monolith", // monolith | microservices | frontend_only | backend_only
    "scale": "S2", // S1: <3模块 | S2: 3-8模块 | S3: 9-20模块 | S4: >20模块
    "created_at": "2026-08-11T14:30:00+08:00",
    "updated_at": "2026-08-11T14:35:00+08:00",
    "is_running": 1,
    "run_count": 1,
    "current_layer": "L3", // 当前正在推进哪一层
    "small_project_fastpath": null, // S1 超小项目快速通道标记（phase-protocol 设置）
    "project_git_head_sha": null, // 项目 git HEAD（附录E证据索引用，无 git 则 null）
    "user_preferences": {
      "document_style": "detailed", // concise | detailed | rich_media
      "role_focus": null, // 如 "只写销售人员操作"，null为全角色
      "module_priority": [], // 用户显式点名的优先模块（仍全量覆盖全部模块，仅调整顺序；空=全量）
      "depth_level": "full", // basic | standard | full
      "language": "zh-CN",
      "custom_notes": null // 用户自定义备注（原样传递）
    },
    "work_mode": "full" // full=全量覆盖(默认，覆盖100%模块) | core_priority=仅当用户显式点名模块范围时启用
  },

  "progress": {
    "START": "✅",
    "L0_SKELETON": "✅",
    "L1_MODULE": "✅",
    "L2_REGION": "✅",
    "L3_FUNCTION": "🔄",
    "L4_OPERATION": "⬜",
    "L5_DETAIL": "⬜",
    "GRAPH_BUILD": "⬜",
    "GAP_ANALYSIS": "⬜",
    "AUTO_REVIEW": "⬜",
    "RESOLVE": "⬜",
    "WRITE": "⬜",
    "REFINE": "⬜",
    "REFERENCE_CHECK": "⬜",
    "INTEGRATE": "⬜",
    "AUDIT": "⬜",
    "TODO_RESOLVE": "⬜",
    "JUDGE": "⬜",
    "DONE": "⬜",
    "GATE_G0_L0_L1": "✅", // L0闸门
    "GATE_G1_L1_L2": "✅", // L1闸门
    "GATE_G2_L2_L3": "✅", // L2闸门
    "GATE_G3_L3_L4": "⬜", // L3闸门
    "GATE_G4_L4_L5": "⬜",
    "GATE_G5_L5_GRAPH": "⬜",
    "GATE_WRITE_QUALITY": "⬜"
  },

  "layers": {
    "L0": {
      "status": "completed",
      "modules_total": 7,
      "modules_completed": 7,
      "roles_total": 5,
      "roles_completed": 5,
      "dependency_edges": 12,
      "data_chain_length": 6,
      "quality_score": 92,
      "artifacts": [".agent/harness/_kb/L0_skeleton.json", ".agent/harness/_kb/L0_skeleton_report.md"]
    },
    "L1": {
      "status": "completed",
      "modules_batches_total": 3, // 分3批处理（每批2-3个模块）
      "modules_batches_done": 3,
      "current_batch": null,
      "pages_total": 24,
      "pages_completed": 24,
      "entities_total": 18,
      "entities_completed": 17,
      "scenarios_total": 35,
      "scenarios_completed": 35,
      "quality_score": 88,
      "artifacts": [".agent/harness/_kb/L1_modules/*.json", ".agent/harness/_kb/L1_index.json"]
    },
    "L2": {
      "status": "completed",
      "pages_batches_total": 8, // 每批3页
      "pages_batches_done": 8,
      "current_batch": null,
      "regions_total": 87,
      "regions_completed": 85,
      "regions_with_visibility": 12,
      "quality_score": 83,
      "artifacts": [".agent/harness/_kb/L2_regions/*.json"]
    },
    "L3": {
      "status": "in_progress",
      "regions_batches_total": 15, // 每批6个区域
      "regions_batches_done": 9,
      "current_batch": 10,
      "current_batch_regions": ["REG_040", "REG_041", "REG_042", "REG_043", "REG_044", "REG_045"],
      "functions_total_expected": 95,
      "functions_completed": 67,
      "functions_with_evidence": 52,
      "permission_entries": 142,
      "quality_score": 76,
      "artifacts": [".agent/harness/_kb/L3_functions/*.json"]
    },
    "L4": {
      "status": "not_started",
      "functions_batches_total": null,
      "functions_batches_done": 0,
      "current_batch": null,
      "operations_total_expected": 0,
      "operations_completed": 0,
      "flowcharts_generated": 0,
      "branch_paths_covered": 0,
      "quality_score": null,
      "artifacts": [".agent/harness/_kb/L4_operations/*.json"]
    },
    "L5": {
      "status": "not_started",
      "operations_batches_total": null,
      "operations_batches_done": 0,
      "current_batch": null,
      "fields_documented": 0,
      "elements_documented": 0,
      "permission_matrix_coverage": 0,
      "error_messages_collected": 0,
      "quality_score": null,
      "artifacts": [".agent/harness/_kb/L5_details/*.json"]
    }
  },

  "graph": {
    "nodes_total": 312,
    "nodes_by_type": {
      "MODULE": 7,
      "PAGE": 24,
      "REGION": 85,
      "FUNCTION": 67,
      "ENTITY": 17,
      "ROLE": 5,
      "ELEMENT": 83,
      "STEP": 24
    },
    "triples_total": 518,
    "triples_by_predicate": {
      "HAS_PAGE": 24,
      "HAS_REGION": 85,
      "HAS_FUNCTION": 67,
      "OPERATES_ON": 58,
      "CAN_EXECUTE": 142,
      "OTHERS": 142
    },
    "evidence_total": 847,
    "evidence_cross_verified_rate": 0.62, // 62%的节点有双源验证
    "low_confidence_nodes_count": 23, // 置信度 < 0.7 的节点数
    "snakes_discovered": 3, // 已发现的Snake概念链数量
    "snakes_verified": 0,
    "entity_alignment_pending": 2, // 需要实体对齐的疑似重复节点
    "graph_completeness_score": 68,
    "graph_quality_score": 71,
    "graph_builds": 0 // 已完成的全量/增量构建次数（0=首次→FULL，>0→INCREMENTAL）
  },

  "batch": {
    "work_mode": "full", // full=全量覆盖(默认) | core_priority=仅用户显式指定模块范围时启用，禁止自行降级
    "core_module_ids": [], // core_priority 模式下用户点名的模块；全量模式下为空数组
    "secondary_modules_ids": [], // core_priority 模式下其余模块（仍全量扫到L2作背景）
    "skipped_modules": [], // 未达到L3+深度的模块清单（core_priority 模式交付时强制进「附录F」）
    "modules_per_batch": 3,
    "pages_per_batch": 3,
    "regions_per_batch": 6,
    "functions_per_batch": 4,  // L4 每批4个FUNCTION
    "operations_per_batch": 5, // L5 每批5个OPERATION/STEP
    "skipped_batches": [], // 跳过的批次（原因写在 rework）
    "appendix_batches_done": []
  },

  "counters": { // 全局ID分配与防重复（00-master 唯一维护）
    "module_id": 0,
    "page_id": 0,
    "region_id": 0,
    "function_id": 0,
    "entity_id": 0,
    "step_id": 0,
    "element_id": 0
  },

  "artifacts": {
    "kb_root": ".agent/harness/_kb/",
    "auto_decisions": ".agent/harness/_kb/_auto_decisions.md", // AUTO_REVIEW 全自主裁决记录（03-resolver 写入）
    "L0_skeleton": ".agent/harness/_kb/L0_skeleton.json",
    "L0_report": ".agent/harness/_kb/L0_skeleton_report.md",
    "L1_index": ".agent/harness/_kb/L1_index.json",
    "L1_dir": ".agent/harness/_kb/L1_modules/",
    "L2_dir": ".agent/harness/_kb/L2_regions/",
    "L3_dir": ".agent/harness/_kb/L3_functions/",
    "L4_dir": ".agent/harness/_kb/L4_operations/",
    "L5_dir": ".agent/harness/_kb/L5_details/",
    "graph_nodes": ".agent/harness/_kb/graph/_nodes.json",
    "graph_triples": ".agent/harness/_kb/graph/_triples.json",
    "graph_evidence": ".agent/harness/_kb/graph/_evidence.json",
    "graph_snakes": ".agent/harness/_kb/graph/_snakes.json",
    "graph_layer_index": ".agent/harness/_kb/graph/_layer_index.json",
    "graph_quality": ".agent/harness/_kb/graph/_quality.json",
    "gap_analysis": ".agent/harness/_gap_analysis.md",
    "resolution": ".agent/harness/_resolution.md",
    "modules_dir": "output_user_manual/_modules/",
    "refine_log": ".agent/harness/_refine_log.md",
    "reference_check": ".agent/harness/_reference_check.md",
    "integration": ".agent/harness/_integration.md",
    "todo_list": ".agent/harness/_todo_list.md",
    "todo_resolution": ".agent/harness/_todo_resolution.md",
    "audit": ".agent/harness/_audit.md",
    "judgment": ".agent/harness/_judgment.md",
    "backfill_log": ".agent/harness/_kb/_backfill_log.md",
    "final_output": null // 完成后填入 "{项目名} 用户操作手册.md" 的完整路径
  },

  "auto_review_stage": {
    "last_reviewed_at": "2026-08-11T16:20:00+08:00",
    "low_confidence_nodes_processed": [
      { "node_id": "FN_088", "name": "客户合并功能", "initial_confidence": 0.62, "decision": "ACCEPTED_BY_PROPAGATION", "final_confidence": 0.76, "reason": "邻居 2×0.9 传播支持" },
      { "node_id": "ROLE_003_PERM_FN_045", "name": "财务主管删除订单权限", "initial_confidence": 0.58, "decision": "INFERRED_WITH_WARNING", "final_confidence": 0.58, "reason": "只看到查看权限，删除权限为推断→WRITE阶段加⚠️" }
    ],
    "snakes_processed": [
      { "snake_id": "SNAKE_001", "name": "订单全生命周期链", "decision": "COMPLETED", "changes": "data_creation_chain投票补齐「扣库存」节点" }
    ],
    "still_requires_attention_ids": ["FN_103", "ROLE_007"], // 附录C列示的高风险推断项（不等待用户，仅⚠️标注交付）
    "backfill_triggered": 1,
    "backfill_summary": "回灌 L3 客户管理_批量删除 区域 1 批，补到证据"
  },

  "rework": {
    "retry_count": 0,
    "last_blocker": null, // 最近一次 FAILED 原因：{ "stage": "<阶段名>", "reason": "原因" }（FAILED 恢复时读 .stage 定位）
    "graph_retries": 0, // GRAPH_BUILD 阶段重试次数（HIGH_LOW_CONFIDENCE_RATE 触发，<2 才允许再跑）
    "global_retries": 0, // 全局 FAILED 恢复重试计数（≥3 不再自动重试，转人工提示）
    "backfill_count_total": 0,
    "backfill_recent": [
      {
        "at": "2026-08-11T13:45:00+08:00",
        "layer": "L1",
        "reason": "L3时发现L1漏了「数据字典」模块的一个页面",
        "files_modified": [".agent/harness/_kb/L1_modules/数据字典.json"],
        "dirty_nodes_marked": ["REG_099", "FN_101"]
      }
    ],
    "stage_retries": {}, // 如 { "L3_FUNCTION": 1 }
    "write_rerun_modules": [], // JUDGE 打回需重写的模块ID列表（如 ["MOD_002"]），WRITE 阶段只重写这些模块
    "manual_modules": [], // REFINE 连修3次仍FAIL → 标⚠️交付的模块ID列表（不阻塞其他模块）
    "history": []
  }
}
```

---

## 二、控制规则（全部强制）

### 1. 单点写规则
只有 00-master-controller 写接力棒。
- 所有子Agent（Skeleton/NodeWeaver/GraphBuilder/EntityAligner/模块Writer）**只读不写**
- 子Agent完成后把结果回报给主控，主控写入 `layers.*` / `graph.*` / `batch.*`
- 任何子Agent直接改 `_baton.json` → 判定违规，该子Agent产出全部作废重来

### 2. 阶段闸门（Gates）
进入下一阶段/下一层前必须验证：
```
验证顺序：
  1. progress 中当前阶段是否为 ✅
  2. 当前层 quality_score ≥ 最低阈值（L0≥80, L1≥75, L2≥70, L3≥65, L4≥65, L5≥60）
  3. 该层 artifacts 路径下文件非空（逐个打开验证，不看文件名看内容）
  4. graph 中该层节点的 evidence_cross_verified_rate ≥ 层阈值
不通过 → 回退当前层重做，不推进到下一层
```

### 3. 批进度规则
每层每批完成后，主控必须：
- 把当前批所有节点**立即落盘**到对应 `Lx_xxx/*.json` 文件
- 同步更新 `graph.nodes_total` / `triples_total` / `evidence_total` 计数
- 在 `layers.Lx.current_batch` 写入下一个待处理批次
- 把 `layers.Lx.regions_batches_done` 等计数 +1

### 4. 断点续跑
会话中断后再次激活时：
```
1. 读 _baton.json
2. 找到 progress 中第一个非 ✅ 非 🔄 的阶段
3. 校验：progress 标记 ✅ 但对应 artifacts 缺失 → 回退到该层重做，记入 rework.history
4. 含闸门的阶段（GATE_*）：如果标记 ⬜ → 强制重新跑闸门验证
5. 对 L3/L4/L5：按 layers.Lx.current_batch 从该批次继续，不重跑已完成批次
6. GRAPH_BUILD 续跑：只处理 dirty=true 的节点和新加入的节点，不重建全图
```

### 5. 打回重做进度重置（AUTO_REVIEW / JUDGE / 用户主动指出问题 触发）
增量回灌触发重做某层某模块时（例：AI 在 AUTO_REVIEW 裁定 / JUDGE 打回 / 用户说"客户管理模块的功能识别有问题，重新分析"）：
```
  1. 只把 MOD_001（客户管理）相关的 L2/L3 节点标记为 dirty=true
  2. 清空 layers.L3.current_batch，重新把 MOD_001 的 REGION 排入 L3_FUNCTION 的首批
  3. 不清空其他模块的进度！其他模块已完成的保持 ✅
  4. 在 rework.backfill_recent 记录这次局部重做
```
**禁止**：一要求修改就把整层所有文件全部删除重来（那是v5的问题，浪费token和时间）
**额外规则（全流程托管兼容）**：如果是 AI 自主触发的回灌而非用户指出的 → 做完回灌后**自动继续推进流程**，不等待用户确认。

### 6. 熔断
- 单批（batch）执行异常（找不到文件/代码结构突变/节点数暴涨暴跌）→ 自动重试1次
- 仍失败 → `rework.last_blocker = { stage: meta.state, reason: "<原因>" }`，`meta.state = FAILED`，`is_running = 1`
- 同一阶段累计重试 ≥3次 → 禁止自动重试，转人工（在回复中明确告诉用户卡在哪批、什么原因）
- WRITE 阶段子Agent产出不合格（REFINE连修3次仍FAIL）→ 记录该模块为 "待手动"，先继续其他模块不阻塞

### 7. 完成收口
JUDGE 通过后：
1. 把 `auto_review_stage`（低置信裁决）+ graph_quality + judgment.per_module_scores 等信息存入 history
2. `meta.state = DONE`，`is_running = 0`
3. `artifacts.final_output = "{项目路径}/{项目名} 用户操作手册.md"`
4. 写 `rework.history` 最后一条记录：总耗时、总batches数、总backfill次数、最终质量评分、AI 自主裁决条数、HUMAN_REVIEW_REQUIRED 条数

---

## 三、状态异常处理

### state = FAILED
下次调用 00-master 先展示：
```
上次会话异常终止：
  卡住阶段：L3_FUNCTION，批次10
  原因：处理 REG_044 时，源码文件 src/views/xxx.vue 读取为空（可能被移动/删除）
  已重试次数：2次
请选择：
  [1] 跳过该批次，先处理其他 → 继续L3后续批次
  [2] 手动指定文件路径后重试
  [3] 重置整个L3层从头来（不推荐，浪费已有成果）
```

### 进度 ✅ 但产物缺失
- 回退该阶段/该层到 🔄（重做）
- 记入 `rework.history`，记录是哪一层哪个产物丢了
- **不影响其他层的已完成产物**

### 接力棒 JSON 损坏 / 解析失败
1. 先备份：`.agent/harness/_baton.corrupt_YYYYMMDD_HHMMSS.json`
2. 尝试从最近的完整 artifacts 反推进度：
   - L0 文件存在 → L0 标记 ✅
   - L1_index.json 存在且含N个模块 → L1 标记对应进度
   - 依此类推
3. 如果反推不出来 → 按初始化结构重建（状态 START），告知用户
4. **永远不要静默删除接力棒，一定要留备份**

---

**版本**: 6.2.0-json
**最后更新**: 2026-08-11
