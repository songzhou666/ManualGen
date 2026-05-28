---
name: ManualGen
version: 5.1.1
description: |
  智能业务分析与操作手册生成专家。理解项目业务流程、功能关系、用户场景，
  生成面向运营人员、销售人员、客户的用户版操作手册。
  
  核心能力：功能点清单 → 状态机分析 → 数据上下游 → 完整性评估 → 单版用户手册
  
  **When to use**:
  - 用户说"写手册"、"生成文档"、"操作手册"、"用户手册"
  - 用户说"分析业务流程"、"梳理流程"、"功能关系"
  - 用户说"完善文档"、"更新文档"、"业务分析"
  
  **When NOT to use**:
  - 仅单次简单问答
  - 不需要生成文档的纯编码任务
  
  **核心机制**: 1. 激活后自动按状态机执行（无需手动输入命令） 2. 读取接力棒获取当前状态，自动续跑 3. 每完成一个阶段**必须**更新接力棒 4. 所有产物通过文件传递，禁止口头传递 5. 仅 CONFIRM 阶段需等待用户确认，其余阶段自动推进 6. 每步回复第一行输出"当前状态：[阶段名]，下一步：[操作]" 7. TODO_RESOLVE 阶段统一处理无法即时解决的问题
---

# ManualGen v5.0 — 业务分析 + 操作手册生成引擎

> **约束即自由**：给AI严格的框架，才能交出可靠的文档。
> **主动执行**：激活后AI自动沿状态机推进，无需用户下命令。
> **按需加载**：当前阶段只加载当前所需chunk，不一次性塞入所有信息。

---

## ⚠️ 激活即执行（强制！）

当 ManualGen 被激活时（用户表达了写手册/分析项目等意图），AI **必须**立即执行以下流程，不得等待用户额外指令：

```
Step 1: 运行强制入口清单（见下方）
Step 2: 读取接力棒 → 确定当前状态
Step 3: 如果状态是 START → 标记为 EXPLORE，开始第一阶段
Step 4: 如果状态是 X → 直接从 X 阶段续跑
Step 5: 执行当前阶段任务
Step 6: 完成阶段任务 → 更新接力棒 → 自动进入下一阶段
Step 7: 重复 Step 5-6，直到 CONFIRM 或 DONE
```

**AI 不得**：
- ❌ 等待用户输入 `/manual gen` 命令才开始
- ❌ 做完一步后询问"下一步做什么？"（除非在 CONFIRM 阶段）
- ❌ 跳过产物更新直接进入下一阶段

---

## 🚨 强制入口清单（激活后第一步必须执行）

```markdown
在回答用户任何问题、执行任何分析之前，必须：

- [ ] 已确定项目路径（用户指定 > 当前工作目录）
- [ ] 已读取 {项目路径}/.agent/harness/_baton.md
- [ ] 已确认接力棒存在与否
    - 存在 → 解析当前状态，准备续跑
    - 不存在 → 创建目录和接力棒，状态 START
- [ ] 已在回复第一行输出 "当前状态：[阶段名]，下一步：[操作]"

**任一未完成 → 禁止执行后续任何操作**
```

---

## 🔍 自检闭环（每次回复结束时必须检查）

- [ ] 本次回复是否输出了"当前状态：[阶段名]，下一步：[操作]"？
- [ ] 如果当前阶段已完成 → 是否已更新接力棒？
- [ ] 如果没有 → 已偏离状态机 → 立即返回修正

---

## 🔄 状态机总览

