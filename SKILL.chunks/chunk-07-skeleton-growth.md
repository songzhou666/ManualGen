# Chunk 07: 六层骨架生长执行细则（Skeleton Growth）

> **加载时机**：L0~L5每层开始时，只加载对应 §Lx 节，不加载整章。
> **执行Agent**：Skeleton-Agent (L0/L1)、NodeWeaver-Agent (L2~L5)

---

## §L0 骨架层：项目全貌探索

### 分批策略
不分批（最浅层），一次性完成。

### 代码读取范围（最浅，不读具体业务代码）
```
只读：
 README / package.json / pom.xml （项目介绍）
 路由配置文件总览：router/index.js 目录名 / 菜单配置文件结构
 数据库 DDL / schema.sql 文件目录名（不读字段细节）
 角色权限配置文件顶层结构（角色名列表，不读具体权限）
不读：
 具体 .vue/.jsx 组件
 具体 Controller/Service 实现
 具体字段定义
```

### 必须提取并落盘到 `L0_skeleton.json`
| 字段 | 类型 | 说明 |
|------|------|------|
| modules[].id / name / category | string | MOD_xxx + 模块显示名 + core/config/report/system |
| modules[].menu_path | string | 菜单路径（证明存在入口） |
| modules[].sort_order | int | 菜单排序，决定WRITE阶段顺序 |
| dependency_edges[] | {from,to,type} | 模块依赖图，type=data/logic/ui |
| roles[].id / name / display_name | string | ROLE_xxx + 内部名 + 显示名 |
| data_creation_chain[] | entity_name[] | 按创建依赖顺序排列，如 ["字典数据", "部门", "用户", "订单"] |
| project_shape / tech_stack | string | 单体/微服务，前后端技术栈 |
| scale_estimate | string | S1~S4预估 |
| core_module_ids | string[] | 自动识别的核心模块（功能最多/处于数据链中游）——**仅用于排序/推荐，绝不允许用于跳过层级生长；默认全量模式仍须覆盖全部模块** |
| evidence[].file / snippet | — | 每个模块、角色的来源证据 |

### 同步生成 `L0_skeleton_report.md`（给 AUTO_REVIEW 自审、附录 C、用户主动追问进度共享）
```markdown
# L0 项目骨架报告

## 1. 项目概况
- 形状：S2 单体前后端分离
- 技术栈：Vue 3 + Spring Boot + MySQL
- 预估模块数：7（核心3个：MOD_001客户 / MOD_002订单 / MOD_003库存）

## 2. 模块依赖图（Mermaid）
\`\`\`mermaid
flowchart LR
 MOD_001[客户管理] --> MOD_002[订单管理]
 MOD_003[库存管理] --> MOD_002
 MOD_004[财务] --> MOD_002
 MOD_005[系统设置] --> MOD_001 & MOD_002 & MOD_003 & MOD_004
\`\`\`

## 3. 角色清单（5个）
- ROLE_001 超级管理员：可操作全部模块
- ROLE_002 销售经理：客户/订单
- ROLE_003 仓库管理员：库存
- ROLE_004 财务主管：财务
- ROLE_005 只读用户：仅查询

## 4. 数据创建链（需按此顺序操作）
字典数据 → 部门/组织 → 用户/员工 → 客户档案 → 商品档案 → 订单 → 收付款

## 5. 模块处理顺序（默认全量覆盖，core 仅决定先后）
全量模式下 L1 起按 sort_order 逐批覆盖**全部模块**，直至 `batches_done == batches_total`；
core_module_ids 只用于决定批次先后顺序（先处理核心），**不得省略任何模块**。
（仅当用户在对话中显式点名模块范围时才进入核心优先模式，见 §分批策略。）
```

