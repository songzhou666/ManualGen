# RESOLVE + WRITE + INTEGRATE 阶段详情

---

## AUTO_REVIEW（AI 自主裁决，取代 v5 CONFIRM）

> 与 v5 核心区别：**不再展示面板让用户确认**，所有决策由 AI 按 chunk-07 §自主裁决规则自动完成。
> 裁决结果和依据全部写入 `_auto_decisions.md`（最终手册附录 C 呈现，保留事后人工复核链路）。

**职责**：
1. 低置信节点（confidence < 0.7）：逐节点走「补证据→传播→加警告」三选一路径
2. Snake 审查：incomplete_snake=true 的逐条补边或判定为"流程中断 + 附录C列示"
3. 权限覆盖率 < 60% 的模块：基于注解聚合 + 推断补全
4. ENTITY.fields 缺失 ≥ 40% 的模块：基于 JPA / MyBatis mapper XML / DTO 扫字段补全

**必做检查（不阻断流程，但必须已处理过）**：
- 以上 4 类节点/模块，每一项都经过至少 1 条自主裁决规则
- 处理后的节点/蛇/权限/字段都有明确结果标签（ACCEPTED_BY_PROPAGATION / INFERRED_WITH_WARNING / EVIDENCE_SUPPLEMENTED / HUMAN_REVIEW_REQUIRED）

**分支**（AI 自主决定，不等用户）：
- low_confidence_nodes 占比 ≤ 15% 或已处理 → 进入 RESOLVE
- 仍 > 15% 且 GAP 判定 P0 级 → 触发增量回灌（回到对应 Lx 补证据 → 再回 GRAPH → 再 GAP → 再 AUTO_REVIEW；熔断=3次后自动放行并附录 C 列示，与 chunk-09 §五一致）

---

## RESOLVE 阶段

**职责**：检测和解决多源信息冲突（6 类高频冲突全自主，**不询问用户**）。

### 冲突分级 & 决策策略（v6 替代 v5 P0 人工确认）
- C1 业务流程冲突：保守解优先（以路由/菜单可见性最高证据为准），次优解写附录 C
- C2 字段定义冲突：自动选 confidence 高者；差值<0.1选更新的源码版本
- C3 描述细节冲突：自动合并取最优（两条证据同时保留，证据表双向指向）
- C4 角色权限冲突：以 `@PreAuthorize` / `hasRole` / 路由 meta.roles 三个证据聚合后多数决
- C5 操作顺序冲突：以 2+ STEP.next_steps 有 80%+ 一致的路径为准
- C6 Snake 节点顺序冲突：以 data_creation_chain（L0层）+ 实体上下游 + 路由跳转三重证据投票

### 产物
`_resolution.md` + 合并结果**同步写回 graph/_nodes.json / _triples.json**（写回必做，避免下游用旧数据）



---

## WRITE 阶段

**职责**：使用独立子 Agent 生成用户版模块文档，隔离技术上下文污染。**v6 关键改动：模块信息全部从知识图谱（`_kb/graph/`）查询，不读源码、不读 v5 旧产物（`_extraction.md`/`_analysis.md`/`_function_survey.md` 在 v6 流程中不再产生）。**

### 为什么需要子 Agent？

> **核心问题**：主控在 L0~L5 六层提取阶段接触了大量技术内容（API端点、数据库、路由、源码），
> 如果继续由同一个 Agent 写用户手册，它会"记得"这些技术信息，导致手册变成技术文档。
>
> **解决方案**：拉起一个全新的子 Agent 来写模块文档，它只知道"要写什么功能"，
> 不知道"API是怎么实现的"。

### 执行方式

使用 `Task` 工具的 `general_purpose_task` 拉起子 Agent，query 中只传入以下信息：

```
你是一个用户操作手册编写专家。你只负责写一个功能模块的用户文档。

你完全不知道系统的技术实现细节：
- 你不知道有哪些API接口
- 你不知道数据库结构
- 你不知道后端服务名
- 你不知道代码架构
- 你不知道任何技术术语的底层原理

你知道的只有（从知识图谱按模块查询而来，不含实现细节）：
1. 模块名称：{模块名}
2. 模块用途：{从 graph 查询 MODULE 节点 + 关联 PAGE/FUNCTION 的语义描述}
3. 用户需要该模块做什么：{从 graph 查询该模块下 FUNCTION 节点 + Snake 关联场景}
4. 操作步骤与流程图素材：{从 graph 查询 MODULE→PAGE→REGION→FUNCTION→STEP 链 + ELEMENT/ROLE 关联}
5. 字段/权限/异常素材：{从 graph 查询 ENTITY.fields / ROLE 权限 / error_message}

你的任务是写一份用户手册的独立模块文件。

必须遵守：
1. 操作步骤必须描述"点击什么按钮、填写什么字段、看到什么结果"
2. 禁止出现任何API端点（如 POST /api/xxx）
3. 禁止出现任何HTTP代码块（如 ```http）
4. 禁止出现后端服务/数据库名（如 SQLite/Neo4j/FastAPI）
5. 禁止出现技术术语无解释（如 RAG/LLM/Embedding/Top-K）
6. 每个操作必须有1张 Mermaid 流程图（flowchart TD 或 flowchart LR）
7. 流程图必须包含：正常走向 + 分支判断 + 驳回/退回走向 + 终止走向
8. 流程图节点文字必须使用用户语言，不得出现代码术语
9. 必须有角色权限说明（谁可以操作这个功能）
10. 必须有字段说明表（含必填/规则/格式/示例）
11. 必须有风险提示（高危操作标注）
12. 必须有前置条件说明
13. 置信度 <0.7 且 AI 推断的节点：写 提示语，不写明确操作语句

 **Mermaid 语法强制规则**（违反会导致流程图渲染失败）：
