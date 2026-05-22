# Context Manager

上下文管理器负责在整个文档生成过程中管理和优化上下文使用。

## 核心原则

⚠️ **最重要**：**内容完整性永远优先于上下文优化！**

```yaml
core_principles:
  1. "内容完整第一"
     - 绝对不能因为token限制而截断内容
     - 如果上下文不够，应该分多次生成
     - 任何情况下都不能牺牲内容完整性

  2. "拆分是为了结构，不是为了截断"
     - 拆分是基于功能完整性
     - 拆分后的内容仍然必须完整
     - 拆分是为了便于查阅，不是为了限制

  3. "智能多次生成"
     - 内容过多时分多次生成
     - 每次生成都是完整内容
     - 最终合并时确保无遗漏

  4. "内部处理不影响输出"
     - AI内部的token限制是处理策略
     - 最终输出的文档不受任何字数限制
     - 操作手册本身就是越详细越好
```

## 上下文管理策略

### 问题与正确解决方案

| 问题 | ❌ 错误做法 | ✅ 正确做法 |
|------|-------------|-------------|
| 内容过多 | 截断内容 | 分多次生成完整内容 |
| 上下文不够 | 跳过部分内容 | 多次加载逐步生成 |
| 大型项目 | 简化内容 | 分模块逐步生成 |

### 分块策略

```yaml
chunking_strategy:
  principle: "基于功能完整性，不基于token数量"

  chunking_reasons:
    - "结构清晰": "按功能模块拆分"
    - "便于查阅": "按操作流程拆分"
    - "独立性": "独立功能单独成文件"

  when_to_chunk:
    - "功能完整性时": "一个完整功能一块"
    - "内容关联时": "关联内容合并"
    - "独立性强时": "独立功能拆分"

  chunking_rules:
    - "每个块必须完整": true
    - "不得因拆分丢失内容": true
    - "拆分后仍然详细": true
```

### 代码分块（用于输入读取）

```yaml
code_chunking:
  purpose: "读取源代码时的分块策略（仅用于输入）"

  strategies:
    by_file:
      enabled: true
      description: "按文件读取，每个文件完整读取"

    by_module:
      enabled: true
      description: "按模块读取，每个模块完整读取"

  reading_principles:
    - "每个文件必须完整读取"
    - "不得跳过任何文件"
    - "注释和代码同样重要"
```

### 文档分块（用于输出生成）

```yaml
document_chunking:
  purpose: "生成文档时的分块策略"

  principles:
    - "基于功能完整性分块"
    - "每个块内容必须完整"
    - "拆分后仍然详细"

  chunking_decisions:
    - "内容完整性": "优先保证内容完整"
    - "功能独立性": "独立功能单独成文件"
    - "便于查阅": "按操作流程组织"
```

## 增量加载机制

### 模块级增量

```yaml
incremental_loading:
  enabled: true

  principles:
    - "已完成的内容不重复加载"
    - "新内容追加加载"
    - "始终保持上下文完整"

  states:
    not_loaded:
      action: "load"
      priority: 1

    loaded:
      action: "skip"
      check: "checksum"

    stale:
      action: "reload"
      check: "last_modified"

    error:
      action: "retry"
      max_retries: 3
```

## 缓存策略

### 多级缓存

```yaml
cache_hierarchy:
  l1_memory:
    type: "in_memory"
    size: "100 entries"
    ttl: "session"
    use: "高频访问的KB条目"

  l2_disk:
    type: "file_system"
    size: "unlimited"
    ttl: "project"
    use: "已提取的知识条目"

  l3_remote:
    type: "optional_cloud"
    size: "unlimited"
    ttl: "unlimited"
    use: "长期归档"
```

## 错误恢复

### 内容截断防护

```yaml
content_protection:
  absolute_rules:
    - "绝对不能截断内容"
    - "绝对不能因token限制跳过内容"
    - "绝对不能简化内容以适应限制"

  recovery_strategies:
    on_context_full:
      - "保存当前进度"
      - "生成当前完整内容"
      - "继续生成剩余内容"
      - "最终合并所有内容"

    on_large_content:
      - "拆分为多个文件"
      - "每个文件内容完整"
      - "合并时确保无遗漏"
```

**版本**: 1.0.0
**最后更新**: 2026-04-29
