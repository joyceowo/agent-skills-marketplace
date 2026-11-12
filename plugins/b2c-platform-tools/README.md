# B2C Platform Tools

支援 Codex 與 Claude Code；兩端共用同一份技能來源。

| Skill | 用途 |
| --- | --- |
| [b2c-issue-diagnosis](skills/b2c-issue-diagnosis/SKILL.md) | 辨識系統、查 Notion、核對程式，按需唯讀查 DB／Storage，依授權修復並更新同張工作卡。 |
| [b2c-system-maintenance](skills/b2c-system-maintenance/SKILL.md) | 使用者明確要求時，整理可重用系統知識與依據。 |

診斷依 KISS、DRY、YAGNI 按需工作，不要求系統登記或外部設定檔。聊天只摘要與連結；完整 SQL 與驗收只放同張 Notion 工作卡，異動 SQL 預設只檢查、透過參數才正式執行。工作類型依已確認原因及必要處理判斷，文字重點使用原生顏色；相關圖片先標註並取得明確上傳同意，再放在說明旁，不預設遮碼個人資訊。

- [Notion 工作追蹤](skills/b2c-issue-diagnosis/references/notion-workflow.md)：卡片確認、結構、色彩、圖片及人工驗收。
- [程式診斷與交付收尾](skills/b2c-issue-diagnosis/references/repository-workflow.md)：修改範圍、驗證、分支與 Commit。
- [資料存取](skills/b2c-issue-diagnosis/references/data-log-access.md)：先確認環境與範圍；本機帳密按需存 OS keyring，等待輸入完成才續查，不輸出秘密。
- [交付與 SQL](skills/b2c-issue-diagnosis/references/response-template.md)：SQL 優先與簡潔交付，不預設建立個案檔案。

一般讀碼沒有額外工具前提；本機憑證工具需 Python 3.10 以上，可選範圍工具需 PowerShell 7。Notion 與現場查核需可用連接工具及對應權限。安裝、發布與更新兩端方式見 [市集說明](../../README.md)；上線／測試通知另用 [B2C Notice](../b2c-notice/README.md)。