12. 使用 `flowchart TD` 替代 `graph TD`（新版语法兼容性更好）
13. 节点文字中的中文引号用 `「」` 替代 `"..."`（弯引号会破坏解析器）
 - 正确：A[点击「创建知识库」按钮]
 - 错误：A[点击"创建知识库"按钮]
14. 菱形判断节点 `{...}` 内的文字避免使用 `?` `≥` `≤` 等特殊符号
15. 禁止在流程图节点中使用反斜杠 `\` 或未转义的引号

格式要求见 templates/user-manual.md
```

### 子 Agent 输入规范（v6 从图谱查）

| 输入项 | 来源（v6 graph 查询） | 说明 |
|:-------|:-----|:-----|
| 模块名称 | `_kb/graph/_nodes.json` 中 type=MODULE 节点 | 只传名称，不传任何技术细节 |
| 模块用途 | 从 MODULE 节点 + 关联 PAGE/FUNCTION 的语义字段聚合 | 1-2句话的用户视角描述 |
| 用户场景 | 从 MODULE→FUNCTION 关联 + 相关 Snake 场景提取 | 3-5个高频场景 |
| 操作步骤/流程图素材 | 从 MODULE→PAGE→REGION→FUNCTION→STEP 链查询 | 只传用户语言层素材 |
| 字段/权限/异常素材 | ENTITY.fields + ROLE 权限 + error_message 节点 | 用于字段表/权限说明/风险提示 |
| 输出路径 | `output_user_manual/_modules/{模块名}.md` | 写入文件 |

### 子 Agent 的上下文隔离

子 Agent **不得获取**以下信息：
- `_extraction.md`（API提取结果）
- `_analysis.md` 中的技术分析部分
- 项目源代码
- 任何 API 端点、数据库结构、配置文件

### 数量标准
- 每模块≥3个操作（挖掘用户高频场景）
- 每个操作必须配1张 Mermaid 流程图（不可共用）
- 字段说明表的必填/格式/示例列不得为空

### 产物
`output_user_manual/_modules/*.md`（每个模块一个文件）

---

## REFINE 阶段（强制回扫 — 子Agent模式）

**职责**：使用独立子 Agent 逐模块扫描检查，确保每模块达到标准。

### 为什么需要子 Agent？

> **核心问题**：如果由同一个 Agent 做 REFINE，它会认为"自己写得不错"，
> 发现不了流程图缺失、权限表缺失等问题。
>
> **解决方案**：子 Agent 只看到模块文件，不知道谁写的、怎么写出来的，
> 能够客观地发现缺陷。

### 执行方式

对每个 `output_user_manual/_modules/*.md` 文件，使用 `Task(general_purpose_task)` 拉起一个子 Agent，
每个子 Agent 只接收一个模块文件 + 检查清单：

```
你是一个文档质量检查员。你只负责检查一页文档的质量。

你完全不知道这个文档是谁写的、经历了哪些阶段。

你看到的只有：
1. 一个模块文件：{文件名}
2. 下面这份检查清单

请逐项检查该文件，对每个不合格项给出具体原因：

检查清单：
 是否包含 ≥1 个 Mermaid 流程图（```mermaid）？
 流程图是否包含正常/分支/驳回/终止走向？
 是否有 API 端点表（| POST /api/）或 HTTP 代码？
 操作步骤是描述界面操作（点击、填写）还是调用API？
 是否标注了哪些角色可以操作？
 是否包含风险提示或警示？
 是否有前置条件说明？
 是否有操作结果说明？
 是否有字段说明表（含必填/格式/示例）？

输出格式：
 [PASS/FAIL] Mermaid流程图: 原因
 [PASS/FAIL] 链路完整性: 原因
 [PASS/FAIL] API内容: 原因
 [PASS/FAIL] 界面操作: 原因
 [PASS/FAIL] 角色权限: 原因
 [PASS/FAIL] 风险提示: 原因
 [PASS/FAIL] 前置条件: 原因
 [PASS/FAIL] 操作结果: 原因
 [PASS/FAIL] 字段说明: 原因
