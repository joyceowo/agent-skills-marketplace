---
name: b2c-setup
description: 初始化、檢查或修改 B2C 工具的前後端本機路徑、DB 憑證與 Blob log 來源及登入；允許分項設定與略過。
---

# B2C 工具初始設定

以繁體中文完成使用者要求的設定，不要求一次填滿。此技能與診斷共用同一套設定工具及流程，不另存第二份資料。

1. 讀取 [B2C 系統資料](../b2c-issue-diagnosis/references/systems/b2c/index.md)，採用其中的預設來源；儲存庫網址不等於使用者本機路徑。
2. 依 [共用初始化與缺項詢問](../b2c-issue-diagnosis/references/common/initialization.md) 檢查路徑狀態，沿用已提交的選擇，詢問這次要設定的項目。只有需要路徑時才請提供本機資料夾；可只設前端、後端或某一筆憑證，不強制設定另一項。
3. 路徑用 [settings.py](../b2c-issue-diagnosis/scripts/settings.py) 保存；DB／既有憑證依 [資料存取](../b2c-issue-diagnosis/references/common/data-log-access.md) 與 [B2C 對應](../b2c-issue-diagnosis/references/systems/b2c/data-access.md)。Blob log 依 [Azure Blob 流程](../b2c-issue-diagnosis/references/common/azure-blob-logs.md) 保存非秘密來源，提供「現在登入並檢查讀取／稍後」；選前者才最小驗證，已有可用登入就沿用，缺少才開登入介面。DB 保存不連線。
4. 依工具實際完成結果回報來源已保存、登入可用與讀取已驗證，三者分開；視窗已開啟／程序執行中不算完成。DB 帳密追蹤本次進度檔，Blob 登入追蹤宿主執行 session，直到完成、取消或失敗。部分完成如實說明，不用單一 initialized=true 代表全部可用。

優先使用宿主適用的提問卡片，沒有才使用聊天；必要答案未提交時暫停依賴工作。使用者取消或略過後不重問同一缺項。從診斷轉入設定時，成功後直接接續原任務，不要求使用者重新下指令。

初始化不自動 clone／pull、啟動服務、查 DB 或修改業務程式；Blob 只有使用者選擇登入並檢查讀取時才做指定來源的最小驗證，不額外搜尋日誌。外掛目前以完整套件安裝，這個入口需要同套件的 b2c-issue-diagnosis 資源。
