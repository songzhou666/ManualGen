#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ManualGen 硬校验工具层 (run.py) — v1.3.0
==========================================
定位：ManualGen v6.3 的「外部见证者」。所有可客观判定的事情（文件存在性、批次计数、
技术泄漏、覆盖完整性、产物清单）由本工具用确定性逻辑判定，AI 不得自述结果。

背景：v6.2 曾因全部约束为「AI 自我约束」（软约束）导致执行 AI 伪造接力棒、跳层
不落盘、技术参数泄漏进用户手册（E:\\test_agent 实测：baton 谎报 L2/L3/L4 共 38 批
done，但对应产物目录完全不存在，最终手册仅 435 行且通篇 API 端点）。本工具把
「工程骨架层」约束从 AI 手里接管，改为机器判定（强约束），与 conspect_tools /
medic_tools 的 CLI 工具层模式对齐。

用法（对齐 conspect/skill-medic CLI 约定，Windows PowerShell 请优先用管道）：
    cd {Skill 安装目录}/manualgen_tools
    '{"project_path": "E:/test_agent"}' | python run.py verify
    '{"project_path": "E:/test_agent", "manual_path": "E:/test_agent/xxx 用户操作手册.md"}' | python run.py scan_tech
    '{"project_path": "E:/test_agent"}' | python run.py check_deliverables
    '{"project_path": "E:/test_agent"}' | python run.py coverage
    '{"project_path": "E:/test_agent"}' | python run.py baton_fix
    '{"project_path": "E:/test_agent", "purge_kb": true}' | python run.py reset

Actions:
    verify              校验接力棒「声称已完成」的各层产物是否真实存在（PASS/FAIL）
    scan_tech           扫描手册/模块文档的技术泄漏（API端点/数据库名/参数名/HTTP代码）
    scan_flowcharts     校验每模块 ≥1 张非空 Mermaid 流程图 + 手册全文 ≥3 张（流程图硬门）
    check_deliverables  检查 v6 全部产物清单是否齐全（含附录 B~F，缺失即阻断）
    coverage            比对 L1 全部模块 vs 手册章节标题，输出未覆盖模块
    check_evidence      校验 L0~L3 源码证据（路径可解析、代码证据带行号、FUNCTION 不缺证据）
    normalize_evidence  把 L0~L3 的 path:line 字符串归一化为 graph/_evidence.json + 节点索引
    check_depth         检查操作深度与证据链（步数/流程图/节点或 EVD 引用/证据可解析）
    check_reports       检查阶段报告是否空壳（AUDIT 维度/逐模块评分/修订覆盖/缺口分级）
    baton_fix           从磁盘实际产物反推各层 completed 计数（total 只读，禁止改写）
    reset               备份并重置接力棒为 START（供全量重跑）
    ping                工具自检（目录可读性 / Python 版本，快速确认 CLI 可用）

