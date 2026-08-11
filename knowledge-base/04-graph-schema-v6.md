# 知识图谱 Schema v6（带三元组 + Snake概念链 + 证据溯源）

> 参考：Wiki-Graph 的三元组提取 + 证据回链 + SpineDigest 的 Snake 语义聚类
> 设计目标：不是为了"看起来高级"，而是为了在 WRITE 阶段能从任意节点出发，查询到完整上下文。

---

## 总体架构：6 类节点 + 8 类关系 + 4 类辅助表

```
节点(Nodes)          关系(Relations)         辅助表(Auxiliary)
──────────          ────────────────        ──────────────────
MODULE (模块)       DEPENDS_ON (依赖)       Triples (三元组表)
PAGE (页面)         HAS_PAGE (含页面)       Snakes (概念链表)
REGION (区域)       HAS_REGION (含区域)     Evidence (证据溯源表)
FUNCTION (功能)     HAS_FUNCTION (含功能)   LayerIndex (层级索引)
ENTITY (实体)       OPERATES_ON (操作实体)
ROLE (角色)         CAN_EXECUTE (可执行)
ELEMENT (界面元素)  TRIGGERS (触发)
STEP (操作步骤)     REQUIRES (需要前置)
                    MANAGES (管理)
```

---

## 一、节点类型（8 类，统一带 `layer` 属性）

### 1. MODULE（模块）— L0/L1层
```json
{
  "id": "MOD_001",
  "type": "MODULE",
  "layer": "L1",
  "name": "客户管理",
  "display_name": "客户档案管理",
  "description": "管理客户基本信息、等级、联系方式等",
  "category": "core_business", // core_business | config | report | system
  "sort_order": 1, // 菜单顺序
  "entry_points": [
    { "menu_path": "主菜单 > 业务管理 > 客户管理", "icon": "user" }
  ],
  "status": "active", // active | deprecated | planned
  "meta": {
    "source_files": ["src/router/modules/customer.js"],
    "confidence": 0.98,
    "backfill_count": 0 // 被回灌补充的次数
  }
}
```

### 2. PAGE（页面）— L1层
```json
{
  "id": "PAGE_001",
  "type": "PAGE",
  "layer": "L1",
  "name": "客户列表",
  "module_id": "MOD_001",
  "route": "/customer/list",
  "component_path": "src/views/customer/CustomerList.vue",
  "layout": "list_layout", // list_layout | form_layout | detail_layout | dashboard_layout
  "tabs": [
    { "key": "all", "label": "全部客户" },
    { "key": "vip", "label": "VIP客户" }
  ],
  "meta": { "confidence": 0.95 }
}
```

### 3. REGION（区域）— L2层
```json
{
  "id": "REG_001",
  "type": "REGION",
  "layer": "L2",
  "name": "搜索筛选区",
  "page_id": "PAGE_001",
  "module_id": "MOD_001",
  "region_type": "search_bar", // search_bar | data_table | detail_form | tab_panel | sidebar | action_bar | pager
  "layout_position": "top", // top | left | right | center | bottom
  "visible_conditions": [
    { "role": ["admin", "sales_manager"], "state": null }
  ],
  "meta": { "confidence": 0.9 }
}
```

### 4. FUNCTION（功能）— L3层
```json
{
  "id": "FN_001",
  "type": "FUNCTION",
  "layer": "L3",
  "name": "新增客户",
  "region_id": "REG_005", // 在哪个区域触发（可能是action_bar）
  "page_id": "PAGE_001",
  "module_id": "MOD_001",
  "function_type": "create", // create | read | update | delete | import | export | approve | workflow | query | config
  "target_entity_id": "ENT_001",
  "opens_page_id": "PAGE_002", // 可能跳转到表单页
  "preconditions": [
    { "type": "permission", "role_required": ["sales", "admin"] },
    { "type": "data", "required_entity": "ENT_005:department", "note": "需要先有部门数据" }
  ],
  "risk_level": "low", // low | medium | high | critical
  "requires_confirmation": false, // 是否需要二次确认弹窗
  "meta": { "confidence": 0.93 }
}
```

