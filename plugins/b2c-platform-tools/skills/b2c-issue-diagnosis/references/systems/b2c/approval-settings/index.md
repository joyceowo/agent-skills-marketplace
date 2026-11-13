# 簽核設定舊頁

[核對範圍與路徑縮寫](../index.md)。關鍵字：簽核流程設定舊頁。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/Approval_Flow/README.md`、`V/src/pages/Approval_Flow_Add/README.md`、`V/src/pages/Approval_Edit/README.md`。 |
| 前端／封裝 | `V/src/pages/Approval_Flow`、`V/src/pages/Approval_Flow_Add`、`V/src/pages/Approval_Edit` |
| 後端 | **已核對原型資料**：各 `App.vue` 的查詢／編輯主要操作本機陣列，未見流程設定持久化 API；需求見上方 v1。實際啟用、替代管理入口仍待確認，不視為 Confirm 管理後台。 |
| 定位狀態 | 原型頁；啟用狀態待確認；入口核對不代表操作或部署驗收。 |

此處為舊設定頁原型，不能當成已部署的流程管理後台；現行簽核入口見 [簽核模組](../approval/index.md)。

舊設定 UI 的歷史需求見 [簽核需求來源](../approval/index.md#既有需求來源)，原型頁未觀察到設定持久化 API。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
