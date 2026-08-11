# Quality Assurance System

> ⚠️ **说明**：本文件汇总 v6 各阶段的 QA 要求。
> - 六层闸门（G0~G5）：见 SKILL.md 七层闸门体系；
> - AUDIT 阶段：10 维度自评（6 原维 80% + 图谱交叉验证率 10% + Snake 完整性 10%，7/8 号快速入门/术语统一为 0% 引用维度）；
> - JUDGE 阶段：模块级盲审 6 维度（25/20/15/15/15/10，每模块 100 分、70 合格，PASS_rate≥0.70）。
> 详细审核标准见 `SKILL.chunks/chunk-05-audit-judge.md`

质量保证系统贯穿整个文档生成过程，确保最终输出的准确性和一致性。

## 质量控制层级

```
┌─────────────────────────────────────────────────────┐
│                   最终审核                            │
│              (JUDGE 盲审 + AUDIT 10维)               │
└─────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────┐
│                  模块质量控制                         │
│              (Module-Writer + Refiner)              │
└─────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────┐
│                 六层信息质量控制                       │
│              (Skeleton + NodeWeaver·批级质量门)      │
└─────────────────────────────────────────────────────┘
                         ▲
┌─────────────────────────────────────────────────────┐
│                 图谱质量控制                          │
│            (Graph-Builder + Entity-Aligner)          │
└─────────────────────────────────────────────────────┘
```

## 提取阶段质量控制

### 提取完整性检查

```yaml
extraction_quality:
  completeness:
    required_items:
      api:
        - method
        - path
        - parameters
        - response
        - summary

      entity:
        - name
        - fields
        - relationships
        - constraints

      flow:
        - nodes
        - transitions
        - handlers

    threshold:
      min_coverage: 0.8  # 80%覆盖率才合格

  accuracy:
    syntax_check: true
    path_validation: true
    type_check: true

  reporting:
    - extraction_success_rate
    - missing_fields_count
    - error_files_list
```

### 提取质量报告

```markdown
## 提取质量报告

**时间**: 2026-04-29 10:30:00
**模块**: 客户管理

### 完整性

| 类型 | 应提取 | 实际提取 | 覆盖率 |
|------|--------|----------|--------|
| API | 8 | 8 | 100% |
| 实体 | 1 | 1 | 100% |
| 字段 | 25 | 23 | 92% |
| 规则 | 5 | 4 | 80% |

### 缺失项

| 类型 | 字段名 | 缺失原因 |
|------|--------|----------|
| 字段 | updatedBy | 注释缺失 |
| 规则 | 批量删除限制 | 代码未实现 |

### 准确性

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 语法正确 | ✓ | 所有文件通过 |
| 路径有效 | ✓ | 所有路径已验证 |
| 类型匹配 | ✓ | 所有类型一致 |
```

## 分析阶段质量控制

### 分析一致性检查

```yaml
analysis_quality:
  consistency:
    cross_check:
      - api_vs_entity: true      # API参数与实体一致性
      - frontend_vs_backend: true # 前后端一致性
      - flow_vs_code: true       # 流程与代码一致性

    thresholds:
      api_entity_match: 0.95      # 95%匹配
      frontend_backend_match: 0.90 # 90%匹配

  completeness:
    business_rules: 0.85         # 85%规则提取
    flow_completeness: 0.90      # 90%流程完整

  verification:
    - 自动验证代码引用存在
    - 自动验证流程节点连通
    - 自动验证规则触发条件
```

## 模块编写质量控制

### 编写时自检

```yaml
writing_quality:
  completeness:
    required_sections:
      - module_overview
      - permissions
      - operation_entry (操作入口详细路径)
      - operation_preparation (操作前准备)
      - detailed_steps (详细操作步骤，每步包含位置、方法、变化、标志)
      - field_details (字段详细说明)
      - notes (注意事项)
      - error_handling (异常处理)
      - success_confirmation (操作完成确认)

    threshold:
      min_sections: 9
      min_operations: 3
      min_steps_per_operation: 5
      min_fields: 10

  detail_level_check:
    - 操作步骤是否包含操作位置
    - 操作步骤是否包含操作方法
    - 操作步骤是否包含观察变化
    - 操作步骤是否包含成功/失败标志
    - 字段是否有填写规则
    - 字段是否有正确/错误示例
    - 异常处理是否包含原因和处理方法

  accuracy:
    source_citation: required     # 必须标注来源
    inference_mark: required      # 推断内容必须标注
    example_verifiable: true      # 示例必须可验证

  consistency:
    terminology_check: true
    format_check: true
    cross_ref_check: true
```

### 自检清单

