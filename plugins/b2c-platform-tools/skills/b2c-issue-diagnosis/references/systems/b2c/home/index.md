# 首頁、選單與待辦

[核對範圍與路徑縮寫](../index.md)。關鍵字：首頁、選單、待辦。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/Main/README.md`、`V/src/pages/TodoList/README.md`。 |
| 前端／封裝 | `V/src/pages/Main`、`V/src/pages/TodoList`；`V/src/api/commonApi.js`、`V/src/api/processSign.js` |
| 後端 | `A/Areas/Digital.System/Controllers/ProgramController.cs`；`A/Areas/Digital.Process/Controllers/ConfirmController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

選單由 API 依身分取得；靜態 menu.json 不代表現行選單，見 [共用機制](../shared-mechanisms.md)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