### L0 闸门 G0 自检清单（全部通过才能进L1）
- [ ] modules.length ≥ 2
- [ ] dependency_edges 中 **所有模块** 都被连接（无孤立节点）
- [ ] roles.length ≥ 2（不会只有超级管理员）
- [ ] data_creation_chain.length ≥ 3
- [ ] 每个模块都有 ≥1 条 evidence（菜单/路由配置引用）
- [ ] L0_skeleton_report.md 模块依赖图有 Mermaid 代码块

---

## §L1 模块层：按模块分批深入

### 分批策略
```
全量模式（默认，最高优先级）：
 每批 2-3 个模块，顺序按 sort_order，循环批次直到**覆盖 L0 骨架中全部模块**。
 batches_total = ceil(模块总数 / 每批上限)，进入 L1 时写入 baton 并只增不减。
 batches_done < batches_total 时禁止进入 L2。
核心优先模式（ 仅当用户在对话中显式点名模块范围时才启用）：
 批次 1：[MOD_001, MOD_002, MOD_003]（用户指定的核心模块）
 批次 2：[MOD_004, MOD_005] （其余模块仍全量扫到L2作背景）
 …… 未进入核心优先指定的模块，最终必须列入「附录 F：未覆盖模块/功能清单」，禁止静默跳过。
普通模式（等价全量，仅排序偏好）：
 每批 2-3 个模块，顺序按 sort_order
```

### 代码读取范围（每批只读对应模块）
```
批次处理 MOD_x 时只读：
 {前端}/views/对应模块目录/ 的文件名（不读内容）→ 页面清单
 {前端}/router/modules/对应模块.js → 路由 → 页面路径 + 组件路径
 {后端}/controller/对应模块Controller.java → 方法名列表 → 核心实体线索
 {后端}/entity/ 目录下文件名 → 实体名 + 数量估算
 菜单组件中对应模块的 menuItem 结构 → 页面入口路径
绝对不读：
 其他模块的任何文件
 具体 methods/handlers 代码内容
```

### 每个模块落盘到 `L1_modules/MOD_xxx_{模块名}.json`
```json
{
 "module_id": "MOD_001",
 "module_name": "客户管理",
 "completed_layers": ["L0", "L1"],
 "pages": [
 {
 "page_id": "PAGE_001",
 "name": "客户列表",
 "route": "/customer/list",
 "component_path": "src/views/customer/CustomerList.vue",
 "entry_points": [
 { "menu_path": "业务 > 客户管理 > 客户列表", "icon": "user" },
 { "menu_path": "工作台 > 快捷入口 > 客户管理", "icon": null }
 ],
 "tabs": [{"key":"all","label":"全部"}],
 "layout": "list_layout"
 },
 {
 "page_id": "PAGE_002",
 "name": "客户详情",
 "route": "/customer/detail/:id",
 "component_path": "src/views/customer/CustomerDetail.vue",
 "entry_points": [
 { "from_page": "PAGE_001", "action": "点击列表行进入详情" }
 ],
 "layout": "detail_layout"
 }
 ],
 "entities": [
 {
 "entity_id": "ENT_001",
 "name": "Customer",
 "display_name": "客户",
 "table_name": "t_customer",
 "fields_count_estimate": 18,
 "managed_by_controller": "CustomerController.java"
 }
 ],
 "high_frequency_scenarios": [
 "销售人员新增客户档案并分配跟进人",
 "销售经理查看客户状态并审核VIP申请",
 "客服录入客户沟通记录",
 "导出客户名单给市场部做活动"
 ],
 "batch_evidence": [
 { "file": "src/router/modules/customer.js", "line": 1, "snippet": "...", "confidence": 0.97 }
 ]
}
```

### 同步更新 `L1_index.json`（追踪模块进度）
```json
{
 "modules_summary": [
 { "module_id": "MOD_001", "name": "客户管理", "L1": "completed", "pages_count": 5, "entities_count": 2 },
 { "module_id": "MOD_002", "name": "订单管理", "L1": "in_progress", "pages_count": 3, "entities_count": 1 },
 { "module_id": "MOD_003", "name": "库存管理", "L1": "pending", "pages_count": 0, "entities_count": 0 }
 ],
 "total_pages_discovered": 8,
 "total_entities_discovered": 3,
 "last_updated_batch": 1
}
```

