# PMForecast 範圍與共用限制

以下路徑相對於使用者提供的 PortalAPI 工作區，供定位與判斷相依；先確認檔案及呼叫關係，不要求外部設定。參考資料不代表已部署版本，也不替代個案修改授權。

## 專屬程式

目錄前綴：`PortalAPI_Net5/Areas/Sales.Fcst/`。

| 用途 | 候選專屬路徑 |
| --- | --- |
| API 入口 | Controllers/PmForecastController.cs |
| Service | Service/IPmForecastService.cs、Service/PmForecastService.cs |
| Repository | Repository/IPmForecastRepository.cs、Repository/PmForecastRepository.cs |
| 請求／回應 | Model/PmForecastModel.cs |
| 實體 | Entity/SD/PmForecast_ModelConfigs.cs、PmForecast_PartConfigs.cs、PmForecast_ModelForecasts.cs、PmForecast_PartForecasts.cs |

本次需求涉及的上述專屬檔案可讀取；使用者要求開發／修復時，依實際影響修改必要檔案。新增業務測試放在 repository 的相應目錄，先核對現有結構與風格；個案修正、查詢與驗證 SQL 直接放同一 Notion 工作卡，不另產生檔案。未列出的直接相依可依呼叫關係追查，不必先維護登記。

## 共用元件

- 同 Area 的 `Entity/SD/SDContext.cs`、`Profiles/FcstMappings.cs`、`Controllers/BaseSalesFcstController.cs`。
- 平台 ICommonExcel／ICommonStorage、數字 Mapping 及 Utility 套件；實際宣告與實作位置由引用追查。

共用元件先讀取必要部分。PMForecast 的修改授權不自動涵蓋其他使用者的行為改變；需修改時先分析其他呼叫者、影響與回歸方式，缺少涵蓋該影響的授權時再詢問。不得將整個 Sales.Fcst 當成 PMForecast 專屬範圍。

## 測試與編譯線索

先確認目前工作區的專案檔與測試；歷史資料曾使用 `PortalAPI_Net5/PortalAPI.csproj`、`PortalAPI.Tests/PortalAPI.Tests.csproj`。只有相關測試確實存在才執行，不要求不存在的 CountryCode 測試，也不以背景摘要宣稱測試通過。隔離輸出可避免正在執行的 API 鎖檔；不停止原程序，不啟動可能連正式資料的 API。

業務背景與 API 線索見 [knowledge.md](knowledge.md)。