### 5. ENTITY（实体）— L0/L1层
```json
{
  "id": "ENT_001",
  "type": "ENTITY",
  "layer": "L1",
  "name": "Customer",
  "display_name": "客户",
  "table_name": "t_customer",
  "managed_by_module": "MOD_001",
  "fields": [
    {
      "name": "id",
      "label": "客户ID",
      "type": "Long",
      "column": "id",
      "primary_key": true,
      "required": false, // 前端填不填
      "visible_in_form": false,
      "visible_in_list": true
    },
    {
      "name": "name",
      "label": "客户姓名",
      "type": "String",
      "column": "name",
      "max_length": 50,
      "required": true,
      "validation": { "pattern": "^[\\u4e00-\\u9fa5A-Za-z0-9]{2,50}$", "message": "2-50个中英文或数字" },
      "default_value": null,
      "example": "张三",
      "visible_in_form": true,
      "visible_in_list": true,
      "form_widget": "input", // input | textarea | select | datepicker | radio | checkbox | upload
      "list_options": null
    },
    {
      "name": "level",
      "label": "客户等级",
      "type": "Integer",
      "column": "level",
      "required": true,
      "enum_values": [
        { "value": 1, "label": "普通客户" },
        { "value": 2, "label": "银卡客户" },
        { "value": 3, "label": "金卡客户" },
        { "value": 4, "label": "钻石客户" }
      ],
      "default_value": 1,
      "example": 2,
      "form_widget": "select",
      "visible_in_form": true,
      "visible_in_list": true
    }
  ],
  "state_machine": {
    "states": ["潜在", "跟进中", "已成交", "流失"],
    "transitions": [
      { "from": "潜在", "to": "跟进中", "trigger": "分配销售" },
      { "from": "跟进中", "to": "已成交", "trigger": "签约", "requires_role": ["sales_manager"] }
    ]
  },
  "meta": { "confidence": 0.96 }
}
```

### 6. ROLE（角色）— L0层
```json
{
  "id": "ROLE_001",
  "type": "ROLE",
  "layer": "L0",
  "name": "sales",
  "display_name": "销售人员",
  "description": "负责客户跟进和签约",
  "login_accessible": true,
  "permission_scope": "own_department", // all | own_department | own
  "inherits_from": null, // 角色继承
  "meta": { "confidence": 0.85 } // 角色定义置信度通常较低，由 AUTO_REVIEW 阶段 AI 按规则校验补强
}
```

### 7. ELEMENT（界面元素）— L3/L5层
```json
{
  "id": "ELM_001",
  "type": "ELEMENT",
  "layer": "L3",
  "name": "新增客户按钮",
  "element_type": "button", // button | input | select | link | tab | menu_item | icon | tooltip | modal
  "label": "新增客户",
  "region_id": "REG_005",
  "function_id": "FN_001",
  "selector": "button.el-button--primary:has(+ 新增客户)", // CSS选择器（用于验证）
  "states": {
    "normal":   { "enabled": true,  "visible": true,  "color": "primary" },
    "disabled": { "enabled": false, "visible": true,  "color": "primary", "condition": "无新增权限时" },
    "hidden":   { "enabled": false, "visible": false, "condition": "角色为只读用户时" }
  },
  "tooltip": "创建一个新的客户档案",
  "shortcut": "Ctrl+N",
  "meta": { "confidence": 0.88 }
}
```

### 8. STEP（操作步骤）— L4层
```json
{
  "id": "STEP_001",
  "type": "STEP",
  "layer": "L4",
  "function_id": "FN_001",
  "step_index": 1,
  "step_type": "action", // action | decision | input | navigation | feedback | error
  "action_type": "click", // click | fill | select | check | upload | submit | cancel | search
  "target_element_id": "ELM_001",
  "description": "点击「新增客户」按钮",
  "expected_result": "弹出客户信息填写表单窗口",
  "next_step_ids": ["STEP_002"],
  "branch_on_condition": null,
  "error_to_step_id": null,
  "diagram_node_label": "点击「新增客户」按钮",
  "meta": { "confidence": 0.9 }
}
```

---

## 二、三元组表（Triples）— 通用关系存储

> 节点间的任意关系都存三元组。好处：新增关系类型不需要改表结构。

```json
{
  "triple_id": "TRIPLE_00001",
  "subject_id": "MOD_001",
  "subject_type": "MODULE",
  "predicate": "HAS_PAGE",
  "object_id": "PAGE_001",
  "object_type": "PAGE",
  "properties": {
    "sort_order": 1,
    "is_default_entry": true
  },
  "evidence_ids": ["EVD_001", "EVD_002"],
  "extracted_at_layer": "L1",
  "confidence": 0.95,
  "created_at": "2026-08-11T10:30:00+08:00",
  "dirty": false // 回灌后需要下游刷新
}
```

