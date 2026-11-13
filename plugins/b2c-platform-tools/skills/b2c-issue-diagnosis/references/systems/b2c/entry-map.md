# B2C 前後端入口對照

用途是從請求快速找到檔案，沒有列出所有 API 或宣稱已重現。版本與縮寫見 [索引](index.md)；需要頁面／文件線索才查 [功能索引](functions.md)，已有對應檔案就直接追查。

下表封裝都在 `V/src/api/`。`Area:Controller.Action` 表示 `A/Areas/<Area>/Controllers/<Controller>.cs` 及其方法；Controller 名稱保留 `Controller` 後綴。已靜態核對呼叫字串、Controller 路由與方法，尚未實際連線。除特別標示外，均為 PortalAPI；各模組再由 Controller 的注入介面追到同 Area 的 Service／Repository，不依相似名稱猜實作。

| 功能／前端封裝 | Method／API 路徑 | 後端定位 |
| --- | --- | --- |
| 選單 `commonApi.js:GetMenuList` | POST `/api/Digital/System/Program/GetMenuList` | `Digital.System:ProgramController.GetMenuList` |
| 待辦 `processSign.js:GetPendingList` | GET `/api/Digital/Process/Confirm/GetPendingList` | `Digital.Process:ConfirmController.GetPendingList` |
| 公告 `announcementApi.js:GetAnnouncementList` | POST `/api/Global/Bulletin/Announcement/GetAnnouncementList` | `Global.Bulletin:AnnouncementController.GetAnnouncementList` |
| 簽呈 `rebateSign.js:GetRebateSignList` | POST `/api/Global/BURebateSign/ReBateSign/GetRebateSignList` | `Global.BURebateSign:RebateSignController.GetRebateSignList` |
| 簽呈統計 `rebateSign.js:GetSignStatsForm` | POST `/api/Global/BURebateSign/ReBateSign/GetSignStatsForm` | `Global.BURebateSign:RebateSignController.GetSignStatsForm` |
| 銷折 `ecreditApi.js:GetECreditList` | POST `/api/Global/ECredit/ECredit/GetECreditList` | `Global.ECredit:ECreditController.GetECreditList` |
| 付款 `paymentApi.js:GetFEEInfo` | POST `/api/Global/BUFee/Fee/GetFeeList` | `Global.BUFee:FeeController.GetFeeList` |
| RMA 客服 `rmaServiceApi.js:GetRMAServiceList` | POST `/api/Global/RMAServices/CustomerService/GetCustomerServiceList` | `Global.RMAServices:CustomerServiceController.GetCustomerServiceList` |
| Forecast 範本 `forecastApi.js:ExportNewestWeekTemplate` | POST `/api/Sales/Fcst/Forecast/ExportNewestWeekTemplate` | `Sales.Fcst:ForecastController.ExportNewestWeekTemplate` |
| Rolling 匯出 `forecastApi.js:ExportRollingData` | POST `/api/Sales/Fcst/Rolling/ExportRollingData` | `Sales.Fcst:RollingController.ExportRollingData` |
| PM 機種 `forecastApi.js:GetPmForecastModelList` | GET `/api/Sales/Fcst/PmForecast/GetModelList` | `Sales.Fcst:PmForecastController.GetModelList` |
| PM 匯出 `forecastApi.js:ExportPmForecast` | GET `/api/Sales/Fcst/PmForecast/ExportForecast` | `Sales.Fcst:PmForecastController.ExportForecast` |
| PM 匯入 `forecastApi.js:ImportPmForecast` | POST `/api/Sales/Fcst/PmForecast/ImportForecast` | `Sales.Fcst:PmForecastController.ImportForecast`；`FromForm` |
| 同步紀錄 `fcstRollingApi.js:GetRolling_SyncLog` | GET `/api/Sales.FCSTRolling/RegionMap/GetRolling_SyncLog` | `Sales.FCSTRolling:RegionMapController.GetRolling_SyncLog` |
| 接單 `orderAndWeekMangerApi.js:GetOrderRequestList` | POST `/api/Sales/HQOrder/OrderRequest/GetOrderRequestList` | `Sales.HQOrder:OrderRequestController.GetOrderRequestList` |
| 費用預算 `hqExpenseBudgetApi.js:GetHQExpenseDept` | GET `/api/Sales/Target/HQExpenseBudget/GetHQExpenseDept` | `Sales.Target:HQExpenseBudgetController.GetHQExpenseDept` |
| MKT `MKTUploadApi.js:MKTFilter` | POST `/api/Sales/MKTUpload/MKTUpload/MKTFilter` | `Sales.MKTUpload:MKTUploadController.MKTFilter` |
| 價格 `priceManagementUploadApi.js:GetQueryInfo` | POST `/api/Sales.PMUploadPrice/UploadPrice/GetQueryInfo` | `Sales.PMUploadPrice:UploadPriceController.GetQueryInfo` |
| 成品運輸 `salesTranApi.js:GetTranType` | GET `/api/Sales/Tran/SalesTran/GetTranType` | `Sales.Tran:SalesTranController.GetTranType` |
| TQM `salesTQMApi.js:GetSalesTQM` | GET `/api/Sales/TQM/SalesTQM/GetProdLineSheetName` | `Sales.TQM:SalesTQMController.GetProdLineSheetName` |
| 預估 `estimateApi.js:GetEstimateList` | POST `/api/Sales/Estimate/Estimate/GetEstimateList` | `Sales.Estimate:EstimateController.GetEstimateList` |
| RMA 費用 `rmaExpsApi.js:GetSource` | GET `/api/Sales/RMAExps/RMAExps/GetSource` | `Sales.RMAExps:RMAExpsController.GetSource` |
| ELearning `eLearningApi.js:ImportExcel` | POST `/api/Sales/ELearning/ELearning/ImportExcel` | `Sales.ELearning:ELearningController.ImportExcel` |
| EDI `purchaseOrderAckApi.js:EdiTransactionsSearch` | POST `/api/Sales.USOrder/Common/GetEdiTransactions` | `Sales.USOrder:CommonController.GetEdiTransactions` |
| Share Rate `shareRateApi.js:GetQualityList` | GET `/api/Purchase/ShareRate/ShareRate/GetQualityList` | `Purchase.ShareRate:ShareRateController.GetQualityList` |
| Share Rate 計算 `shareRateApi.js:TriggerCalculation` | POST `/api/Purchase/ShareRate/ShareRate/TriggerCalculation` | `Purchase.ShareRate:ShareRateController.TriggerCalculation` |
| Power BI `powerBI.js:GetToken` | GET `/api/Reporting/PowerBi/GetToken` | `Reporting:PowerBiController.GetToken` |
| Tableau `tableauApi.js:GetToken` | GET `/api/Reporting/Tableau/GetToken` | `Reporting:TableauController.GetToken` |

