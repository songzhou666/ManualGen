# 智能冲突解决增强模块

这是ManualGen冲突解决系统的v2.0版本，增加了智能推测和交互式确认机制。

## 核心改进

### 改进1: 智能推测引擎

基于置信度算法自动推测最优解决方案，减少人工干预。

### 改进2: 交互式确认

对于关键冲突，提供清晰的选项和详细分析，让用户快速做出决策。

### 改进3: 冲突溯源

记录冲突的完整推理过程，便于审计和追溯。

---

## 智能推测算法

### 置信度计算公式

```python
def calculate_confidence(source_info):
    """
    计算信息源的置信度得分
    """
    score = (
        source_priority[source_info.type] *      # 来源优先级
        recency_factor[source_info.timestamp] *   # 时间新度
        explicitness_boost[source_info.explicit] * # 明确程度
        cross_validation_multiplier[source_info.confirmed_count]  # 多方印证
    )
    
    return score

# 优先级权重
source_priority = {
    "backend_code": 10,      # 代码实现 - 最高
    "frontend_code": 8,      # 前端实现 - 次高
    "database_schema": 7,    # 数据库结构
    "pm_document": 6,        # PM文档
    "api_contract": 7,      # API契约
    "test_code": 6,          # 测试代码
    "old_document": 4,       # 旧文档
    "legacy_comment": 3      # 遗留注释 - 最低
}

# 时间衰减因子（越新权重越高）
recency_factor = {
    "within_1_week": 1.5,
    "within_1_month": 1.3,
    "within_3_months": 1.1,
    "within_6_months": 1.0,
    "within_1_year": 0.9,
    "older": 0.7
}

# 明确性加成
explicitness_boost = {
    "explicit": 1.5,     # 明确声明
    "implicit": 1.0,     # 隐含推断
    "ambiguous": 0.5     # 模糊不清
}

# 多方印证倍数
cross_validation_multiplier = {
    0: 1.0,   # 无印证
    1: 1.2,   # 单方印证
    2: 1.5,   # 双方印证
    3: 2.0    # 多方印证
}
```

### 自动解决策略

```yaml
auto_resolution_rules:
  immediate_resolve:
    conditions:
      - "最高置信度得分 > 第二名 * 1.5"  # 明显领先
      - "最高置信度 > 8.0"
      - "冲突类型 in [P2, P3]"
    action: "自动采用置信度最高者"
    notification: "silent"  # 不打扰用户
  
  recommend_resolve:
    conditions:
      - "最高置信度得分 > 6.0"
      - "冲突类型 in [P1]"
    action: "推荐最优方案"
    notification: "summary"  # 简报提醒
  
  require_confirm:
    conditions:
      - "最高置信度得分 <= 6.0"
      - "冲突类型 in [P0, P1]"
    action: "需要人工确认"
    notification: "detailed"  # 详细说明
```

---

## 冲突类型扩展

### 增强的冲突分级

```yaml
conflict_levels_extended:
  P0_CRITICAL:
    name: "致命冲突"
    description: "影响核心业务流程或数据完整性"
    examples:
      - "审核流程级数不一致"
      - "必填字段在不同模块定义矛盾"
      - "状态流转规则冲突"
    handling:
      auto_resolve: false
      block_process: true
      escalate: "immediate"
      require: "人工确认"
  
  P1_HIGH:
    name: "重要冲突"
    description: "影响功能实现但不影响核心流程"
    examples:
      - "字段类型定义不一致"
      - "长度限制冲突"
      - "默认值不一致"
    handling:
      auto_resolve: true
      auto_threshold: 0.8
      fallback: "推荐方案"
      require: "确认推荐方案"
  
  P2_MEDIUM:
    name: "一般冲突"
    description: "描述性差异，不影响功能"
    examples:
      - "字段描述措辞不一致"
      - "错误提示信息差异"
      - "帮助文档描述差异"
    handling:
      auto_resolve: true
      strategy: "merge_best"
      notification: "summary"
  
  P3_LOW:
    name: "轻微冲突"
    description: "格式、命名等表面差异"
    examples:
      - "日期格式差异"
      - "命名风格差异"
      - "注释格式差异"
    handling:
      auto_resolve: true
      strategy: "standardize"
      notification: "none"
```

---

## 交互式冲突解决界面

### 完整交互示例

