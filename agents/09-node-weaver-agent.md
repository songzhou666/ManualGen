# NodeWeaver-Agent：节点级信息抽取 & 证据绑定（L1~L5 每批内 AI 抽取工作的核心）

> Skeleton-Agent 是批调度框架，NodeWeaver-Agent 是单批内真正做"读代码/读模板/读DB → 抽节点 → 绑证据 → 算置信度"的干活 AI。
> 两层关系：Skeleton 切批 + 落盘，NodeWeaver 处理单批抽取。

---

## 一、核心输出单元

每批处理完返回一个 `BatchResult`，结构固定：

```json
{
 "layer": "L3",
 "batch_tag": "L3_BATCH_02_MOD_002",
 "output_files": [
 {
 "path": "_kb/L3_functions/REG_001_搜索区.json", // L3 按 REGION 粒度落盘（REG_xxx_{区域名}.json）
 "content": {
 "schema_version": "6.2.0",
 "module": { "module_id": "MOD_002", "name": "订单管理", "display_name": "订单管理" },
 "functions": [ /* FUNCTION v6 节点 */ ],
 "elements": [ /* ELEMENT v6 节点 */ ],
 "evidences": [
 {
 "evidence_id": "E_L3_MOD002_014",
 "source_type": "frontend",
 "file_path": "src/views/order/Detail.vue",
 "line_numbers": [128, 136, 142],
 "snippet": "... onCancelOrder() { this.$confirm('是否取消...') ... }",
 "supports_node_ids": ["FN_021"],
 "extraction_method": "template_method_parse",
 "confidence": 0.92
 }
 ]
 }
 }
 ],
 "items_written": 6,
 "new_entity_references": ["ENT_订单", "ENT_订单明细"],
 "missing_upstream_notes": []
}
```

所有节点严格按照 [knowledge-base/04-graph-schema-v6.md] 定义的 v6 NODE schema，不允许额外字段。

---

## 二、证据绑定三原则

### 1. 节点必带≥1条 evidence
所有 FUNCTION / STEP / ELEMENT / ENTITY.fields 必须**至少引用一条证据**。0条证据的节点要么是纯推断，要么不应产生。

### 2. 证据 snippet 必须来自实际读文件
```
 正确：evidence.snippet = 文件第128-136行的方法代码（截取200字符内）
 错误：evidence.snippet = "页面有取消按钮" （没引用代码原文）
```

### 3. extraction_method 固定枚举
| extraction_method | 说明 | 对应 source_type |
|------------------|------|----------------|
| `template_method_parse` | Vue template 里读取 methods 中函数代码段 | frontend |
| `script_setup_parse` | `<script setup>` 函数代码段 | frontend |
| `route_meta_scan` | 路由 meta.roles / meta.title / meta.permission | frontend |
| `store_action_parse` | Pinia/Vuex 的 action 定义 | frontend+backend |
| `api_endpoint_scan` | 后端 Controller @RequestMapping / @PostMapping 等 | backend |
| `service_logic_scan` | Service 层方法 | backend |
| `entity_annotation_scan` | Entity/DTO @Column / @ApiModelProperty / @NotNull 等注解 | db_schema / backend |
| `schema_create_table` | 建表 SQL（CREATE TABLE ...） | db_schema |
| `docstring_scan` | 注释 /** */ | doc |
| `schema_inference` | 跨3处以上提到相同字段名，AI 聚合推理 | 不推荐（confidence 封顶0.6） |

---

## 三、置信度初算规则

每个节点（或 ENTITY.field）在写入时就按证据算 confidence（GRAPH Step6 会再做传播）：

```
单条证据得分（按 extraction_method）：
 schema_create_table / entity_annotation_scan → 0.95
 template_method_parse / script_setup_parse → 0.90
 api_endpoint_scan / service_logic_scan → 0.88
 store_action_parse → 0.82
 route_meta_scan → 0.85
 docstring_scan → 0.72
 schema_inference → 0.55

节点 confidence = clamp(
 证据分 max * 0.6 + min(证据数/2, 1.0) * 0.3 + (cross_source ? 0.1 : 0),
 0.3, 0.98
)
```

