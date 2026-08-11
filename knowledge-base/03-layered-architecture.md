# 六层递进式骨架生长架构（Layered Skeleton Growth）

> 核心思想：不一口气读完整个项目，而是像树木生长一样——先生长骨架（L0），再长出枝干（L1），再分叉出小枝（L2），再长出叶子（L3），再开花（L4），最后结果（L5）。
> 每一层完成后立即落盘，上层只读下层的结构化产物，不回头重读原始代码。

---

## 六层模型总览

```
L5 细节层 (Detail) ← 按钮级交互、字段级校验、权限矩阵、异常提示
 ^ 沉淀节点到图谱
L4 操作层 (Operation) ← 点击什么→填写什么→看到什么，完整用户操作步骤
 ^ 编织操作节点
L3 功能层 (Function) ← CRUD、审核、导入导出、配置等功能点清单
 ^ 划分功能区域
L2 区域层 (Region) ← 页面内的Tab/卡片/侧边栏/表单区域划分
 ^ 识别界面结构
L1 模块层 (Module) ← 菜单级模块（客户管理、订单管理、系统设置...）
 ^ 搭骨架
L0 骨架层 (Skeleton) ← 项目形状：有多少模块、模块关系、角色矩阵、依赖链
```

**每层完成标志**：该层产物已落盘 + 图谱中该层级节点 100% 有来源证据 + 计数验证通过

---

## L0 骨架层（Skeleton）—— 项目全貌 & 依赖关系

### 提取目标
先画一张"地图"，不关心街道上有几栋楼，只关心有几条主干道、它们怎么连的。

### 提取内容
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 模块清单 | 从菜单/路由/目录名识别模块 | `MODULE` |
| 模块依赖图 | 模块A的操作需要模块B先有数据 | `(MODULE)-[:DEPENDS_ON]->(MODULE)` |
| 角色矩阵 | 系统有哪些角色、角色大概管什么 | `ROLE` + `(ROLE)-[:CAN_ACCESS]->(MODULE)` |
| 项目形状 | 单体/微服务、前后端是否分离、技术栈 | ProjectMeta（元数据） |
| 数据创建链 | 哪些实体必须先创建，其他才能工作 | `(ENTITY)-[:REQUIRES]->(ENTITY)` |

### 完成标准
- 模块清单已列出（逐个编号，不遗漏）
- 模块依赖Mermaid图已生成（不是文字描述）
- 角色清单已列出（逐个）
- 数据创建依赖链已识别（如：字典→部门→用户→订单）
- 图谱中所有L0节点都有`source_file`证据溯源

### 产物
```
.agent/harness/_kb/
├── L0_skeleton.json # L0结构化数据（给后续层读，不给人看）
└── L0_skeleton_report.md # L0人类可读报告（供自检与用户追问进度时展示）
```

---

## L1 模块层（Module）—— 每个模块的结构概览

### 提取方式
**按模块分批处理**，每批 2-3 个模块。处理完一批立即落盘，处理下一批时只读本批源码 + 历史L0/L1产物。

### 每个模块提取
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 页面清单 | 该模块有哪些页面（路由/菜单） | `PAGE` + `(MODULE)-[:HAS_PAGE]->(PAGE)` |
| 页面入口 | 每个页面从哪里进入（菜单路径/按钮入口） | `(PAGE)-[:ENTRY_VIA]->(ELEMENT:menu)` |
| 核心实体 | 该模块围绕哪些数据转 | `ENTITY` + `(MODULE)-[:MANAGES]->(ENTITY)` |
| 高频场景 | 3-5个最常用的操作场景（自然语言描述） | `SCENARIO` + `(MODULE)-[:HAS_SCENARIO]->(SCENARIO)` |

### 完成标准（每个模块）
- 页面清单已列出（逐个编号）
- 每个页面有入口说明
- 核心实体已识别（含字段数估算）
- 高频场景已列出（≥3个）
- 图谱中所有L1节点都有证据溯源

### 产物
```
.agent/harness/_kb/
├── L1_modules/
│ ├── MOD_001_客户管理.json # 每个模块独立文件，可独立重读（统一 MOD_xxx_名称 命名）
│ ├── MOD_002_订单管理.json
│ └── ...
├── L1_index.json # 模块进度索引（哪些模块完成了L1）
└── L1_modules_report.md # L1汇总报告（供自检与进度展示）
```

---

## L2 区域层（Region）—— 页面内的结构分区

### 提取方式
**按页面分批处理**，每页独立读源码。只读本页的前端组件/后端Controller，不读其他。