### L1 闸门 G1 自检（默认全量：覆盖全部模块）
- [ ] **全部模块**（L0 骨架 modules 100%）的 pages.length ≥ 2 且每页都有 entry_points
- [ ] **全部模块**的 entities.length ≥ 1
- [ ] **全部模块**的 high_frequency_scenarios.length ≥ 3
- [ ] 每个 PAGE 的 component_path 在项目中实际存在（Glob校验）
- [ ] L1_index.json 非空，progress标记与L1_*.json 文件数量一致
- [ ] `batches_done == batches_total`（批循环已覆盖全部模块）

---

## §L2 区域层：按页面分批划分结构

### 分批策略
每批 3 个页面（不分模块），按页面在模块内的出现顺序排序。
批循环直到覆盖**全部页面**（L1 模块中识别的所有页面），`batches_done < batches_total` 时禁止进入 L3。

### 代码读取范围（每批只读本批3页的组件template）
```
对于 PAGE_xxx.vue / .jsx：
 <template>...</template> 全部（识别结构）
 <script> 中的 data/computed 只看变量声明，不看实现
 visible / v-if / v-show / role-check 指令（识别区域可见性条件）
 <script> 的 methods 内容（L3才读）
 其他页面的组件
```

### 每个页面落盘到 `L2_regions/PAGE_xxx_{页面名}.json`
```json
{
 "page_id": "PAGE_001",
 "page_name": "客户列表",
 "module_id": "MOD_001",
 "regions": [
 {
 "region_id": "REG_001",
 "name": "搜索筛选区",
 "region_type": "search_bar",
 "layout_position": "top",
 "selector": ".customer-search-bar",
 "contains_elements_hint": ["搜索框: 客户姓名/手机号", "下拉: 客户等级", "按钮: 搜索, 重置"],
 "visible_conditions": [],
 "triggers_regions": ["REG_002"],
 "evidence": { "template_line": [5, 45] }
 },
 {
 "region_id": "REG_002",
 "name": "数据列表区",
 "region_type": "data_table",
 "layout_position": "center",
 "selector": ".customer-table-wrapper",
 "columns_hint": ["姓名", "手机号", "等级", "状态", "创建人", "创建时间", "操作列"],
 "visible_conditions": [],
 "triggered_by_regions": ["REG_001"],
 "evidence": { "template_line": [47, 120] }
 },
 {
 "region_id": "REG_003",
 "name": "批量操作栏",
 "region_type": "action_bar",
 "layout_position": "top-left-of-table",
 "selector": ".batch-actions",
 "contains_elements_hint": ["按钮: 批量删除", "按钮: 批量导出"],
 "visible_conditions": [
 { "min_selected_rows": 1, "description": "选中至少一行后才出现" },
 { "allowed_roles": ["ROLE_001", "ROLE_002"], "description": "销售经理及以上可见" }
 ],
 "triggers_regions": [],
 "evidence": { "template_line": [122, 135], "directive": "v-if=\"selectedRows.length\"" }
 },
 {
 "region_id": "REG_004",
 "name": "分页器",
 "region_type": "pager",
 "layout_position": "bottom",
 "selector": ".pagination",
 "contains_elements_hint": ["每页数量下拉", "页码跳转"],
 "visible_conditions": [],
 "triggers_regions": ["REG_002"],
 "evidence": { "template_line": [137, 145] }
 }
 ],
 "regions_count": 4,
 "inter_region_triggers_found": 3
}
```

### L2 闸门 G2 自检
- [ ] **全部页面**的每个页面都有 ≥3 个 REGION（最少：搜索 + 列表 + 分页）
- [ ] ≥ 1 条 inter_region_triggers（区域间有触发关系）
- [ ] 有 visible_conditions 的区域都明确了条件来源（角色/数据/状态）
- [ ] 每个 REGION 的 region_type 在规范枚举内（search_bar/data_table/detail_form/tab_panel/sidebar/action_bar/pager）
- [ ] `batches_done == batches_total`（批循环已覆盖全部页面）

