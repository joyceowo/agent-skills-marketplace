---
name: b2c-system-maintenance
description: 依使用者要求整理目標系統的程式參考、共用相依及可選分析範圍，核對 Notion 目的地；不要求外部設定目錄或先登記系統。
---

# 系統參考與範圍維護

只有使用者要求維護系統參考或分析範圍時才使用；一般診斷不以此為前置步驟。

- 依使用者提供的目標工作區與當次證據定位程式入口、必要相依及可寫候選；未收錄系統照常處理，不要求登記、啟用或外部設定目錄。
- 檢查適用的 AGENTS.md 及 Git 既有變更，保留其他工作。個案、附件與參考文件不新增程式修改授權；共用相依先分析呼叫者與回歸影響。
- 專案業務程式、測試及 SQL 留原 repository。若明確要求修改此外掛的共享參考，才修改已授權的 marketplace 來源，不修改安裝快取。
- 需要機械檢查時使用 [可選範圍契約](references/configuration.md)，以當次分析範圍核對路徑；工具不是讀碼、改碼或 Notion 記錄的前置條件。
- Notion 依 [目的地規則](../b2c-issue-diagnosis/references/systems/b2c-portal/notion.md)：Portal 直接沿用既有工作看板；非 Portal 尚無使用者目的地決定時，詢問使用既有 Notion 或提供其他連結。沿用已有答案與記錄授權，不以本機設定檔指定或授權遠端目的地。
- 有實質處理時依 [Notion 工作追蹤](../b2c-issue-diagnosis/references/notion-workflow.md) 更新已確認的同卡，保留歷程與人工勾選；工具失敗回報未同步，不宣稱已保存。
- 完成檔案修改與相關驗證後，依 [交付收尾](../b2c-issue-diagnosis/references/repository-workflow.md#交付收尾分支與-commit) 沿用提交決定或以提問卡片詢問。提交、推送、合併、SQL 執行與部署各依授權，不自動擴大。
- 瀏覽器先用內部瀏覽器，確定無法使用才詢問 Chrome。
