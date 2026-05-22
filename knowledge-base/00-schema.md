# Knowledge Base Schema

知识库是整个系统的核心数据中心，存储所有提取和分析的结构化信息。

## 目录结构

```
knowledge-base/
├── index/
│   ├── modules.json           # 模块索引
│   ├── apis.json             # API索引
│   ├── entities.json          # 实体索引
│   ├── flows.json             # 流程索引
│   └── rules.json             # 规则索引
├── backend/
│   ├── controllers/           # 后端控制器知识
│   ├── services/              # 后端服务知识
│   ├── repositories/          # 数据访问知识
│   └── entities/              # 实体定义知识
├── frontend/
│   ├── pages/                 # 页面知识
│   ├── components/            # 组件知识
│   └── forms/                  # 表单知识
├── documents/
│   ├── prd/                   # 产品需求文档
│   ├── manuals/               # 操作手册
│   └── api-docs/              # API文档
├── analysis/
│   ├── modules/               # 模块分析结果
│   ├── flows/                 # 流程分析结果
│   └── rules/                 # 规则分析结果
└── conflicts/
    ├── pending.json            # 待处理冲突
    └── resolved.json           # 已解决冲突
```

## 知识条目类型

### 1. API条目

```json
{
  "id": "API_001",
  "type": "api_endpoint",
  "module": "客户管理",
  "content": {
    "method": "POST",
    "path": "/api/v1/customers",
    "summary": "创建客户",
    "description": "创建一个新的客户档案",
    "parameters": [
      {
        "name": "name",
        "type": "string",
        "required": true,
        "description": "客户名称"
      },
      {
        "name": "phone",
        "type": "string",
        "required": true,
        "pattern": "^1[3-9]\\d{9}$",
        "description": "手机号"
      }
    ],
    "request_body": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "phone": { "type": "string" },
        "level": { "type": "integer", "enum": [1,2,3,4,5] }
      }
    },
    "response": {
      "success": {
        "code": 200,
        "data": {
          "id": "long",
          "name": "string",
          "createdAt": "datetime"
        }
      },
      "errors": [
        { "code": 400, "message": "参数校验失败" },
        { "code": 401, "message": "未授权" },
        { "code": 409, "message": "手机号已存在" }
      ]
    },
    "auth": {
      "required": true,
      "roles": ["operator", "admin"]
    }
  },
  "sources": [
    {
      "file": "CustomerController.java",
      "line": 45,
      "type": "backend"
    }
  ],
  "metadata": {
    "extractedAt": "2026-04-29T10:30:00",
    "lastModified": "2026-04-28T15:20:00",
    "confidence": "high",
    "verified": true,
    "verifiedBy": ["backend", "frontend"]
  }
}
```

### 2. 实体条目

```json
{
  "id": "ENTITY_001",
  "type": "entity",
  "module": "客户管理",
  "content": {
    "name": "Customer",
    "tableName": "t_customer",
    "description": "客户实体",
    "fields": [
      {
        "name": "id",
        "column": "id",
        "type": "Long",
        "description": "主键ID",
        "constraints": { "primaryKey": true, "autoIncrement": true }
      },
      {
        "name": "name",
        "column": "name",
        "type": "String",
        "description": "客户名称",
        "constraints": { "maxLength": 100, "required": true }
      },
      {
        "name": "phone",
        "column": "phone",
        "type": "String",
        "description": "手机号",
        "constraints": { "maxLength": 20, "required": true, "unique": true }
      },
      {
        "name": "level",
        "column": "level",
        "type": "Integer",
        "description": "客户等级(1-5)",
        "constraints": { "min": 1, "max": 5 }
      },
      {
        "name": "status",
        "column": "status",
        "type": "String",
        "description": "状态",
        "constraints": { "enum": ["正常", "暂停", "注销"] }
      }
    ],
    "relationships": [
      { "type": "hasMany", "target": "Order", "foreignKey": "customerId" },
      { "type": "hasMany", "target": "Contact", "foreignKey": "customerId" }
    ]
  },
  "sources": [
    {
      "file": "Customer.java",
      "type": "backend",
      "line": 1
    }
  ],
  "metadata": {
    "extractedAt": "2026-04-29T10:30:00",
    "confidence": "high",
    "verified": true
  }
}
```

### 3. 流程条目

