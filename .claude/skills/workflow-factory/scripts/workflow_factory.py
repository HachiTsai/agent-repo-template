#!/usr/bin/env python3
"""工作流工廠產生器：讀 repo 現況，輸出單檔 HTML 模擬頁（觸發 → 技能機台 → 產出倉庫）。

規格：.claude/workflows/workflow-factory.md；版面標準：.claude/workflows/_visualization-standard.md §7。
只用標準函式庫，只讀 repo 內檔案，不連網。

資料分兩層：
- 即時層（每次從 repo 讀）：登記表的流程 ID、名稱、平台、觸發時機、規格路徑；
  各規格檔「技能與腳本」區段的 ●（主責）與 ○（被引用）；.claude/skills 的技能清單。
- 策展層（references/workflow-factory-data.json）：機台顏色與簡稱、倉庫（產出）清單、
  每條流程的產出路線與例外覆寫。repo 裡沒有結構化來源，由人維護；
  與 repo 不一致時本腳本回報 drift，不自行修改資料檔。

用法：
    python .claude/skills/workflow-factory/scripts/workflow_factory.py build OUT.html [--strict]
輸出（stdout）：JSON，含 out、rows、skills、outputs、drift。--strict：drift 非空時退出碼 1。
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REF = Path(__file__).resolve().parents[1] / "references"
REGISTRY = ".claude/workflows/workflow-registry.md"
MAX_SKILLS = 9  # 版面為 3x3 機台
MAX_OUTPUTS = 15  # 右側倉庫欄高度上限
PLATFORMS = [("gha", ("GitHub Actions", "GitHub")), ("cld", ("Claude 雲端", "雲端排程", "Claude")),
             ("man", ("手動", "本地", "Antigravity", "Webhook", "CI 事件"))]


# ---------- 即時層：解析 repo ----------

def _plat(text):
    """取文字中最早出現的平台關鍵字；都沒有回 man。"""
    best, code = len(text) + 1, "man"
    for c, keys in PLATFORMS:
        for k in keys:
            i = text.find(k)
            if 0 <= i < best:
                best, code = i, c
    return code


def _plain(text):
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return text.replace("`", "").strip()


def parse_registry(text):
    """回傳 [{id, name, plat, when, spec}]。表格欄序：ID｜名稱｜類型｜平台｜觸發時機｜規格…"""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rid = cells[0].strip("`") if cells else ""
        if len(cells) >= 6 and re.fullmatch(r"[A-Z]+\d+", rid):
            m = re.search(r"\.claude/workflows/[\w.\-]+\.md", cells[5])
            rows.append({"id": rid, "name": _plain(re.sub(r"\s*\(範例\)", "", cells[1])),
                         "plat": _plat(cells[3]), "when": _plain(cells[4]), "spec": m.group(0) if m else ""})
    return rows


def scan_skills(root):
    return sorted(p.parent.name for p in (root / ".claude" / "skills").glob("*/SKILL.md"))


def parse_spec_skills(text):
    """讀規格檔「技能與腳本」區段：回傳 (主責 ●, 被引用 ○) 的技能名稱清單。"""
    m = re.search(r"^##[^\n]*技能與腳本[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    main, also = [], []
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"\s*[-*]?\s*([●○])\s*`?([a-z0-9][a-z0-9\-]*)`?", line)
            if mm:
                (main if mm.group(1) == "●" else also).append(mm.group(2))
    return main, also


# ---------- 合併與比對 ----------

def merge(data, root):
    """回傳 (rows, drift)。rows 為頁面用的列；不改動傳入的 data。"""
    drift = []
    sk_names = [k[0] for k in data["SK"]]
    out_names = [o[0] for o in data["OUT"]]
    if len(sk_names) > MAX_SKILLS:
        raise ValueError(f"SK 最多 {MAX_SKILLS} 台機台，現有 {len(sk_names)}")
    if len(out_names) > MAX_OUTPUTS:
        raise ValueError(f"OUT 最多 {MAX_OUTPUTS} 個倉庫，現有 {len(out_names)}")
    reg_path = root / REGISTRY
    reg = {r["id"]: r for r in parse_registry(reg_path.read_text(encoding="utf-8"))} if reg_path.is_file() else {}
    if not reg:
        drift.append(f"{REGISTRY} 沒有解析出任何流程")

    repo_skills = scan_skills(root)
    for s in sk_names:
        if s not in repo_skills:
            drift.append(f"工廠資料列有技能 {s}，repo 已找不到")
    for s in repo_skills:
        if s not in sk_names:
            drift.append(f"技能 {s} 還沒出現在工廠資料")
    for rid in reg:
        if rid not in data["ROWS"]:
            drift.append(f"登記表有 {rid}，工廠資料沒有這個流程")

    rows = []
    for rid in data["ROWS"]:
        ov = data.get("OVR", {}).get(rid, {})
        r = reg.get(rid)
        if r is None and not ("plat" in ov and "name" in ov):
            drift.append(f"工廠資料有 {rid}，登記表沒有（可能已停用；虛擬列需在 OVR 給 plat 與 name）")
        r = r or {}
        base = reg.get(ov.get("when_from", ""), {})
        if "skills" in ov:
            main, also = ov["skills"], ov.get("also", [])
        else:
            main, also = [], []
            spec = root / r.get("spec", "")
            if r.get("spec") and spec.is_file():
                main, also = parse_spec_skills(spec.read_text(encoding="utf-8"))
            elif r.get("spec"):
                drift.append(f"{rid} 的規格檔 {r['spec']} 不存在")
        for n in main + also:
            if n not in sk_names:
                if n in repo_skills:
                    drift.append(f"{rid} 規格列了技能 {n}，工廠資料沒有這台機台")
                continue
        main = [n for n in main if n in sk_names]
        also = [n for n in also if n in sk_names and n not in main]
        outs = data.get("OUTS", {}).get(rid, [])
        for n in outs:
            if n not in out_names:
                raise ValueError(f"工廠資料沒有產出倉庫 {n}（{rid}）")
        when = ov.get("when") or (base.get("when") if "when_from" in ov else r.get("when", ""))
        rows.append([rid, ov.get("plat") or r.get("plat", "man"), ov.get("name") or r.get("name", rid), when,
                     [sk_names.index(n) for n in main], [sk_names.index(n) for n in also],
                     [out_names.index(n) for n in outs], ov.get("cap", "")])
    return rows, drift


# ---------- 輸出 ----------

def _js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def render(template, data, rows):
    sk = [[k[0], k[1], k[2] if len(k) > 2 else k[0]] for k in data["SK"]]
    js = f"var SK={_js(sk)};\nvar O={_js(data['OUT'])};\nvar W={_js(rows)};"
    title = html.escape(data.get("META", {}).get("title", "工作流工廠"))
    aria = f"工廠平面圖：左側觸發，中間 {len(sk)} 台技能機台，右側產出倉庫"
    return template.replace("/*@@FDATA@@*/", js).replace("@@TITLE@@", title).replace("@@ARIA@@", aria)


def build(root, out_path):
    data = json.loads((REF / "workflow-factory-data.json").read_text(encoding="utf-8"))
    template = (REF / "workflow-factory-template.html").read_text(encoding="utf-8")
    rows, drift = merge(data, root)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(render(template, data, rows), encoding="utf-8")
    return {"out": str(out_path), "rows": len(rows), "skills": len(data["SK"]), "outputs": len(data["OUT"]),
            "drift": drift}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="產生工廠模擬頁 HTML")
    b.add_argument("out")
    b.add_argument("--strict", action="store_true", help="工廠資料與 repo 不一致時退出碼 1")
    a = ap.parse_args(argv)
    res = build(ROOT, a.out)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 1 if (a.strict and res["drift"]) else 0


if __name__ == "__main__":
    sys.exit(main())