---

## §L3 功能层：按区域分批识别功能点

### 分批策略
每批 6 个 REGION（可跨页面跨模块），按模块 → 页面 → 区域顺序排序。
批循环直到覆盖**全部区域**（L2 页面中识别的所有区域），`batches_done < batches_total` 时禁止进入 L4。

### 代码读取范围（每批只读本批6区域的 handler 代码片段）
```
对于 REG_xxx：
 对应页面组件 <script> 的 methods 名 + 简短实现（前5行，不深挖）
 同目录下 {Module}Controller.java 的方法签名（@RequestMapping 行）
 该区域 template 中出现的按钮/链接文字 + @click 方法名
 不读其他区域的方法实现
 不读 service/repository 层（太深了，L5才需要读字段校验的model）
```

### 每个区域落盘到 `L3_functions/REG_xxx_{区域名}.json`
```json
{
 "region_id": "REG_003",
 "region_name": "批量操作栏",
 "page_id": "PAGE_001",
 "module_id": "MOD_001",
 "functions": [
 {
 "function_id": "FN_007",
 "name": "批量删除客户",
 "function_type": "delete",
 "opens_page_id": null,
 "opens_modal_id": "MODAL_CONFIRM_BATCH_DELETE",
 "trigger_element": {
 "element_id": "ELM_012",
 "type": "button",
 "label": "批量删除",
 "selector": "button:contains('批量删除')"
 },
 "target_entity_id": "ENT_001",
 "preconditions": [
 { "type": "selection", "required": "≥1行被选中", "detail": "selectedRows.length ≥ 1" },
 { "type": "permission", "role_required": ["ROLE_001", "ROLE_002"], "detail": "销售经理及以上权限" }
 ],
 "risk_level": "high",
 "requires_confirmation": true,
 "confirm_message": "确认删除选中的 {N} 位客户？此操作不可恢复。",
 "evidence": [
 { "file": "CustomerList.vue", "line": 180, "snippet": "handleBatchDelete() { this.$confirm(...) }", "confidence": 0.96 },
 { "file": "CustomerController.java", "line": 205, "snippet": "@DeleteMapping(\"/batch\")", "confidence": 0.92 }
 ]
 },
 {
 "function_id": "FN_008",
 "name": "批量导出客户",
 "function_type": "export",
 "trigger_element": {
 "element_id": "ELM_013",
 "type": "button",
 "label": "批量导出Excel"
 },
 "target_entity_id": "ENT_001",
 "preconditions": [
 { "type": "permission", "role_required": ["ROLE_001", "ROLE_002", "ROLE_004"], "detail": "含财务主管" }
 ],
 "risk_level": "low",
 "requires_confirmation": false,
 "evidence": [
 { "file": "CustomerList.vue", "line": 195, "snippet": "handleBatchExport() { download(...) }", "confidence": 0.9 }
 ]
 }
 ],
 "functions_count": 2
}
```

### L3 闸门 G3 自检（通过才能进L4）
- [ ] **全部区域**的 FUNCTION 数 ≥ 2（列表操作区应该有新增/编辑/删除/导出等）
- [ ] 每个 FUNCTION 都有 trigger_element（知道点哪个按钮触发）
- [ ] 每个 FUNCTION 都有 ≥ 1 条 evidence（前端或后端），cross_verified优先
- [ ] 高风险操作 risk_level=high/critical 都有 requires_confirmation=true
- [ ] `batches_done == batches_total`（批循环已覆盖全部区域）

---

## §L4 操作层：按功能分批编织步骤（不读源码！从图谱织）

### 分批策略
每批 4 个 FUNCTION。优先按模块分组，同模块的 FUNCTION 放一批（共享上下文）。
批循环直到覆盖**全部功能**（L3 区域中识别的所有功能），`batches_done < batches_total` 时禁止进入 L5。

