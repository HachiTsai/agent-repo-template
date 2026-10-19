# {{PROJECT_NAME}}

> Project initialized from `HachiTsai/agent-repo-template`

## 🧠 核心架構 (Core Architecture)

本專案遵循 **Claude Code & Antigravity** 雙 Agent 協作模式，以 `.claude/` 作為單一真實來源（Single Source of Truth, SSOT）。

- **技術規範與治理**：請見根目錄 [`CLAUDE.md`](CLAUDE.md)
- **Antigravity 入口指標**：請見 [`.agent/rules/AGENT.md`](.agent/rules/AGENT.md)
- **模組化規則庫**：
  - [Python 環境與依賴同步規範](.claude/rules/python-environment.md)
  - [Git 結構化提交與 PR 流程規範](.claude/rules/git-commit-workflow.md)
  - [教學導師角色與互動綱領](.claude/rules/teaching-persona.md)

---

## 🛠️ 開發與快速啟動 (Quick Start)

### 1. 執行測試
```bash
pytest -q
```

### 2. 代碼檢查
```bash
ruff check .
```

### 3. 結構化提交（自動檢查敏感檔與套件依賴）
```bash
python .claude/skills/commit-workflow/scripts/committer.py --message-file <msg_file> --no-push
```
