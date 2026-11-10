"""workflow_factory.py：解析登記表與規格、合併 repo 現況、輸出頁面。只讀 repo，不連網。"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "workflow_factory.py"
spec = importlib.util.spec_from_file_location("workflow_factory", SCRIPT)
wf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wf)

REGISTRY = (
    "| ID | 流程名稱 | 類型 | 平台 | 觸發時機 | 規格文件 | 產出 | 健康 |\n"
    "| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
    "| `S1` | 每日巡檢 (範例) | Schedule | GitHub Actions / 雲端排程 | 平日 09:00 | "
    "[`.claude/workflows/a.md`](a.md) | 報告 | Gate |\n"
    "| `C1` | 雲端發布 | Schedule | Claude 雲端 | 每日 23:10 | `.claude/workflows/b.md` | x | y |\n"
    "| `T1` | 手動維運 | Task | 本地 CLI | 依需求 | `.claude/workflows/c.md` | x | y |\n"
)


def make_root(tmp_path, registry=REGISTRY, skills=("alpha", "beta"), specs=None):
    (tmp_path / ".claude/workflows").mkdir(parents=True)
    (tmp_path / ".claude/workflows/workflow-registry.md").write_text(registry, encoding="utf-8")
    for s in skills:
        (tmp_path / f".claude/skills/{s}").mkdir(parents=True)
        (tmp_path / f".claude/skills/{s}/SKILL.md").write_text("x", encoding="utf-8")
    for name, body in (specs or {}).items():
        (tmp_path / f".claude/workflows/{name}").write_text(body, encoding="utf-8")
    return tmp_path


def data(**kw):
    d = {"SK": [["alpha", "#111", "甲"], ["beta", "#222"]], "OUT": [["報告", "#333"]],
         "ROWS": ["S1", "C1", "T1"], "OUTS": {"S1": ["報告"]}, "OVR": {}}
    d.update(kw)
    return d


def test_parse_registry_reads_columns():
    rows = wf.parse_registry(REGISTRY)
    assert [r["id"] for r in rows] == ["S1", "C1", "T1"]
    assert rows[0]["name"] == "每日巡檢"  # 去掉「(範例)」
    assert [r["plat"] for r in rows] == ["gha", "cld", "man"]  # 取最早出現的平台
    assert rows[0]["spec"] == ".claude/workflows/a.md"
    assert rows[1]["when"] == "每日 23:10"


def test_parse_spec_skills_main_and_also():
    text = "## 技能與腳本\n\n- ● `alpha`：腳本\n- ○ `beta`：被引用\n- 說明文字\n\n## 讀取\n- ● `gamma`\n"
    assert wf.parse_spec_skills(text) == (["alpha"], ["beta"])
    assert wf.parse_spec_skills("沒有區段") == ([], [])


def test_merge_uses_spec_skills_and_registry(tmp_path):
    root = make_root(tmp_path, specs={"a.md": "## 技能與腳本\n- ● `alpha`：x\n- ○ `beta`：y\n",
                                      "b.md": "# b", "c.md": "# c"})
    rows, drift = wf.merge(data(), root)
    assert rows[0] == ["S1", "gha", "每日巡檢", "平日 09:00", [0], [1], [0], ""]
    assert rows[1][4] == [] and rows[1][6] == []
    assert drift == []


def test_merge_override_and_virtual_row(tmp_path):
    root = make_root(tmp_path, specs={"a.md": "# a", "b.md": "# b", "c.md": "# c"})
    d = data(ROWS=["S1", "C1", "T1", "HC"],
             OVR={"HC": {"plat": "gha", "name": "健康檢查", "when_from": "S1", "skills": ["beta"]}})
    rows, drift = wf.merge(d, root)
    hc = rows[3]
    assert hc[1:4] == ["gha", "健康檢查", "平日 09:00"] and hc[4] == [1]
    assert drift == []


def test_drift_reports_mismatches(tmp_path):
    root = make_root(tmp_path, skills=("alpha", "gamma"), specs={"a.md": "# a", "b.md": "# b"})
    d = data(ROWS=["S1", "X9"])
    _, drift = wf.merge(d, root)
    joined = "\n".join(drift)
    assert "beta" in joined  # 資料有、repo 沒有
    assert "gamma" in joined  # repo 有、資料沒有
    assert "C1" in joined and "T1" in joined  # 登記表有、資料沒有
    assert "X9" in joined  # 資料有、登記表沒有


def test_limits_and_unknown_output(tmp_path):
    root = make_root(tmp_path)
    with pytest.raises(ValueError):
        wf.merge(data(SK=[[f"s{i}", "#000"] for i in range(10)]), root)
    with pytest.raises(ValueError):
        wf.merge(data(OUTS={"S1": ["不存在"]}), root)


def test_render_replaces_all_markers():
    tpl = (wf.REF / "workflow-factory-template.html").read_text(encoding="utf-8")
    d = data(META={"title": "A<B"})
    page = wf.render(tpl, d, [["S1", "gha", "n", "w", [0], [], [0], ""]])
    assert "@@" not in page and "/*@@" not in page
    assert "<title>A&lt;B</title>" in page
    assert "中間 2 台技能機台" in page
    assert "var W=" + json.dumps([["S1", "gha", "n", "w", [0], [], [0], ""]], ensure_ascii=False) in page


def test_build_real_repo(tmp_path):
    out = tmp_path / "factory.html"
    res = wf.build(wf.ROOT, out)
    page = out.read_text(encoding="utf-8")
    assert "@@" not in page
    assert res["rows"] == len(json.loads((wf.REF / "workflow-factory-data.json").read_text("utf-8"))["ROWS"])
    assert res["drift"] == [], res["drift"]


def test_assets_have_no_secrets_or_drive_ids():
    for p in wf.REF.iterdir():
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"\b1[A-Za-z0-9_-]{43}\b", text), f"{p.name} 含疑似 Drive ID"
        assert not re.search(r"(github_pat_|AIza|-----BEGIN)", text), f"{p.name} 含疑似金鑰"