### 核心规则：**禁止读源码！** 只能从 `_kb/L0~L3/*.json` 查询节点信息编织。
> 为什么？因为L4起写出来的内容**直接会变成用户手册文字**，如果这步还读源码，上下文会被API/数据库污染，WRITE阶段隔离就没用了。

### 每个功能落盘到 `L4_operations/FN_xxx_{功能名}.json`
```json
{
 "function_id": "FN_001",
 "function_name": "新增客户",
 "module_id": "MOD_001",
 "steps": [
 {
 "step_id": "STEP_00001",
 "index": 0,
 "type": "precondition",
 "description": "前置检查",
 "detail": "确保用户已登录且拥有「销售」或「管理员」角色",
 "expected_result": "若权限不足，页面不显示「新增客户」按钮",
 "next_steps": ["STEP_00002"],
 "branch_on_condition": null
 },
 {
 "step_id": "STEP_00002",
 "index": 1,
 "type": "action",
 "action_type": "click",
 "description": "点击「新增客户」按钮",
 "target_element_id": "ELM_001",
 "target_element_label": "新增客户",
 "expected_result": "弹出「客户信息录入」表单窗口（或跳转到新增表单页）",
 "next_steps": ["STEP_00003"],
 "branch_on_condition": null,
 "error_to": "STEP_00009_ERROR1",
 "error_reason": "未分配部门 → 弹提示「请先分配所属部门」"
 },
 {
 "step_id": "STEP_00003",
 "index": 2,
 "type": "input",
 "action_type": "fill",
 "description": "填写客户基本信息",
 "fields_referenced": ["ENT_001.name", "ENT_001.phone", "ENT_001.level"],
 "detail": "按表单顺序填写：客户姓名、联系手机、客户等级（必填项会标红星）",
 "expected_result": "字段输入完成，未标红（校验通过）",
 "next_steps": ["STEP_00004"],
 "branch_on_condition": "FIELD_VALID"
 },
 // ... STEP_00004 ~ STEP_00008 ...
 {
 "step_id": "STEP_00008",
 "index": 7,
 "type": "feedback",
 "description": "保存成功",
 "detail": "页面右上角弹出「保存成功」绿色Toast，客户列表刷新并显示新创建的客户",
 "expected_result": "列表顶部出现新记录，状态为「正常」",
 "next_steps": [],
 "branch_on_condition": null
 }
 ],
 "flowchart_mermaid": "```mermaid\nflowchart TD\n S[开始: 进入客户列表页] --> A[检查权限]\n A -->|有权限| B[点击「新增客户」按钮]\n A -->|无权限| Z1[按钮不显示，结束]\n B --> C{弹窗是否打开?}\n C -->|是| D[填写姓名/手机/等级等必填项]\n C -->|否| Z2[系统繁忙，稍后重试]\n D --> E{字段校验通过?}\n E -->|是| F[点击「确认保存」]\n E -->|否| D1[按红字提示修正后重填]\n D1 --> E\n F --> G[二次确认弹窗点击「确定」]\n G --> H[系统处理 → 保存成功Toast]\n H --> Z[结束: 返回列表查看新记录]\n```",
 "branch_paths_count": 4, // 除了主路径外的分支数
 "evidence_refs": ["EVD_001", "EVD_002", "EVD_015"],
 "auto_generated_from_graph": true
}
```

### L4 闸门 G4 自检
- [ ] **全部 FUNCTION** 的 steps.length ≥ 5（含前置条件 + 错误分支）
- [ ] 每个 FUNCTION 的 flowchart_mermaid 为合法 Mermaid 代码（含 `flowchart` 关键字）
- [ ] 有 ≥ 2 个 branch_paths（不是一条直线）
- [ ] 每个 STEP 的 target_element_id 能在 L3_FUNCTION / ELEMENT 中找到（或合理为 precondition/feedback）
- [ ] `batches_done == batches_total`（批循环已覆盖全部功能）