```markdown
🔍 检测到冲突: CFG-001 审核级数不一致

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 冲突详情
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

冲突类型: P0（致命冲突）
影响范围: 订单审核流程
严重程度: ⚠️ 高
是否阻塞: ✅ 暂时阻塞后续流程

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 来源分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────┬──────────┬──────────┬─────────────┐
│ 来源        │ 描述     │ 置信度   │ 更新时间    │
├─────────────┼──────────┼──────────┼─────────────┤
│ 后端代码    │ 3级审批  │ ⭐⭐⭐⭐⭐ │ 2026-05-10  │
│ 前端代码    │ 2级审批  │ ⭐⭐⭐⭐  │ 2026-05-08  │
│ PM文档V2.1  │ 3级审批  │ ⭐⭐⭐    │ 2026-05-01  │
│ PM文档V2.0  │ 2级审批  │ ⭐⭐      │ 2026-04-15  │
└─────────────┴──────────┴──────────┴─────────────┘

置信度得分计算:
• 后端代码: 10(来源) × 1.3(时间) × 1.5(明确) × 1.2(印证) = 23.4
• 前端代码: 8(来源) × 1.3(时间) × 1.0(隐含) × 1.0(无印证) = 10.4
• PM文档V2.1: 6(来源) × 1.0(时间) × 1.0(隐含) × 1.2(印证) = 7.2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 智能推测
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

基于置信度分析，系统推测应以"后端代码3级审批"为准。

推理过程:
1. ✅ 后端代码置信度最高（23.4分）
2. ✅ 后端更新时间最近（2026-05-10）
3. ✅ PM文档V2.1与后端一致，形成印证
4. ✅ 前端可能未同步更新

风险提示:
• 前端代码与后端不一致，可能需要同步修改
• 修改涉及{2个文件，估算工时2小时}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ 解决方案
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[A] 采纳系统推荐（3级审批）
    → 自动更新文档，采用后端实现
    → 记录前端需要同步修改
    → 预计总耗时: 2小时（含前端修改）

[B] 手动选择方案
    → 可以选择前端2级审批
    → 但需要说明原因
    → 需要同步修改后端

[C] 查看详细代码引用
    → 查看后端代码位置
    → 查看前端代码位置
    → 查看PM文档位置

[D] 稍后处理
    → 加入待确认队列
    → 继续处理其他冲突
    → 最终需要回来确认

[E] 生成冲突报告
    → 输出完整冲突分析报告
    → 发送给相关人员确认

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请输入选项（A/B/C/D/E）: _
```

### 快速确认模式

对于低优先级冲突，使用快速确认模式：

```markdown
🔍 检测到3个P3级别冲突（格式差异）

✅ 已自动解决:
• 日期格式标准化为 YYYY-MM-DD
• 枚举值命名统一为 camelCase
• 注释格式统一为 JSDoc

💡 如需查看详情，请输入 /ManualGen conflicts --detail
```

---

## 冲突溯源机制

### 溯源数据结构

```json
{
  "conflict_id": "CFG-001",
  "conflict_type": "P0",
  "detected_at": "2026-05-15T14:30:00Z",
  
  "sources": [
    {
      "source_id": "SRC-001",
      "source_type": "backend_code",
      "file_path": "/backend/src/service/OrderService.java",
      "line_number": 156,
      "content": "if (approvalLevel >= 3) { ... }",
      "confidence": {
        "base_score": 10,
        "recency_factor": 1.3,
        "explicitness_boost": 1.5,
        "validation_multiplier": 1.2,
        "total_score": 23.4
      }
    }
  ],
  
  "reasoning_chain": [
    {
      "step": 1,
      "action": "识别冲突",
      "finding": "发现审核级数存在差异"
    },
    {
      "step": 2,
      "action": "收集来源",
      "finding": "收集到4个相关来源"
    },
    {
      "step": 3,
      "action": "计算置信度",
      "finding": "后端代码置信度最高"
    },
    {
      "step": 4,
      "action": "智能推测",
      "finding": "推测应以3级审批为准"
    }
  ],
  
  "resolution": {
    "status": "pending",
    "recommended_solution": "采用后端实现",
    "confidence": 0.85,
    "requires_manual_confirm": true
  }
}
```

### 溯源查询命令

```bash
/ManualGen conflicts trace CFG-001
# 输出完整的推理链路

/ManualGen conflicts history
# 输出所有历史冲突及解决过程

/ManualGen conflicts export --format json
# 导出冲突记录用于审计
```

---

## 冲突解决策略库

### 常见冲突的标准解决方案