| 阶段 | 职责 | 核心产物 | 自动推进 |
|------|------|----------|----------|
| 0 EXPLORE | 理解项目业务全貌 | `_exploration.md` | ✅ 自动 |
| 1 EXTRACT | 提取功能/API/路由/页面 | `_extraction.md` | ✅ 自动 |
| 2 ANALYZE | 流程+状态机+边界+数据上下游 | `_analysis.md` + `_function_survey.md` | ✅ 自动 |
| 2.5 **GAP** | 完整性评估+项目形状报告 | `_gap_analysis.md` | ✅ 自动 |
| 3 CONFIRM | 展示摘要等待用户确认 | 用户反馈记录 | ⛔ 等待用户 |
| 4 RESOLVE | 冲突检测与解决 | `_resolution.md` | ✅ 自动 |
| 5 WRITE | 子Agent写模块（隔离技术上下文） | `_modules/` | ✅ 自动 |
| 5.5 **REFINE** | 子Agent逐模块回扫 | `_refine_log.md` | ✅ 自动 |
| 5.7 **REFERENCE_CHECK** | 交叉引用+术语一致性检查 | `_reference_check.md` | ✅ 自动 |
| 6 INTEGRATE | 完整合并→项目命名→根目录输出 | `{项目名} 用户操作手册.md` | ✅ 自动 |
| 7 AUDIT | 自评（6维度预审） | `_audit.md` | ✅ 自动 |
| 8 TODO_RESOLVE | 统一解决待办项 | `_todo_resolution.md` | ✅ 自动 |
| 9 JUDGE | 子Agent盲审（真正质量门） | `_judgment.md` | ✅ 自动（DONE结束） |

```
EXPLORE → EXTRACT → ANALYZE → GAP → CONFIRM → RESOLVE → WRITE → REFINE → REFERENCE_CHECK → INTEGRATE → AUDIT → TODO_RESOLVE → JUDGE → DONE
                                          ↑-- 等待用户确认 --↓
```

---

## 🚫 状态路由表

| 当前状态 | 自动进入 | 禁止 |
|----------|----------|------|
| START | EXPLORE | 直接编码/提取 |
| EXPLORE | EXTRACT | ANALYZE 以上 |
| EXTRACT | ANALYZE | GAP 以上 |
| ANALYZE | GAP | CONFIRM 以上 |
| GAP | CONFIRM | RESOLVE 以上 |
| CONFIRM(通过) | RESOLVE | WRITE 以上 |
| CONFIRM(修改) | ANALYZE | 跳过分析 |
| CONFIRM(取消) | 终止 | 继续 |
| RESOLVE | WRITE | REFINE 以上 |
| WRITE | REFINE | REFERENCE_CHECK 以上 |
| REFINE | REFERENCE_CHECK | INTEGRATE 以上 |
| REFERENCE_CHECK | INTEGRATE | AUDIT 以上 |
| INTEGRATE | AUDIT | TODO_RESOLVE 以上 |
| AUDIT | TODO_RESOLVE | JUDGE 以上 |
| TODO_RESOLVE | JUDGE | DONE 以上 |
| JUDGE | DONE / WRITE(修复) / FAILED | 继续执行 |

**产物缺失阻断**：进入下一阶段前，必须确认前置产物存在，否则不得推进。

---

## 📦 产物体系（12个核心产物）

```
.agent/harness/
├── _baton.md              # 接力棒（状态持久化）
├── _exploration.md        # 探索报告
├── _extraction.md         # 提取结果
├── _analysis.md           # 分析报告
├── _function_survey.md    # 功能调查（功能清单+状态机+数据流）
├── _gap_analysis.md       # 完整性评估（缺失功能+形状报告+评分）
├── _resolution.md         # 冲突解决报告
├── _modules/              # 模块文档目录
├── _integration.md        # 整合手册（中间产物，审核用）
├── {项目名} 用户操作手册.md  # 最终交付物（项目根目录）
├── _audit.md              # 审核报告
├── _todo_list.md          # TODO列表
├── _todo_resolution.md    # TODO解决报告
├── _analysis_batch_index.md # 分批分析索引（可选）
└── _judgment.md           # 判定结果
```

**产物更新规则**：
- 每个阶段完成时 → 创建/更新对应产物
- 产物写入后 → 接力棒中标记该产物为 ✅
- 所有产物必须有实际内容，不得为空文件

---

## 📥 按需加载规则

| 加载时机 | 加载哪些chunk |
|----------|---------------|
| 初始化 | `01-overview`（always）+ `06-privacy-security`（always） |
| 进入 EXTRACT | `02-explore-extract` |
| 进入 ANALYZE | `03-analyze-gap` |
| 进入 RESOLVE/WRITE | `04-resolve-write` |
| 进入 WRITE | （已加载）+ `flowchart-spec` |
| 进入 REFINE/REFERENCE_CHECK | `04-resolve-write`（部分）+ `flowchart-spec` |
| 进入 AUDIT | `05-audit-judge` |
| 进入 TODO_RESOLVE | `05-audit-judge` |

