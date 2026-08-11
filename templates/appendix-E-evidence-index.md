# 附录 E 模板：证据索引（可追溯到源码行号）
> 本附录从 `graph/_evidence.json` 的反向索引生成（node_id → 多条 evidence，按文件分组）。
> **覆盖率要求**：≥ 证据总数的 80%（phase-protocol.md §14 INTEGRATE 阻断）；其余 20% 写在 §E.4「未覆盖的证据清单」。

---

## E.1 使用说明

### 如何用本附录定位到某段手册文字的证据来源？

1. 正文某段（例：「订单详情页顶部有【作废】按钮」）有脚注或内嵌标记「[EVID: FN_042 + ELEM_071]」。
2. 在本附录「§E.2 按节点 ID 索引」搜 FN_042 / ELEM_071 → 得到 `源文件路径 : 行号范围` + 代码片段摘要。
3. 打开你本地项目对应源码文件跳转到对应行号即可验证。

> 每段操作文字的最低证据要求：≥ 3 条不同 source_type（前端 template / 前端 script handler / 后端 controller / 后端 service / SQL DDL / 路由配置 / 权限注解 等 7 类）。

### 证据置信度代码（在每条证据后标注）

| 代码 | 含义 |
|------|------|
| 🟢 A 级 | ≥3 条不同 source_type 交叉验证一致（cross_verified=true） |
| 🟡 B 级 | 仅 1-2 种 source_type，但 AUTO_REVIEW 裁决 ACCEPTED 或 INFERRED_␣WARNING |
| 🔴 C 级 | 仍需人工复核（对应附录 C 第四清单） |

---

## E.2 按节点 ID 索引（主索引·按模块分组）

### 模块 1：{{ MODULE_001.name }}

#### 节点 FN_001：{{ 名称 }}

| 证据 ID | source_type | 源文件路径 | 起始行 | 结束行 | 代码片段（摘要，≤80字符） | 等级 |
|---------|-------------|-----------|:-----:|:-----:|-------------------------|:----:|
| EV_000121 | frontend_template | frontend/src/views/OrderList.vue | 28 | 31 | `<el-button type="danger" @click="batchDelete">作废</el-button>` | 🟢 |
| EV_000122 | frontend_script | frontend/src/views/OrderList.vue | 142 | 148 | `batchDelete() { this.$confirm(...) => api.cancelOrder(ids) }` | 🟢 |
| EV_000123 | backend_controller | backend/routers/order.py | 55 | 60 | `@router.post("/orders/cancel")  def cancel_order(ids: List[str])` | 🟢 |
| EV_000124 | permission_annotation | backend/routers/order.py | 54 | 54 | `@PreAuthorize("hasRole('ADMIN','OPERATOR')")` | 🟡 |

#### 节点 FN_002：…

…（同结构）

### 模块 2：{{ MODULE_002.name }}

…（同结构）

---

## E.3 按源文件反向索引（副索引·给代码维护者用）

| 源文件路径 | 关联节点数 | 主要关联节点 ID 列表（≤10 个，其余写「共 N 个」） |
|-----------|:----------:|-----------------------------------------------|
| frontend/src/views/OrderList.vue | 8 | FN_001, FN_002, ELEM_041~045, STEP_021 |
| backend/routers/order.py | 6 | FN_001, FN_002, ENT_007.field.price, … |
| … | … | … |

---

## E.4 未覆盖的证据清单（20% 允许，必须显式列原因）

| 证据 ID | 关联节点 | 为什么未进入 §E.2（原因） | 处理说明 |
|---------|---------|------------------------|---------|
| EV_000998 | FN_088（客户合并） | 代码片段过长（>500 行，且含敏感业务规则） | 仅记录路径：backend/services/customer_merge.py L120-430，必要时由用户在本地打开查看 |
| EV_000999 | ROLE_007（售后主管） | 从权限系统外部接口拉取，无本地源码对应 | 由系统管理员核实权限配置 |
| … | … | … | … |

**未覆盖率统计**：（未覆盖条目数）/（总证据数）= %（目标 ≤20%，超标则 INTEGRATE 阶段阻断返回补充）

---

## E.5 证据版本信息（便于增量生成时 diff）

| 项目 | 取值 |
|------|------|
| 手册生成时间 | 2026-08-11 hh:mm:ss |
| 关联的 git commit hash | （取 baton.meta.project_git_head_sha，无则写「本地未提交」） |
| 证据总数（total） | （= baton.graph.evidence_total） |
| 附录 E 已覆盖数 | 条 |
| 附录 E 覆盖率 | % |

---

**版本**: v6.1-appendix-E
**最后更新**: 2026-08-11
