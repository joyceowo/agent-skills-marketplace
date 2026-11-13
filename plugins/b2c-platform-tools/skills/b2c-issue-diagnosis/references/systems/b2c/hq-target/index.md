# HQ 費用預算與業績目標

[核對範圍與路徑縮寫](../index.md)。關鍵字：HQ 費用預算／業績目標。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/HQExpenseBudget/README.md`、`V/src/pages/HQSalesTarget/README.md`。 |
| 前端／封裝 | `V/src/pages/HQExpenseBudget`、`V/src/pages/HQSalesTarget`；`V/src/api/hqExpenseBudgetApi.js`、`V/src/api/hqSalesTargetUploadApi.js` |
| 後端 | `A/Areas/Sales.Target/Controllers/`；`A/Areas/Sales.Target/Controllers/HQSalesTargetController .cs` 的檔名在 Controller 後有空白。匯入也經 Portal 中介。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

匯入另經 Portal 的 HQExpenseBudgetController／HQSalesTargetController，見 [中介對照](../entry-map.md#經-portal-中介的請求)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
