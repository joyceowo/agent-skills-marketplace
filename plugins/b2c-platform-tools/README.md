# B2C Platform Tools

依「辨識系統 → 查 Notion → 核對程式 → 解決與驗證 → 更新 Notion」處理系統問題與需求。支援 Codex 與 Claude Code。

| Skill | 用途 |
| --- | --- |
| [b2c-issue-diagnosis](skills/b2c-issue-diagnosis/SKILL.md) | 辨識目標、核對程式、依授權解決並更新工作卡。 |
| [b2c-system-maintenance](skills/b2c-system-maintenance/SKILL.md) | 依要求整理目標系統的程式參考、共用相依及可選分析範圍。 |

不需先建立、登記或啟用系統，不要求 ConfigRoot、systems.yaml 或 notion.json。程式範圍依當次工作區、實作與使用者授權核對；[系統參考](skills/b2c-issue-diagnosis/references/systems/index.md) 只是定位線索。

Portal／PortalAPI／B2C Portal 所屬系統直接使用既有 Notion 工作看板；另開新案也不重問位置。非 Portal 需要記錄且尚無使用者目的地決定時，以提問卡片詢問「使用既有 Notion」或「提供其他 Notion 連結」；已有適用答案就沿用。詳見 [目的地規則](skills/b2c-issue-diagnosis/references/systems/b2c-portal/notion.md)。

先以同系統、標題與未完成狀態找工作卡候選，經使用者確認後讀取並更新同卡。Notion 連線或權限不足時回報未同步，繼續不依賴目的地的已授權工作，不重問本機設定路徑。

依照[市集說明](../../README.md)安裝；Codex 使用 $b2c-issue-diagnosis，Claude Code 使用 /b2c-platform-tools:b2c-issue-diagnosis。修改業務程式沿用使用者授權，不自動部署、執行 SQL 或傳送訊息。

一般分析不需 PowerShell。可選工具需 PowerShell 7，只接受明確工作區與當次分析範圍，見[範圍契約](skills/b2c-system-maintenance/references/configuration.md)。工具測試位於診斷 Skill 的 scripts/tests/Run-Tests.ps1，僅使用合成資料。
