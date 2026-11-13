# Forecast／Rolling 同步紀錄

[核對範圍與路徑縮寫](../index.md)。關鍵字：Forecast／Rolling 同步紀錄。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/Forecast_RPTRolling/README.md`。 |
| 前端／封裝 | `V/src/pages/Forecast_RPTRolling`；`V/src/api/fcstRollingApi.js` |
| 後端 | `A/Areas/Sales.FCSTRolling/Controllers/RegionMapController.cs`、`A/Areas/Sales.FCSTRolling/Controllers/RptFCSTRollingController.cs`；與上一組 `Sales.Fcst` 分開。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

後端 Area 與路由為 Sales.FCSTRolling，與 Sales.Fcst 的 Forecast／Rolling 分開，見 [入口對照](../entry-map.md)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
