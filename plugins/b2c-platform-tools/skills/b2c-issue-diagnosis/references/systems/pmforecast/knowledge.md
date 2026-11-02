# PMForecast 背景與程式入口索引

system_id：`pmforecast`；名稱：PMForecast／PM Forecast。此文件只作背景與入口索引。診斷直接讀取使用者本次提供的程式碼，不要求 commit、分支或同步基線；以下既有程式摘要僅供定位，不能取代本次讀碼或覆蓋提供的實作。

## 來源與適用範圍

- 初次盤點：2026-10-28；後續整併 CountryCode 與範本檢核相關資料。此為歷史參考，不要求將本次提供的程式碼對應到歷史版本。
- 2026-10-30 整併既有文件並核對相關方法；此次整理未重新執行業務測試，也未確認任何環境的部署狀態。各環境的實際執行／驗收結果由 Notion 工作卡記錄，不隨共用知識推定。
- 除已註明的使用者確認規則外，內容來自後端程式觀察，不是完整的業務核准操作手冊。原始碼路徑以 PortalAPI repository 為基準，前綴 P＝`PortalAPI_Net5/Areas/Sales.Fcst/`；它們是定位提示，使用者直接提供片段時以片段為準；不能只依本文件推定程式行為。
- 未涵蓋前端操作畫面、角色權限、現場 Log、實際環境 DB／Storage。文件不足以確認新問題根因時，標明待核對資訊。

## 系統與資料

PMForecast 提供機種查詢、啟用狀態／MP 日期維護，以及機種數量與零件比例的預測匯入／匯出。`SaveModel` 更新既有機種，不提供新增機種功能。

後端流程：`PmForecastController` → `IPmForecastService`／`PmForecastService` → `IPmForecastRepository`／`PmForecastRepository` → `SDContext` → SQL Server。匯入／匯出另使用 `ICommonExcel`、`ICommonStorage` 與 `FcstMappings`。

四張核心表：`PmForecast_ModelConfigs`、`PmForecast_PartConfigs`、`PmForecast_ModelForecasts`、`PmForecast_PartForecasts`；以 SYS_ID、Model_SYS_ID、Part_SYS_ID、SYS_PARENT_ID 關聯。週別來自 `VIEW_AZN_FILE` 的 AZN01／WeekID；月份在每月一號落於週日～週三時歸該月，否則用該週最早日期月份（`Repository.GetWeekIDs`）。

## CountryCode 背景與既有實作摘要（按需核對）

### 業務與資料隔離

| CountryCode | 顯示名稱 | 規則 |
| --- | --- | --- |
| 空字串 | 其他國家 | 不含印度、巴西；獨立維護，並非全部角度加總 |
| IN | 印度 | 印度預測 |
| BR | 巴西 | 巴西預測 |

- 上傳前選擇一次，整份檔案共用角度；匯出與資料更新依角度區分，不需逐列新增國家欄。
- 使用者確認既有資料歸其他國家；不自動從既有數量扣除 IN／BR。機型設定共用，預測數量與零件比例按角度維護。
- 省略或 null 視為空字串；US、小寫 in、國家中文等非法值拒絕，不回退為其他國家。模型、Service、Repository 均有角度限制。
- 預測主檔 CountryCode 為 varchar(2) NOT NULL；唯一鍵為 Model_SYS_ID＋WeekID＋CountryCode。零件以 SYS_PARENT_ID 連到對應主檔，無須再存一份角度。批次分組、查找及更新都包含角度；重傳 IN 不改其他國家與 BR。
- 原 Repository 未提供角度的查詢只取其他國家。欄位使用同名映射；SDContext、FcstMappings、CommonExcel 與 Storage 是共用相依，不能因維護 PMForecast 就視為專屬可修改檔案。

### API 與範本契約

路由前綴為 `/api/Sales/Fcst/PmForecast/`；具體參數規格以目前 Swagger 為準。

| Method／完整 API 路徑 | 功能與契約 |
| --- | --- |
| GET /api/Sales/Fcst/PmForecast/GetModelList | Query：ModelName、BrandName、SYS_ACTI、StartIndex、GetCount；回傳總數及分頁 |
| GET /api/Sales/Fcst/PmForecast/GetModel | Query：SYS_ID；找不到回 NoData |
| POST /api/Sales/Fcst/PmForecast/SaveModel | JSON：UserID、SYS_ID、SYS_ACTI、MpDate；只更新既有機種啟用狀態及 MP 日期 |
| GET /api/Sales/Fcst/PmForecast/GetCountryCodeOptions | ApiResponseBase.Result 提供三組 CountryCode／Name，順序為其他國家、印度、巴西 |
| GET /api/Sales/Fcst/PmForecast/ExportForecast | Query：UserID、CountryCode；回傳所選角度 Excel 的 FilePath，B2 顯示角度 |
| POST /api/Sales/Fcst/PmForecast/ImportForecast | multipart/form-data：UserID、File、CountryCode；全檔套用同一角度並檢核 B2、週別及資料，全部無錯誤才寫入預測資料 |

