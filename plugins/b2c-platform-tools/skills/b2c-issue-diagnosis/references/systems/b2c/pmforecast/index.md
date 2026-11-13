# PMForecast

[核對範圍與路徑縮寫](../index.md)。關鍵字：PM Forecast、國家角度。

| 定位項目 | 來源 |
| --- | --- |
| 前端／封裝 | `V/src/pages/Forecast/PmFcstModelList`、`V/src/pages/Forecast/PmFcstManagementList`；`V/src/api/forecastApi.js` |
| 後端 | `A/Areas/Sales.Fcst/Controllers/PmForecastController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

以下 `P/`＝`A/Areas/Sales.Fcst/`。

## 特殊規則

以下為程式已核對的摘要，使用時核對當次來源。

| 問題 | 容易誤判的規則 | 優先來源（相對於 P/） |
| --- | --- | --- |
| CountryCode 是什麼 | 空字串＝其他國家，不含印度／巴西，也不是總計；`IN`／`BR` 獨立維護。缺省／null 歸空字串，其他值（含小寫）拒絕。 | `Model/PmForecastModel.cs`；`Controllers/PmForecastController.cs:GetCountryCodeOptions` |
| 重傳是否影響其他國家 | 機種設定共用，預測按國別隔離；主檔唯一鍵為 Model_SYS_ID＋WeekID＋CountryCode，零件經 SYS_PARENT_ID 關聯。未帶角度的舊查詢只取其他國家。 | `Repository/PmForecastRepository.cs:SavePmForecastData`；`Entity/SD/PmForecast_ModelForecasts.cs` |
| B2 與選定國家不同 | 整檔共用請求角度；B2 不一致／缺漏時先擋下，不進入預測資料查詢、原檔備存與儲存。錯誤 Excel 的 A2 有原因。 | `Service/PmForecastService.cs:ImportForecast` |
| 舊範本能否使用 | 接受舊 B2「角度：空白（不含印度／巴西）。」對應其他國家；現行名稱為「角度：其他國家。」／「角度：印度。」／「角度：巴西。」。仍須通過 A2 當週 WeekID、機型與數值檢核。 | `Service/PmForecastService.cs:ImportForecast`／`ExportForecast` |
| 數量與比例 | 匯入取 Ceiling(總數 × 配置用量 × 比例 / 100)，不直接採信 PartQuantity；匯出用 ROUNDUP。畫面 50% 不足以證明 Excel 讀入值是 50 或 0.5。 | `Service/PmForecastService.cs:ImportForecast`／`ExportForecast`；`Profiles/FcstMappings.cs` |
| 週別與 MP 日期 | startWeekNum=14／endWeekNum=26 不能直接當固定匯出週數；實際依日期推算。每月 1 號落週日～週三歸該月，否則採該週最早日期月份；匯入略過該週最後日期早於 MpDate 的週。 | `Service/PmForecastService.cs:ExportForecast`／`ImportForecast`；`Repository/PmForecastRepository.cs:GetWeekIDs` |
| 機種新增與儲存 | SaveModel 只更新既有機種的啟用狀態與 MpDate，Controller 註解不能證明支援新增。 | `Repository/PmForecastRepository.cs:SaveModel` |
| 有 FilePath 是否成功 | 可能是錯誤 Excel；讀業務狀態並檢查錯誤檔，不由 HTTP 200 或下載成功推定匯入成功。 | `Service/PmForecastService.cs:ImportForecast`；共用回應見 [共用機制](../shared-mechanisms.md) |

既有整理（2026-10-28／30）標示使用者已確認：原有資料歸其他國家，不自動扣除 IN／BR；原工作卡連結未附，這裡保留該紀錄，不當成本次重新確認。變更此業務預期時需回查原需求。

## 排查線索

| 現象 | 直達來源／仍需驗證的點 |
| --- | --- |
| 同名跨品牌機種匯入異常 | `P/Service/PmForecastService.cs:ImportForecast`：機種查找缺 BrandName，preModelName 卻記 BrandName；是待重現風險，不能直接宣稱根因。 |
| 週別缺漏／匯出例外 | `P/Repository/PmForecastRepository.cs:GetWeekIDs` 的 null／Count 判斷與後續 Min／Max；另查 `P/Model/PmForecastModel.cs` 的 Quantity1～80／PartRatio1～80 容量。 |
| 比例、格式或 MP 邊界 | 數字轉換再追 `A/Providers/StringToDecimalMappingAction.cs`，Excel 底層為 Utility.BaseExcel；實際檔案儲存值與 nullable MP 日期邊界尚待驗證。 |
| 錯誤碼／中文訊息不同 | `A/Models/CommonStatusModel.cs`、`V/public/locales/zh-tw.json:CommonStatus`；頁面封裝與共用 2016 下載處理見 [共用機制](../shared-mechanisms.md)。 |
| CountryCode 欄位／唯一鍵未部署 | PortalAPI 的 Git 版本 `d92346d1^` 下 `docs/issue-assistant/systems/pmforecast/` 可定位 `add-country-code.sql`、`verify-country-code.sql`、`query-country-forecast.sql`；目前工作樹缺少。歷史 SQL 須核對現行 schema，不代表已執行；已有國別資料時回滾有唯一鍵碰撞／資料流失風險。 |

角色、現行 SOP、實際部署、週別業務認可與現場檔案尚未驗證；只在問題依賴時補查。可用環境入口見 [前端定位](../frontend.md)，個案處理與證據保存沿用 [共用診斷流程](../../../common/repository-workflow.md)。

## 相依與驗證

| 範圍 | 入口 |
| --- | --- |
| PM 專屬邏輯 | `P/Controllers/PmForecastController.cs` → `P/Service/IPmForecastService.cs`／`PmForecastService.cs` → `P/Repository/IPmForecastRepository.cs`／`PmForecastRepository.cs`；請求／回應在 `P/Model/PmForecastModel.cs`。 |
| PM 實體 | `P/Entity/SD/` 的 `PmForecast_ModelConfigs.cs`、`PmForecast_PartConfigs.cs`、`PmForecast_ModelForecasts.cs`、`PmForecast_PartForecasts.cs`。 |
| 同 Area 共用 | `P/Entity/SD/SDContext.cs`、`P/Profiles/FcstMappings.cs`、`P/Controllers/BaseSalesFcstController.cs`；整個 Sales.Fcst 並非 PMForecast 專屬。 |
| 平台共用 | ICommonExcel／ICommonStorage、數字 Mapping 與 Utility；從實際引用追實作，[共用機制](../shared-mechanisms.md) 提供入口。 |

`PortalAPI:PortalAPI.Tests/PMForecast/PmForecastCountryCodeTests.cs` 含國別選項／非法值、B2 九組配對、週別不符與國家隔離，使用介面替身與 SQLite 記憶體資料庫；也有合成工作簿。2026-11-13 僅讀碼定位，未執行，不代表 SQL Server／Storage 或操作驗收。

在 PortalAPI 根目錄：`dotnet test PortalAPI.Tests/PortalAPI.Tests.csproj --filter FullyQualifiedName~PmForecastCountryCodeTests`；API 專案為 `PortalAPI_Net5/PortalAPI.csproj`。執行前確認目前工作區適用，相關檔案與命令只在這裡維護。