```markdown
## 模块编写自检清单

模块: [模块名]
时间: [时间]

### 完整性检查

- [ ] 功能概述已填写
- [ ] 权限说明已填写
- [ ] 操作入口详细路径已填写
- [ ] 操作前准备条件已填写
- [ ] 详细操作步骤已填写(≥3个操作，每操作≥5步)
- [ ] 字段详细说明已填写(≥10个)
- [ ] 注意事项已填写
- [ ] 异常处理已填写
- [ ] 操作完成确认已填写
- [ ] 相关操作已填写

### 详细程度检查

- [ ] 操作步骤包含"操作位置"
- [ ] 操作步骤包含"操作方法"
- [ ] 操作步骤包含"观察变化"
- [ ] 操作步骤包含"截图标记占位符"
- [ ] 操作步骤包含"成功/失败标志"
- [ ] 字段包含"基本信息"
- [ ] 字段包含"填写规则"
- [ ] 字段包含"允许值"
- [ ] 字段包含"正确示例"
- [ ] 字段包含"错误示例"
- [ ] 异常处理包含"异常情况"
- [ ] 异常处理包含"可能原因"
- [ ] 异常处理包含"处理方法"

### 准确性检查

- [ ] 所有步骤可执行
- [ ] 字段说明与代码一致
- [ ] 规则说明有来源依据
- [ ] 推断内容已标注

### 一致性检查

- [ ] 术语使用统一
- [ ] 格式符合规范
- [ ] 交叉引用有效
```

## 冲突质量控制

### 冲突分级处理

```yaml
conflict_quality:
  p0_critical:
    handling: "auto_review_judge"    # v6 全自主：AI 按证据链规则裁决（不询用户）
    requires: "证据链≥2条独立源"
    escalation: "附录 C Top 清单 + 对应模块⚠️标注"

  p1_high:
    handling: "auto_with_evidence"
    requires: "置信度>0.8"
    fallback: "标记 ⚠️ 推断（记录到 _auto_decisions.md）"

  p2_medium:
    handling: "auto_merge"
    requires: "无逻辑矛盾"
    fallback: "保留多版本"

  p3_low:
    handling: "auto_standardize"
    requires: "格式转换"
```

### 冲突检测规则

```yaml
conflict_detection:
  rules:
    - name: "字段类型冲突"
      condition: "同一字段在不同来源类型不同"
      severity: "P1"

    - name: "必填性冲突"
      condition: "同一字段在必填要求上冲突"
      severity: "P1"

    - name: "枚举值冲突"
      condition: "同一字段枚举值集合不一致"
      severity: "P1"

    - name: "流程节点冲突"
      condition: "流程节点数量或顺序不一致"
      severity: "P0"

    - name: "路径不一致"
      condition: "同一功能API路径不一致"
      severity: "P1"
```

## 最终审核质量控制（JUDGE 模块级盲审 6 维）

> **注意**：本段 6 维（25/20/15/15/15/10）是 **JUDGE 模块级盲审**配置（见 agents/14-judge-agent.md）；
> **AUDIT 阶段为 10 维**（6 原维各降至 20/16/12/12/12/8 + ⑨图谱交叉验证率 10% + ⑩Snake 完整性 10%），见 SKILL.chunks/chunk-05-audit-judge.md。

### 审核检查项

