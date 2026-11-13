---
name: b2c-system-maintenance
description: 維護 Notion 中可重用的系統知識，保存業務規則、流程、資料關係、共用限制與設計原因，區分程式已核對、使用者已確認與待確認推測。僅在使用者明確要求整理系統知識時使用；不由問題診斷自動觸發。
---

# 系統知識維護

僅在使用者明確要求整理或維護系統知識時執行；日常診斷、修復及工作卡更新不自動觸發。保留既有技能識別碼，與診斷共用同一份流程及系統資料。

1. 辨識當次系統；B2C 的 Notion 主頁、知識父位置及專屬索引讀 [B2C 系統資料](../b2c-issue-diagnosis/references/systems/b2c/index.md) 與 [Notion 目的地](../b2c-issue-diagnosis/references/systems/b2c/notion.md)，不把預設套用其他系統。
2. 依 [共用系統知識維護](../b2c-issue-diagnosis/references/common/system-maintenance.md) 保存業務規則、流程、資料關係、共用限制與設計原因，區分程式已核對、使用者已確認與待確認推測。保留他人資料、歷史及人工驗收，不自動修改安裝快取。
3. 需要核對本機程式時才依 [初始化與缺項詢問](../b2c-issue-diagnosis/references/common/initialization.md) 解析相應路徑；設定成功後直接接續維護。不依賴程式的既有知識整理不要求先初始化。
4. 目的地與更新權限依系統資料及共用流程處理，缺項時實際提問並等待；以工具回傳及回讀結果確認已保存內容，未同步部分如實回報。

可選的程式範圍物件見 [範圍檢查](references/configuration.md)。入口需要完整外掛內的 b2c-issue-diagnosis 共用資源。
