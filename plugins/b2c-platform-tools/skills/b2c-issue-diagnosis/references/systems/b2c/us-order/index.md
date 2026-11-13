# 美國 EDI、PO Ack 與產品資料

[核對範圍與路徑縮寫](../index.md)。關鍵字：美國 EDI／PO Ack、產品資料。

| 定位項目 | 來源 |
| --- | --- |
| 前端／封裝 | `V/src/pages/EDITransactions`、`V/src/pages/ProductInfo`；`V/src/api/purchaseOrderAckApi.js` |
| 後端 | `A/Areas/Sales.USOrder/Controllers/CommonController.cs`、`A/Areas/Sales.USOrder/Controllers/PurchaseOrderAckController.cs`、`A/Areas/Sales.USOrder/Controllers/ProductInfoController.cs`；部分選項走 Portal `Portal:Portal_Net5/Controllers/USOrderController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

部分選項經 Portal 的 USOrderController；路由中的 Sales.USOrder 保留點號，見 [入口對照](../entry-map.md)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
