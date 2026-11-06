# B2C Platform Tools

使用者提出問題／需求後，依「辨識系統 → 查 Notion → 核對程式 → 解決與驗證 → 更新 Notion」處理。支援 Codex 與 Claude Code。

| Skill | 用途 |
| --- | --- |
| [b2c-issue-diagnosis](skills/b2c-issue-diagnosis/SKILL.md) | 辨識目標、查同案與規格、核對程式，依授權解決並更新工作卡。 |
| [b2c-system-maintenance](skills/b2c-system-maintenance/SKILL.md) 系統知識維護 | 保存業務規則、流程、資料關係與設計原因，標示知識依據；僅在使用者明確要求時執行。 |
| [b2c-release-test-notice](skills/b2c-release-test-notice/SKILL.md) 上線／測試通知 | 從 Notion 或貼上的文字產生單一通知 HTML，可複製到 Outlook 並下載 `Document.pdf`。上線通知可依授權建立 System 公告，儲存後核對公告編號及附件。 |

不需先建立／登記系統，不要求外部設定目錄。Skill 先使用對話、畫面、API 與工作區線索辨識，仍無法確定才詢問；未收錄系統照常處理。[系統參考](skills/b2c-issue-diagnosis/references/systems/index.md) 只在相關時讀取。

Notion 先以同系統、標題關鍵字與未完成狀態找候選，只列標題、狀態與連結；由使用者確認接續哪張或另開新案後，才讀取選定卡片的明細、規格與驗收並更新。已確認卡片不重問，已完成項目僅在使用者明確指定或要求追查時讀取。查無紀錄或工具不可用不阻擋證據足夠的工作，Portal 直接使用既有看板，非 Portal 尚無目的地決定時才詢問使用既有 Notion 或提供其他連結。一般背景問答不必建卡。

修改業務程式沿用使用者的開發／修復授權，共用元件先分析影響。業務程式、測試及 SQL 留目標 repository；通用技能與隨附參考留此外掛；需求、修改與驗收集中在工作卡。可選範圍檢查需 PowerShell 7，格式見 [範圍契約](skills/b2c-system-maintenance/references/configuration.md)，無系統清單或啟用程序。不自動部署、執行 SQL 或傳送訊息。

資訊釐清僅在系統不明、相似工作卡尚待使用者確認，或非 Portal 需要記錄且目的地尚未經使用者確認時使用宿主提問卡片；已有答案不重問，必要答案送出前不進行依賴該答案的修改，預選不視為確認。規則見診斷 Skill。

診斷不自動建立或維護系統知識頁，也不在工作卡加入系統知識頁導覽。獨立的系統知識維護 Skill 僅在使用者明確要求時執行。

Portal／PortalAPI／B2C Portal 所屬系統直接使用既有 Notion 工作看板，不另問位置；另開新案也沿用。非 Portal 需要記錄且尚無使用者目的地決定時，以提問卡片詢問「使用既有 Notion」或「提供其他 Notion 連結」；已有適用答案不重問。目的地解析見診斷 Skill 的 B2C 專屬參考。