### 每个页面提取
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 区域划分 | 页面分几块：搜索区/列表区/详情区/Tab1/Tab2... | `REGION` + `(PAGE)-[:HAS_REGION]->(REGION)` |
| 区域类型 | search_bar / data_table / detail_form / tab_panel / sidebar | REGION.type |
| 区域间关系 | 点击搜索区→刷新列表区 | `(REGION)-[:TRIGGERS]->(REGION)` |
| 可见性条件 | 某些区域只有特定角色/状态下才显示 | `(ROLE)-[:CAN_SEE]->(REGION)` |

### 完成标准（每个页面）
- 区域划分完整（无遗漏大区块）
- 区域类型标注正确
- 区域间触发关系已识别
- 可见性条件已记录（如有）

### 产物
```
.agent/harness/_kb/
└── L2_regions/
 ├── 客户管理_客户列表.json # 每页独立文件
 ├── 客户管理_客户详情.json
 └── ...
```

---

## L3 功能层（Function）—— 区域内的功能点

### 提取方式
**按区域逐个深入**，只读该区域相关的代码片段（组件的methods、hook、按钮handler）。

### 每个区域提取
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 功能点清单 | 该区域能做什么：新增/编辑/删除/导出/筛选/批量操作... | `FUNCTION` + `(REGION)-[:HAS_FUNCTION]->(FUNCTION)` |
| 功能入口 | 通过哪个按钮/链接/快捷键触发 | `ELEMENT:button` + `(FUNCTION)-[:TRIGGERED_BY]->(ELEMENT)` |
| 功能类型 | CRUD / workflow / import_export / config / query | FUNCTION.type |
| 关联实体 | 该功能操作哪些实体 | `(FUNCTION)-[:OPERATES_ON]->(ENTITY)` |
| 前置条件 | 什么条件下才能用这个功能 | `(FUNCTION)-[:REQUIRES]->(CONDITION)` |
| 权限要求 | 哪些角色能操作 | `(ROLE)-[:CAN_EXECUTE]->(FUNCTION)` |

### 完成标准（每个区域）
- 功能点清单完整（逐个编号）
- 每个功能有入口按钮说明
- 功能类型标注正确
- 前置条件和权限已记录

### 产物
```
.agent/harness/_kb/
└── L3_functions/
 ├── 客户管理_客户列表_搜索区.json
 ├── 客户管理_客户列表_操作栏.json
 └── ...
```

---

## L4 操作层（Operation）—— 用户视角的操作步骤

### 提取方式
**按功能逐个深入**，跨L3节点关联。此时不再读源码，而是从L0-L3图谱中查询关联信息，编织用户操作路径。

### 每个功能编织
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 操作步骤序列 | 步骤1→步骤2→步骤3...（用户视角：点什么/填什么） | `OPERATION_STEP` + `(FUNCTION)-[:HAS_STEPS]->(STEP_CHAIN)` |
| 分支判断 | 哪些步骤有条件分支（如：是否必填校验） | `(STEP)-[:BRANCHES_TO]->(STEP:condition)` |
| 异常路径 | 操作失败时怎么走 | `(STEP)-[:ON_ERROR]->(ERROR_HANDLER)` |
| 预期反馈 | 每步操作后系统应该给什么反馈 | `(STEP)-[:EXPECTS_FEEDBACK]->(FEEDBACK)` |
| 操作流程图 | Mermaid flowchart（自动生成，不是手绘） | 存储在 STEP_CHAIN.diagram |

### 编织逻辑（不读源码，从图谱查询）
```
输入：功能节点 FUNCTION
 1. 查询 FUNCTION 的触发入口 (ELEMENT:button) → 得到第一个步骤「点击xx按钮」
 2. 查询 FUNCTION.OPERATES_ON 的 ENTITY.fields → 得到「需要填写的字段清单」
 3. 查询 FUNCTION.REQUIRES 的前置条件 → 得到步骤0「确保已满足xxx」
 4. 查询同 PAGE 内其他 FUNCTION 的调用链 → 得到后续步骤
 5. 查询 ROLE 权限 → 得到权限说明
输出：完整的操作步骤链 + Mermaid 流程图
```

### 产物
```
.agent/harness/_kb/
└── L4_operations/
 ├── 客户管理_新增客户.json
 ├── 客户管理_编辑客户.json
 └── ...
```

---

## L5 细节层（Detail）—— 按钮级/字段级极致细节

### 提取方式
**按操作步骤逐个细化**，需要时回到源码精确定位（但只看具体的字段定义/校验函数/API返回，不看全局）。

