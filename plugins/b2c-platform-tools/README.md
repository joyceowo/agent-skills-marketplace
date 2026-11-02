# B2C Platform Tools

直接分析使用者提供的程式碼，診斷系統問題並維護專案範圍與 Notion 紀錄位置。兩個 Skill 共用同一套檢查工具與 Schema，支援 Codex 與 Claude Code。

| Skill | 用途 |
| --- | --- |
| [b2c-issue-diagnosis](skills/b2c-issue-diagnosis/SKILL.md) | 分辨操作問題、程式 Bug、功能需求或證據不足，提供解法與驗證方式，並在已確認的 Notion 位置記錄個案。 |
| [b2c-system-maintenance](skills/b2c-system-maintenance/SKILL.md) | 維護目標專案的系統登記、讀寫範圍、共用相依與 Notion 目的地。 |

依照[市集說明](../../README.md)安裝 `b2c-platform-tools`，在目標專案的新聊天中指定 Skill、系統與問題。Claude Code 的呼叫名稱為 `/b2c-platform-tools:b2c-issue-diagnosis` 與 `/b2c-platform-tools:b2c-system-maintenance`。

一般程式片段分析不需 PowerShell 或完整 repository。本機設定／範圍檢查需要 PowerShell 7，執行隨附工具時明確指定 `-WorkspaceRoot`；命令見[程式碼診斷與修復](skills/b2c-issue-diagnosis/references/repository-workflow.md)。工具回歸測試位於診斷 Skill 的 `scripts/tests/Run-Tests.ps1`，使用自行建立的臨時工作區與合成資料。

目標專案保留自己的 `config/issue-assistant/systems.yaml`、`notion.json`、業務程式、業務測試及 SQL；這個外掛不提供實際專案設定、Notion ID、憑證或業務原始碼。首次接入由維護 Skill 依[設定契約](skills/b2c-system-maintenance/references/configuration.md)整理，沒有預設系統或預設 Notion 位置。PMForecast 參考索引是歷史背景，不代表已取得目標專案原始碼或授權。

Notion 紀錄需要執行環境已有可用的 Notion 連接工具，並確認接收者自己的目的地及權限；外掛不代為安裝或連接服務。缺少工具時可先完成分析，須回報尚未同步。修改業務程式沿用使用者的明確授權；不自動部署、執行 SQL 或傳送訊息。
