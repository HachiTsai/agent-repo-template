# Antigravity 專案導引與 `.claude/` 單一真實來源規範

本檔案為 Antigravity 唯一入口規則，旨在將所有專案規則、技能（Skills）與設定統一收斂至 **`.claude/`** 目錄與根目錄 [`CLAUDE.md`](../../CLAUDE.md) 下管理，避免維護兩套重複檔案。

---

## 1. 單一真實來源（Single Source of Truth）與雙模式協作鐵律

1. **所有實體設定一律集中於 `.claude/` 與 `CLAUDE.md`**：
   - 專案憲法與核心執行規範統一載於根目錄 [`CLAUDE.md`](../../CLAUDE.md)。
   - 模組化通用規則與人設統一存放於 `.claude/rules/*.md`。
   - 技能與自動化腳本統一存放於 `.claude/skills/`。
   - 工作流與排程標準作業程序（SOP）統一存放於 `.claude/workflows/`。

2. **統一工程協作權限 + 可切換教學導師角色**：
   - **工程協作模式（預設執行模式）**：Antigravity 與 Claude Code 享有完全對等的全專案讀寫、技能維護與 Git 提交權限。
   - **教學導師模式（可切換角色）**：當使用者提問、要求講解或明確指定切換為「教學導師角色」時，立即依 [`.claude/rules/teaching-persona.md`](../../.claude/rules/teaching-persona.md) 啟動「先見林再見樹、先看物理再看邏輯」的四步引導式教學框架。

3. **先測試、後主動使用技能提交（Auto-Commit with Skill After Test）**：
   - 任何程式碼、腳本、依賴或規則變更，在提交前必須先透過專案虛擬環境執行測試與品質驗證（`pytest`、`ruff check`）。
   - 確認通過後，Agent 必須主動透過 `.claude/skills/commit-workflow/scripts/committer.py` 執行結構化 Commit 與 Push。

4. **分支與 PR 鐵律（Branch & PR Protocol）**：
   - 所有變更一律在指定的分支上進行並向 `main` 發起 Pull Request，禁止直接 push 到 `main` 分支。
   - GitHub Actions CI 全綠後採 Merge Commit（`--merge`）合併。

---

## 2. 專案規則與技能自動載入（指向 `CLAUDE.md` 與 `.claude/`）

- **專案主規範入口**：@[CLAUDE.md](../../CLAUDE.md)
- **Python 環境與套件同步規範**：@[.claude/rules/python-environment.md](../../.claude/rules/python-environment.md)
- **Git 結構化提交與 PR 流程規範**：@[.claude/rules/git-commit-workflow.md](../../.claude/rules/git-commit-workflow.md)
- **教學導師角色與互動綱領（可切換人設）**：@[.claude/rules/teaching-persona.md](../../.claude/rules/teaching-persona.md)
- **Git 提交流程 Skill**：@[.claude/skills/commit-workflow/SKILL.md](../../.claude/skills/commit-workflow/SKILL.md)
- **跨專案通用學習筆記 Skill**：@[.claude/skills/study-notes/SKILL.md](../../.claude/skills/study-notes/SKILL.md)
- **工作流與排程登記總表**：@[.claude/workflows/workflow-registry.md](../../.claude/workflows/workflow-registry.md)
- **工作流執行範本**：@[.claude/workflows/_template-workflow.md](../../.claude/workflows/_template-workflow.md)
- **工作流可視化標準**：@[.claude/workflows/_visualization-standard.md](../../.claude/workflows/_visualization-standard.md)
- **工作流工廠 Skill**：@[.claude/skills/workflow-factory/SKILL.md](../../.claude/skills/workflow-factory/SKILL.md)
- **工作流工廠更新排程**：@[.claude/workflows/workflow-factory.md](../../.claude/workflows/workflow-factory.md)

---

## 3. 與 Claude 協作（Antigravity 與 Claude 雙 Agent 守則）

Antigravity（本機）與 Claude（雲端或本機）對等協作，兩邊看不到彼此的對話與記憶，**約定一律寫進 repo 或 GitHub Issue，不靠口頭轉述**。

1. **分支命名**：Antigravity 一律用 `agy/<task-name>`，Claude 一律用 `claude/<task-name>`；兩邊都不直接 push 到 `main`，一律 PR、CI 全綠後以 Merge Commit 合併。
2. **開工先同步**：先執行 `python .claude/skills/commit-workflow/scripts/committer.py --sync`（只 fast-forward），再讀最近 5 筆 Commit 的 `Session-Sync`，了解對方留下的狀態與下一步。
3. **Session-Sync 交接**：額度用盡或工作未完成時，提交到自己的分支，並在 Commit 的 `Session-Sync` 區塊寫清楚「狀態、下一步、阻塞」，讓對方能直接接手。
4. **動工前討論走 GitHub Issue**：每個議題開一個 Issue 當共用討論板，留言開頭標「Claude：」或「agy：」。不在 PR 底下討論（CI 綠燈後可能立即合併，來不及審），不為討論另寫 repo 草稿檔。使用者拍板後，由執行方把結論留言到 Issue、開 PR 實作，合併後關閉 Issue。推送與留言不會叫醒對方，由使用者轉知「看 #N」。
5. **治理核心先揭露**：修改 `CLAUDE.md`、`.agent/`、`.claude/rules/`、`committer.py`、`settings.json` 前，先向使用者揭露並取得同意；PR 描述加「規則掃描」段落（CI 的 `rule-scan` 會檢查）。
6. **含個資或機密的共享檔案不進 repo**：放在使用者指定的雲端共享資料夾（例如 Drive 的「Claude_agy_共享」），Issue 只寫檔名，不貼內容。非個資的約定一律寫進 repo。
7. **只有一方看得到的資訊要落地**：雲端排程結果、專案記憶中的決定、本機回測結果等，若對方需要，寫成 repo 文件或 Issue 留言；已決定不做的事要記下「為什麼」與「什麼條件下回頭」，避免對方重提。
8. **工作流與排程**：新增或調整排程時，同步更新 [`workflow-registry.md`](../../.claude/workflows/workflow-registry.md) 與工廠資料檔（見 [`_visualization-standard.md`](../../.claude/workflows/_visualization-standard.md) §7）；外部排程只用單行呼叫 prompt。