### 常用谓词（Predicates）清单
| 谓词 | 说明 | 主语类型 → 宾语类型 |
|------|------|-------------------|
| `HAS_PAGE` | 模块包含页面 | MODULE → PAGE |
| `HAS_REGION` | 页面包含区域 | PAGE → REGION |
| `HAS_FUNCTION` | 区域包含功能 | REGION → FUNCTION |
| `HAS_STEP` | 功能包含步骤 | FUNCTION → STEP |
| `NEXT_STEP` | 步骤间流转 | STEP → STEP |
| `MANAGES` | 模块管理实体 | MODULE → ENTITY |
| `OPERATES_ON` | 功能操作实体 | FUNCTION → ENTITY |
| `DEPENDS_ON` | 模块依赖模块 | MODULE → MODULE |
| `REQUIRES` | 功能需要前置条件 | FUNCTION → ENTITY / FUNCTION |
| `TRIGGERS` | 元素触发功能 | ELEMENT → FUNCTION |
| `CAN_EXECUTE` | 角色可执行功能 | ROLE → FUNCTION，带 properties.level |
| `CAN_SEE` | 角色可见区域 | ROLE → REGION |
| `TRIGGERED_BY` | 功能由元素触发 | FUNCTION → ELEMENT |
| `OPENS_PAGE` | 功能打开页面 | FUNCTION → PAGE |
| `BELONGS_TO` | 子元素归属 | ELEMENT → REGION |
| `INHERITS_FROM` | 角色继承 | ROLE → ROLE |
| `CONTAINS` | 间接归属（派生·R1 传递闭包，快速查询用） | MODULE → PAGE/REGION，带 properties.indirect=true |
| `CAN_PERFORM` | 权限传播（派生·R2 权限继承） | ROLE → STEP，带 properties.source="inherit" |
| `PROVIDES_CONTEXT_FOR` | 实体传播（派生·R3 Snake 聚类） | MODULE → FUNCTION，带 properties.count=n |

---

## 三、Snake 概念链（语义聚类链）

> 参考 SpineDigest 的 Snake 设计：不是按模块分组，而是按"语义关联"把跨模块的概念串成一条链。
> 比如「订单创建 → 库存扣减 → 发货 → 客户签收 → 财务结算」这条业务链，跨了订单/库存/物流/财务4个模块。

### Snake 表结构
```json
{
  "snake_id": "SNAKE_001",
  "name": "订单全生命周期链",
  "description": "从客户下单到款项到账的完整业务流",
  "category": "end_to_end_flow", // end_to_end_flow | user_journey | data_propagation | rule_chain
  "confidence": 0.9,
  "node_ids": [
    {
      "node_id": "FN_ORD_CREATE",
      "node_type": "FUNCTION",
      "module": "订单管理",
      "role_in_chain": "initiator", // initiator | middle | terminator | branch
      "link_to_next": {
        "type": "data_flow",
        "description": "创建订单后产生待发货订单记录"
      }
    },
    {
      "node_id": "FN_INV_DEDUCT",
      "node_type": "FUNCTION",
      "module": "库存管理",
      "role_in_chain": "middle",
      "link_to_next": {
        "type": "event_trigger",
        "description": "订单审核通过自动触发库存扣减"
      }
    },
    {
      "node_id": "FN_LOG_CREATE",
      "node_type": "FUNCTION",
      "module": "物流管理",
      "role_in_chain": "middle",
      "link_to_next": {
        "type": "manual_trigger",
        "description": "仓库人员点击发货，生成物流单"
      }
    },
    {
      "node_id": "FN_ORD_SIGN",
      "node_type": "FUNCTION",
      "module": "订单管理",
      "role_in_chain": "middle",
      "link_to_next": {
        "type": "event_trigger",
        "description": "客户签收后触发结算流程"
      }
    },
    {
      "node_id": "FN_FIN_SETTLE",
      "node_type": "FUNCTION",
      "module": "财务管理",
      "role_in_chain": "terminator",
      "link_to_next": null
    }
  ],
  "extracted_from": [
    { "triple_ids": ["TRIPLE_00045", "TRIPLE_00067"] },
    { "source_file": "docs/业务流程说明.docx", "line": 120 }
  ],
  "meta": {
    "manual_verified": true,
    "verified_at": "2026-08-11T14:00:00+08:00"
  }
}
```

### Snake 自动发现算法（GraphBuilder-Agent执行）
1. 从L3 FUNCTION节点中，查找跨模块的 `DEPENDS_ON` + `OPERATES_ON(ENTITY)` 组合
2. 如果 FUNCTION A 的输出实体 == FUNCTION B 的输入实体 → 可能同属一条链
3. 用语义相似度聚类 FUNCTION.description → 把描述相近的跨模块功能归为同一条 Snake
4. 全自主校验：每条 Snake 在 AUTO_REVIEW 阶段由 AI 按规则自动校验/调整（无 CONFIRM 人工确认环节）
5. Snake 产出：在 WRITE 阶段生成"跨模块操作指南"章节（ManualGen v5缺少这个！）

---

## 四、证据溯源表（Evidence）

> **铁律：图谱中没有证据的节点 = 不可靠 = WRITE阶段默认不采纳，除非 AUTO_REVIEW 阶段已裁决（补证据/推断⚠️）或列入附录 C 人工复核清单。**

