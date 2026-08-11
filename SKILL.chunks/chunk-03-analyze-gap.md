# S1 小项目捷径（ANALYZE + GAP）+ GAP_ANALYSIS 阶段详情（v6）

> v6 定位：完整大项目走「L0~L5 六层 + 图谱」主线，本 chunk 只服务两类场景：
> ① S1 小项目捷径（**口径与 phase-protocol §一 一致：MODULE < 3 且 PAGE < 10**）：保留 v5 的 EXPLORE/EXTRACT/ANALYZE 快速路径；**但必须同步产出 `_kb/L1_index.json`（模块清单），供 AUDIT ⑪ 覆盖完整性比对**；
> ② GAP_ANALYSIS 阶段（阶段 8）：**从图谱查询缺口**（v6 替代 v5 的 _analysis/_function_survey 输入）。
> 注意：v6 主线中 `_analysis.md`/`_function_survey.md` 不再产生，GAP 输入一律从 `_kb/graph/` 查。

---

## §ANALYZE（S1 小项目捷径·v5 兼容）

**职责**（仅 S1 快速路径用，主线由六层 L4/L5 承担）：深度理解业务逻辑，建立完整业务模型。

### 执行内容
1. **业务流程分析**：每个功能的完整流程（起点→节点→分支→异常→终点），Mermaid流程图
2. **功能关系分析**：模块调用关系、数据依赖关系、功能组合路径
3. **用户场景分析**：典型用户操作路径、常见操作组合、异常场景
4. **业务规则建模**：规则提取、触发条件、依赖关系
5. **数据关系建模**：实体关系、数据流转路径
6. **状态机分析**：每个模块的状态流转图（stateDiagram-v2）
7. **模块边界定义**：职责边界、输入/输出、上下游
8. **数据上下游分析**：生产者+消费者+流转路径+Mermaid全景图

### 产物（S1 路径）
- `_analysis.md` + `_function_survey.md`（v5 产物，仅 S1 路径产生；主线不产生）

### 检查点
- 含状态机图 + 边界定义表 + 数据流全景图
- 计数验证通过

---

## §GAP_ANALYSIS（阶段 8 · v6 从图谱查询）

**职责**：图谱构建完成后，从图谱查缺口，评估项目功能完整性，识别未闭环功能，生成项目形状报告与缺口分级。
> 完整执行规范见 `agents/07-gap-analyst-agent.md`（v6 升级版）。

### 前置产物（v6：全部从图谱读，不依赖 v5 文本产物）
- `_kb/graph/_nodes.json`（8 类节点）
- `_kb/graph/_triples.json`（20+ 谓词关系）
- `_kb/graph/_quality.json`（质量评估：cross_verified_nodes_pct / low_confidence / snake_breakdown / scale_target_snakes）
- `_kb/L0_skeleton.json`（模块/角色/依赖基线）
- 项目源码（仅局部验证时精读对应文件补证据）

### v6 缺口查询路径（替代 v5 的 _analysis/_function_survey 比对）
```
① 模块覆盖缺口：MODULE 节点数 vs L0_skeleton.modules → 缺失模块 = P0
② 页面/功能缺口：MODULE→PAGE→REGION→FUNCTION 链是否断 → 断链 = P0/P1
③ 证据缺口：confidence<0.7 且未过 AUTO_REVIEW 的节点 → P1（可补）或 P2
④ 权限缺口：ROLE×FUNCTION 覆盖 <60% 的模块 → P2
⑤ 字段缺口：ENTITY.fields 缺失 ≥40% 的模块 → P2
⑥ Snake 缺口：incomplete_snake + discovered < scale_target → P1（回灌补边）
```

### 执行内容
#### 0. 跨模块流转检查（新增）
- 用户旅程级流程：从用户视角出发的完整操作链路是否畅通（读 Snake 节点链）
- 跨模块数据同步：模块A产出的数据变更，模块B是否能感知（读 data_propagation 蛇）
- 跨模块状态一致性：跨模块流程中各环节的状态是否匹配
- 端到端错误处理：跨模块流程中一个环节失败，整体如何处理

1. **功能完整性检查**：CRUD检查 + 入口出口检查 + 工作流检查 + 前后端匹配
2. **数据流完整性检查**：生产者消费者匹配、必填数据来源、链中断点
3. **异常处理完整性检查**：失败反馈、边界条件、状态异常
4. **项目形状分析**：全景图 + 功能矩阵 + 复杂度评估 + 改进建议

### 缺失分级（P0~P3 四级，与 phase-protocol.md:20 检查点对齐）
- **P0**：功能完全缺失（模块/页面/功能缺失，或 API 与页面均缺失）
- **P1**：功能部分实现（有页面无 API / 有 API 无页面 / 断链 / Snake 不完整）
- **P2**：缺少异常处理或细节（无边界条件/失败反馈/字段或权限覆盖不足）
- **P3**：完善性建议（术语不统一/表述可优化/非阻断优化项，不影响交付）

### 产物
- `_gap_analysis.md`（缺口清单 + 完整性评分 + 项目形状报告）
- `_auto_decisions.md`（回灌决策段：哪些 P0/P1 缺口触发增量回灌）

### 检查点
- 含 P0/P1/P2/P3 四级缺失清单
- 含完整性评分（各维度有依据）
- 含项目形状报告（全景图+功能矩阵）
- 含跨模块用户旅程检查（端到端流程完整性）
