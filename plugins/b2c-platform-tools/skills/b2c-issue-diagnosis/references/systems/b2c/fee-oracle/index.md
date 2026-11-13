# Oracle 服務費轉 AP

[核對範圍與路徑縮寫](../index.md)。關鍵字：Oracle 服務費轉 AP。

| 定位項目 | 來源 |
| --- | --- |
| 前端／封裝 | `V/src/pages/PaymentOracleTransAp`；`V/src/api/paymentApi.js` |
| 後端 | **歷史已對上、現行工作樹缺少**：`git show 1b108040:PortalAPI_Net5/Areas/Global.BUFee/Controllers/FeeOracleController.cs` 可讀兩個 POST 方法 `GetFeeOracleServiceList`／`FeeSendAP`，繼承 BaseBUFeeController，對應前端 `/api/Global/BUFee/FeeOracle/...`。現行服務／部署版本仍待確認；不自動還原。 |
| 定位狀態 | 歷史 Controller；現行服務待確認；入口核對不代表操作或部署驗收。 |

現行服務／部署版本待確認；歷史 Controller 是定位證據，不自行還原或執行 FeeSendAP。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