### 每个操作步骤补充
| 子项 | 说明 | 图谱节点类型 |
|------|------|-------------|
| 按钮级细节 | 按钮文案、图标、禁用条件、Tooltip、快捷键 | ELEMENT（属性细化） |
| 字段级细节 | 字段名/标签/类型/长度/必填/默认值/校验规则/示例值 | FIELD_DETAIL |
| 权限矩阵 | 某功能下：角色A能看但不能改、角色B能改但不能删 | `(ROLE)-[:PERMISSION {level:r|rw|rwd}]->(FUNCTION)` |
| 异常提示语 | 每种异常场景下的具体提示文案 | ERROR_HANDLER.message |
| 风险提示 | 哪些操作不可恢复、需要二次确认 | FUNCTION.risk_level + WARNING |

### 完成标准
- 每个可输入字段都有属性表
- 每个按钮的状态（正常/禁用/隐藏）都有条件说明
- 权限矩阵覆盖所有角色×功能
- 异常提示语与代码中实际提示一致

### 产物
```
.agent/harness/_kb/
└── L5_details/
 ├── 客户管理_客户表单_字段详情.json
 ├── 客户管理_权限矩阵.json
 └── ...
```

---

## 层级推进闸门（Layer Gates）

每层完成后必须通过闸门才能进入下一层：

| 闸门 | 检查内容 | 不通过怎么办 |
|------|---------|-------------|
| G0: L0→L1 | 模块清单完整、依赖图无孤立节点 | 补充L0探索 |
| G1: L1→L2 | **全部模块**的L1完成（批循环覆盖100%，`batches_done==batches_total`） | 补齐缺失模块的批次，禁止带缺放行 |
| G2: L2→L3 | **全部页面**的区域划分完整 | 补齐缺失页面 |
| G3: L3→L4 | **全部区域 100% 覆盖**（批循环 `batches_done==batches_total`）+ 已识别 FUNCTION ≥90% 带 trigger_element | 补充缺失功能识别 |
| G4: L4→L5 | **全部功能**≥5步操作，含流程图 | 补充操作步骤 |
| G5: L5→WRITE | **全部实体**字段覆盖率≥80%，权限矩阵完成度≥70%（全 ROLE×FUNCTION） | 补充细节 |

**默认模式 = 全量覆盖**：L0→L5 必须覆盖项目 100% 的模块/页面/区域/功能/字段，缺一不可，任何闸门不得以"核心模块已完成"为由放行。
**核心优先模式（仅用户显式点名模块范围时启用）**：指定模块走完L0→L5；其余模块仍全量扫到 L2 作背景，并列入交付物「附录 F：未覆盖模块/功能清单」强制披露。

---

## 增量回灌机制（Incremental Backfill）

> 场景：写到L4时发现L1漏了一个页面，或者L5时发现L3少识别了一个功能。不要重跑所有层。

**回灌规则**：
1. 发现缺失 → 只补充缺失节点所在层的对应文件（如L1少了页面→追加写`L1_modules/xx.json`）
2. 标记下游需要刷新的节点（在图谱中标记`dirty=true`）
3. 后续阶段读取时，遇到`dirty`节点自动触发该节点的增量重算
4. 回灌记录写入`.agent/harness/_kb/_backfill_log.md`，可追溯谁在什么时候补了什么

---

## 证据溯源强制规则

**每个图谱节点必须有来源证据**，无证据的节点视为"猜测"，在AUTO_REVIEW阶段自动裁决（补证据/推断/附录C待复核）并标记：

```json
{
 "node_id": "FN_customer_create",
 "type": "FUNCTION",
 "name": "新增客户",
 "evidence": [
 {
 "file": "src/pages/customer/CustomerList.vue",
 "line_range": [120, 135],
 "snippet": "<button @click=\"handleCreate\">新增客户</button>",
 "extracted_at_layer": "L3",
 "confidence": 0.95
 },
 {
 "file": "src/api/customer.js",
 "line_range": [1, 15],
 "snippet": "export function createCustomer(data) { return request.post('/customers', data) }",
 "extracted_at_layer": "L3",
 "confidence": 0.98
 }
 ]
}
```

**置信度分级**：
- ≥0.95：双源验证（前端+后端/页面+API都有证据）
- 0.7~0.95：单源有明确代码证据
- 0.4~0.7：从上下文推断（AUTO_REVIEW阶段裁决：补证据/推断/附录C待复核，裁决写入 `_auto_decisions.md`）
- <0.4：纯猜测（必须标记待复核，否则WRITE阶段禁止使用）

---

**版本**: 6.2.0-layered
**最后更新**: 2026-08-11
