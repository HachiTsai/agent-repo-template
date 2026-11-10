---
name: workflow-factory
description: 由工作流登記表、規格檔與技能清單產生「工作流工廠」單檔 HTML 模擬頁（觸發 → 技能機台 → 產出倉庫），並回報與 repo 的不一致（drift）。
whenToUse: 當用戶說「更新工作流工廠」「產生工廠頁」，或新增、修改工作流與技能後需要同步視覺化頁面時
disableModelInvocation: false
metadata:
  version: "2026.11.10.1"
---

# Workflow Factory Skill

把 `.claude/workflows/` 的流程畫成一張「工廠平面圖」：左側是三種觸發平台（GitHub 排程、Claude 排程、手動），中間是技能機台，右側是產出倉庫。點選上方的流程籃，就能看到該流程的貨物如何經過哪些機台、落到哪個倉庫。版面規則見 [`_visualization-standard.md`](../../workflows/_visualization-standard.md) §7。

## 指令

```bash
python .claude/skills/workflow-factory/scripts/workflow_factory.py build factory.html          # 產生頁面
python .claude/skills/workflow-factory/scripts/workflow_factory.py build factory.html --strict # drift 非空時退出碼 1
```

輸出 JSON：`out`、`rows`、`skills`、`outputs`、`drift`。排程流程見 [`workflow-factory.md`](../../workflows/workflow-factory.md)。

## 資料來源（兩層）

| 層 | 來源 | 內容 |
| :-- | :-- | :-- |
| 即時層 | `workflow-registry.md` | 流程 ID、名稱、平台、觸發時機、規格路徑 |
| 即時層 | 各規格檔「技能與腳本」區段 | `●` 主責技能（機台亮起）、`○` 被引用技能（虛線框） |
| 即時層 | `.claude/skills/*/SKILL.md` | 技能清單（機台是否存在） |
| 策展層 | `references/workflow-factory-data.json` | 機台顏色與簡稱 `SK`、倉庫 `OUT`、流程順序 `ROWS`、產出路線 `OUTS`、例外覆寫 `OVR` |

新增工作流或技能後，同一個 PR 內更新資料檔與登記表。策展資料落後時，腳本只在 `drift` 列出，不自行修改資料檔。

## 資料檔欄位

- `META.title`：頁面標題。
- `SK`：`[技能名, 顏色, 簡稱]`，最多 9 台（3×3 版面）；簡稱可省略。
- `OUT`：`[倉庫名, 顏色]`，最多 15 個。
- `ROWS`：流程 ID 與顯示順序；必須涵蓋登記表所有流程。
- `OUTS`：`{流程ID: [倉庫名…]}`，沒有對外產出的流程給空陣列。
- `OVR`：`{流程ID: {...}}`，可覆寫 `name`、`when`、`plat`（`gha`／`cld`／`man`）、`skills`、`also`、`cap`（說明尾註）；`when_from` 借用另一流程的時間；登記表沒有的虛擬列（例如 CI 內的子流程）必須給 `plat` 與 `name`。

## 通用與專案專屬的分界

- **通用（本技能內建）**：解析登記表與規格、drift 比對、頁面模板、機台與倉庫的繪製、動畫。
- **專案專屬（只放資料檔）**：機台與倉庫的名稱與顏色、流程路線、Artifact 網址（寫在排程規格，不寫進頁面）。
- 頁面不放金鑰、試算表或 Drive ID、個人資料；測試會掃描 `references/` 內是否出現。

## 限制

- 只用 Python 標準函式庫，只讀 repo，不連網、不 commit。
- 模板需要瀏覽器執行 JavaScript；頁面載入 Google Fonts 樣式表。