```json
{
  "id": "FLOW_001",
  "type": "workflow",
  "module": "客户管理",
  "content": {
    "name": "客户审核流程",
    "description": "新建客户的审批流程",
    "type": "approval",
    "nodes": [
      {
        "id": "start",
        "type": "start",
        "name": "开始",
        "handler": null
      },
      {
        "id": "submit",
        "type": "action",
        "name": "提交审核",
        "handler": "申请人"
      },
      {
        "id": "approve",
        "type": "approval",
        "name": "主管审核",
        "handler": "supervisor"
      },
      {
        "id": "end",
        "type": "end",
        "name": "结束",
        "handler": null
      }
    ],
    "transitions": [
      { "from": "start", "to": "submit", "condition": null },
      { "from": "submit", "to": "approve", "condition": null },
      { "from": "approve", "to": "end", "condition": "approved" },
      { "from": "approve", "to": "submit", "condition": "rejected" }
    ],
    "diagram": "```mermaid\ngraph TD\n  S[开始] --> A[提交审核]\n  A --> B[主管审核]\n  B -->|通过| E[结束]\n  B -->|驳回| A\n```"
  },
  "sources": [
    { "file": "CustomerWorkflow.java", "type": "backend" },
    { "file": "客户管理PRD.md", "type": "document", "line": 45 }
  ],
  "metadata": {
    "extractedAt": "2026-04-29T10:30:00",
    "confidence": "high",
    "verified": false
  }
}
```

### 4. 规则条目

```json
{
  "id": "RULE_001",
  "type": "business_rule",
  "module": "客户管理",
  "content": {
    "name": "手机号唯一性规则",
    "category": "validation",
    "description": "同一手机号不能重复注册客户",
    "implementation": {
      "type": "unique_constraint",
      "field": "phone",
      "table": "t_customer",
      "errorCode": "CUSTOMER_PHONE_DUPLICATE",
      "errorMessage": "该手机号已被注册"
    },
    "scenarios": [
      { "trigger": "新增客户", "check": "before_insert" },
      { "trigger": "修改手机号", "check": "before_update" }
    ]
  },
  "sources": [
    { "file": "CustomerValidator.java", "type": "backend", "line": 25 }
  ],
  "metadata": {
    "extractedAt": "2026-04-29T10:30:00",
    "confidence": "high",
    "verified": true
  }
}
```

### 5. 模块条目

```json
{
  "id": "MODULE_001",
  "type": "module",
  "content": {
    "name": "客户管理",
    "displayName": "客户管理模块",
    "description": "管理客户档案、客户等级、客户审核等",
    "category": "core",
    "functions": [
      {
        "name": "客户新增",
        "type": "create",
        "entry": {
          "page": "/customer/create",
          "api": "POST /api/v1/customers"
        }
      },
      {
        "name": "客户查询",
        "type": "read",
        "entry": {
          "page": "/customer/list",
          "api": "GET /api/v1/customers"
        }
      },
      {
        "name": "客户编辑",
        "type": "update",
        "entry": {
          "page": "/customer/edit/:id",
          "api": "PUT /api/v1/customers/:id"
        }
      },
      {
        "name": "客户删除",
        "type": "delete",
        "entry": {
          "page": "/customer/list",
          "api": "DELETE /api/v1/customers/:id"
        }
      }
    ],
    "relatedModules": [
      { "name": "订单管理", "relation": "has_orders" },
      { "name": "联系人管理", "relation": "has_contacts" }
    ]
  },
  "sources": [
    { "file": "CustomerController.java", "type": "backend" },
    { "file": "CustomerList.vue", "type": "frontend" },
    { "file": "客户管理PRD.md", "type": "document" }
  ],
  "metadata": {
    "extractedAt": "2026-04-29T10:30:00",
    "confidence": "high",
    "complete": true
  }
}
```

## 索引结构

### 模块索引

```json
{
  "modules": [
    {
      "id": "MODULE_001",
      "name": "客户管理",
      "status": "completed",
      "knowledgeCount": {
        "apis": 8,
        "entities": 1,
        "flows": 2,
        "rules": 5
      },
      "qualityScore": 90,
      "lastUpdated": "2026-04-29T10:30:00"
    }
  ]
}
```

### API索引

```json
{
  "apis": [
    {
      "id": "API_001",
      "module": "客户管理",
      "method": "POST",
      "path": "/api/v1/customers",
      "summary": "创建客户",
      "status": "verified"
    }
  ]
}
```

## 搜索查询

### 按模块查询

```json
{
  "query": {
    "type": "module",
    "moduleName": "客户管理",
    "includeRelated": true
  }
}
```

### 按类型查询

```json
{
  "query": {
    "type": "api",
    "module": "客户管理",
    "method": "POST"
  }
}
```

### 按关键词查询

```json
{
  "query": {
    "type": "search",
    "keyword": "手机号",
    "filters": {
      "type": ["entity", "rule"],
      "module": "客户管理"
    }
  }
}
```

**版本**: 1.0.0
**最后更新**: 2026-04-29
