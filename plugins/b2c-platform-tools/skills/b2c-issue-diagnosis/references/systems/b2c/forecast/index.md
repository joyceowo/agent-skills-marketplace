# Forecast 預測

[核對範圍與路徑縮寫](../index.md)。關鍵字：Forecast、區域、機種。

| 定位項目 | 來源 |
| --- | --- |
| 前端／封裝 | `V/src/pages/Forecast/FcstManagementList`、`V/src/pages/Forecast/FcstModelList`、`V/src/pages/Forecast/RegionMap`；`V/src/api/forecastApi.js` |
| 後端 | `A/Areas/Sales.Fcst/Controllers/ForecastController.cs`、`A/Areas/Sales.Fcst/Controllers/BasicSettingsController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

與 Rolling／PMForecast 同 Area，專屬流程依 Controller 分開追；同目錄不能代表同一功能。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