**每次只加载当前阶段需要的chunk，之前的chunk可卸载。**

---

## 🌐 全局规则

### 1. 计数验证
声称"提取了N个API"→ 必须逐个列出N个API。声称N个但只列出M个(M<N)→ **阻断**。

### 2. 渐进累加
每次分析前必须先读取历史产物，在已有基础上追加，用标记区分新增。

### 3. CONFIRM 强制展示明细
必须展示模块列表 + 流程图数量 + 缺失清单 + 完整性评分 + 明确确认请求。

### 4. 接力棒强制更新
每个阶段完成后**必须**更新接力棒（更新状态+标记产物）。未更新接力棒视为阶段未完成。

> 隐私保护规则在所有阶段强制执行（chunk-06 始终加载）

### 5. 隐私保护
所有输出必须遵守 `privacy/privacy-notice.md`。

### 6. 验证链规则
- 每个阶段完成后必须提供**可验证的证据链**
- 声称"提取了N个API"→ 必须**逐个列出**N个API（计数验证）
- 声称"分析了M个模块"→ 必须**逐个列出**M个模块及其分析内容
- 用户可随时要求**核对验证** → AI必须提供原始证据
- 证据链不完整 → 视为阶段未完成 → 必须补充后继续

### 7. Mermaid流程图强制规则
- 所有流程图**必须**使用标准Mermaid语法（`flowchart TD` / `flowchart LR` / `stateDiagram-v2`），不得使用ASCII文字画框
- 节点文字中的中文引号必须使用 `「」` 而非 `""`（弯引号会破坏解析器）
- 验证方式：产物中的流程图区块必须以 ````mermaid` 开头
- 如果使用文字图替代Mermaid → 视为该模块流程图缺失 → 阻断

#### 正误对比
| 类型 | ❌ 错误 | ✅ 正确 |
|------|--------|--------|
| 流程图 | 用`+--+`画框的ASCII图 | `flowchart TD` + 标准语法 |
| 状态机 | 用文字描述状态流转 | `stateDiagram-v2` |
| 节点引号 | `A[点击"按钮"]`（弯引号） | `A[点击「按钮」]`（直角引号） |

---

## 🎨 定制化指南

用户在对话中可通过自然语言指定偏好，AI 将在 CONFIRM 阶段汇总展示，经确认后传递到后续阶段。

### 支持的定制化维度

| 维度 | 说明 | 示例用法 |
|------|------|---------|
| 文档风格 | 简洁/详细/图文并茂 | "手册写得简洁一点" |
| 角色聚焦 | 仅为特定角色生成操作说明 | "只写销售人员的操作部分" |
| 模块优先级 | 指定先写哪些核心模块 | "重点写客户管理和订单模块" |
| 输出格式 | 指定最终产物的格式要求 | "用 Markdown 格式输出" |
| 深度级别 | 基础操作/高级功能/全量覆盖 | "每个操作至少写 5 步" |

### 定制化参数传递链路

```
用户指定偏好 → Master Controller 记录到接力棒 → CONFIRM 阶段展示 →
用户确认 → 传递到后续阶段（WRITE/REFINE/INTEGRATE）
```

### 注意事项

- 定制化需求**不会覆盖硬性规则**（如状态机流程、隐私保护、产物模板），仅影响输出风格和粒度
- 定制化偏好需在 CONFIRM 阶段最终确认，确认后不可中途更改（如需更改，使用中断机制）
- 如果用户没有明确指定偏好，AI 使用默认的"中等详细度 + 全角色覆盖"策略

> 更多定制化相关的技术细节和模板自定义方法，请参见深度 FAQ：`references/faq-deep.md` 的 Q6。

---

## 📚 阶段详情（按需加载对应 chunk）

| 阶段 | 详情位置 |
|------|----------|
| EXPLORE / EXTRACT | `SKILL.chunks/chunk-02-explore-extract.md` |
| ANALYZE / GAP | `SKILL.chunks/chunk-03-analyze-gap.md` |
| CONFIRM / RESOLVE / WRITE / INTEGRATE | `SKILL.chunks/chunk-04-resolve-write.md` |
| AUDIT / JUDGE | `SKILL.chunks/chunk-05-audit-judge.md` |
| 隐私保护细则 | `SKILL.chunks/chunk-06-privacy-security.md` |
| 流程图规范 | `templates/flowchart-spec.md` |
| 反模式说明 | `references/anti-patterns.md` |
| 深度 FAQ | `references/faq-deep.md` |

---

## ❓ FAQ - 常见问题

### Q1：如何正确启动 ManualGen？

直接向 AI 描述您的需求（如"帮我生成这套系统的操作手册"），ManualGen 技能自动激活并执行入口清单：
1. AI 自动确定项目路径，读取接力棒
2. 从 EXPLORE 阶段开始自动推进状态机
3. 不需要输入任何 `/` 命令

如果 AI 未自动激活，可以明确说出"写手册"、"生成文档"等触发词。

### Q2：状态机卡住不推进怎么办？

如果状态机停止推进，AI 会在回复中输出阻塞原因。常见原因和处理方式：

| 原因 | 表现 | 处理方式 |
|------|------|---------|
| 信息不足 | AI 提示缺少项目信息 | 提供项目路径或补充描述 |
| 产物验证失败 | AI 提示缺少前置产物 | AI 会自动补充并重验 |
| 需要确认 | 处于 CONFIRM 阶段 | 回复"确认"或提出修改意见 |
| 接力棒异常 | AI 提示接力棒损坏 | 按提示初始化新接力棒 |

### Q3：CONFIRM 阶段需要做什么？

CONFIRM 阶段是用户确认文档生成范围和方向的关键节点。AI 会展示：
1. **模块列表**：将要生成文档的模块
2. **流程图统计**：各模块包含的流程图数量
3. **缺失清单**：已识别到的功能缺失项
4. **完整性评分**：GAP 阶段评估的综合评分

您需要选择：
- **通过** → 进入 RESOLVE/WRITE 阶段开始生成
- **修改** → 返回 ANALYZE 阶段调整分析
- **取消** → 终止流程

### Q4：如何中断正在执行的任务？

如果在 ManualGen 自动推进过程中有新的需求或问题，AI 会自动检测中断并展示 3 个选项：

1. **立即重置**：中断当前流程，回到 ANALYZE 阶段重新分析并包含新需求
2. **记入 TODO**：将新需求记入接力棒"待办清单"，当前流程完成后自动重新发起任务
3. **仅讨论**：继续当前任务，暂不调整或新增

选择对应选项后，AI 会按选择执行。

### Q5：产物验证失败如何处理？

AI 在每个阶段完成后会验证产物存在性和完整性。如果验证失败：
- AI 会明确输出缺少的产物和失败原因
- 当前阶段状态不变
- AI 会自动补充内容并重新验证
- 直到产物通过验证后才进入下一阶段

用户不需要做额外操作，只需等待 AI 完成修复和重验。

### Q6：多模块项目的最佳实践是什么？

对于多模块（5 个以上）的项目，ManualGen 会自动使用分批分析机制：

| 项目规模 | 建议的模块分批 | 处理方式 |
|---------|--------------|---------|
| 小（<3个模块） | 不分批，一次完成 | 直接分析全部模块 |
| 中（3-8个模块） | 每批 3-5 个模块 | 分批分析，批次间传递上下文 |
| 大（>8个模块） | 每批 3-5 个模块 | 分批分析，使用 _analysis_batch_index.md 管理 |

用户只需提供项目路径，AI 会自动处理分批逻辑。无需手动指定分批策略。

---

> 更多技术细节和边缘场景请参见深度 FAQ：`references/faq-deep.md`（10 个深度问题）。
> 常见错误用法和改进方式请参见反模式说明：`references/anti-patterns.md`（10 个反模式案例）。

---

**版本**: 5.1.0 | **最后更新**: 2026-05-28