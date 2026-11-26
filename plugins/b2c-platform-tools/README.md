# B2C Platform Tools

支援 Codex 與 Claude Code；兩端共用同一份技能來源。

| Skill | 用途 |
| --- | --- |
| [b2c-setup](skills/b2c-setup/SKILL.md) | 初始化程式路徑、DB／Blob 與維運手冊目的地、自動維護開關；可分項設定。 |
| [b2c-issue-diagnosis](skills/b2c-issue-diagnosis/SKILL.md) | 查用手冊、診斷問題／處理權限申請，按需唯讀取證，依授權處理並更新工作卡；已啟用時僅自動維護常用且可照做的手冊。 |
| [b2c-system-maintenance](skills/b2c-system-maintenance/SKILL.md) | 明確要求時整理系統知識，或修訂、合併與停用維運手冊。 |

適用 B2C 平台內所有系統／功能模組，共用同一套診斷、初始化與文件定位流程。共用流程放在 `skills/b2c-issue-diagnosis/references/common/`；預設來源、定位索引與模組參考集中於 [systems/b2c](skills/b2c-issue-diagnosis/references/systems/b2c/index.md)。模組沿用 `--system b2c`，沒有專屬文件或尚未列索引也能分析。B2C 以外的獨立系統不套用 B2C 登入。

診斷依 KISS、DRY、YAGNI 按需工作，不要求先填完設定或登記系統。聊天只摘要與連結；完整 SQL 與驗收只放同張 Notion 工作卡，異動 SQL 預設只檢查、透過參數才正式執行。工作類型依已確認原因及必要處理判斷，文字重點使用原生顏色；相關圖片先標註並取得明確上傳同意，再放在說明旁，不預設遮碼個人資訊。

## 初始化與使用

安裝完整外掛後，可說「使用 b2c-setup 初始化 B2C 工具」；Claude Code 也可輸入 `/b2c-platform-tools:b2c-setup`。這是使用者啟動的技能流程，不是安裝時自動執行的 hook。

1. 先顯示前後端路徑設定狀態，選擇本次要設定的項目；已提供選擇就沿用。
2. B2C 前端 Portal／後端 PortalAPI 的 Azure DevOps 預設來源保存在 [system.json](skills/b2c-issue-diagnosis/references/systems/b2c/system.json)。初始化另外詢問使用者已下載的本機資料夾，核對身分、存在與可讀後保存；不把網址當路徑，也不自動 clone／pull。
3. 路徑保存在 `~/.local/share/b2c-diagnostics/settings.json`，沿用 v1；DB／既有憑證仍用 OS 保管庫。Blob 的非秘密來源另存同目錄 `blob-sources.json`，登入由 Azure CLI／Entra 管理，不另存短效 token。只設路徑不需 keyring 或 Azure CLI。
4. Blob log 可選「現在設定／稍後」；保存來源後可選「現在登入並檢查讀取／稍後」。選前者才驗證最小讀取，已有可用登入就沿用，缺少才開登入介面；DB 憑證保存不連線。來源保存、登入可用及讀取驗證分開回報，登入不能取得原本沒有的資料權限。
5. 後續缺少／失效路徑時詢問「設定並保存」「本次提供、不保存」「暫不設定」。需要 log 才檢查來源與登入，缺少時詢問設定／登入或略過；已有可用登入不重問。未答先等，取消只暫停依賴部分，成功直接接續原任務。

已有有效設定不重問；本次明確指定的路徑優先，暫用不覆寫保存值。單純 Notion／一般問答或已提供片段不要求初始化；路徑保存不代表授予寫入權限。初始化不自動生成專案指引。設定工具與完整狀態／命令見 [初始化與缺項詢問](skills/b2c-issue-diagnosis/references/common/initialization.md)。

## 維運手冊

先提供自己有權限的 Notion「B2C 維運手冊」父頁／資料庫，並指定是否啟用自動維護；可單獨設定，不需先完成路徑或 DB 初始化。目的地、開關及允許類型用 `handbooks.py` 保存在 `~/.local/share/b2c-diagnostics/handbooks.json`，更新外掛後仍保留，私人 ID 不隨套件分發。`disable` 保留位置並停用自動寫入；`clear` 移除本機該系統設定，不刪 Notion。

