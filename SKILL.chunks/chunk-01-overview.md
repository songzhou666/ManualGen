# 状态机自动驱动说明（v6 · 全流程托管版）

> ManualGen 采用**状态机自动驱动**模式，激活后自动沿 18 阶段状态机推进，无需用户下命令、不询问用户决策。
> 变更 v5→v6：13 阶段 → 18 阶段，取消 CONFIRM 改为 AUTO_REVIEW（AI 全自主裁决，不打断）。

## 执行流程

```
激活 → 强制入口清单 → 读取 JSON 接力棒 → 确定当前状态 + 批进度 → 执行当前批任务 → 原子写 _kb/Lx_*/*.json → 强制更新 baton.layers.* → 自动进入下一批 / 下一层 / 下一阶段
```

| 步骤 | 说明 |
|------|------|
| 1 | 用户激活 ManualGen 后（说任何"写手册/分析项目"类意图），立即执行强制入口清单 |
| 2 | 读接力棒 `.agent/harness/_baton.json`（JSON 格式，不是 MD），确定状态 + 层 + 批 |
| 3 | 状态为 START → 初始化 baton.layers.* 计数器 → 标记 L0_SKELETON 开始 |
| 4 | 状态为 X ∈ {L0..L5} → 从 baton.layers[Lx].current_batch + 1 续跑下一批 |
| 5 | 每批完成 → 原子写 `_kb/Lx_*/xxx.json`（先 .tmp 再 rename）→ 更新 baton |
| 6 | 状态推进 18 阶段：见下表 |
| 7 | 循环推进，直到 DONE（达到合格 / 不合格加⚠️过） |

## 18 阶段简述（v6）

| 阶段 | 职责 |
|------|------|
| START | 初始化接力棒和目录（L0/L1/L2/L3/L4/L5/graph 目录） |
| L0_SKELETON | 搭骨架：模块/角色/依赖/数据创建链（最浅全局扫） |
| L1_MODULE | 模块分批：每模块路由/菜单/入口页/核心实体/高频场景 |
| L2_REGION | 页面分批：每页 REGION（搜索区/操作栏/表格/详情/分页）+ 可见性 |
| L3_FUNCTION | 功能分批：区域内 ELEMENT→methods→FUNCTION→入口按钮→OPERATES_ON |
| L4_OPERATION | 操作分批（**不读源码**，只看图谱节点）：FUNCTION→STEP→NEXT_STEP/分支 |
| L5_DETAIL | 细节分批（局部精读读代码）：字段/角色×功能矩阵/ELEMENT/校验/异常 |
| GRAPH_BUILD | 7 步图谱流水线：归一化→三元组→实体对齐→证据聚合→Snake→传播→质量落盘 |
| GAP_ANALYSIS | 缺口分级（P0~P3）+ AI 自主判定：哪些回灌/哪些标⚠️ |
| AUTO_REVIEW | AI 自主裁决：低置信+Snake+权限+字段缺口处理，全部写 _auto_decisions.md |
| RESOLVE | 冲突解决（6类高频冲突全自主规则，不询问用户） |
| WRITE | Module-Writer 子 Agent 按模块隔离上下文写文档（6 件套齐全） |
| REFINE | 独立子 Agent 盲检每个模块，失败项自动修复 |
| REFERENCE_CHECK | 交叉引用+术语一致性+风格统一检查（用 Graph 反向查询） |
| INTEGRATE | 整合为最终完整手册 + 4 大附录 B/C/D/E（权限矩阵/AI决策/Snake全景/证据索引） |
| AUDIT | 10 维度自评（含新增2个图谱维度：交叉验证率+Snake覆盖率） |
| TODO_RESOLVE | AI 逐条解决 TODO，P0 必须解决，无依据的加⚠️，不卡全局 |
| JUDGE | 子 Agent 盲审按模块打分，不合格只打回单模块最多3次，其余模块不动 |

## 状态查询 & 用户主动打断

在任意时刻，AI 会自动在回复开头输出：
```
📘 当前状态：L3_FUNCTION（第4层），批次：[客户管理_客户列表搜索区, 客户管理_客户列表操作栏]，下一步：识别区域内的 ELEMENT 按钮 → methods 解析 → FUNCTION 节点沉淀
```

用户主动说「进度」「暂停」「看一下」时：
1. AI 输出进度仪表盘 + 最近 20 条 _auto_decisions.md 条目
2. 不要求用户确认：**用户回「继续」或下一消息不说别的 → 自动按原阶段接着跑**
3. 用户指出具体问题（例「订单模块的价格修改角色不对」）→ 定位对应图谱节点，标记 dirty → 从该层局部回灌改完再继续
