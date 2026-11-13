# 中國訂單、客戶與產品

[核對範圍與路徑縮寫](../index.md)。關鍵字：Sales.CNOrder、中國訂單、客戶與產品。

| 定位項目 | 來源 |
| --- | --- |
| 前端／呼叫者 | 本次未在 Vue 找到對應路由呼叫；外部呼叫者、選單與啟用狀態待確認。 |
| 後端 | `A/Areas/Sales.CNOrder/Controllers/OrderRequestController.cs:GetOrderRequestListToFront`／`GetOrderRequestListToBack`；`A/Areas/Sales.CNOrder/Controllers/CustomerController.cs`、`A/Areas/Sales.CNOrder/Controllers/ProductInfoController.cs`：訂單、客戶與產品。 |
| 定位狀態 | 僅後端入口；呼叫者待確認；入口核對不代表操作或部署驗收。 |

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