---

## §L5 细节层：按操作分批填极致细节（局部精读源码）

### 分批策略
每批 5 个 STEP。按 FUNCTION 顺序覆盖**全部操作**（不允许只挑核心 FUNCTION），字段和按钮细节一律补齐。

### 代码读取范围（局部精读，不读全局）
```
对于需要字段详情的 ENTITY：
 后端 Entity.java 的字段注解（@Column/@NotNull/@Pattern 等）
 前端对应表单的 <el-form-item prop=xxx rules=xxx>
 Validator 类中的校验规则
 error.js / message.js 中的错误提示文案
对于需要权限矩阵的 ROLE × FUNCTION 组合：
 @PreAuthorize / hasPermission 注解
 前端路由 meta: { roles: ['admin'] }
 菜单配置中的 role-check
```

### 落盘文件 1：`L5_details/ENTITY/ENT_xxx_{实体名}_字段详情.json`
```json
{
 "entity_id": "ENT_001",
 "entity_name": "客户",
 "fields_full_spec": [
 {
 "field_id": "FLD_0001",
 "name": "name",
 "label": "客户姓名",
 "type": "String",
 "column": "name",
 "db_type": "varchar(50)",
 "max_length": 50,
 "min_length": 2,
 "required": true,
 "form_widget": "input",
 "placeholder": "请输入客户真实姓名",
 "tooltip": "请与身份证保持一致",
 "validation": [
 { "type": "not_blank", "message": "客户姓名不能为空" },
 { "type": "pattern", "pattern": "^[\\u4e00-\\u9fa5A-Za-z0-9·\\s]{2,50}$", "message": "2-50个中英文或数字" },
 { "type": "unique", "scope": "全系统", "message": "该客户姓名已存在" }
 ],
 "default_value": null,
 "example_value": "张三",
 "visible_in_list": true,
 "list_order": 2,
 "visible_in_form": true,
 "form_order": 1,
 "editable": true,
 "readonly_roles": [],
 "used_in_functions": ["FN_001", "FN_002", "FN_004"]
 }
 // ... 其他 17 个字段
 ],
 "fields_total": 18,
 "documented_fields": 18
}
```

### 落盘文件 2：`L5_details/ROLE/权限矩阵.json`
```json
{
 "generated_at": "2026-08-11T16:00:00+08:00",
 "roles": ["ROLE_001", "ROLE_002", "ROLE_003", "ROLE_004", "ROLE_005"],
 "functions_total": 95,
 "matrix_entries": [
 { "function_id": "FN_001", "function_name": "新增客户", "role_permissions": {
 "ROLE_001": "rwd", "ROLE_002": "rwd", "ROLE_003": "r--",
 "ROLE_004": "r--", "ROLE_005": "r--" } },
 { "function_id": "FN_007", "function_name": "批量删除客户", "role_permissions": {
 "ROLE_001": "rwd", "ROLE_002": "rw-", "ROLE_003": "---",
 "ROLE_004": "---", "ROLE_005": "---" } }
 ],
 "coverage_percent": 72
}
```

### 落盘文件 3：`L5_details/ELEMENT/按钮状态.json`（ELEMENT级）
```json
{
 "elements": [
 {
 "element_id": "ELM_001",
 "label": "新增客户按钮",
 "states": {
 "normal": { "enabled": true, "visible": true, "color": "primary", "tooltip": "创建客户档案" },
 "disabled": { "enabled": false, "visible": true, "color": "primary",
 "condition": "当前用户所属部门未分配时",
 "message": "请先到「系统设置」配置所属部门" },
 "hidden": { "enabled": false, "visible": false,
 "condition": "用户角色为 ROLE_005(只读)" }
 }
 }
 ]
}
```