退出码：0 = 全部 PASS；1 = 存在 FAIL（用于流程门禁阻断，AI 不得忽略）
异常/中断：结构化 JSON 错误 + 非零退出码（对齐 conspect_tools），不裸抛 traceback
"""
import argparse
import glob
import json
import logging
import os
import re
import shutil
import sys
from datetime import datetime

# 模块级日志器（对齐 conspect_tools：诊断日志走 stderr，不污染 stdout 的 JSON 结果）
logger = logging.getLogger("manualgen.run")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

# ==================== 常量定义 ====================

# 六层产物目录（相对 _kb/，os.path.join(kb, rel_dir) 使用；**/*.json 递归匹配子目录）
LAYER_DIRS = {
    "L1": ("L1_modules", "**/*.json"),
    "L2": ("L2_regions", "**/*.json"),
    "L3": ("L3_functions", "**/*.json"),
    "L4": ("L4_operations", "**/*.json"),
    "L5": ("L5_details", "**/*.json"),
}

# L5 五类子目录（字段/角色/元素/校验/聚合）
L5_SUBDIRS = ["ENTITY", "ROLE", "ELEMENT", "VALIDATION", "AGGREGATE"]

# 各层批次计数字段（"该层是否真的按批跑完"的机器判定口径）
# 只有 done == total 且 total 存在，才允许认定该层完成；total 由父层推导写入，AI 只能通过
# baton_fix 的 completed 计数反推，不得手改 total（否则分母会被抹成分子）。
BATCH_FIELDS = {
    "L1": ("modules_batches_total", "modules_batches_done"),
    "L2": ("pages_batches_total", "pages_batches_done"),
    "L3": ("regions_batches_total", "regions_batches_done"),
    "L4": ("functions_batches_total", "functions_batches_done"),
    "L5": ("operations_batches_total", "operations_batches_done"),
}

# ==================== 深度检查阈值（check_depth） ====================
# 依据用户手册质量要求：核心操作要有可执行步骤与流程图，证据要能回到源码行。
CORE_MIN_STEPS = 5          # core 类操作最少步骤数（G4 闸门要求）
MICRO_MIN_STEPS = 2         # micro 类操作（如“导航到某页”）最少步骤数
EVIDENCE_RESOLVABLE_MIN = 0.8   # 证据 file_path 可解析率下限
EVIDENCE_LINE_MIN = 0.5         # 代码类证据带行号比例下限

# 图谱 6 个必需文件
GRAPH_FILES = [
    "_nodes.json", "_triples.json", "_evidence.json",
    "_snakes.json", "_layer_index.json", "_quality.json",
]

# 阶段 → 报告文件映射（baton 声称进入该阶段后文件必须存在）
PHASE_FILES = {
    "GAP_ANALYSIS": "_gap_analysis.md",
    "AUTO_REVIEW": "_kb/_auto_decisions.md",
    "RESOLVE": "_resolution.md",
    "WRITE": None,          # 特殊处理：output_user_manual/_modules/*.md
    "REFINE": "_refine_log.md",
    "REFERENCE_CHECK": "_reference_check.md",
    "INTEGRATE": "_integration.md",
    "AUDIT": "_audit.md",
    "TODO_RESOLVE": "_todo_resolution.md",
    "JUDGE": "_judgment.md",
    "DONE": None,           # 特殊处理：最终手册 {项目名} 用户操作手册.md
}

# 阶段推进顺序（用于判断 baton.meta.state 已到达哪些阶段）
STATE_ORDER = [
    "START", "L0_SKELETON", "L1_MODULE", "L2_REGION", "L3_FUNCTION",
    "L4_OPERATION", "L5_DETAIL", "GRAPH_BUILD", "GAP_ANALYSIS",
    "AUTO_REVIEW", "RESOLVE", "WRITE", "REFINE", "REFERENCE_CHECK",
    "INTEGRATE", "AUDIT", "TODO_RESOLVE", "JUDGE", "DONE", "FAILED",
]

# ==================== 技术泄漏扫描模式 ====================
# (模式名, 正则, 级别, 说明)
TECH_PATTERNS = [
    ("api_table", r"\|[\s]*(?:POST|GET|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+/api/", "P0", "API端点表格"),
    ("api_inline", r"\b(?:POST|GET|PUT|DELETE|PATCH|OPTIONS)\s+/api/", "P0", "API端点行内"),
    ("http_block", r"```\s*http", "P0", "HTTP 代码块"),
    ("curl_cmd", r"\bcurl\s+(?:-[A-Za-z]\s+)?['\"]?-X", "P0", "curl 命令"),
    ("db_names", r"\b(?:SQLite|MySQL|PostgreSQL|Neo4j|Redis|FAISS|sqlite-vec|MongoDB|Elasticsearch|ClickHouse)\b", "P0", "数据库名"),
    ("framework", r"\b(?:FastAPI|Spring Boot|LangGraph|LangChain|Celery|Django|Flask|NestJS|Spring|MyBatis|JPA)\b", "P0", "后端框架名"),
    ("tech_param", r"\b(?:chunk_size|overlap|top_k|max_hops|temperature|similarity_threshold|use_hyde|llm_chunking|enable_thinking|enable_rewrite|llm_model|top_p|batch_size|embedding|relevance_score)\b", "P0", "技术参数名"),
    ("code_block", r"```\s*(?:python|javascript|java|go|sql|bash|shell|json|yaml|xml)\b", "P0", "程序语言代码块"),
    ("src_line", r"\b[a-zA-Z0-9_/\\\-]+\.(?:py|vue|js|jsx|ts|tsx|java|go|sql|php)\s*:\s*\d+", "P2", "源码行号引用"),
    ("local_port", r"\b(?:localhost|127\.0\.0\.1)\s*:\s*\d{2,5}", "P2", "本机端口引用"),
    ("tech_stack", r"\b(?:Vue 3|Vue3|Element Plus|React 18|React18|vite|webpack|Docker|docker-compose)\b", "P2", "技术栈名"),
]

# 附录 E 豁免区标题（证据索引设计上允许源码行号/代码片段，不参与技术泄漏扫描）
APPENDIX_E_HEADER = "## 附录 E"
APPENDIX_E_ALIASES = ("## 附录 E", "## 附录E", "## Appendix E", "## 附录 E：")

# 附录 B~F 清单（check_deliverables 用；F=未覆盖模块清单，core_priority 模式强制交付）
APPENDIX_FILES = [
    "appendix-B-permission-matrix.md",
    "appendix-C-AI-auto-decisions.md",
    "appendix-D-snake-flows.md",
    "appendix-E-evidence-index.md",
    "appendix-F-uncalled-modules.md",
]

# ==================== 流程图硬校验常量 ====================
# Mermaid 流程图代码块（flowchart TD/LR 或 stateDiagram-v2；graph TD 属禁用的旧语法）
MERMAID_BLOCK_RE = re.compile(r"```\s*mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
# 流程图声明行（允许 flowchart TD / flowchart LR / stateDiagram-v2，忽略大小写）
MERMAID_FLOW_RE = re.compile(r"^\s*(?:flowchart\s+(?:TD|LR|TB|RL)|stateDiagram-v2)\b", re.MULTILINE | re.IGNORECASE)
# 判定「图非空」：除声明行与纯装饰行外，至少存在一个节点/状态行（A-->B / A-.->B / A--oB / A[方框] / state "文本" as S 等）
MERMAID_CONTENT_RE = re.compile(
    r"(?:-->|->>|---|==>|-\.->|--o|--x)|\[[^\]]*\]|state\s+|\{[\s\S]*?\}",
    re.IGNORECASE,
)

# 层状态「完成」的合法值（文档 schema 统一用 completed / completed_with_pending，兼容历史 done）
DONE_STATUSES = {"done", "completed", "completed_with_pending"}

# 手册全文 Mermaid 下限（judge-agent 流程图可用性 20 分门槛：全文 ≥3 个 Mermaid）
MANUAL_MIN_MERMAID = 3

# ==================== 通用工具函数 ====================


def norm_path(p):
    """规范化路径：统一正斜杠，去掉引号包裹。"""
    if not p:
        return p
    p = str(p).strip().strip("\"'")
    return p.replace("\\", "/")


def load_json(path):
    """读取 JSON 文件，失败返回 None。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_json(path, data):
    """写入 UTF-8 JSON（自动建父目录），供 normalize_evidence 等生成器使用。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def count_files(pattern):
    """统计匹配 glob 模式的文件数（递归）。"""
    return len(glob.glob(pattern, recursive=True))


def path_exists(*parts):
    """拼接路径并判断是否存在。"""
    p = os.path.join(*[str(x) for x in parts if x])
    return os.path.exists(p)


def report(ok, title, details=None):
    """输出统一格式的校验报告。"""
    tag = "PASS" if ok else "FAIL"
    print("=" * 60)
    print(f"[{tag}] {title}")
    print("=" * 60)
    if details:
        for d in details:
            if isinstance(d, (list, tuple)):
                flag, msg = d[0], d[1]
            else:
                flag, msg = "?", d
            print(f"  - [{flag}] {msg}")
    return ok


def layer_status(baton, layer_key):
    """兼容两种接力棒 key 命名（L0 / L0_SKELETON），返回 (status, data)。"""
    layers = baton.get("layers", {})
    for k in (layer_key,):
        if k in layers:
            return layers[k].get("status"), layers[k]
    # 阶段名带后缀的 key
    full = {"L0": "L0_SKELETON", "L1": "L1_MODULE", "L2": "L2_REGION",
            "L3": "L3_FUNCTION", "L4": "L4_OPERATION", "L5": "L5_DETAIL"}.get(layer_key)
    if full and full in layers:
        return layers[full].get("status"), layers[full]
    return None, None


def state_reached(baton, state_name):
    """判断 baton.meta.state 是否已到达/越过某阶段。"""
    state = baton.get("meta", {}).get("state", "")
    if state not in STATE_ORDER:
        return False
    return STATE_ORDER.index(state) >= STATE_ORDER.index(state_name)


def get_layer_count(baton, layer_key, fields):
    """从接力棒层数据中取计数（兼容缺失字段）。"""
    _, data = layer_status(baton, layer_key)
    if not data:
        return None
    for f in fields:
        if f in data and data[f] is not None:
            return data[f]
    return None


def split_body_and_appendix_e(text):
    """把手册文本切分为「正文段」与「附录 E 段」。附录 E 为设计豁免区。

    兼容 `## 附录 E` / `## 附录E` / `## Appendix E` 三种写法，避免因标题格式差异
    把证据索引当成正文扫描，产生技术泄漏误报。
    """
    idx = -1
    for header in APPENDIX_E_ALIASES:
        pos = text.find(header)
        if pos != -1 and (idx == -1 or pos < idx):
            idx = pos
    if idx == -1:
        return text, ""
    return text[:idx], text[idx:]


def normalize_heading(line):
    """归一化标题：去 Markdown 标记、章节序号、全角空格与装饰符号。

    用于 coverage 比对，避免「1. 客户管理」「第一篇 客户管理」「客户管理｜概述」
    因序号/装饰未剥离而误判为未覆盖。
    """
    h = line.strip().lstrip("#").strip()
    h = re.sub(r"^第\s*[一二三四五六七八九十百零\d]+\s*[篇章节部分卷]\s*", "", h)
    h = re.sub(r"^[（(]?[一二三四五六七八九十\d]+[）)、.．:：]\s*", "", h)
    h = re.sub(r"[\s\u3000]+", "", h)
    return h.strip("：:|｜-—·")


# ==================== 证据链公共助手（check_evidence / normalize_evidence / check_depth 共用） ====================

CODE_EXTS = (".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".java", ".go", ".sql", ".php")
CONFIG_EXTS = (".json", ".yaml", ".yml", ".toml", ".ini", ".env", ".conf")
DOC_EXTS = (".md", ".txt", ".rst")


def parse_evidence_ref(ref):
    """解析证据引用字符串 → (path, line_start, line_end)。

    支持三种写法：`a/b.vue:12-30`、`a/b.py:12`、`README.md`。
    Windows 盘符（E:/x.py:12）不会被误切，因为盘符后的冒号不跟数字。
    """
    s = (ref or "").strip()
    if not s:
        return "", None, None
    m = re.match(r"^(?P<path>.+?):(?P<start>\d+)(?:-(?P<end>\d+))?$", s)
    if not m:
        return s, None, None
    return m.group("path"), int(m.group("start")), int(m.group("end") or m.group("start"))


def source_type_of(path):
    """按扩展名判定证据来源类型。"""
    p = (path or "").lower()
    if p.endswith(CODE_EXTS):
        return "code_file"
    if p.endswith(CONFIG_EXTS):
        return "config_file"
    if p.endswith(DOC_EXTS):
        return "doc_file"
    return "other"


def resolve_source_path(project, path):
    """把证据里的相对路径解析为项目内实际路径；不存在返回 None。"""
    p = (path or "").strip().replace("\\", "/")
    if not p:
        return None
    full = p if os.path.isabs(p) else os.path.join(project, p)
    return full if os.path.exists(full) else None


def iter_layer_evidence(project):
    """遍历 L0~L3 层产物中的源码证据引用，产出 (layer, node_id, ref)。

    各层证据字段口径：
      L0  meta.evidence（PROJECT） / modules[].evidence（MOD_xxx）
      L1  modules/*.json 的 evidence（MOD_xxx）
      L2  regions[].evidence（REG_xxx）
      L3  functions[].frontend_evidence / backend_evidence（FN_xxx）
    """
    kb = os.path.join(project, ".agent", "harness", "_kb")
    l0 = load_json(os.path.join(kb, "L0_skeleton.json"))
    if isinstance(l0, dict):
        for ref in ((l0.get("meta") or {}).get("evidence") or []):
            if isinstance(ref, str):
                yield "L0", "PROJECT", ref
        for mod in (l0.get("modules") or []):
            if isinstance(mod, dict):
                for ref in (mod.get("evidence") or []):
                    if isinstance(ref, str):
                        yield "L0", mod.get("id") or "?", ref

    for fp in sorted(glob.glob(os.path.join(kb, "L1_modules", "*.json"))):
        data = load_json(fp)
        if isinstance(data, dict):
            for ref in (data.get("evidence") or []):
                if isinstance(ref, str):
                    yield "L1", data.get("id") or "?", ref

    for fp in sorted(glob.glob(os.path.join(kb, "L2_regions", "*.json"))):
        data = load_json(fp)
        if isinstance(data, dict):
            for reg in (data.get("regions") or []):
                if isinstance(reg, dict):
                    for ref in (reg.get("evidence") or []):
                        if isinstance(ref, str):
                            yield "L2", reg.get("id") or "?", ref

    for fp in sorted(glob.glob(os.path.join(kb, "L3_functions", "*.json"))):
        data = load_json(fp)
        if isinstance(data, dict):
            for fn in (data.get("functions") or []):
                if isinstance(fn, dict):
                    for key in ("frontend_evidence", "backend_evidence"):
                        for ref in (fn.get(key) or []):
                            if isinstance(ref, str):
                                yield "L3", fn.get("id") or "?", ref


def find_functions_missing_evidence(project):
    """返回缺少任何源码证据的 FUNCTION 节点 ID 列表（L3 必填项）。"""
    kb = os.path.join(project, ".agent", "harness", "_kb")
    missing = []
    for fp in sorted(glob.glob(os.path.join(kb, "L3_functions", "*.json"))):
        data = load_json(fp)
        if not isinstance(data, dict):
            continue
        for fn in (data.get("functions") or []):
            if not isinstance(fn, dict):
                continue
            refs = (fn.get("frontend_evidence") or []) + (fn.get("backend_evidence") or [])
            if not [r for r in refs if isinstance(r, str) and r.strip()]:
                missing.append(fn.get("id") or "?")
    return missing



def scan_text_for_tech(text, patterns):
    """对文本执行技术模式扫描，返回 (P0 命中列表, P2 命中列表)。每个命中为 (模式名, 描述, 行号+片段)。"""
    p0_hits, p2_hits = [], []
    for name, pattern, level, desc in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            line_no = text[:m.start()].count("\n") + 1
            snippet = m.group(0).strip()
            if len(snippet) > 60:
                snippet = snippet[:60] + "..."
            hit = f"第{line_no}行: {snippet}"
            entry = (name, desc, hit)
            if level == "P0":
                p0_hits.append(entry)
            else:
                p2_hits.append(entry)
    return p0_hits, p2_hits


# ==================== Action: verify ====================


def cmd_verify(params):
    """校验接力棒各层「声称完成」与实际磁盘产物是否一致。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    harness = os.path.join(project, ".agent", "harness")
    kb = os.path.join(harness, "_kb")
    baton_path = os.path.join(harness, "_baton.json")

    if not os.path.exists(baton_path):
        return report(False, f"接力棒不存在: {baton_path}",
                      [("P0", "流程尚未初始化，或接力棒被误删")])
    baton = load_json(baton_path)
    if not baton:
        return report(False, "接力棒 JSON 解析失败",
                      [("P0", "接力棒损坏，按 baton-protocol §三 恢复流程处理")])

    checks = []
    ok_all = True
    meta = baton.get("meta", {})
    print(f"项目: {meta.get('project_name', '?')} | 状态: {meta.get('state', '?')}")

    # --- 层产物存在性校验 ---
    for lk, (rel_dir, pattern) in LAYER_DIRS.items():
        status, ldata = layer_status(baton, lk)
        if status not in DONE_STATUSES:
            continue
        layer_dir = os.path.join(kb, rel_dir)
        file_count = count_files(os.path.join(layer_dir, pattern)) if os.path.isdir(layer_dir) else 0
        label = lk  # lk 本身就是 "L1" 形式
        if file_count == 0:
            ok_all = False
            checks.append(("P0", f"{label} 声称 done，但产物目录 {rel_dir} 为空/不存在"))
        else:
            # 计数一致性：声称完成的节点数不能大于磁盘文件数
            claimed = None
            if lk == "L1":
                claimed = get_layer_count(baton, "L1", ["modules_completed", "modules_total"])
            elif lk == "L3":
                claimed = get_layer_count(baton, "L3", ["functions_completed", "functions_total_expected"])
            elif lk == "L4":
                claimed = get_layer_count(baton, "L4", ["operations_completed", "operations_total_expected"])
            if claimed and file_count < claimed:
                ok_all = False
                checks.append(("P0", f"{label} 声称完成 {claimed} 个节点，但磁盘仅 {file_count} 个文件（计数造假嫌疑）"))
            else:
                cnt_msg = f"（声称 {claimed} / 磁盘 {file_count}）" if claimed else f"（磁盘 {file_count} 个文件）"
                checks.append(("OK", f"{label} 产物存在 {cnt_msg}"))

        # 批次一致性：声称完成但批次没跑完 → 阻断。文件存在只说明"做了几批"，
        # 不能说明"全部批次都做完了"，这里补上 v6.3 缺失的那半边判定。
        total_key, done_key = BATCH_FIELDS[lk]
        btotal = (ldata or {}).get(total_key)
        bdone = (ldata or {}).get(done_key)
        if not btotal:
            ok_all = False
            checks.append(("P0", f"{label} 声称完成，但接力棒缺少 {total_key}（无法证明批次已全部跑完）"))
        elif bdone is None:
            ok_all = False
            checks.append(("P0", f"{label} 声称完成，但接力棒缺少 {done_key}"))
        elif bdone < btotal:
            ok_all = False
            checks.append(("P0", f"{label} 批次未跑完：{done_key}={bdone} < {total_key}={btotal}"))
        else:
            checks.append(("OK", f"{label} 批次已跑完（{bdone}/{btotal}）"))

    # --- L5 子目录校验（空目录不算覆盖，必须有实际产物文件） ---
    status, _ = layer_status(baton, "L5")
    if status in DONE_STATUSES:
        present = [d for d in L5_SUBDIRS
                   if count_files(os.path.join(kb, "L5_details", d, "*.json")) > 0]
        missing = [d for d in L5_SUBDIRS if d not in present]
        if present:
            checks.append(("OK", f"L5 子目录有产物: {', '.join(present)}"))
        if missing:
            ok_all = False
            checks.append(("P0", f"L5 声称 done 但子目录无产物文件: {', '.join(missing)}"))

    # --- 图谱 6 文件校验（存在 + 合法 JSON，防止写一半崩溃后带病推进） ---
    if state_reached(baton, "GRAPH_BUILD"):
        missing_g = [f for f in GRAPH_FILES if not path_exists(kb, "graph", f)]
        if missing_g:
            ok_all = False
            checks.append(("P0", f"GRAPH_BUILD 声称完成但图谱文件缺失: {', '.join(missing_g)}"))
        else:
            broken = [f for f in GRAPH_FILES
                      if load_json(os.path.join(kb, "graph", f)) is None]
            if broken:
                ok_all = False
                checks.append(("P0", f"图谱文件存在但 JSON 非法（可能写一半崩溃）: {', '.join(broken)}；回 GRAPH_BUILD 重写"))
            else:
                checks.append(("OK", "graph 6 文件齐全且 JSON 合法"))

    # --- 阶段报告文件校验 ---
    for phase, fname in PHASE_FILES.items():
        if not state_reached(baton, phase):
            continue
        if fname is None:
            continue  # WRITE/DONE 特殊处理
        fpath = os.path.join(harness, fname)
        if not os.path.exists(fpath):
            ok_all = False
            checks.append(("P0", f"阶段 {phase} 已声称进入，但报告文件缺失: {fname}"))
        else:
            checks.append(("OK", f"阶段 {phase} 报告存在: {fname}"))

    # --- WRITE 阶段：模块文档必须存在 ---
    if state_reached(baton, "WRITE"):
        modules_dir = os.path.join(project, "output_user_manual", "_modules")
        mod_count = count_files(os.path.join(modules_dir, "*.md")) if os.path.isdir(modules_dir) else 0
        if mod_count == 0:
            ok_all = False
            checks.append(("P0", "WRITE 声称完成，但 output_user_manual/_modules/ 下没有任何模块文档（WRITE 隔离机制未执行）"))
        else:
            checks.append(("OK", f"WRITE 模块文档存在: {mod_count} 篇"))

    # --- DONE 阶段：最终手册必须存在于项目根目录 ---
    if baton.get("meta", {}).get("state") == "DONE":
        manual_name = params.get("manual_name") or f"{meta.get('project_name', '')} 用户操作手册.md"
        manual_path = os.path.join(project, manual_name)
        if not os.path.exists(manual_path):
            ok_all = False
            checks.append(("P0", f"DONE 但最终手册不存在于项目根目录: {manual_name}"))
        else:
            checks.append(("OK", f"最终手册存在: {manual_name}"))

    return report(ok_all, "verify 结果", checks)


# ==================== Action: scan_tech ====================


def cmd_scan_tech(params):
    """扫描手册/模块文档中的技术泄漏（API端点/数据库名/参数名等）。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    manual_path = norm_path(params.get("manual_path") or params.get("file"))
    if not manual_path and project:
        meta = load_json(os.path.join(project, ".agent", "harness", "_baton.json")) or {}
        manual_path = os.path.join(project, f"{meta.get('meta', {}).get('project_name', '')} 用户操作手册.md")
    if not manual_path or not os.path.exists(manual_path):
        return report(False, f"手册文件不存在: {manual_path}")

    with open(manual_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 附录 E 为设计豁免区（证据索引允许源码行号/代码片段）
    exempt_e = params.get("exclude_appendix_e", True)
    scan_text = text
    if exempt_e:
        body, appendix_e = split_body_and_appendix_e(text)
        scan_text = body
        if appendix_e.strip():
            print(f"[INFO] 已豁免「{APPENDIX_E_HEADER}」段（设计允许的技术内容）")

    p0_hits, p2_hits = scan_text_for_tech(scan_text, TECH_PATTERNS)

    # 业务白名单：某些系统本身就是 Redis/MySQL 管理工具，手册里出现这些词是正常业务描述。
    # allow_terms 命中的片段放行（不参与 P0/P2 判定），放行数量在输出中披露。
    allow_terms = [str(t).strip().lower() for t in (params.get("allow_terms") or []) if str(t).strip()]
    allowed_count = 0
    if allow_terms:
        def _allowed(hit):
            """命中片段包含任一白名单词则放行。"""
            text_hit = hit[2].lower()
            return any(t in text_hit for t in allow_terms)

        before = len(p0_hits) + len(p2_hits)
        p0_hits = [h for h in p0_hits if not _allowed(h)]
        p2_hits = [h for h in p2_hits if not _allowed(h)]
        allowed_count = before - len(p0_hits) - len(p2_hits)

    # 去重（同一模式同一行只报一次）+ 按模式分组（便于 AI 按类定位打回）
    def group_dedup(hits):
        """按模式名分组去重，返回 [(模式名, 描述, [命中片段...])]。"""
        seen, grouped = set(), {}
        for name, desc, hit in hits:
            key = (name, hit)
            if key in seen:
                continue
            seen.add(key)
            grouped.setdefault(name, (desc, []))[1].append(hit)
        return grouped

    g0 = group_dedup(p0_hits)
    g2 = group_dedup(p2_hits)

    ok = len(p0_hits) == 0
    details = []
    if allowed_count:
        details.append(("OK", f"按 allow_terms 放行业务词 {allowed_count} 处（{', '.join(allow_terms)}）"))
    if not g0:
        details.append(("OK", "未发现 P0 级技术泄漏（API端点/HTTP代码/数据库名/框架名/参数名/代码块）"))
    else:
        total = sum(len(v[1]) for v in g0.values())
        details.append(("P0", f"发现 {total} 处 P0 级技术泄漏，按模式分组如下（命中即 GW/AUDIT 阻断，打回 REFINE）"))
        for name, (desc, hits) in g0.items():
            details.append(("P0", f"[{name}] {desc} — {len(hits)} 处"))
            for h in hits[:8]:
                details.append(("P0", f"  {h}"))
            if len(hits) > 8:
                details.append(("P0", f"  ... {name} 其余 {len(hits) - 8} 处省略"))
    if g2:
        total2 = sum(len(v[1]) for v in g2.values())
        details.append(("P2", f"发现 {total2} 处 P2 提示项（不阻断，建议清理）"))
        for name, (desc, hits) in g2.items():
            details.append(("P2", f"[{name}] {desc} — {len(hits)} 处"))
            for h in hits[:3]:
                details.append(("P2", f"  {h}"))
            if len(hits) > 3:
                details.append(("P2", f"  ... {name} 其余 {len(hits) - 3} 处省略"))
    return report(ok, f"scan_tech 结果（{os.path.basename(manual_path)}）", details)


# ==================== Action: scan_flowcharts ====================


def extract_mermaid_blocks(text):
    """提取文本中的所有 Mermaid 代码块，返回 (声明行, 块内容) 列表。块类型由调用方判定（flowchart/stateDiagram 合法，graph 禁用）。"""
    blocks = []
    for m in MERMAID_BLOCK_RE.finditer(text):
        content = m.group(1).strip()
        if not content:
            continue
        blocks.append((content.splitlines()[0].strip(), content))
    return blocks


def mermaid_nonempty(block):
    """判定 Mermaid 流程图块是否有实际内容（含节点/连线/状态，而非只有声明行）。"""
    lines = [ln for ln in block.splitlines() if ln.strip() and not ln.strip().startswith("%%")]
    return len(lines) >= 2 and bool(MERMAID_CONTENT_RE.search(block))


def count_operation_sections(text):
    """统计模块文档中的操作小节数。

    按模板约定：操作小节是「## 详细操作步骤」章节下的 ### 三级标题（{操作名称1/2/...}）。
    取该章节到下一个 ## 标题之间的 ### 数量，避免把「功能简介/操作前准备/注意事项」下的
    ### 子标题误计为操作。
    """
    step_m = re.search(r"^##\s*详细操作步骤\s*$", text, re.MULTILINE)
    if not step_m:
        return 0
    ends = [m.start() for m in re.finditer(r"^##\s", text, re.MULTILINE) if m.start() > step_m.end()]
    end = min(ends) if ends else len(text)
    section = text[step_m.end():end]
    return len(re.findall(r"^###\s+\S", section, re.MULTILINE))


def cmd_scan_flowcharts(params):
    """流程图硬门：每模块文档 ≥1 张非空 Mermaid 流程图；最终手册全文 ≥3 张 Mermaid。

    机器判定（强约束），堵住「模块文档写满文字但没有流程图」的偷懒路径：
    - 扫描 output_user_manual/_modules/*.md，逐篇提取 Mermaid 代码块
    - 每篇模块文档：≥1 张非空流程图（flowchart TD/LR 或 stateDiagram-v2，graph TD 禁用）
    - 最终手册（若存在）：全文 Mermaid ≥3 张（judge-agent 流程图可用性门槛）
    任一 FAIL 即退出码 1，AI 不得自述「流程图已画」代替本检查。
    """
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    modules_dir = os.path.join(project, "output_user_manual", "_modules")
    checks = []
    ok_all = True

    # --- 模块文档逐篇校验 ---
    mod_files = sorted(glob.glob(os.path.join(modules_dir, "*.md"))) if os.path.isdir(modules_dir) else []
    if not mod_files:
        return report(False, f"output_user_manual/_modules/ 下无模块文档（目录: {modules_dir}）",
                      [("P0", "WRITE 隔离机制未执行，模块文档缺失")])

    for fp in mod_files:
        name = os.path.basename(fp)
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()
        blocks = extract_mermaid_blocks(text)
        if not blocks:
            ok_all = False
            checks.append(("P0", f"{name}: 0 张 Mermaid 流程图（每模块必须 ≥1 张）"))
            continue
        # 非空检查 + 语法检查（graph TD 禁用）
        bad = []
        for decl, block in blocks:
            if re.search(r"^\s*graph\s+", block, re.MULTILINE | re.IGNORECASE):
                bad.append(f"{decl} 使用了禁用的 graph 旧语法（必须 flowchart TD/LR）")
                continue
            if not MERMAID_FLOW_RE.search(block):
                bad.append(f"{decl} 不是流程图声明（必须 flowchart TD/LR 或 stateDiagram-v2）")
                continue
            if not mermaid_nonempty(block):
                bad.append(f"{decl} 为空图（只有声明行，无节点/连线）")
        if bad:
            ok_all = False
            checks.append(("P0", f"{name}: {len(blocks)} 张图但含问题 -> {'; '.join(bad[:3])}"))
        else:
            checks.append(("OK", f"{name}: {len(blocks)} 张非空 Mermaid 流程图"))

        # 操作级校验：每个操作小节必须有 ≥1 张有效流程图（chunk-04 约束：每个操作配1张，不可共用）
        valid_count = sum(1 for b in blocks
                          if MERMAID_FLOW_RE.search(b[1]) and mermaid_nonempty(b[1]))
        op_count = count_operation_sections(text)
        if op_count > 0 and valid_count < op_count:
            ok_all = False
            checks.append(("P0", f"{name}: {op_count} 个操作小节，仅 {valid_count} 张有效流程图（每个操作必须 ≥1 张，不可共用）"))

    # --- 最终手册全文校验（≥3 张） ---
    manual_path = norm_path(params.get("manual_path") or params.get("file"))
    if not manual_path:
        meta = load_json(os.path.join(project, ".agent", "harness", "_baton.json")) or {}
        manual_path = os.path.join(project, f"{meta.get('meta', {}).get('project_name', '')} 用户操作手册.md")
    if os.path.exists(manual_path):
        with open(manual_path, "r", encoding="utf-8") as f:
            manual_text = f.read()
        # 全文统计口径与模块级一致：只算合法声明 + 非空图（空图不能凑满门槛）
        m_count = len([b for b in extract_mermaid_blocks(manual_text)
                       if MERMAID_FLOW_RE.search(b[1]) and mermaid_nonempty(b[1])])
        if m_count < MANUAL_MIN_MERMAID:
            ok_all = False
            checks.append(("P0", f"最终手册 Mermaid 流程图 {m_count} 张 < {MANUAL_MIN_MERMAID} 张（judge-agent 门槛，全文必须 ≥3 张）"))
        else:
            checks.append(("OK", f"最终手册 Mermaid 流程图 {m_count} 张 ≥ {MANUAL_MIN_MERMAID} 张"))
    else:
        checks.append(("P2", f"最终手册未找到（{os.path.basename(manual_path) or manual_path}），跳过全文校验"))

    return report(ok_all, "scan_flowcharts 结果（流程图硬门）", checks)


# ==================== Action: check_deliverables ====================


def cmd_check_deliverables(params):
    """检查 v6 全部产物清单是否齐全（缺失即阻断）。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    harness = os.path.join(project, ".agent", "harness")
    kb = os.path.join(harness, "_kb")

    checks = []
    ok_all = True

    # 核心 kb 产物（目录类必须非空才算存在，防止空目录/空壳目录蒙混）
    kb_required = [
        ("L0_skeleton.json", os.path.join(kb, "L0_skeleton.json"), "file"),
        ("L0_skeleton_report.md", os.path.join(kb, "L0_skeleton_report.md"), "file"),
        ("L1_index.json", os.path.join(kb, "L1_index.json"), "file"),
        ("L1 模块目录", os.path.join(kb, "L1_modules"), "dir"),
        ("L2 区域目录", os.path.join(kb, "L2_regions"), "dir"),
        ("L3 功能目录", os.path.join(kb, "L3_functions"), "dir"),
        ("L4 操作目录", os.path.join(kb, "L4_operations"), "dir"),
        ("L5 细节目录", os.path.join(kb, "L5_details"), "dir"),
    ]
    for name, p, kind in kb_required:
        if kind == "file":
            exists = os.path.exists(p)
        else:
            # 目录必须包含至少一个 .json 产物文件，空目录 = 未执行
            exists = count_files(os.path.join(p, "**", "*.json")) > 0
        if not exists:
            ok_all = False
            checks.append(("P0", f"kb 产物缺失或为空: {name}"))
        else:
            checks.append(("OK", f"kb 产物存在: {name}"))

    # 图谱 6 文件
    for gf in GRAPH_FILES:
        p = os.path.join(kb, "graph", gf)
        if os.path.exists(p):
            checks.append(("OK", f"graph/{gf}"))
        else:
            ok_all = False
            checks.append(("P0", f"graph/{gf} 缺失"))

    # 模块文档
    modules_dir = os.path.join(project, "output_user_manual", "_modules")
    mod_count = count_files(os.path.join(modules_dir, "*.md")) if os.path.isdir(modules_dir) else 0
    if mod_count > 0:
        checks.append(("OK", f"模块文档 {mod_count} 篇"))
    else:
        ok_all = False
        checks.append(("P0", "output_user_manual/_modules/ 无模块文档（WRITE 未执行）"))

    # 附录 B~F（5 个；F=未覆盖模块清单，core_priority 模式强制交付）
    appendix_dir = os.path.join(project, "output_user_manual", "_appendix")
    for ap in APPENDIX_FILES:
        p = os.path.join(appendix_dir, ap)
        if os.path.exists(p):
            checks.append(("OK", f"附录 {ap}"))
        else:
            ok_all = False
            checks.append(("P0", f"附录 {ap} 缺失"))

    return report(ok_all, "check_deliverables 结果", checks)


# ==================== Action: coverage ====================


def cmd_coverage(params):
    """比对 L1 全部模块 vs 手册章节标题，输出未覆盖模块。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    manual_path = norm_path(params.get("manual_path") or params.get("file"))
    if not project:
        return report(False, "缺少 project_path 参数")
    kb = os.path.join(project, ".agent", "harness", "_kb")

    # 收集 L1 模块名（优先 L1_index.json，其次 L1_modules/*.json）
    modules = []
    l1_index = load_json(os.path.join(kb, "L1_index.json"))
    if l1_index and isinstance(l1_index, list):
        modules = [m.get("name", "") for m in l1_index]
    if not modules:
        for fp in sorted(glob.glob(os.path.join(kb, "L1_modules", "*.json"))):
            m = load_json(fp)
            if m and m.get("name"):
                modules.append(m["name"])

    # 读取手册
    if not manual_path:
        meta = load_json(os.path.join(project, ".agent", "harness", "_baton.json")) or {}
        manual_path = os.path.join(project, f"{meta.get('meta', {}).get('project_name', '')} 用户操作手册.md")
    if not os.path.exists(manual_path):
        return report(False, f"手册文件不存在: {manual_path}")
    with open(manual_path, "r", encoding="utf-8") as f:
        text = f.read()

    # 提取所有标题行（归一化：去 #、章节序号、空格与装饰符）
    headings = set()
    for line in text.splitlines():
        if line.strip().startswith("#"):
            h = normalize_heading(line)
            if h:
                headings.add(h)

    # 覆盖比对：模块名必须完整出现在某个标题中。
    # 只保留「模块名 ⊂ 标题」方向；反向（标题 ⊂ 模块名）会把「客户」这种短标题
    # 误判成覆盖了「客户管理」，是 v6.3 coverage 的假 PASS 通道。
    missing, covered = [], []
    for mod in modules:
        norm_mod = normalize_heading(mod)
        if norm_mod and any(norm_mod in h for h in headings):
            covered.append(mod)
        else:
            missing.append(mod)

    ok = len(missing) == 0
    details = [
        ("OK", f"L1 模块总数: {len(modules)}"),
        ("OK", f"手册已覆盖: {len(covered)} 个模块"),
    ]
    for m in covered:
        details.append(("OK", f"已覆盖: {m}"))
    if missing:
        for m in missing:
            details.append(("P0", f"未覆盖: {m}（AUDIT ⑪ 硬门不通过，回 GAP_ANALYSIS 补齐）"))
    return report(ok, "coverage 结果", details)


def _summarize_layer_evidence(project):
    """汇总 L0~L3 源码证据引用：总数、分层计数、节点索引、不可解析、代码缺行号。"""
    total = 0
    unresolvable, no_line = [], []
    node_sources = {}
    per_layer = {}
    for layer, node_id, ref in iter_layer_evidence(project):
        total += 1
        per_layer[layer] = per_layer.get(layer, 0) + 1
        node_sources.setdefault(node_id, []).append(ref)
        path, start, _ = parse_evidence_ref(ref)
        if resolve_source_path(project, path) is None:
            unresolvable.append(f"{node_id} {ref}")
        elif source_type_of(path) == "code_file" and start is None:
            no_line.append(f"{node_id} {ref}")
    return {
        "total": total,
        "per_layer": per_layer,
        "node_sources": node_sources,
        "unresolvable": unresolvable,
        "no_line": no_line,
    }


def _collect_layer_node_ids(project):
    """收集 L0~L3 中出现的所有节点 ID，用于判断 L4 引用是否指向已知节点。"""
    kb = os.path.join(project, ".agent", "harness", "_kb")
    ids = set()
    l0 = load_json(os.path.join(kb, "L0_skeleton.json"))
    if isinstance(l0, dict):
        for mod in (l0.get("modules") or []):
            if isinstance(mod, dict) and mod.get("id"):
                ids.add(mod["id"])
    for fp in glob.glob(os.path.join(kb, "L1_modules", "*.json")):
        data = load_json(fp)
        if isinstance(data, dict) and data.get("id"):
            ids.add(data["id"])
        for pg in ((data or {}).get("pages") or []) if isinstance(data, dict) else []:
            if isinstance(pg, dict) and pg.get("id"):
                ids.add(pg["id"])
    for fp in glob.glob(os.path.join(kb, "L2_regions", "*.json")):
        data = load_json(fp)
        if isinstance(data, dict) and data.get("page_id"):
            ids.add(data["page_id"])
        for reg in ((data or {}).get("regions") or []) if isinstance(data, dict) else []:
            if isinstance(reg, dict) and reg.get("id"):
                ids.add(reg["id"])
    for fp in glob.glob(os.path.join(kb, "L3_functions", "*.json")):
        data = load_json(fp)
        for fn in ((data or {}).get("functions") or []) if isinstance(data, dict) else []:
            if isinstance(fn, dict) and fn.get("id"):
                ids.add(fn["id"])
    return ids


# ==================== Action: check_depth ====================


def cmd_check_depth(params):
    """检查产物「内容深度」：操作步数、流程图、证据引用、证据可解析性。

    两种模式（按图谱是否已归一化自动切换）：
      - **预图谱模式**（G4，尚无 graph/_evidence.json）：L4 的 evidence_refs 允许写
        节点 ID（FN_/REG_/PAGE_/MOD_，L4 阶段 EVD 尚不存在），但引用节点必须存在、
        必须包含本操作自身节点，且该 FUNCTION 在 L3 有带行号的源码证据。
      - **图谱后模式**（AUDIT，已有 graph/_evidence.json）：evidence_refs / evidence_ids
        必须是存在的 EVD_*，证据文件可解析且代码证据带行号。

    共同硬门：core 操作 ≥5 步、micro 操作 ≥2 步（`atomic: true` + `atomic_reason`
    的 micro 操作可豁免）；core 操作必须有非空 Mermaid 流程图。
    """
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    kb = os.path.join(project, ".agent", "harness", "_kb")
    ops_dir = os.path.join(kb, "L4_operations")
    ops = [load_json(fp) for fp in sorted(glob.glob(os.path.join(ops_dir, "*.json")))]
    ops = [o for o in ops if isinstance(o, dict)]
    if not ops:
        return report(False, "check_depth 需要 L4 操作产物，但 L4_operations/*.json 为空",
                      [("P0", "先完成 L4_OPERATION 再跑深度检查")])

    strict = os.path.exists(os.path.join(kb, "graph", "_evidence.json"))
    summary = _summarize_layer_evidence(project)
    known_nodes = _collect_layer_node_ids(project) | set(summary["node_sources"])

    evidence = load_json(os.path.join(kb, "graph", "_evidence.json"))
    if isinstance(evidence, dict):
        evidence = evidence.get("evidence") or []
    evidence = evidence if isinstance(evidence, list) else []
    ev_ids = {e.get("evidence_id") for e in evidence if isinstance(e, dict)}

    details = []
    ok_all = True
    short_core, no_flow, no_evd, dangling = [], [], [], []
    unknown_refs, unrelated, fn_no_source, atomic_bad = [], [], [], []
    core_n = 0

    for op in ops:
        fid = op.get("function_id") or op.get("id") or "?"
        fname = op.get("function_name") or op.get("name") or ""
        cls = (op.get("operation_class") or op.get("function_type") or "core").lower()
        if cls != "micro":
            core_n += 1
        atomic = bool(op.get("atomic"))
        atomic_reason = (op.get("atomic_reason") or "").strip()
        if atomic:
            if cls != "micro":
                atomic_bad.append(f"{fid}（atomic 仅允许 micro，当前 {cls}）")
                atomic = False
            elif not atomic_reason:
                atomic_bad.append(f"{fid}（atomic 缺少 atomic_reason）")
                atomic = False

        steps = op.get("steps") or []
        min_steps = MICRO_MIN_STEPS if cls == "micro" else CORE_MIN_STEPS
        if not atomic and len(steps) < min_steps:
            short_core.append(f"{fid} {fname}（{len(steps)}/{min_steps} 步，{cls}）")
        fc = (op.get("flowchart_mermaid") or "").strip()
        if not atomic and cls != "micro" and len(fc) < 10:
            no_flow.append(f"{fid} {fname}")

        refs = [r for r in (op.get("evidence_refs") or []) if isinstance(r, str)]
        if strict:
            effective = [r for r in (op.get("evidence_ids") or []) if isinstance(r, str)]
            if not effective:
                effective = [r for r in refs if r.startswith("EVD_")]
            if not effective:
                no_evd.append(f"{fid} {fname}（无 evidence_ids / EVD 引用）")
            for r in effective:
                if r.startswith("EVD_") and r not in ev_ids:
                    dangling.append(f"{fid} → {r}")
        else:
            if not refs:
                no_evd.append(f"{fid} {fname}（无节点/证据引用）")
            else:
                unknown = [r for r in refs if not r.startswith("EVD_") and r not in known_nodes]
                if unknown:
                    unknown_refs.append(f"{fid} → {unknown[:2]}")
                own = {fid, op.get("region_id")} - {None, ""}
                if not (set(refs) & own):
                    unrelated.append(f"{fid} {fname}（refs={refs[:2]}）")
            if not summary["node_sources"].get(fid):
                fn_no_source.append(f"{fid} {fname}")

    if atomic_bad:
        ok_all = False
        details.append(("P0", f"{len(atomic_bad)} 个操作的 atomic 标记不合法：" + "；".join(atomic_bad[:5])))
    if short_core:
        ok_all = False
        details.append(("P0", f"{len(short_core)} 个操作步骤不足（core≥{CORE_MIN_STEPS}，micro≥{MICRO_MIN_STEPS}）："
                              + "；".join(short_core[:8]) + (" ..." if len(short_core) > 8 else "")))
    if no_flow:
        ok_all = False
        details.append(("P0", f"{len(no_flow)} 个 core 操作缺 Mermaid 流程图：" + "；".join(no_flow[:8])
                              + (" ..." if len(no_flow) > 8 else "")))
    if no_evd:
        ok_all = False
        label = "未绑定 EVD 证据" if strict else "未引用节点/证据"
        details.append(("P0", f"{len(no_evd)} 个操作{label}：" + "；".join(no_evd[:5])
                              + (" ..." if len(no_evd) > 5 else "")))
    if dangling:
        ok_all = False
        details.append(("P0", f"{len(dangling)} 条 EVD 引用不存在（悬空）：" + "；".join(dangling[:5])))
    if unknown_refs:
        ok_all = False
        details.append(("P0", f"{len(unknown_refs)} 个操作引用了未知节点：" + "；".join(unknown_refs[:5])))
    if unrelated:
        ok_all = False
        details.append(("P0", f"{len(unrelated)} 个操作的引用与自身节点无关：" + "；".join(unrelated[:5])))
    if fn_no_source:
        ok_all = False
        details.append(("P0", f"{len(fn_no_source)} 个操作对应 FUNCTION 在 L3 无源码证据："
                              + "；".join(fn_no_source[:8]) + (" ..." if len(fn_no_source) > 8 else "")))

    if strict:
        resolvable = sum(1 for e in evidence if isinstance(e, dict)
                         and resolve_source_path(project, e.get("file_path")) is not None)
        code_total = sum(1 for e in evidence if isinstance(e, dict)
                         and source_type_of(e.get("file_path")) == "code_file")
        code_with_line = sum(1 for e in evidence if isinstance(e, dict)
                             and source_type_of(e.get("file_path")) == "code_file"
                             and e.get("line_start") is not None)
        ev_n = len(evidence)
        if not ev_n:
            ok_all = False
            details.append(("P0", "graph/_evidence.json 为空，证据链无法成立；先跑 normalize_evidence"))
        else:
            ratio = resolvable / ev_n
            if ratio < EVIDENCE_RESOLVABLE_MIN:
                ok_all = False
                details.append(("P0", f"证据文件可解析率 {ratio:.0%} < {EVIDENCE_RESOLVABLE_MIN:.0%}（{resolvable}/{ev_n}）"))
            else:
                details.append(("OK", f"证据文件可解析率 {ratio:.0%}（{resolvable}/{ev_n}）"))
            line_ratio = (code_with_line / code_total) if code_total else 1.0
            if line_ratio < EVIDENCE_LINE_MIN:
                ok_all = False
                details.append(("P0", f"代码类证据带行号比例 {line_ratio:.0%} < {EVIDENCE_LINE_MIN:.0%}"
                                      f"（{code_with_line}/{code_total}）"))
            else:
                details.append(("OK", f"代码类证据带行号比例 {line_ratio:.0%}（{code_with_line}/{code_total}）"))
        details.insert(0, ("OK", f"[图谱后模式] 操作 {len(ops)} 个（core {core_n} / micro {len(ops) - core_n}），"
                                f"图谱证据 {ev_n} 条"))
    else:
        total = summary["total"]
        if not total:
            ok_all = False
            details.append(("P0", "L0~L3 未产出任何源码证据，证据链无法成立"))
        else:
            bad = len(summary["unresolvable"])
            ratio = 1 - bad / total
            if ratio < 0.95:
                ok_all = False
                details.append(("P0", f"分层证据可解析率 {ratio:.0%} < 95%（{total - bad}/{total}）："
                                      + "；".join(summary["unresolvable"][:6])))
            else:
                details.append(("OK", f"分层证据可解析率 {ratio:.0%}（{total - bad}/{total}）"))
            if summary["no_line"]:
                ok_all = False
                details.append(("P0", f"{len(summary['no_line'])} 条代码证据缺行号："
                                      + "；".join(summary["no_line"][:6])))
            else:
                details.append(("OK", "代码证据均带行号"))
        details.insert(0, ("OK", f"[预图谱模式] 操作 {len(ops)} 个（core {core_n} / micro {len(ops) - core_n}），"
                                f"分层源码证据 {total} 条"))
    return report(ok_all, "check_depth 结果（操作深度 + 证据链）", details)


# ==================== Action: check_evidence ====================


def cmd_check_evidence(params):
    """在 L0~L3 出口校验源码证据质量（早失败，避免拖到 G4 才返工）。

    判据：
      - 每个 L1 模块、每个 L3 FUNCTION 至少 1 条证据
      - 证据路径可解析率 ≥95%
      - 代码类证据必须带行号（`path:start-end`）
    """
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    summary = _summarize_layer_evidence(project)
    details = []
    ok_all = True
    total = summary["total"]
    if not total:
        return report(False, "check_evidence 未发现任何 L0~L3 源码证据",
                      [("P0", "各层 evidence 字段为空；按 chunk-07 的 evidence 写法补全后重跑")])

    details.append(("OK", "分层证据条数：" + "，".join(f"{k}={v}" for k, v in sorted(summary["per_layer"].items()))))
    bad = len(summary["unresolvable"])
    ratio = 1 - bad / total
    if ratio < 0.95:
        ok_all = False
        details.append(("P0", f"证据路径可解析率 {ratio:.0%} < 95%（{total - bad}/{total}）："
                              + "；".join(summary["unresolvable"][:8])))
    else:
        details.append(("OK", f"证据路径可解析率 {ratio:.0%}（{total - bad}/{total}）"))
    if summary["no_line"]:
        ok_all = False
        details.append(("P0", f"{len(summary['no_line'])} 条代码证据缺行号（必须写成 path:start-end）："
                              + "；".join(summary["no_line"][:8])))
    else:
        details.append(("OK", "代码证据均带行号"))

    missing = find_functions_missing_evidence(project)
    if missing:
        ok_all = False
        details.append(("P0", f"{len(missing)} 个 FUNCTION 无任何源码证据：" + "、".join(missing[:10])
                              + (" ..." if len(missing) > 10 else "")))
    return report(ok_all, "check_evidence 结果（L0~L3 源码证据）", details)


# ==================== Action: normalize_evidence ====================


def cmd_normalize_evidence(params):
    """把 L0~L3 的 `path:line-line` 字符串证据归一化为结构化 `graph/_evidence.json`。

    这是 GRAPH_BUILD Step4 的机器实现：确定性解析、保留行号、按来源去重合并，
    并生成 node→EVD 索引供 L4/AUDIT 追溯。禁止由 AI 手写证据表。
    """
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    dry_run = bool(params.get("dry_run"))
    kb = os.path.join(project, ".agent", "harness", "_kb")

    merged = {}
    skipped = []
    total_refs = 0
    for layer, node_id, ref in iter_layer_evidence(project):
        total_refs += 1
        path, start, end = parse_evidence_ref(ref)
        if resolve_source_path(project, path) is None:
            skipped.append(f"{node_id} {ref}")
            continue
        key = (path.replace("\\", "/"), start, end)
        entry = merged.setdefault(key, {
            "layer": layer,
            "source_type": source_type_of(path),
            "file_path": path.replace("\\", "/"),
            "file_type": os.path.splitext(path)[1].lower(),
            "line_start": start,
            "line_end": end,
            "code_snippet": "",
            "supporting_node_ids": [],
            "supporting_triple_ids": [],
        })
        if node_id and node_id not in entry["supporting_node_ids"]:
            entry["supporting_node_ids"].append(node_id)

    if total_refs == 0:
        return report(False, "normalize_evidence 未发现任何 L0~L3 源码证据",
                      [("P0", "先完成 L0~L3 并确保 evidence 字段为 path:start-end 形式")])

    entries = []
    index = {}
    for i, ((path, start, end), entry) in enumerate(sorted(merged.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0)), 1):
        eid = f"EVD_{i:05d}"
        entry["evidence_id"] = eid
        entry["verification_status"] = "cross_verified" if len(entry["supporting_node_ids"]) >= 2 else "single_source"
        entry["cross_verified_with"] = []
        entry["extracted_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        entries.append(entry)
        for node in entry["supporting_node_ids"]:
            index.setdefault(node, []).append(eid)

    linked = 0
    if not dry_run:
        graph_dir = os.path.join(kb, "graph")
        os.makedirs(graph_dir, exist_ok=True)
        write_json(os.path.join(graph_dir, "_evidence.json"), {
            "normalized_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "source": "L0~L3 layer evidence (path:line-line)",
            "evidence": entries,
        })
        write_json(os.path.join(graph_dir, "_node_evidence.json"), {
            "normalized_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "index": index,
        })

        # 给 L4 操作补 evidence_ids（保留原 evidence_refs，不覆盖作者字段）
        for fp in sorted(glob.glob(os.path.join(kb, "L4_operations", "*.json"))):
            op = load_json(fp)
            if not isinstance(op, dict):
                continue
            refs = [r for r in (op.get("evidence_refs") or []) if isinstance(r, str)]
            ids = []
            for r in refs:
                for eid in index.get(r, []):
                    if eid not in ids:
                        ids.append(eid)
            if ids:
                op["evidence_ids"] = ids
                write_json(fp, op)
                linked += 1

    code_total = sum(1 for e in entries if e["source_type"] == "code_file")
    code_with_line = sum(1 for e in entries if e["source_type"] == "code_file" and e["line_start"] is not None)
    cross = sum(1 for e in entries if e["verification_status"] == "cross_verified")
    mode = "dry_run（未写盘）" if dry_run else "已写盘"
    details = [
        ("OK", f"{mode}：evidence {len(entries)} 条（去重合并后），节点索引 {len(index)} 个"),
        ("OK", f"L4 evidence_ids：{linked} 个操作" + ("（dry_run 未写盘）" if dry_run else "")),
        ("OK", f"代码证据带行号：{code_with_line}/{code_total}；交叉验证：{cross}/{len(entries)}"),
    ]
    ok_all = True
    if skipped:
        ok_all = False
        details.append(("P0", f"{len(skipped)} 条证据路径不可解析，已跳过（先修 L0~L3 的 evidence）："
                              + "；".join(skipped[:8])))
    if code_total and code_with_line < code_total:
        ok_all = False
        details.append(("P0", f"{code_total - code_with_line} 条代码证据无行号（归一化不会凭空补行号，需回 L0~L3 重抽）"))
    return report(ok_all, "normalize_evidence 结果（证据归一化 + 节点索引）", details)


# ==================== Action: check_reports ====================


def cmd_check_reports(params):
    """校验阶段报告不是空壳：按 L1 模块数核对报告的实际覆盖度。

    背景：实测 E:\\test_agent 的 `_audit.md`(1.3KB) / `_judgment.md`(917B) /
    `_refine_log.md`(699B) 都是结论式短文，却判 DONE 并给出 97 分。只查文件存在
    拦不住这种「报告写结论、没写过程」。本 action 用可判定的结构检查兜底：
      - `_audit.md`：至少 8 个维度标记（①~⑩）+ ⑪ 或「覆盖完整性」
      - `_judgment.md`：模块评分行数 ≥ ceil(模块数×0.8)
      - `_refine_log.md`：出现的模块名数 ≥ ceil(模块数×0.8)
      - `_gap_analysis.md`：含 P0，且含 P1 或 P2
      - `_auto_decisions.md`：≥200 字节且含「裁决/决策/decision」
    """
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    harness = os.path.join(project, ".agent", "harness")
    kb = os.path.join(harness, "_kb")

    module_names = []
    for fp in sorted(glob.glob(os.path.join(kb, "L1_modules", "*.json"))):
        data = load_json(fp)
        if isinstance(data, dict) and data.get("name"):
            module_names.append(str(data["name"]))
    module_count = len(module_names)
    if module_count == 0:
        return report(False, "check_reports 需要 L1 模块产物（L1_modules/*.json 为空）",
                      [("P0", "先完成 L1 再校验报告覆盖度")])
    need = max(1, int(module_count * 0.8 + 0.999))

    def read_text(name):
        """读取阶段报告文本，不存在返回空串。"""
        p = os.path.join(harness, name)
        if not os.path.exists(p):
            return ""
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    details = []
    ok_all = True

    audit = read_text("_audit.md")
    dims = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
    dim_hit = sum(1 for d in dims if d in audit)
    if dim_hit < 8 or ("⑪" not in audit and "覆盖完整性" not in audit):
        ok_all = False
        details.append(("P0", f"_audit.md 维度覆盖不足（命中 {dim_hit}/10 + "
                              f"{'有' if ('⑪' in audit or '覆盖完整性' in audit) else '缺'}⑪）；"
                              "必须是逐维打分的表，不能只写结论"))
    else:
        details.append(("OK", f"_audit.md 维度齐备（{dim_hit}/10 + ⑪）"))

    judgment = read_text("_judgment.md")
    score_rows = [ln for ln in judgment.splitlines()
                  if re.match(r"^\|.*\|\s*\d{2,3}\s*\|", ln.strip())]
    if len(score_rows) < need:
        ok_all = False
        details.append(("P0", f"_judgment.md 模块评分行 {len(score_rows)} < 要求 {need}"
                              f"（模块数 {module_count}×0.8）；盲审必须逐模块给分"))
    else:
        details.append(("OK", f"_judgment.md 模块评分行 {len(score_rows)}/{module_count}"))

    refine = read_text("_refine_log.md")
    found = [n for n in module_names if n in refine]
    if len(found) < need:
        ok_all = False
        missing = [n for n in module_names if n not in refine][:6]
        details.append(("P0", f"_refine_log.md 只覆盖 {len(found)}/{module_count} 个模块"
                              f"（要求 ≥{need}）；缺：{'、'.join(missing)}"))
    else:
        details.append(("OK", f"_refine_log.md 覆盖 {len(found)}/{module_count} 个模块"))

    gap = read_text("_gap_analysis.md")
    if "P0" not in gap or ("P1" not in gap and "P2" not in gap):
        ok_all = False
        details.append(("P0", "_gap_analysis.md 缺少 P0/P1/P2 分级（不能只写「无重大缺口」）"))
    else:
        details.append(("OK", "_gap_analysis.md 含 P0/P1/P2 分级"))

    decisions = read_text(os.path.join("_kb", "_auto_decisions.md"))
    if len(decisions) < 200 or not re.search(r"裁决|决策|decision", decisions, re.IGNORECASE):
        ok_all = False
        details.append(("P0", "_kb/_auto_decisions.md 过短或缺裁决记录（≥200 字节且含裁决依据）"))
    else:
        details.append(("OK", "_kb/_auto_decisions.md 有裁决记录"))

    return report(ok_all, "check_reports 结果（报告非空壳）", details)


# ==================== Action: baton_fix ====================


def cmd_baton_fix(params):
    """从磁盘实际产物反推各层计数并修正接力棒（替代 AI 手填计数）。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    harness = os.path.join(project, ".agent", "harness")
    kb = os.path.join(harness, "_kb")
    baton_path = os.path.join(harness, "_baton.json")

    if not os.path.exists(baton_path):
        return report(False, f"接力棒不存在: {baton_path}")
    baton = load_json(baton_path)
    if not baton:
        return report(False, "接力棒 JSON 解析失败")

    # 备份原接力棒
    backup = baton_path.replace("_baton.json", f"_baton.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    shutil.copy2(baton_path, backup)
    print(f"[INFO] 已备份原接力棒 -> {os.path.basename(backup)}")

    layers = baton.setdefault("layers", {})
    updated = []
    problems = []

    def require_batch_total(lk):
        """已声称完成的层必须有批次总数；缺失只报 P0，不自动补齐（避免把分母改成分子）。"""
        status, data = layer_status(baton, lk)
        if status not in DONE_STATUSES:
            return
        total_key, _ = BATCH_FIELDS[lk]
        if not data or not data.get(total_key):
            problems.append(("P0", f"{lk} 已声称完成但缺少 {total_key}：应由父层节点数推导后写入，禁止用磁盘数顶替"))

    def set_layers_counts(lk, counts):
        """向接力棒层写入计数（兼容两种 key）。"""
        targets = [k for k in layers if k == lk or k.startswith(lk + "_")]
        for t in targets:
            for field, val in counts.items():
                if val is not None:
                    layers[t][field] = val
        return targets

    def count_layer(lk):
        """统计某层产物文件数（递归，与 LAYER_DIRS 口径一致）。"""
        rel_dir = {"L1": "L1_modules", "L2": "L2_regions", "L3": "L3_functions",
                   "L4": "L4_operations", "L5": "L5_details"}.get(lk)
        if not rel_dir:
            return 0
        return count_files(os.path.join(kb, rel_dir, "**", "*.json"))

    # L1 模块数 / L2 区域数 / L3 功能数 / L4 操作数（递归统计）
    # 注意：只反推 *_completed，绝不改写 *_total / *_total_expected / *_batches_total。
    # v6.3 曾在此处把 total 写成磁盘数，导致“只做了 3/10 模块”的项目在 baton_fix 后
    # 变成 3/3，完成判据恒真。total 是计划量，只能由父层节点数推导。
    l1_n = count_layer("L1")
    if l1_n:
        set_layers_counts("L1", {"modules_completed": l1_n})
        updated.append(f"L1 modules: 磁盘反推 {l1_n}")
    l2_n = count_layer("L2")
    if l2_n:
        set_layers_counts("L2", {"regions_completed": l2_n})
        updated.append(f"L2 regions: 磁盘反推 {l2_n}")
    l3_n = count_layer("L3")
    if l3_n:
        set_layers_counts("L3", {"functions_completed": l3_n})
        updated.append(f"L3 functions: 磁盘反推 {l3_n}")
    l4_n = count_layer("L4")
    if l4_n:
        set_layers_counts("L4", {"operations_completed": l4_n})
        updated.append(f"L4 operations: 磁盘反推 {l4_n}")
    for lk in BATCH_FIELDS:
        require_batch_total(lk)
    # L5 五类子目录计数（ENTITY/ROLE/ELEMENT/VALIDATION/AGGREGATE）
    l5_counts = {}
    for sub, field in [("ENTITY", "fields_documented"), ("ROLE", "roles_documented"),
                       ("ELEMENT", "elements_documented"), ("VALIDATION", "validation_rules_documented"),
                       ("AGGREGATE", "aggregates_documented")]:
        n = count_files(os.path.join(kb, "L5_details", sub, "**", "*.json"))
        if n:
            l5_counts[field] = n
    if l5_counts:
        l5_total = sum(l5_counts.values())
        l5_counts["detail_files_total"] = l5_total
        set_layers_counts("L5", l5_counts)
        updated.append(f"L5 details: 磁盘反推 {l5_total} 个文件（五类子目录合计）")
    # 图谱节点/三元组/证据/Snake 计数（兼容 list 顶层 与 {key: [...]} 包装两种 schema）
    graph = baton.setdefault("graph", {})
    nodes = load_json(os.path.join(kb, "graph", "_nodes.json"))
    triples = load_json(os.path.join(kb, "graph", "_triples.json"))
    evidence = load_json(os.path.join(kb, "graph", "_evidence.json"))
    snakes = load_json(os.path.join(kb, "graph", "_snakes.json"))

    def _count_json_items(data, key):
        """统计 JSON 内容条数：list 顶层直接 len；dict 包装取 data[key]（如 _nodes.json 顶层是 {"normalized_at":..., "nodes":[...]}）。"""
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict):
            v = data.get(key)
            if isinstance(v, list):
                return len(v)
        return None

    for key, label in [("nodes", "nodes_total"), ("triples", "triples_total"),
                       ("evidence", "evidence_total"), ("snakes", "snakes_total")]:
        n = _count_json_items(locals()[key], key)
        if n is not None:
            graph[label] = n
            updated.append(f"graph.{label}: 磁盘反推 {n}")

    baton["meta"]["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(baton_path, "w", encoding="utf-8") as f:
        json.dump(baton, f, ensure_ascii=False, indent=2)

    details = [("OK", u) for u in updated] if updated else [("OK", "无需修正（磁盘无产物可反推）")]
    details.extend(problems)
    return report(not problems, "baton_fix 结果（completed 由磁盘反推；total 只读，AI 不得手改）", details)


# ==================== Action: reset ====================


def cmd_reset(params):
    """备份并重置接力棒为 START（供全量重跑）。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    if not project:
        return report(False, "缺少 project_path 参数")
    harness = os.path.join(project, ".agent", "harness")
    baton_path = os.path.join(harness, "_baton.json")

    if os.path.exists(baton_path):
        backup = baton_path.replace("_baton.json", f"_baton.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy2(baton_path, backup)
        print(f"[INFO] 已备份原接力棒 -> {os.path.basename(backup)}")

    os.makedirs(harness, exist_ok=True)
    fresh = {
        "meta": {
            "state": "START",
            "current_layer": 0,
            "project_path": project,
            "project_name": params.get("project_name", ""),
            "api_version": "2.2.0",
            "work_mode": params.get("work_mode", "full"),
            "user_preferences": {},
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "layers": {},
        "graph": {"nodes_total": 0, "triples_total": 0, "evidence_total": 0, "snakes_total": 0},
        "rework": {"retry_count": 0, "backfill_recent": [], "history": []},
    }
    with open(baton_path, "w", encoding="utf-8") as f:
        json.dump(fresh, f, ensure_ascii=False, indent=2)

    details = [("OK", "接力棒已重置为 START")]
    if params.get("purge_kb"):
        kb = os.path.join(harness, "_kb")
        if os.path.isdir(kb):
            shutil.rmtree(kb)
            details.append(("OK", "已清除旧 _kb 产物"))
    return report(True, "reset 结果", details)


# ==================== Action: ping ====================


def cmd_ping(params):
    """工具自检：快速确认 CLI 可用、项目目录可读、关键目录结构预期（对齐 skill-medic 的 ping）。"""
    project = norm_path(params.get("project_path") or params.get("project"))
    harness = os.path.join(project, ".agent", "harness") if project else None
    baton_path = os.path.join(harness, "_baton.json") if harness else None
    details = [
        ("OK", f"Python: {sys.version.split()[0]}"),
        ("OK", f"项目路径: {project or '(未指定，仅检查工具自身)'}"),
    ]
    ok_all = True
    if project:
        if sys.version_info < (3, 8):
            ok_all = False
            details.append(("P0", f"Python {sys.version.split()[0]} 过低：需要 ≥3.8"))
        else:
            details.append(("OK", "Python 版本满足 ≥3.8"))
        ok_all = ok_all and os.path.isdir(project)
        details.append(("OK" if os.path.isdir(project) else "P0", f"项目目录可读: {project}"))
        if harness:
            has_baton = os.path.isfile(baton_path) if baton_path else False
            details.append(("OK" if has_baton else "P2",
                            f"接力棒存在: {baton_path}（P2=未初始化，正常流程从 START 写入）"))
    return report(ok_all, "ping 结果（工具自检）", details)


# ==================== 参数解析与主入口 ====================


def parse_params(args):
    """解析 CLI 参数：优先 --params-file，其次命令行 JSON，最后 stdin 管道。

    顺序与 conspect_tools 一致：命令行 JSON 在 stdin 之前，避免非交互环境（IDE RunCommand）
    下 stdin 句柄保持打开导致 read() 永久阻塞挂死。管道调用（'...' | python run.py xxx）
    时 args.json 为空，仍会 fallback 到 stdin。
    """
    if args.params_file:
        with open(args.params_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if args.json:
        try:
            return json.loads(args.json)
        except json.JSONDecodeError:
            print(f"[ERROR] 参数 JSON 解析失败: {args.json}", file=sys.stderr)
            sys.exit(1)
    # stdin 管道（PowerShell: '{"project_path": "..."}' | python run.py verify）
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                print(f"[WARN] stdin 数据不是合法 JSON: {raw[:80]}...", file=sys.stderr)
    return {}


def main():
    """主入口：路由 action 到对应命令函数。任何异常输出结构化 JSON 错误并非零退出（对齐 conspect_tools）。"""
    action_name = None
    try:
        parser = argparse.ArgumentParser(description="ManualGen 硬校验工具层")
        parser.add_argument("action", help="verify/scan_tech/scan_flowcharts/check_deliverables/coverage/check_evidence/normalize_evidence/check_depth/check_reports/baton_fix/reset/ping")
        parser.add_argument("json", nargs="?", default=None,
                            help="JSON 参数（也可用 stdin 管道或 --params-file 传入）")
        parser.add_argument("--params-file", default=None, help="从 JSON 文件读取参数")
        try:
            args = parser.parse_args()
        except SystemExit as e:
            # argparse 参数错误（缺 action/未知选项等）→ 结构化 JSON（-h 帮助的 exit 0 放行）
            if e.code:
                print(json.dumps({"status": "error", "message": "参数错误", "error_code": "E400"},
                                 ensure_ascii=False))
                sys.exit(1)
            raise
        action_name = args.action

        handlers = {
            "verify": cmd_verify,
            "scan_tech": cmd_scan_tech,
            "scan_flowcharts": cmd_scan_flowcharts,
            "check_deliverables": cmd_check_deliverables,
            "coverage": cmd_coverage,
            "check_evidence": cmd_check_evidence,
            "normalize_evidence": cmd_normalize_evidence,
            "check_depth": cmd_check_depth,
            "check_reports": cmd_check_reports,
            "baton_fix": cmd_baton_fix,
            "reset": cmd_reset,
            "ping": cmd_ping,
        }
        if args.action not in handlers:
            print(json.dumps({
                "status": "error",
                "message": f"未知 action: {args.action}",
                "valid": sorted(handlers.keys()),
                "error_code": "E400",
            }, ensure_ascii=False))
            sys.exit(1)

        params = parse_params(args)
        ok = handlers[args.action](params)
        sys.exit(0 if ok else 1)
    except KeyboardInterrupt:
        # 用户中断：优雅退出（对齐 conspect_tools 退出码 130）
        logger.warning("用户中断执行: action=%s", action_name)
        print(json.dumps({"status": "error", "message": "User interrupted"}, ensure_ascii=False))
        sys.exit(130)
    except Exception as e:
        # 未预期异常：记录诊断日志 + 结构化错误 JSON，不裸抛 traceback（AI 可机读）
        logger.exception("CLI 执行异常: action=%s", action_name)
        print(json.dumps({
            "status": "error",
            "message": str(e),
            "action": action_name,
            "error_code": "E500",
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