```yaml
standard_solutions:
  approval_levels_conflict:
    description: "审批级数冲突"
    resolution_strategy: "code_wins"
    code_location_priority:
      - "workflow_config"
      - "service_logic"
      - "controller_validation"
  
  field_type_conflict:
    description: "字段类型冲突"
    resolution_strategy: "database_wins"
    fallback_strategy: "strictest_wins"
  
  required_field_conflict:
    description: "必填性冲突"
    resolution_strategy: "strictest_wins"
    note: "更严格的定义通常更安全"
  
  enum_value_conflict:
    description: "枚举值冲突"
    resolution_strategy: "superset_union"
    note: "合并所有枚举值，确保兼容性"
  
  naming_convention_conflict:
    description: "命名规范冲突"
    resolution_strategy: "project_convention"
    note: "遵循项目统一的命名规范"
  
  date_format_conflict:
    description: "日期格式冲突"
    resolution_strategy: "iso8601"
    note: "统一使用 ISO 8601 标准"
```

---

## 性能优化

### 冲突检测优化

```yaml
conflict_detection_optimization:
  enabled: true
  
  caching:
    strategy: "lru"
    max_size: 100
    ttl: "1hour"
  
  parallel_detection:
    enabled: true
    max_workers: 4
    chunk_size: 10
  
  incremental_check:
    enabled: true
    check_only_changed: true
    use_git_diff: true
```

### 批量处理优化

```yaml
batch_processing:
  enabled: true
  
  strategy:
    - "group_by_level"     # 按严重级别分组
    - "auto_first"         # P3自动解决
    - "review_second"       # P2快速确认
    - "confirm_third"       # P1推荐确认
    - "block_fourth"       # P0暂停处理
  
  notification_batching:
    aggregate_interval: "5min"
    max_batch_size: 10
```

---

## 集成指南

### 与Master Controller集成

```yaml
integration_with_master:
  on_conflict_detected:
    trigger: "冲突数量 > 0"
    action: "暂停相关模块处理"
    notify: "Master Controller"
  
  on_conflict_resolved:
    trigger: "冲突已解决"
    action: "恢复模块处理"
    log: "冲突解决记录"
  
  on_critical_conflict:
    trigger: "P0冲突检测"
    action: "暂停整个流程"
    notify: "用户 + Master Controller"
    escalation: "立即通知"
```

### 与Analyzer集成

```yaml
integration_with_analyzer:
  conflict_hint:
    source: "Analyzer"
    content: "在分析过程中发现潜在冲突"
    format: "conflict_hint"
  
  analyzer_feedback:
    source: "冲突解决结果"
    target: "Analyzer"
    content: "哪些冲突与业务分析相关"
```

---

## 使用示例

### 示例1: 首次运行冲突检测

```bash
用户: /ManualGen resolve
系统: 
🔍 开始冲突检测...

扫描范围:
• 后端代码: 156个文件
• 前端代码: 234个文件
• 文档: 12份

检测结果:
┌─────────┬────────┬─────────────┐
│ 级别    │ 数量    │ 处理方式    │
├─────────┼────────┼─────────────┤
│ P0      │ 1个     │ ⚠️ 需确认   │
│ P1      │ 3个     │ 📝 推荐确认 │
│ P2      │ 5个     │ ✅ 已解决   │
│ P3      │ 12个    │ ✅ 已解决   │
└─────────┴────────┴─────────────┘

总冲突数: 21个
已自动解决: 17个 (81%)
需确认: 4个

是否开始处理需要确认的冲突？ [Y/n]
```

### 示例2: 查看冲突汇总

```bash
用户: /ManualGen conflicts --summary
系统:
📋 冲突汇总报告

【P0 - 致命冲突】1个
┌────────────────────────────────────────────────────┐
│ CFG-001: 订单审核级数不一致                          │
│ 影响: 核心业务流程                                   │
│ 状态: ⏸️ 暂停处理                                   │
│ 建议: 采用后端3级审批                                │
└────────────────────────────────────────────────────┘

【P1 - 重要冲突】3个
┌────────────────────────────────────────────────────┐
│ CFG-002: 客户手机号长度限制不一致 (前端12位/后端11位) │
│ CFG-003: 订单状态流转规则部分冲突                    │
│ CFG-004: 金额精度定义不一致 (前端2位/后端4位)        │
└────────────────────────────────────────────────────┘

【P2 - 已解决】5个
✅ 字段描述措辞已统一
✅ 错误提示信息已标准化
✅ API路径格式已统一

【P3 - 已解决】12个
✅ 命名规范已标准化
✅ 日期格式已统一
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.0.0 | 2026-05-15 | 新增智能推测引擎、交互式界面、溯源机制 |
| 1.0.0 | 2026-04-29 | 初始版本 |

**版本**: 2.0.0
**最后更新**: 2026-05-15
**维护者**: songzhou
**更新说明**: 全面升级冲突解决系统，增加智能推测和交互确认机制
