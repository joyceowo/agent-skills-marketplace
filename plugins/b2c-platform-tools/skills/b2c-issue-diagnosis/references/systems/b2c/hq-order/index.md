# 總部接單與週次管理

[核對範圍與路徑縮寫](../index.md)。關鍵字：總部接單、申請、週次、報表、產能。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/OrderRequest/README.md`、`V/src/pages/OrderHQOrder/README.md`；其餘看對應頁面 README。 |
| 前端／封裝 | `V/src/pages/OrderHQOrder`、`V/src/pages/OrderRequest`／`V/src/pages/OrderRequest_Add`／`V/src/pages/OrderRequest_Edit`／`V/src/pages/OrderRequest_Detail`／`V/src/pages/OrderRequest_Record`、`V/src/pages/OrderForecast`、`V/src/pages/OrderWeekManager`、`V/src/pages/OrderReport`／`V/src/pages/OrderReport_Distribution`、`V/src/pages/OrderCapacity`；`V/src/api/orderAndWeekMangerApi.js` |
| 後端 | `A/Areas/Sales.HQOrder/Controllers/`：`A/Areas/Sales.HQOrder/Controllers/OrderRequestController.cs`、`A/Areas/Sales.HQOrder/Controllers/OrderRequestDetailController.cs`、`A/Areas/Sales.HQOrder/Controllers/WeekManagerController.cs`、`A/Areas/Sales.HQOrder/Controllers/OrderReportController.cs`、`A/Areas/Sales.HQOrder/Controllers/OrderCapacityController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