共用下載沿用 `GET /api/DownloadFile/{Type}/{AreaFileFolder}/{FileFolder}/{OtherFilePath}`。FilePath 是儲存相對路徑，不是可直接使用的 HTTP 網址；它也可能指向錯誤檔，不等於匯入成功。HTTP 200 不保證業務成功，仍需判讀回應狀態。

- 匯入先比對 B2「角度：名稱。」與請求 CountryCode；不一致、缺少或無法辨識時回 ImportDataError 與中文錯誤 Excel，停止明細解析、原檔備存及預測資料庫查詢／儲存。錯誤訊息位於錯誤 Excel 的 A2；錯誤檔輸出失敗另回 OtherError。
- 新標頭為「角度：其他國家。」／「角度：印度。」／「角度：巴西。」；舊標頭「角度：空白（不含印度／巴西）。」仍對應空字串。無 B2 角度資訊的範本須重新下載。
- 三種範本與三種請求共九組配對，只有同角度三組可繼續既有資料驗證，六種不同角度組合均阻擋。B2 是可編輯說明，不是數位簽章或不可竄改證明。
- 保留隱藏 Key、A2 當週 WeekID、原欄位與有效比例；使用同週下載的範本。角度通過仍須通過週別、機型、必填、數量與比例等原有檢查。

來源：P + Controllers/PmForecastController.cs、Model/PmForecastModel.cs、Service/PmForecastService.cs、Repository/PmForecastRepository.cs、Repository/IPmForecastRepository.cs、Entity/SD/PmForecast_ModelForecasts.cs。

### 資料庫與部署相依

- 資料庫執行腳本留在 PortalAPI repository：`docs/issue-assistant/systems/pmforecast/add-country-code.sql`（轉換）、`verify-country-code.sql`（唯讀結構檢查）。這些是工程交付檔，未隨 Skill 提供；需要執行時由有權限的維護者取得對應版本。
- 先在確認的測試環境轉換欄位／索引，再部署依賴 CountryCode 的 API。轉換新增欄位並以空字串回填既有資料，建立合法值檢查及三欄唯一索引；先確認備份、既有索引與資料。
- 舊的 Model_SYS_ID＋WeekID 唯一索引會阻止多角度並存；腳本發現時停止，不自動刪除索引。非法既有角度、重複三欄組合或不符的欄位／索引定義也需先處理。
- 唯讀 SQL 只查 CountryCode 欄位、唯一索引與合法值限制，不需填測試機型或 WeekID。預測數值與角度隔離由 API 上傳後重新下載確認；已驗證的結果不再安排相同 SQL 數值查核。
- 初始欄位轉換只需按環境確認；後續範本角度檢核與名稱調整不需新增 SQL。提供腳本或通過測試不代表已執行資料庫變更。
- 有 IN／BR 資料後不可直接刪欄回滾，需先保全三角度資料並檢查機型／週別唯一性碰撞，再另行規劃。

### 按需查核與驗收原則

API 回應與下載檔已確認的結果無須重複驗證。需要直接查 DB 排錯時，repository 的 `docs/issue-assistant/systems/pmforecast/query-country-forecast.sql` 可限定測試機型與週別查詢數量；使用前確認測試環境與授權。

### 可重做的核心驗證

- 使用同一可覆寫的測試機型及 MP 日期後可填寫週次，其他國家／IN／BR 分別上傳 10／20／30；只重傳 IN＝40 後，三份匯出應為 10／40／30。已確認通過的同版本、同環境結果無須再以 SQL 重複核對；新變更、失敗或資料疑義時再安排相關驗證。
- 另驗證缺省角度、非法值、全部九組範本配對、缺漏 B2 與舊名稱相容；具體人工操作及歷程保存在 Notion，完成勾選不等同工具實測。
- 可執行測試與命令留在 repository，工程人員按需讀取 [Repository 診斷與修復](../../repository-workflow.md)。通過隔離測試不能視為 SQL Server、實際 Storage 或完整使用流程已驗收。