- cross_source：≥2 种 source_type 同时支持这个节点。
- schema_inference 单独一类：即使多个推断证据也不升 confidence（仍是0.6封顶）。

---

## 四、L2~L3 功能判定算法（避免"差不多就行"）

问题根源（v5 旧版）：看到页面右侧有个"操作栏"就写 CRUD 4个功能，按钮细节完全不验证。v6 严格按"先看有什么按钮→再看每个按钮对应 methods→再看后端→再组装 FUNCTION"。

```
L3 单页区域判定算法：
1. 读 template（template_method_parse）：
 - 找到所有 <el-button>、<a-button>、带 @click 的可点击元素
 - 每个按钮 → 生成一个 ELEMENT 节点（el-type=button，name=按钮显示文字，text=显示文字）
 - 映射 @click=methodName → 去 methods 里找对应函数名
2. 读 methods（script_setup_parse）：
 - 每个被绑定的 method → 读其代码体：
 a. 有没有调 confirm / 弹窗？ → FUNCTION.preconditions.REQUIRES_CONFIRM = true
 b. 有没有调 API？ → 映射到后端 endpoint（找 api/*.js 的 axios 请求）
 c. 有没有操作 store？ → ENTITY 关联（store action target）
 d. 成功后有没有跳转 / 刷新列表？ → post_conditions / 副作用
3. 读 router → 确认该页面 route.meta.roles：→ FUNCTION.preconditions.roles[] 可继承
4. 读 API 对应后端 Controller → OPERATES_ON(ENTITY) 绑定
5. 组装 FUNCTION 节点：
 - trigger_element = 步骤1生成的按钮 ELEMENT
 - steps = 把 methods 内部流程拆成 STEP（步骤 d=执行, b=后端调用, c=刷新 等）
6. evidence 覆盖以上 1/2/3/4 每项产生的证据 ID 列表
→ 这样生成的 FUNCTION：每个有**对应按钮**（ELEMENT）+ **对应后端逻辑**（STEP+证据）+ **权限**（roles）
→ 避免了"差不多的概括"，而是真实梳理按钮→方法→后端→实体的完整脉络
```

---

## 五、节点 ID 分配规范

每批内用局部递增，写文件时再归一化全局唯一（GRAPH Step1 会做）：

```
MODULE → MOD_001, MOD_002 ...（按 L0 顺序）
PAGE → PAGE_001, PAGE_002 ...（按 L1 全局递增）
REGION → REG_001, REG_002 ...（按 L2 全局递增）
FUNCTION → FN_001, FN_002 ...（按 L3 全局递增）
ELEMENT → ELM_0001, ELM_0002 ...（4位，按 L3 批顺序，因为量多）
STEP → STEP_00001 ...（5位）
ENTITY → ENT_001, ENT_002 ...
ROLE → ROLE_ADMIN, ROLE_USER ...（按原字符串规范）
```

> **不允许重复 ID**：写 L1_INDEX 时同步分配模块的号段区间，跨批 ID 冲突则由 Master 在 Skeleton-Agent 写完 Lx 后统一调 baton 维护 ID 计数器。

---

## 六、错误回退（不是"差不多就行"，是"实在不行记录原因再继续"）

遇到没法正确识别的情况：
1. 节点照样写，但 confidence 标低（<0.55）
2. evidence 里记录 schema_inference + 备注 `failed_to_parse: xxx`
3. 在 `_auto_decisions.md` 追加一条：
 ```
 [NODE_FN039_DEDUCE] 「客户画像」页「同步画像」按钮
 - 无法解析：对应 methods syncProfile() 为空函数无实现
 - 退而：依据 tooltip "同步CRM" 推断操作实体=客户，action=SYNC，confidence=0.48
 ```

**严禁的旧做法（已禁止）**：
- "这个按钮应该是删除吧？我就写 delete 了" → 必须依据代码判断，不然 confidence 强制 ≤ 0.45
- "反正用户不细看，写个大概" → GAP 会查，JUDGE 盲审会 catch
- 缺少 entity 就不写 OPERATES_ON → 标记 unsupported_entity=true，后续 GRAPH Step6 置信度传播

---

**版本**: 6.2.0-agent09
**最后更新**: 2026-08-11
