# 知识累加机制

> **核心原则**：每次分析都在前一次基础上累加，禁止从零开始。

---

## 一、演进模型

```
Session 1: 首次分析
  → 生成 _exploration.md, _extraction.md, _analysis.md, _function_survey.md, _gap_analysis.md
  → 存档会话快照到 knowledge-base/history/v1/

Session 2（代码变更后）:
  → 读取历史产物（全部读取，理解已有内容）
  → 对比代码变更（git diff / 文件对比）
  → 在已有产物末尾追加变更内容
  → 存档到 knowledge-base/history/v2/
```

## 二、增量标记规范

所有产物中的版本标记格式：

```markdown
--- v1 (2026-05-20) ---
原始分析内容...

--- v2 (2026-05-22) [新增] ---
本次新增的分析内容...

--- v2 (2026-05-22) [修正] ---
修正 v1 错误：[具体说明]
修正前：[错误内容]
修正后：[正确内容]
```

## 三、历史版本管理

```
knowledge-base/history/
├── v1/
│   ├── exploration.md
│   ├── analysis-partial.md
│   └── checklist-v1.json
├── v2/
│   ├── extraction.md
│   ├── analysis-full.md
│   └── checklist-v2.json
└── index.yaml  # 版本索引（记录每版时间戳和变更摘要）
```

## 四、检查规则

- 每次进入 ANALYZE 前，必须检查 `knowledge-base/history/` 是否存在历史产物
- 如果存在 → 读取最新版本 → 增量追加（而非覆盖）
- 如果不存在 → 首次分析 → 按正常流程生成
- 增量完成后 → 生成新的版本快照并存档