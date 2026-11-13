# Rebate、促銷簽呈與統計

[核對範圍與路徑縮寫](../index.md)。關鍵字：簽呈、Rebate、促銷、簽呈統計、促銷簽呈、PPRebate。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/RebateSign/README.md`、`V/src/pages/SignFormStatsPage/README.md`。 |
| 前端／封裝 | `V/src/pages/RebateSign`；`V/src/api/rebateSign.js`；`V/src/pages/SignFormStatsPage`；`V/src/api/rebateSign.js`；`V/src/pages/PPRebate`；`V/src/api/rebateSign.js`、`V/src/api/processSign.js` |
| 後端 | `A/Areas/Global.BURebateSign/Controllers/RebateSignController.cs`。 **已對上** `A/Areas/Global.BURebateSign/Controllers/RebateSignController.cs` 的 `GetPromotionRebateSignDetail`、`SaveRebateSign`、`DownloadPromotionTemplateAndSavePromotionRebateSign`、`UploadPromotionInfo`；`Edit.vue`／`Sign.vue` 使用 `ProgramID=PPRebate`。角色與流程設定仍依現場資料確認。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

簽呈統計由同一 Controller 的 `GetSignStatsForm` 系列定位。

簽核經 `V/src/api/processSign.js`；前後處理與 Portal 中介見 [簽核模組](../approval/index.md)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