日常診斷先查手冊並核對條件；自動維護預設不新增，僅已確認常用且能照步驟處理與驗證的「常見問題／權限申請」才收錄，優先更新既有手冊，不逐案重問文字收錄。單次 Bug、程式修復與個案修正留工作卡。草稿同樣須符合收錄門檻，只用於確有常態需要、流程具體但待驗證的手冊；驗證通過才標可使用，衝突標待更新，人工停用不自動復用。工作卡保存本次對象、核准、SQL 與結果，手冊提供人工可照做的共用流程；寫後回讀並分開回報案件／同步狀態。

此流程在技能執行時運作，不監控 Notion 後續操作；人工驗收後再次執行才補同步。未更新的已安裝快取不會自動取得本次來源修改，依宿主正常流程更新並開新工作階段後使用。設定存在也不代表遠端權限或業務操作授權。完整設定、收錄與範本見 [共用手冊流程](skills/b2c-issue-diagnosis/references/common/handbook-workflow.md)。

## 流程與系統資料

- [Notion 工作追蹤](skills/b2c-issue-diagnosis/references/common/notion-workflow.md)：卡片確認、結構、色彩、圖片及人工驗收。
- [程式診斷與交付收尾](skills/b2c-issue-diagnosis/references/common/repository-workflow.md)：修改範圍、驗證、分支與 Commit。
- [資料存取](skills/b2c-issue-diagnosis/references/common/data-log-access.md)：先確認環境與範圍；本機帳密按需存 OS keyring，等待輸入完成才續查，不輸出秘密。
- [Azure Blob log](skills/b2c-issue-diagnosis/references/common/azure-blob-logs.md)：非秘密來源設定、Entra 互動登入與有限量唯讀查詢；保留多行例外，回報讀取與截斷限制。
- [交付與 SQL](skills/b2c-issue-diagnosis/references/common/response-template.md)：SQL 優先與簡潔交付，不預設建立個案檔案。
- [共用系統知識維護](skills/b2c-issue-diagnosis/references/common/system-maintenance.md)：證據分類、保存與更新規則。
- [維運手冊](skills/b2c-issue-diagnosis/references/common/handbook-workflow.md)：目的地與開關、查用、收錄去重、人工範本與寫入驗證。

共用資源只維護一份；setup 與 maintenance 入口引用 diagnosis 的資源，需一起安裝完整外掛，不支援單獨上傳這兩個技能資料夾。

文件依問題按需讀取，已有線索可直達來源；模組統一由功能索引定位，專項資料只保留有助判斷的規則與邊界。內容取捨與建立條件集中於 [共用索引原則](skills/b2c-issue-diagnosis/references/common/system-maintenance.md#隨附索引的取捨)。

[功能索引](skills/b2c-issue-diagnosis/references/systems/b2c/functions.md) 已連到 32 份 `<模組>/index.md`，包括公告、接單、Rebate、費用、TQM、Share Rate 與 PMForecast，格式一致。PMForecast 原 scope／knowledge 已整合；其餘模組連到既有說明及入口，未確認的外站、歷史 Controller 或後端呼叫者如實標示。

一般讀碼沒有額外工具前提；本機工具需 Python 3.10 以上，Blob 登入／查詢另需 Azure CLI，可選範圍工具需 PowerShell 7。Notion 與現場查核需可用連接工具及對應權限。安裝、發布與更新兩端方式見 [市集說明](../../README.md)；上線／測試通知另用 [B2C Notice](../b2c-notice/README.md)。

## 開發驗證

在儲存庫根目錄，使用可用的 Python 3.10 以上、PowerShell 7 與 Node.js 22 以上執行：

```powershell
python -I -m unittest discover -s 'plugins/b2c-platform-tools/skills/b2c-issue-diagnosis/scripts/tests' -p 'test_*.py'
pwsh -NoProfile -File 'plugins/b2c-platform-tools/skills/b2c-issue-diagnosis/scripts/tests/Run-Tests.ps1'
node scripts/validate-marketplace.mjs
```

測試使用暫存目錄、合成憑證與 Azure CLI／HTTP 替身，不改使用者設定、不登入或連 B2C／Notion／Azure。流程的人工／模型檢查見 [回歸情境](skills/b2c-issue-diagnosis/references/common/scenarios.md)。真實登入與讀取驗收須在明確選定來源及授權環境進行，模擬測試不能代替。