## 經 Portal 中介的請求

`VUE_APP_API_URL` 與 `VUE_APP_API_URL_API` 的實際值決定送到哪台主機，不由變數名稱推定正式／測試。不能見到前端 `/api/...` 就只搜尋 PortalAPI：

| 前端呼叫 | 先讀 Portal 的 `Portal_Net5/Controllers/` | 再追 PortalAPI |
| --- | --- | --- |
| `hqExpenseBudgetApi.js:ImportHQExpenseBudget` → POST `/api/HQExpenseBudget/ImportHQExpenseBudget` | `HQExpenseBudgetController.cs`：上傳後傳 `FilePath`、由目前身分補 `UserID` | `Sales.Target:HQExpenseBudgetController.ImportHQExpenseBudget` |
| `hqSalesTargetUploadApi.js:ImportHQSalesTarget` → POST `/api/HQSalesTarget/ImportHQSalesTarget` | `HQSalesTargetController.cs` | `Sales.Target` 的 `HQSalesTargetController .cs:ImportHQSalesTarget` |
| `salesTQMApi.js:ImportFile` → POST `/api/SalesTQM/ImportFile` | `SalesTQMController.cs`：檔案／身分轉交 | `Sales.TQM:SalesTQMController.ImportFile` |
| `processSign.js:Sign` → POST `/api/Process/Sign` | `ProcessController.cs` | `Digital.Process:ConfirmController.Sign`；實際轉交條件按該方法核對 |

路由中的 `Sales.FCSTRolling`、`Sales.PMUploadPrice`、`Sales.USOrder` 含點號，不要自行改成斜線。`paymentApi.js` 的 `/api/Global/BUFee/FeeOracle/...` 已對上本機 Git 歷史 Controller，來源見 [Oracle 模組索引](fee-oracle/index.md)；目前工作樹缺少該檔，現行服務／部署版本仍待確認，不計入上述現行 API 對照。其餘未列 API 按同一封裝檔的實際呼叫查找。
