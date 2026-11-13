# Share Rate 品質與品牌配合度

[核對範圍與路徑縮寫](../index.md)。關鍵字：品質、品牌配合度風險、Share Rate。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `PortalAPI:Docs/ShareRate/README.md` → `PortalAPI:Docs/ShareRate/Base/README.md`、`PortalAPI:Docs/ShareRate/Calculation/README.md`；表結構見 `PortalAPI:Docs/ShareRate/Base/ShareRate_DB_Schema.md`。 |
| 前端／封裝 | `V/src/pages/ShareRate/QualityUpload`、`V/src/pages/ShareRate/CooperationRiskUpload`、`V/src/pages/ShareRate/ShareRateData`；`V/src/api/shareRateApi.js` |
| 後端 | `A/Areas/Purchase.ShareRate/Controllers/ShareRateController.cs`；先讀上方專屬文件。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