## 操作與功能
- 查詢：P + Repository/PmForecastRepository.cs:GetModelList。機種／品牌使用 Contains；SYS_ACTI 預設 Y（Model/PmForecastModel.cs:GetModelListRequest）。分頁 skip=(StartIndex-1)*GetCount，建議從 1、正數筆數開始；省略這兩個 int 欄位會是 0，可能空結果或負 Skip，應先核對請求，不能斷言一定是資料遺失。
- 維護：Repository.SaveModel 只找既有 SYS_ID，更新 SYS_ACTI 和 MpDate；找不到時 Service.SaveModel 回 NoData。Controller 的新增／修改註解不能證明已有新增功能。
- 匯出：Service.ExportForecast，第 1 列為隱藏欄位 Key，第 2 列 A2 為當週 WeekID，第 3 列顯示欄名，第 4 列起為資料。每週含總數、比例(%)、數量。
- 週範圍：Service.ExportForecast／ImportForecast 設 startWeekNum=14、endWeekNum=26。開始為 currentSunday+15週；結束依 currentSunday+26週所在年的下一年一月一日減七天。不能簡化說成「只輸出 14～26 週」。
- 數量：Service.ImportForecast 計算 Ceiling(總數 × 配置用量 × 比例 / 100)。匯出 Excel 使用 ROUNDUP。匯入不直接採信 PartQuantity 欄；UsageQty 使用配置。輸入比例的實際 Excel 儲存值如何由共用 Utility 讀取，需以測試檔驗證，不能僅憑畫面 50% 就斷定後端讀到 50 或 0.5。
- MP 日期：匯出時 MP 前週格以灰底顯示；匯入時 weekInfo.Dates.Max < MpDate 的週資料略過。MpDate 為 nullable，邊界行為仍需測試確認。
- 匯入：先通過上述角度標頭檢查，才進入第 4 列起的明細讀取、空資料判斷、原檔備存及既有資料驗證／寫入；空白 ModelName 列會被略過，不能推測 Utility 對合併儲存格一定有補值。

## 常見訊息與處理
| 訊息／狀態名稱 | 程式判斷 | 建議下一步 |
| --- | --- | --- |
| Template week mismatch. Please download the latest PM Forecast template and import again. | Service.ImportForecast，A2 與 GetWeekIDs(currentSunday,currentSunday) 不同 | 重新匯出當週範本，保留隱藏列與 A2，再移入資料；勿只改 A2 掩蓋舊週欄位 |
| Model '…' for Brand '…' not found. | ImportForecast | 核對啟用機種與實際檔案；存在品牌同名機種風險，不能斷言品牌比對正確 |
| Part '…' with Category '…' not found for model '…'. | ImportForecast | 核對機種對應的啟用零件、Category 及 ItemName |
| ImportDataError | ImportForecast，有任一錯誤先產生錯誤 Excel 並返回，不執行 SavePmForecastData | 從回傳 FilePath 取得錯誤檔，讀每列新增第一欄訊息後逐一處理 |
| UploadFileError | ImportForecast，Storage 上傳失敗 | 提供發生時間與去識別 Log；涉及共用 Storage 時標 SHARED_COMPONENT，不能直接改共用元件 |
| OtherError | SaveModel 或 ImportForecast catch Exception | 先取得去識別例外與時間，不能單由此狀態判定根因 |

上述為 enum 名稱，未確認前端顯示文案或數值碼。

## 已知風險，尚未現場重現或修復
1. ImportForecast 以 ModelName 找機種，沒有 BrandName 條件；同名跨品牌時可能選錯。ImportForecast 將 preModelName 設成 dto.BrandName，與迴圈內的 ModelName 比較不一致；應分別重現，不能合併斷言造成所有匯入失敗。
2. Repository.GetWeekIDs 使用 weekData == null && weekData.Count == 0。ToListAsync 通常回空集合；空週別未在此明確擋下，ExportForecast 後續 Min/Max 遇空集合可能例外。需隔離測試確認日期資料缺漏案例。
3. 數字 DTO 有 Quantity1～80／PartRatio1～80；實際匯出週數依日期計算，超出容量的行為尚未驗證。

## Log 與待補資料
共用 Skill 不包含現場 Log 或連線資料。可請使用者提供限定 PMForecast、去識別化的錯誤時間／訊息／Correlation ID／測試 Excel；有 repository 時，外部檔案須經核准才納入檢索範圍。
待補：前端 Repository／測試網址、角色權限與操作 SOP、週別與比例業務規格、去識別範本及錯誤檔、隔離 DB／Storage 與測試方式。
