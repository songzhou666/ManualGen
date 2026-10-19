#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ManualGen 硬校验工具层单元测试。

覆盖 v6.3.1 修复的四类可回归缺陷：
  1. verify 必须校验批次是否跑完（不能只看文件存在）
  2. baton_fix 只反推 completed，不得改写 total（防止分母变分子）
  3. coverage 不得因短标题子串而假 PASS
  4. check_depth 必须拦截「步数不足 / 无图 / 无证据引用 / 证据不可解析」

运行：cd {Skill 目录} && python -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

RUN_PY = pathlib.Path(__file__).resolve().parent.parent / "manualgen_tools" / "run.py"
spec = importlib.util.spec_from_file_location("manualgen_run", RUN_PY)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


def write_json(path, data):
    """写入 UTF-8 JSON，自动建父目录。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def call(func, params):
    """调用命令函数并吞掉 stdout，返回 (是否通过, 输出文本)。"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = func(params)
    return ok, buf.getvalue()


class VerifyBatchTest(unittest.TestCase):
    """verify：批次没跑完时，即使文件存在也必须 FAIL。"""

    def _make_project(self, tmp, done, total):
        harness = os.path.join(tmp, ".agent", "harness")
        write_json(os.path.join(harness, "_baton.json"), {
            "meta": {"state": "L1_MODULE", "project_name": "demo"},
            "layers": {"L1": {
                "status": "completed",
                "modules_batches_total": total,
                "modules_batches_done": done,
                "modules_completed": 2,
            }},
        })
        write_json(os.path.join(harness, "_kb", "L1_modules", "MOD_001.json"), {"name": "A"})
        write_json(os.path.join(harness, "_kb", "L1_modules", "MOD_002.json"), {"name": "B"})

    def test_batch_incomplete_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_project(tmp, done=1, total=3)
            ok, out = call(run.cmd_verify, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("批次未跑完", out)

    def test_batch_complete_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._make_project(tmp, done=2, total=2)
            ok, out = call(run.cmd_verify, {"project_path": tmp})
            self.assertTrue(ok, out)
            self.assertIn("批次已跑完", out)


class BatonFixTest(unittest.TestCase):
    """baton_fix：只写 completed，绝不动 total。"""

    def test_total_is_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            harness = os.path.join(tmp, ".agent", "harness")
            baton_path = os.path.join(harness, "_baton.json")
            write_json(baton_path, {
                "meta": {"state": "L1_MODULE", "project_name": "demo"},
                "layers": {"L1": {
                    "status": "completed",
                    "modules_total": 10,
                    "modules_completed": 10,
                    "modules_batches_total": 5,
                    "modules_batches_done": 5,
                }},
            })
            for i in (1, 2):
                write_json(os.path.join(harness, "_kb", "L1_modules", f"MOD_{i:03d}.json"), {"name": i})

            ok, out = call(run.cmd_baton_fix, {"project_path": tmp})
            with open(baton_path, encoding="utf-8") as f:
                baton = json.load(f)
            self.assertTrue(ok, out)
            self.assertEqual(baton["layers"]["L1"]["modules_total"], 10, "total 是计划量，不得被磁盘数覆盖")
            self.assertEqual(baton["layers"]["L1"]["modules_completed"], 2)
            self.assertEqual(baton["layers"]["L1"]["modules_batches_total"], 5)
            self.assertEqual(baton["layers"]["L1"]["modules_batches_done"], 5)


class CoverageTest(unittest.TestCase):
    """coverage：短标题不能冒充模块章节。"""

    def test_short_heading_not_covered(self):
        with tempfile.TemporaryDirectory() as tmp:
            kb = os.path.join(tmp, ".agent", "harness", "_kb")
            write_json(os.path.join(kb, "L1_index.json"), [{"name": "客户管理"}, {"name": "订单管理"}])
            manual = os.path.join(tmp, "手册.md")
            with open(manual, "w", encoding="utf-8") as f:
                f.write("# 客户\n\n## 订单管理\n")

            ok, out = call(run.cmd_coverage, {"project_path": tmp, "manual_path": manual})
            self.assertFalse(ok)
            self.assertIn("未覆盖: 客户管理", out)
            self.assertIn("已覆盖: 订单管理", out)

    def test_numbered_heading_matches(self):
        self.assertEqual(run.normalize_heading("## 第一篇 客户管理"), "客户管理")
        self.assertEqual(run.normalize_heading("### 3. 订单管理"), "订单管理")


class CheckDepthTest(unittest.TestCase):
    """check_depth：操作深度与证据链四条硬门。"""

    def _setup(self, tmp, op):
        kb = os.path.join(tmp, ".agent", "harness", "_kb")
        write_json(os.path.join(kb, "L4_operations", "FN_001.json"), op)
        write_json(os.path.join(kb, "graph", "_evidence.json"), [
            {"evidence_id": "EVD_00001", "file_path": "src/main.py", "file_type": ".py", "line_start": 10}
        ])
        os.makedirs(os.path.join(tmp, "src"), exist_ok=True)
        with open(os.path.join(tmp, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write("print('x')\n")

    def _op(self, **over):
        base = {
            "function_id": "FN_001",
            "function_name": "创建知识库",
            "operation_class": "core",
            "steps": [{"no": i, "action": "a", "expect": "b"} for i in range(1, 6)],
            "flowchart_mermaid": "flowchart TD\n A-->B",
            "evidence_refs": ["EVD_00001"],
        }
        base.update(over)
        return base

    def test_compliant_op_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op())
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertTrue(ok, out)

    def test_short_steps_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op(steps=[{"no": 1, "action": "a"}]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("步骤不足", out)

    def test_missing_flowchart_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op(flowchart_mermaid=""))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("缺 Mermaid 流程图", out)

    def test_missing_evidence_ref_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op(evidence_refs=["FN_001"]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("未绑定 EVD", out)

    def test_dangling_evidence_ref_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op(evidence_refs=["EVD_99999"]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("悬空", out)

    def test_unresolvable_evidence_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._setup(tmp, self._op())
            write_json(os.path.join(tmp, ".agent", "harness", "_kb", "graph", "_evidence.json"),
                       [{"evidence_id": "EVD_00001", "file_path": "src/ghost.py",
                         "file_type": ".py", "line_start": 1}])
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("可解析率", out)


class EvidenceChainTest(unittest.TestCase):
    """check_evidence / normalize_evidence / check_depth 预图谱模式的证据链。"""

    def _layers(self, tmp, ref="src/main.py:1-3", fn_evidence=True):
        kb = os.path.join(tmp, ".agent", "harness", "_kb")
        write_json(os.path.join(kb, "L1_modules", "MOD_001.json"),
                   {"id": "MOD_001", "name": "模块", "evidence": [ref]})
        write_json(os.path.join(kb, "L2_regions", "PAGE_001.json"),
                   {"page_id": "PAGE_001", "regions": [{"id": "REG_001", "evidence": [ref]}]})
        write_json(os.path.join(kb, "L3_functions", "REG_001.json"),
                   {"region_id": "REG_001", "functions": [{
                       "id": "FN_001", "name": "新建",
                       "frontend_evidence": [ref] if fn_evidence else [],
                       "backend_evidence": [],
                   }]})
        os.makedirs(os.path.join(tmp, "src"), exist_ok=True)
        with open(os.path.join(tmp, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write("line1\nline2\nline3\n")

    def _op(self, **over):
        base = {
            "function_id": "FN_001", "function_name": "新建", "module_id": "MOD_001",
            "region_id": "REG_001", "operation_class": "core",
            "steps": [{"no": i} for i in range(1, 6)],
            "flowchart_mermaid": "flowchart TD\n A-->B",
            "evidence_refs": ["FN_001", "REG_001"],
        }
        base.update(over)
        return base

    def _write_op(self, tmp, op):
        write_json(os.path.join(tmp, ".agent", "harness", "_kb", "L4_operations", "FN_001.json"), op)

    def test_check_evidence_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            ok, out = call(run.cmd_check_evidence, {"project_path": tmp})
            self.assertTrue(ok, out)

    def test_check_evidence_missing_line_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp, ref="src/main.py")
            ok, out = call(run.cmd_check_evidence, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("缺行号", out)

    def test_check_evidence_unresolvable_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp, ref="src/ghost.py:1-3")
            ok, out = call(run.cmd_check_evidence, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("可解析率", out)

    def test_function_without_evidence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp, fn_evidence=False)
            ok, out = call(run.cmd_check_evidence, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("无任何源码证据", out)

    def test_check_depth_pregraph_passes_with_node_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op())
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertTrue(ok, out)
            self.assertIn("预图谱模式", out)

    def test_check_depth_unknown_node_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op(evidence_refs=["FN_999"]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("未知节点", out)

    def test_check_depth_unrelated_ref_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op(evidence_refs=["MOD_001"]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("与自身节点无关", out)

    def test_micro_atomic_exempts_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op(
                operation_class="micro", steps=[{"no": 1}], flowchart_mermaid="",
                atomic=True, atomic_reason="取消操作只有一步", evidence_refs=["FN_001"]))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertTrue(ok, out)

    def test_atomic_on_core_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op(atomic=True, atomic_reason="偷懒"))
            ok, out = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("atomic 仅允许 micro", out)

    def test_normalize_builds_evidence_and_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._layers(tmp)
            self._write_op(tmp, self._op())
            ok, out = call(run.cmd_normalize_evidence, {"project_path": tmp})
            self.assertTrue(ok, out)

            kb = os.path.join(tmp, ".agent", "harness", "_kb")
            with open(os.path.join(kb, "graph", "_evidence.json"), encoding="utf-8") as f:
                ev = json.load(f)
            self.assertEqual(len(ev["evidence"]), 1, "同源证据应去重合并")
            entry = ev["evidence"][0]
            self.assertEqual(entry["file_path"], "src/main.py")
            self.assertEqual(entry["line_start"], 1)
            self.assertEqual(entry["line_end"], 3)
            self.assertEqual(entry["evidence_id"], "EVD_00001")

            with open(os.path.join(kb, "graph", "_node_evidence.json"), encoding="utf-8") as f:
                idx = json.load(f)
            self.assertIn("FN_001", idx["index"])

            with open(os.path.join(kb, "L4_operations", "FN_001.json"), encoding="utf-8") as f:
                op = json.load(f)
            self.assertEqual(op["evidence_ids"], ["EVD_00001"])
            self.assertEqual(op["evidence_refs"], ["FN_001", "REG_001"], "作者字段不得被覆盖")

            # 归一化后 check_depth 切到图谱后模式，应通过
            ok2, out2 = call(run.cmd_check_depth, {"project_path": tmp})
            self.assertTrue(ok2, out2)
            self.assertIn("图谱后模式", out2)


class EndToEndFlowTest(unittest.TestCase):
    """端到端机制验证：一个最小完整项目应能连续通过全部机器闸门。"""

    def _build_project(self, tmp):
        kb = os.path.join(tmp, ".agent", "harness", "_kb")
        os.makedirs(os.path.join(tmp, "src"), exist_ok=True)
        with open(os.path.join(tmp, "src", "main.py"), "w", encoding="utf-8") as f:
            f.write("a\nb\nc\n")

        ref = "src/main.py:1-3"
        write_json(os.path.join(kb, "L0_skeleton.json"), {
            "meta": {"project_name": "demo", "evidence": [ref]},
            "modules": [{"id": "MOD_001", "name": "客户管理", "evidence": [ref]}],
        })
        with open(os.path.join(kb, "L0_skeleton_report.md"), "w", encoding="utf-8") as f:
            f.write("# L0\n")
        write_json(os.path.join(kb, "L1_index.json"), [{"name": "客户管理"}])
        write_json(os.path.join(kb, "L1_modules", "MOD_001.json"),
                   {"id": "MOD_001", "name": "客户管理", "evidence": [ref]})
        write_json(os.path.join(kb, "L2_regions", "PAGE_001.json"),
                   {"page_id": "PAGE_001", "regions": [{"id": "REG_001", "evidence": [ref]}]})
        write_json(os.path.join(kb, "L3_functions", "REG_001.json"), {
            "region_id": "REG_001",
            "functions": [{"id": "FN_001", "name": "新建客户",
                           "frontend_evidence": [ref], "backend_evidence": []}],
        })
        write_json(os.path.join(kb, "L4_operations", "FN_001.json"), {
            "function_id": "FN_001", "function_name": "新建客户", "module_id": "MOD_001",
            "region_id": "REG_001", "operation_class": "core",
            "steps": [{"no": i, "action": "a", "expect": "b"} for i in range(1, 6)],
            "flowchart_mermaid": "flowchart TD\n A-->B",
            "evidence_refs": ["FN_001", "REG_001"],
        })
        for sub, fname in [("ENTITY", "e.json"), ("ROLE", "r.json"), ("ELEMENT", "el.json"),
                           ("VALIDATION", "v.json"), ("AGGREGATE", "a.json")]:
            write_json(os.path.join(kb, "L5_details", sub, fname), {"ok": True})
        for gf, payload in [("_nodes.json", []), ("_triples.json", []),
                            ("_evidence.json", {"evidence": []}), ("_snakes.json", []),
                            ("_layer_index.json", {}), ("_quality.json", {})]:
            write_json(os.path.join(kb, "graph", gf), payload)

        harness = os.path.join(tmp, ".agent", "harness")
        reports = {
            "_gap_analysis.md": "# 缺口\n\n- P0: 无\n- P1: 无\n- P2: 语言风格待统一\n",
            "_resolution.md": "# 冲突解决\n",
            "_refine_log.md": "# 修订日志\n\n- 客户管理：通过\n",
            "_reference_check.md": "# 一致性检查\n",
            "_integration.md": "# 整合\n",
            "_audit.md": "# 审计\n\n| 维度 | 分 |\n|---|---|\n"
                          "| ① | 90 |\n| ② | 90 |\n| ③ | 90 |\n| ④ | 90 |\n| ⑤ | 90 |\n"
                          "| ⑥ | 90 |\n| ⑦ | 90 |\n| ⑧ | 90 |\n| ⑨ | 90 |\n| ⑩ | 90 |\n"
                          "| ⑪ 覆盖完整性 | PASS |\n",
            "_todo_resolution.md": "# TODO\n",
            "_judgment.md": "# 盲审\n\n| 模块 | 分数 |\n|---|---|\n| 客户管理 | 85 |\n",
        }
        for pf, content in reports.items():
            with open(os.path.join(harness, pf), "w", encoding="utf-8") as f:
                f.write(content)
        with open(os.path.join(harness, "_kb", "_auto_decisions.md"), "w", encoding="utf-8") as f:
            f.write("# AI 自主裁决记录\n\n" + "- 裁决：低置信节点 FN_001 保留并加警告。\n" * 10)

        write_json(os.path.join(harness, "_baton.json"), {
            "meta": {"state": "DONE", "project_name": "demo"},
            "layers": {
                "L1": {"status": "completed", "modules_total": 1, "modules_completed": 1,
                       "modules_batches_total": 1, "modules_batches_done": 1},
                "L2": {"status": "completed", "pages_batches_total": 1, "pages_batches_done": 1},
                "L3": {"status": "completed", "functions_total_expected": 1, "functions_completed": 1,
                       "regions_batches_total": 1, "regions_batches_done": 1},
                "L4": {"status": "completed", "operations_total_expected": 1, "operations_completed": 1,
                       "functions_batches_total": 1, "functions_batches_done": 1},
                "L5": {"status": "completed", "detail_files_total": 5,
                       "operations_batches_total": 1, "operations_batches_done": 1},
            },
        })

        manual_dir = os.path.join(tmp, "output_user_manual")
        os.makedirs(os.path.join(manual_dir, "_modules"), exist_ok=True)
        os.makedirs(os.path.join(manual_dir, "_appendix"), exist_ok=True)
        with open(os.path.join(manual_dir, "_modules", "01_客户管理.md"), "w", encoding="utf-8") as f:
            f.write("# 客户管理\n\n```mermaid\nflowchart TD\n A-->B\n```\n")
        for ap in ["appendix-B-permission-matrix.md", "appendix-C-AI-auto-decisions.md",
                   "appendix-D-snake-flows.md", "appendix-E-evidence-index.md",
                   "appendix-F-uncalled-modules.md"]:
            with open(os.path.join(manual_dir, "_appendix", ap), "w", encoding="utf-8") as f:
                f.write("# appendix\n")
        with open(os.path.join(tmp, "demo 用户操作手册.md"), "w", encoding="utf-8") as f:
            f.write("# 客户管理\n\n```mermaid\nflowchart TD\n A-->B\n```\n"
                    "```mermaid\nflowchart TD\n B-->C\n```\n```mermaid\nflowchart TD\n C-->D\n```\n")

    def test_full_chain_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._build_project(tmp)
            for name, func in [
                ("verify", run.cmd_verify),
                ("check_evidence", run.cmd_check_evidence),
                ("normalize_evidence", run.cmd_normalize_evidence),
                ("check_depth", run.cmd_check_depth),
                ("check_reports", run.cmd_check_reports),
                ("coverage", run.cmd_coverage),
                ("check_deliverables", run.cmd_check_deliverables),
            ]:
                ok, out = call(func, {"project_path": tmp})
                self.assertTrue(ok, f"{name} 应通过，实际失败：\n{out}")

    def test_stub_reports_fail(self):
        """空壳报告（只写结论、无逐模块过程）必须被拦截。"""
        with tempfile.TemporaryDirectory() as tmp:
            self._build_project(tmp)
            harness = os.path.join(tmp, ".agent", "harness")
            for pf, content in {
                "_gap_analysis.md": "# 缺口\n无重大缺口\n",
                "_refine_log.md": "# 修订日志\n质量良好\n",
                "_audit.md": "# 审计\n总分 97 分，通过\n",
                "_judgment.md": "# 裁决\nPASS\n",
                "_kb/_auto_decisions.md": "# 决策\n无\n",
            }.items():
                with open(os.path.join(harness, pf), "w", encoding="utf-8") as f:
                    f.write(content)
            ok, out = call(run.cmd_check_reports, {"project_path": tmp})
            self.assertFalse(ok)
            self.assertIn("维度覆盖不足", out)
            self.assertIn("模块评分行", out)
            self.assertIn("只覆盖", out)


if __name__ == "__main__":
    unittest.main()
