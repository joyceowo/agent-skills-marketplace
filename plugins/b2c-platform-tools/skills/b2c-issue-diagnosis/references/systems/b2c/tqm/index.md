# Sales TQM 與呆滯報表

[核對範圍與路徑縮寫](../index.md)。關鍵字：TQM、呆滯、報表上傳。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/SalesTQM/README.md`。 |
| 前端／封裝 | `V/src/pages/SalesTQM`；`V/src/api/salesTQMApi.js` |
| 後端 | `A/Areas/Sales.TQM/Controllers/SalesTQMController.cs`；匯入／權限也經 Portal 中介。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

匯入／權限另經 Portal，見 [中介對照](../entry-map.md#經-portal-中介的請求)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