### L5 闸门 G5 自检（与 SKILL.md 闸门表对齐）
- [ ] **全部 ENTITY** 的字段 documented_fields / fields_total ≥ 80%（不允许只查核心实体）
- [ ] 权限矩阵 coverage_percent ≥ 70%（覆盖全部 ROLE × FUNCTION 组合）
- [ ] 高风险 FUNCTION 的按钮有 disabled 状态（有条件禁用）
- [ ] ≥ 50 条 error_message（含错误场景 + 文案 + 触发FUNCTION）
- [ ] `batches_done == batches_total`（批循环已覆盖全部操作/实体）

---

## §自主裁决（取代 v5 §CONFIRM · AUTO_REVIEW 阶段使用）

> v6 核心变化：**不再让用户三选一**。AI 按以下规则全自主裁决，写入 `_auto_decisions.md` 存档。
> 用户主动说「进度/暂停/看一下」时，用下方面板格式展示给用户看；不打断自动流程。

### 4 类自主裁决规则（每条低置信 / incomplete 节点必过至少 1 条）

| 类别 | 规则 | 裁决产物标签 |
|------|------|-------------|
| 低置信 FUNCTION/STEP（0.5≤c<0.7） | 先看置信传播：同区域 2+ 邻居节点均 ≥0.85 且有公共边 → 传播提升 c=0.76 | ACCEPTED_BY_PROPAGATION |
| 低置信 ELEMENT/ROLE（c<0.5） | 回 L3/L5 层只读对应组件源码 1 个文件（不重跑全批）→ 找到 handler 证据 → c 提升到 ≥0.75 | EVIDENCE_SUPPLEMENTED |
| 仍 <0.7 且 AI 判定"操作可推断" | WRITE 阶段对应位置加 警告 提示语（不写虚假按钮/明确操作语句） | INFERRED_WITH_WARNING |
| 仍 <0.7 且 AI 也无法判定 | WRITE 阶段不引用；附录 C "仍需人工复核清单" 列示 | HUMAN_REVIEW_REQUIRED |

| 类别 | Snake / incomplete 专项规则 |
|------|---------------------------|
| 蛇 incomplete | 先从 data_creation_chain（L0）+ 路由跳转 + STEP.next_steps 三重证据各投 1 票 → 多数决补边 → complete=true |
| 蛇顺序争议 | 同 6 类冲突 C6 规则：data_creation_chain + 实体上下游 + 路由跳转 投票 |
| 权限覆盖率 < 60% | 扫描 @PreAuthorize / hasRole / router.meta.roles / 菜单隐藏 v-if 4 类 → 聚合补全 |
| 字段缺失 ≥ 40% | JPA 实体注解 / MyBatis XML / DTO class / Zod schema / PropType 5 类源扫描补全 |

### 进度面板格式（用户追问"进度/暂停"时展示）
```
 当前状态：L3_FUNCTION（第4层），批次：[客户管理_列表搜索区, 客户管理_列表操作栏]，下一步：ELEMENT→methods→FUNCTION 沉淀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 6层进度仪表盘
 模块 7/7 (L0完成 L1完成 L2完成 L3 89% L4 67% L5 52%)
 节点 312 | 三元组 518 | 证据 847 | 跨验证率 62%
 Snake 3条（2 complete / 1 incomplete）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. 最近 20 条 AI 自主裁决（来自 _auto_decisions.md）
 AD-021 ACCEPTED_BY_PROPAGATION: FN_088「客户合并」 0.62 → 0.76（邻居 2×0.9 支持）
 AD-022 INFERRED_WITH_WARNING: FN_103「批量导出」 0.41 → 写 推断警告语句
 ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. 待人工复核 Top（requires_human_review=true 节点）
 1. FN_103 批量导出（证据：仅菜单名，无 handler）
 2. ROLE_07 售后主管（权限：仅 38% 功能有映射）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ 说「继续」或关闭本回复 → 自动按当前阶段接着跑
→ 说具体问题（例「FN_088 客户合并顺序不对」）→ 定位节点 + 局部回灌改完再继续
```

---

**版本**: 6.2.0-chunk07
**最后更新**: 2026-08-11