```

### 处理子 Agent 的结果

> **写回协议（实测发现）**：对**同一个文件**的多处编辑**必须串行执行**（一次一处、完成后复核再下一处），
> 禁止对同一文件并行发起多个编辑操作——实测中并行 SearchReplace 会发生写回竞争，部分修改"diff 显示成功但未落盘"。
> 若需批量修改同一文件，遵循 Refiner-Agent 的原子写协议：先备份 `bak` → 写临时文件 `tmp` → 原子 rename 覆盖 → 复检内容。
> 不同文件的编辑可以并行，不受此限制。

- 如果子 Agent 返回 FAIL → **立即修复**该问题（写入模块文件）
- 所有 FAIL 修复后 → 重新拉起子 Agent 确认变 PASS
- 全部 PASS 后 → 记录到 `_refine_log.md`

### v6.3 GW 机器校验（子 Agent 检查之外的强制闭环）

> **为什么需要**：子 Agent 的"API 内容"检查是 AI 自评，实测会放水（E:\test_agent 手册 93 处
> API 泄漏在 REFINE 后仍通过）。子 Agent 检查只覆盖"内容质量"（软约束），
> **技术泄漏判定必须由机器执行**（强约束）。

```
1. 子 Agent 全部 PASS 后，主控运行：
   '{"project_path": "<项目>", "manual_path": "<手册或模块文件>"}' | python run.py scan_tech
   （工作目录：{Skill 目录}/manualgen_tools）
2. scan_tech 输出 P0 命中数 > 0 → GW 不通过 → 打回 REFINE 重写对应模块，禁止进入 REFERENCE_CHECK
3. scan_tech 输出 P0 = 0 → GW 通过，记录到 _refine_log.md
4. 最终手册合并完成后（INTEGRATE），必须再对最终手册运行一次 scan_tech 确认 P0=0
```

### 产物
`_refine_log.md`

---

## REFERENCE_CHECK 阶段（一致性检查）

**职责**：检查所有模块间的交叉引用、术语一致性和格式统一性。

### 执行操作
1. 读取所有 `output_user_manual/_modules/*.md` 文件
2. 检查跨模块引用是否有效（引用的模块名是否存在）
3. 检查术语一致性（同一概念在不同模块中名称是否统一）
4. 检查格式统一性（标题层级、表格格式、Mermaid风格是否一致）
5. 生成 `_reference_check.md`

### 产物
`_reference_check.md`

---

## INTEGRATE 阶段

**职责**：将所有模块完整合并为一份单文件手册，输出到项目根目录。

### 核心要求（违反=交付物不合格）

**1. 完整内联 — 禁止外部引用**
- 将每个 `output_user_manual/_modules/*.md` 的**全部内容**直接写入正文
- **禁止** "详细操作请参阅 xxx.md"
- **禁止** 任何指向 `output_user_manual/_modules/` 的链接
- 所有操作步骤、流程图、字段说明表、风险提示，全部直接写入手册

**2. 项目命名 — 按项目名称**
- 文件名：`{项目名称} 用户操作手册.md`
- 示例：`知识库管理系统 用户操作手册.md`

**3. 根目录输出 — 用户好找**
- 输出到项目根目录（`{项目路径}/`）
- 不要放在 `.agent/harness/` 里

**4. 由 _modules 合并生成（v6.3 强制 · 禁止另起炉灶）**
- 最终手册**必须**由 `output_user_manual/_modules/*.md` 的内容合并而成
- 若 `_modules/` 不存在或为空 → INTEGRATE 直接阻断（说明 WRITE 未执行，回 WRITE 补跑）
- 合并完成后必须运行机器校验（工作目录 manualgen_tools）：
  - `'{"project_path":"<项目>","manual_path":"<最终手册>"}' | python run.py scan_tech` → P0 命中数必须为 0
  - `'{"project_path":"<项目>"}' | python run.py coverage` → 无未覆盖模块
  - `'{"project_path":"<项目>"}' | python run.py verify` → 必须 PASS
  - 任一 FAIL → 不得交付，回对应阶段修复

### 执行内容
- 模块内容完整内联
- 封面目录生成
- 格式统一
- 保存中间件 `_integration.md` 到 `.agent/harness/`（供AUDIT审核）
- 输出交付件 `{项目名称} 用户操作手册.md` 到项目根目录（最终文件）

### 超长文档处理
如果完整手册超出上下文窗口，按业务域分批整合：
- 每批独立文件：`_integration-part1.md`, `_integration-part2.md` ...
- 主 `_integration.md` 作为总索引（但最终输出时仍需合并为单文件）

### 产物
- **中间产物**：`.agent/harness/_integration.md`（供AUDIT审核）
- **交付产物**：`{项目根目录}/{项目名称} 用户操作手册.md`