```yaml
judge_module_check: # 每模块 100 分，70 合格，PASS_rate≥0.70 放行
  dimensions:
    structure_completeness:
      weight: 0.25
      label: "手册结构完整性"
      checks:
        - has_manual_preface: "手册前置说明（概述/版本/名词释义/环境/联系方式）"
        - has_basic_operations: "系统基础操作（账号/页面/通用规则+流程图）"
        - has_core_functions: "核心业务功能（按用户频率排序，每模块含8项标准结构）"
        - has_full_flow: "全流程业务闭环（跨角色全局泳道图）"
        - has_exception_handling: "异常问题与故障处理（报错汇总/边界/紧急）"
        - has_role_permission: "权限与角色对照表（矩阵+权限流转图）"
        - has_appendix: "附则与更新说明（约束/日志/Q&A）"

    flowchart_quality:
      weight: 0.20
      label: "流程图质量"
      checks:
        - correct_type: "分类绘制：线性/分支/泳道使用正确"
        - user_language: "节点通俗：使用用户语言，无技术术语"
        - full_path: "链路完整：含正常/驳回/终止/异常走向，无断点"
        - clear_annotation: "标注清晰：必填/高危/角色/时效已标注"
        - one_to_one: "一一对应：每个核心功能有对应流程图"

    de_tech_compliance:
      weight: 0.15
      label: "去技术化合规性"
      checks:
        - no_api_endpoints: "无API端点表格（如 `| POST /api/xxx`）"
        - no_http_code: "无HTTP代码示例（如 ```http、curl命令）"
        - no_tech_jargon: "无后端服务名/数据库名/底层原理堆砌"
        - ui_based: "操作描述基于界面操作而非API调用"
        - user_language_only: "只讲用户怎么做、做什么、不能做什么"

    operability:
      weight: 0.15
      label: "操作可执行性"
      checks:
        - has_func_intro: "功能简介：一句话说明用途和适用场景"
        - has_permission_note: "权限说明：哪些角色可操作/仅查看/无权限"
        - has_prerequisites: "前置条件：操作前必须完成的步骤和条件"
        - has_steps: "分步操作：1/2/3数字步骤引导"
        - has_field_desc: "字段说明：必填/规则/格式/示例完整"
        - has_result: "操作结果：成功标志+数据变化+后续走向"
        - has_risk_warning: "风险提示：高危操作醒目警示+标注不可逆操作"

    role_clarity:
      weight: 0.15
      label: "角色隔离与权限清晰"
      checks:
        - per_module_role: "每个功能模块标注了可操作的角色"
        - has_global_matrix: "有全局角色权限矩阵（增/删/改/提交/审核/导出/查看）"
        - has_permission_flow: "权限流转图（权限生效/变更/回收）"
        - no_role_mixing: "不同角色操作不混写，角色边界清晰"
        - user_can_judge: "用户能判断我能不能操作这个功能"

    exception_coverage:
      weight: 0.10
      label: "异常覆盖完整度"
      checks:
        - has_error_table: "常见报错汇总：报错文字→产生原因→解决步骤一一对应"
        - has_abnormal_ops: "操作异常处理：提交失败/审核驳回/流程卡死等场景"
        - has_boundary_desc: "边界问题说明：不支持的操作/数据不可修改/流程不可回退"
        - has_emergency: "紧急处理流程：重大错误的应急步骤+反馈渠道"

  scoring:
    level_a: "90-100：可直接发布，零基础用户可独立上手"
    level_b: "75-89：需微调后发布"
    level_c: "60-74：需整改后重新审核"
    level_d: "<60：不合格，返回WRITE阶段重写"
```

### 审核报告格式

```markdown
## 最终审核报告

**文档**: [系统名称] 操作手册 v1.3.0
**审核时间**: 2026-04-29 11:30:00
**审核人**: Quality Agent

### 评分汇总

| 维度 | 权重 | 得分 | 说明 |
|------|------|------|------|
| 业务完整性 | 35% | 92 | 所有章节完整 |
| 技术准确性 | 25% | 88 | 3处推断待验证 |
| 内容完整性 | 20% | 90 | 内容清晰完整 |
| 一致性 | 10% | 95 | 术语统一 |
| 可读性 | 10% | 90 | 逻辑清晰 |

**综合评分**: 91/100 (优秀) ✅

### 问题清单

| 级别 | 问题数 | 说明 |
|------|--------|------|
| P0 | 0 | 无 |
| P1 | 2 | 已自动处理 |
| P2 | 5 | 已合并优化 |
| P3 | 10 | 已标准化 |

### AI 推断项（记录在 _auto_decisions.md）

| 模块 | 内容 | 状态 |
|------|------|------|
| 客户管理 | 审核流程节点数 | ⚠️ AI 推断（按同类模块 5 节点规则） |
| 订单管理 | 退款规则 | ✅ 证据链完整 |

### 发布建议

✅ 文档质量达到优秀标准，建议发布。
```

## 质量趋势追踪

### 质量历史

```json
{
  "project": "CRM系统",
  "qualityHistory": [
    {
      "date": "2026-04-29T10:00:00",
      "phase": "extraction",
      "module": "全部",
      "score": 85,
      "issues": ["字段缺失2项"]
    },
    {
      "date": "2026-04-29T10:30:00",
      "phase": "analysis",
      "module": "全部",
      "score": 82,
      "issues": ["发现3个冲突"]
    },
    {
      "date": "2026-04-29T11:00:00",
      "phase": "writing",
      "module": "客户管理",
      "score": 90,
      "issues": []
    }
  ]
}
```

### 质量趋势图

```markdown
## 质量趋势

| 时间 | 阶段 | 质量分数 | 趋势 |
|------|------|----------|------|
| 10:00 | 提取 | 85 | - |
| 10:30 | 分析 | 82 | ↓ |
| 11:00 | 编写 | 90 | ↑ |
| 11:30 | 整合 | 91 | ↑ |

分析阶段分数下降是因为发现了冲突，属于正常现象。
编写阶段质量提升说明冲突得到了正确解决。
```

**版本**: 6.2.0
**最后更新**: 2026-08-11
