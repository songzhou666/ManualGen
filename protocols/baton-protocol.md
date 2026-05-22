# ManualGen 接力棒协议

> **接力棒是状态机的唯一真相来源。未更新接力棒 = 阶段未完成。**

---

## ⚠️ 强制更新规则（不可违反）

**每个阶段结束后，必须立即更新接力棒，不得延迟、不得忽略、不得口头承诺。**

```markdown
✅ 强制执行：
  阶段完成 → 读取接力棒当前内容 → 修改状态字段 → 标记产物 → 写回文件 → 输出新状态

❌ 禁止行为：
  - "先继续做下一步，稍后更新接力棒" → 视为阶段未完成！
  - "产物已经生成好了，接力棒就不更新了" → 视为阶段未完成！
  - "这次只是分析下一阶段，不更新接力棒" → 视为阶段未完成！
```

**自检**：每次回复结束时，检查接力棒是否已更新。如果应该更新但未更新→**阻断**。

---

## 接力棒模板

```markdown
# ManualGen 接力棒

## 元信息
| 字段 | 值 |
|------|-----|
| 项目 | {项目名} |
| 开始时间 | {ISO 8601} |
| 最后更新 | {ISO 8601} |
| 当前状态 | {EXPLORE/EXTRACT/ANALYZE/GAP/CONFIRM/RESOLVE/WRITE/REFINE/REFERENCE_CHECK/INTEGRATE/AUDIT/TODO_RESOLVE/JUDGE/DONE/ABORT/FAILED} |
| 模式 | {NORMAL/DESIGN_FIX/RETRY_FIX} |
| 文档类型 | user |

## 阶段完成情况
- [ ] EXPLORE - 项目探索
- [ ] EXTRACT - 信息提取
- [ ] ANALYZE - 业务分析
- [ ] GAP - 完整性评估
- [ ] CONFIRM - 用户确认
- [ ] RESOLVE - 冲突解决
- [ ] WRITE - 模块编写
- [ ] REFINE - 模块精炼
- [ ] REFERENCE_CHECK - 一致性检查
- [ ] INTEGRATE - 整合输出
- [ ] AUDIT - 质量审核
- [ ] TODO_RESOLVE - 待办解决
- [ ] JUDGE - 判定
- [ ] DONE - 完成

## 产物清单
- [ ] `_exploration.md` - 探索报告
- [ ] `_extraction.md` - 提取结果
- [ ] `_analysis.md` - 分析报告
- [ ] `_function_survey.md` - 功能调查
- [ ] `_gap_analysis.md` - 完整性评估
- [ ] `_resolution.md` - 冲突解决
- [ ] `_modules/` - 模块文档
- [ ] `_refine_log.md` - 精炼日志
- [ ] `_reference_check.md` - 一致性检查报告
- [ ] `_integration.md` - 整合手册（中间产物）
- [ ] `{项目名称} 用户操作手册.md` - 最终交付物
- [ ] `_audit.md` - 审核报告
- [ ] `_todo_list.md` - TODO列表
- [ ] `_todo_resolution.md` - TODO解决报告
- [ ] `_judgment.md` - 判定结果

---

*最后更新: {ISO 8601}*
```

---

## 更新时机速查

| 时机 | 必须更新 | 更新内容 |
|------|----------|----------|
| 激活时（接力棒不存在） | ✅ | 创建新接力棒，状态 = START |
| 阶段完成时 | ✅ | 当前阶段标记 ✅、状态推进到下一阶段、产物清单标记 ✅ |
| CONFIRM 用户确认后 | ✅ | 记录用户决策、状态推进到 RESOLVE |
| REFINE 完成 | ✅ | 状态推进到 REFERENCE_CHECK、精炼日志标记 ✅ |
| REFERENCE_CHECK 完成 | ✅ | 状态推进到 INTEGRATE、一致性报告标记 ✅ |
| JUDGE 判定后 | ✅ | 状态设为 DONE/FAILED |

---

## 续跑流程

```
读取接力棒 → 解析当前状态 → 读取对应前置产物 → 继续执行
```

| 接力棒状态 | 前置产物检查 | 继续执行 |
|------------|-------------|----------|
| EXPLORE | 无 | 开始探索项目 |
| EXTRACT | _exploration.md | 继续提取信息 |
| ANALYZE | _extraction.md | 开始业务分析 |
| GAP | _analysis.md, _function_survey.md | 完整性评估 |
| CONFIRM | _gap_analysis.md | 等待用户确认 |
| RESOLVE | _gap_analysis.md | 解决冲突 |
| WRITE | _resolution.md | 编写模块 |
| REFINE | _modules/ | 逐模块精炼补全 |
| REFERENCE_CHECK | _modules/ | 一致性检查 |
| INTEGRATE | _modules/ | 整合手册 |
| AUDIT | _integration.md | 质量审核 |
| TODO_RESOLVE | _todo_list.md | 解决待办项 |
| JUDGE | _audit.md | 做出判定 |
| DONE/FAILED | 全部 | 流程已结束 |

---

**版本**: 5.0.0 | **更新**: 2026-05-22