```json
{
  "evidence_id": "EVD_00001",
  "layer": "L3",
  "source_type": "frontend_file", // frontend_file | backend_file | db_schema | doc_file | api_spec | user_interview | screenshot
  "file_path": "src/views/customer/CustomerList.vue",
  "file_type": ".vue",
  "line_start": 120,
  "line_end": 135,
  "code_snippet": "<!-- snippet truncated for brevity -->",
  "raw_extraction": {
    "extracted_fields": ["button text: 新增客户", "click handler: handleCreate"],
    "confidence_per_field": { "button text": 0.99, "click handler": 0.95 }
  },
  "supporting_node_ids": ["FN_001", "ELM_001"],
  "supporting_triple_ids": ["TRIPLE_00003"],
  "extracted_at": "2026-08-11T10:35:00+08:00",
  "verification_status": "single_source", // single_source | cross_verified | manual_confirmed | user_confirmed
  "cross_verified_with": ["EVD_00002"] // 如果和另一个证据（如后端API）相互印证
}
```

### 证据置信度聚合（用于最终节点置信度）
```
单个节点最终置信度 = 
  0.6 * max(各证据.confidence)
+ 0.3 * (存在 cross_verified ? 1.0 : 单个证据的confidence)
+ 0.1 * (manual_confirmed or user_confirmed ? 1.0 : 0.5)
```

### 证据不足时的处理
- 如果节点 `meta.confidence < 0.7`，在 AUTO_REVIEW 阶段按规则三选一裁决：① 补证据（局部精读源码）② 推断⚠️（WRITE 加警告）③ 列附录 C 人工复核清单。裁决明细写入 `_auto_decisions.md`：
  > "以下 N 项是 AI 推断的，未找到明确代码证据，已按 AUTO_REVIEW 规则处理，如需人工复核见附录 C：
  > 1. [功能] 客户合并 — 置信度 0.62，未找到明确的按钮/API → 推断⚠️
  > 2. [角色权限] 财务主管能删除订单 — 置信度 0.58，只看到了查看权限 → 附录C待复核"

---

## 五、层级索引表（LayerIndex）

> 用于快速查询"某层某模块完成了多少"、"哪些节点需要重算"。

```json
{
  "layer": "L3",
  "module_id": "MOD_001",
  "module_name": "客户管理",
  "progress": {
    "total_expected": 12, // 预估有多少个FUNCTION节点
    "completed": 10,      // 已写入图谱的
    "verified": 8,        // 有cross_verified证据的
    "dirty": 2            // 被回灌标记需要重算的
  },
  "completeness_score": 83, // 0-100，基于 completed/expected + verified率
  "quality_score": 75,      // 0-100，基于 evidence 数量和置信度
  "node_ids": ["FN_001", "FN_002", "...", "FN_012"],
  "last_batch_completed_at": "2026-08-11T11:00:00+08:00",
  "next_batch_plan": [
    { 
      "layer_target": "L4", 
      "functions_to_process": ["FN_001", "FN_002", "FN_003"],
      "estimated_cost": "1个Agent调用，~2000 tokens"
    }
  ]
}
```

---

## 六、图谱查询 API（约定，供各Agent使用）

> 注意：实际查询通过读 JSON 文件 + 内存过滤实现，不启动数据库。以下是"约定的查询语言"。

### Q1: 某模块所有功能（用于写模块文档）
```
QUERY FUNCTION WHERE MODULE_ID = "MOD_001" 
  JOIN TRIPLE (FUNCTION -CAN_EXECUTE- ROLE)
  JOIN TRIPLE (FUNCTION -HAS_STEP- STEP)
  ORDER BY FUNCTION.sort_order
OUTPUT: [{ function: {...}, roles: [...], steps: [...] }]
```

### Q2: 某实体被哪些功能操作（用于实体关系图）
```
QUERY TRIPLE WHERE predicate = "OPERATES_ON" AND object_id = "ENT_001"
  JOIN SUBJECT (type=FUNCTION)
OUTPUT: [{ function_id, function_name, op_type }]
```

### Q3: 跨模块Snake（用于写"端到端操作指南"）
```
QUERY SNAKE WHERE category = "end_to_end_flow"
  EXPAND node_ids
OUTPUT: [{ snake_id, name, nodes: [...] }]
```

### Q4: 低置信度节点清单（供AUTO_REVIEW裁决）
```
QUERY NODE WHERE meta.confidence < 0.7
  JOIN EVIDENCE (supporting该node的证据数)
OUTPUT: [{ node_id, name, layer, confidence, evidence_count }]
```

---

**版本**: 6.2.0-graph
**最后更新**: 2026-08-11
