# DB 資料來源、關聯與副作用

本文件協助從功能定位資料來源，並保留會影響查詢、資料修正與重試判斷的關聯及副作用。完整欄位與業務規則沿用既有文件及程式，不在此重複列出。來源路徑縮寫見 [B2C 系統索引](index.md)：`A/` 為後端 `PortalAPI_Net5/`，`PortalAPI:` 為後端儲存庫根目錄；搭配當次本機後端路徑定位。

核對日期：2026-11-13；程式基準：`e821ed599ad7d23ef388894c0f2cac6a057df4eb` 的本機工作樹。以下「程式已核對」表示已閱讀實作，不代表已操作、已部署或取得業務認可；本次未啟動 API、執行 SQL 或連線 DB。現場主機、資料庫、約束與外部程序的實際版本均待確認。

## 資料來源與連線定位（程式已核對）

DbContext 自動註冊（`A/Providers/DbContextExtensions.cs`） 優先讀取 `DbContextConfig.ConnectionString`；未指定時，將類別名稱中的 `Context` 移除後作為 `ConnectionStrings` 的設定鍵，使用 `UseSqlServer` 註冊。`Ignore = true` 的類別不走此流程。認證用 `DefaultDbContext` 則由 OpenIddictProvider（`A/Providers/OpenIddictProvider.cs`） 另外以 `DefaultConnection` 註冊。

下表列設定鍵及使用它的 Area；Area 名稱以 `PortalAPI_Net5/Areas/` 為根。多個 Area 的同名 Context 是不同類別，可能使用同一設定鍵；設定鍵不是實際資料庫名稱，也不能證明不同環境指向相同資源。`Source`／`SOURCE` 保留程式原拼法，不能據此認定為兩個不同 DB。

| 連線設定鍵 | Area／用途與 Context 定位 |
| --- | --- |
| `Digital` | `Digital.Common`、`Digital.Process`、`Digital.System`、`Global.BUFee`、`Global.BURebateSign`、`Global.ECredit`、`Global.RMAServices`、`Reporting`、`Sales.Fcst`；各自的 `Entity/Digital/DigitalContext.cs`。 |
| `Global` | `Global.BUFee`、`Global.Bulletin`、`Global.BURebateSign`、`Global.ECredit`、`Global.RMAServices`、`Reporting`；各自的 `Entity/Global/GlobalContext.cs`。 |
| `SD` | `Sales.Fcst`、`Sales.FCSTRolling`、`Sales.HQOrder` 的 `Entity/SD/SDContext.cs`；`Sample.Test` 的 `Entity/SDContext.cs`。範例入口不代表正式功能。 |
| `Source`／`SOURCE` | `Global.BURebateSign`、`Global.RMAServices`、`Sales.HQOrder` 的 `Entity/Source/SourceContext.cs`；`Sales.PMBottomPrice` 的 `Entity/SOURCE/SOURCEContext.cs`。 |
| `SALES` | `Sales.Estimate` → `EstimateReversingContext`；`Sales.PMBottomPrice` → `PMBottomPriceContext`；`Sales.PMUploadPrice` → `PMUploadPriceContext`；`Sales.Target` → `SalesTargetContext`；`Sales.TQM` → `SALESContext`（檔名 `SalesContext.cs`）；`Sales.Tran` → `TranContext`。均在各 Area 的 `Entity/SALES/`。 |
| `ReportDB` | `Global.FinEngine` → `ReportDBContext`；`Sales.ELearning` → `ELearningContext`；`Sales.RMAExps` → `RMAExpsContext`。均在各 Area 的 `Entity/ReportDB/`。 |
| `B2CDEVGlobal` | `Global.ECredit` 的 B2CDEVGlobalContext（`A/Areas/Global.ECredit/Entity/B2CDEVGlobal/B2CDEVGlobalContext.cs`）；`Purchase.ShareRate` 的 ShareRateB2CDEVGlobalContext（`A/Areas/Purchase.ShareRate/Entity/B2CDEVGlobal/ShareRateB2CDEVGlobalContext.cs`）。後者沒有 DbSet，仍會執行計算 SP。 |
| `Purchase` | `Purchase.ShareRate` 的 ShareRateContext（`A/Areas/Purchase.ShareRate/Entity/Purchase/ShareRateContext.cs`）。 |
| `Marketing` | `Sales.MKTUpload` 的 MarketingContext（`A/Areas/Sales.MKTUpload/Entity/Marketing/MKTContext.cs`）；檔名與類別名稱不同。 |
| `CustStockSystem`、`GUPS` | `Cust.Stock` 的 CustStockSystemContext（`A/Areas/Cust.Stock/Entity/CustStockSystem/CustStockSystemContext.cs`） 與 GUPSContext（`A/Areas/Cust.Stock/Entity/GUPS/GUPSContext.cs`）。 |
| `CNOrder` | `Sales.CNOrder` 的 CNOrderContext（`A/Areas/Sales.CNOrder/Entity/CNOrder/CNOrderContext.cs`）。 |
| `USOrder`、`USOrderAbp` | `Sales.USOrder` 的 USOrderContext（`A/Areas/Sales.USOrder/Entity/USOrder/USOrderContext.cs`） 與 USOrderAbpContext（`A/Areas/Sales.USOrder/Entity/USOrderAbp/USOrderAbpContext.cs`）；不能因 Entity 同名就合併來源。 |
| `DefaultConnection` | 認證用 DefaultDbContext（`A/Entity/Auth/DefaultDbContext.cs`），不屬於業務 Area。 |

ECredit 的外部 ERP 回寫另依 AppSettings 型別（`A/Service/AppSettings.cs`） 的 `ERP.Tiptop.Connection`、`ERP.Tiptop.CNConnection`、`ERP.Navision.Connection` 選擇 linked server，經 `B2CDEVGlobal` 執行 `OPENQUERY`。這些設定不能只從 DbContext 表格得知；實際設定值與遠端對象須於當次環境核對，不在本文件保存連線字串或秘密。

## 關鍵關聯與副作用（程式已核對）

| 流程 | 已核對的關聯／順序及判斷邊界 | 程式來源 |
| --- | --- | --- |
| 客戶庫存匯入 | 先由 `GUPS.SYS_TPFUserInfo` 依工號取得部門，再保存 `CustStockSystem.ImportCustStock_temp`，以 `Upload_Id` 呼叫 `USP_ImportCustStock` 或 USA 分支的 `USP_ImportCustStock_USA`。暫存資料先於 SP 保存；SP 的最終更新表與回復方式待確認。 | CustStockRepository.InsertImportCustStockLaptopTemp（`A/Areas/Cust.Stock/Repository/CustStockRepository.cs`） |
| RMA 費用匯入 | 依 MB／NB／D／VGA 選擇 `FACT_Profit_RMAExps_*_TEMP`，先清空整張表，再 Bulk Copy、執行 `USP_FACT_Profit_RMAExps_Import`，最後保存上傳紀錄。它是共用持久暫存表，不是只清本次批次；此方法未以單一顯式交易包住全部步驟，不能假定失敗會還原整段。 | RMAExpsRepository.ImportRMAExpsExcelAsync（`A/Areas/Sales.RMAExps/Repository/RMAExpsRepository.cs`） |
| ECredit 匯入與 ERP 回寫 | TIPTOP／Navision 的本地頭、明細依 `DocumentNo` 與 `Version` 配對；匯入會增加版本並停用舊版頭檔。Service 先呼叫本地匯入，再回寫 ERP 狀態／B2C 單號，屬不同步驟。TIPTOP 的 HQ／CN 分支選不同 linked server、表與欄位前綴；Navision 也有不同單號分支。程式在 Global Context 開啟的交易不能據此當成 B2CDEVGlobal／遠端 ERP 的共同回復保證。 | TIPTOP 匯入順序（`A/Areas/Global.ECredit/Service/TiptopTransactions.cs`）、TIPTOP Repository（`A/Areas/Global.ECredit/Repository/TiptopRepository.cs`）、Navision 匯入順序（`A/Areas/Global.ECredit/Service/NavisionTransactions.cs`）、Navision Repository（`A/Areas/Global.ECredit/Repository/NavisionRepository.cs`） |
| 簽核父鍵與資源資料 | `SYS_ConfirmProcess` 以 `ProgramID + SYS_PARENT_ID` 定位業務單據；`SYS_ConfirmProcess_MaterialData.SYS_PARENT_ID` 則指向流程主表的 `SYS_ID`，同名欄位不是同一種父鍵。資源更新只處理請求所含 `ColumnID`，會刪除這些欄位中原有但本次未保留的值；不是單純追加。 | ConfirmRepository.UpdateConfirmProcessAndMaterialData（`A/Areas/Digital.Process/Repository/ConfirmRepository.cs`） |
| 簽核前後處理 | API 位址由 `SYS_ConfirmProgram` 關聯 `SYS_ConfirmSystem` 取得。`FullSign` 在有設定時先呼叫前處理，通過後簽核，再以背景工作呼叫後處理；簽核本身會呼叫 `USP_ConfirmProgram_SignOff`。簽核回應與後處理完成須分開判斷，不能視為一個跨 API／DB 的共同交易。 | 設定與程序入口（`A/Areas/Digital.Process/Repository/ConfirmRepository.cs`）、ConfirmService.FullSign（`A/Areas/Digital.Process/Service/ConfirmService.cs`）、程序參數（`A/Areas/Digital.Process/Entity/Digital/DigitalContext.cs`） |
| MKT 與 TQM 匯入 | MKT 先保存 `MKTDetail_UploadData_temp`，再以 `Upload_ID` 呼叫 `USP_MKTDetail_Upload`。TQM 則用 `TransactionScope` 包住暫存新增、批次號更新與 `USP_TQMItem_ReplyUpdated` 呼叫。不同模組不能套用同一種提交、清理或重試假設；外部 SP 內部行為待確認。 | MKTUploadRepository（`A/Areas/Sales.MKTUpload/Repository/MKTUploadRepository.cs`）、SalesTQMRepository.CreateTQMItemList_ReplyData（`A/Areas/Sales.TQM/Repository/SalesTQMRepository.cs`） |
| Forecast 同步 Rolling | `SyncFCST2RollingAccount` 使用 SD Context 的連線呼叫 `USP_Rolling_Forecast_FcstSync2Rolling`，傳入區域、子區域、產品線、機種類型與使用者，取回 `ErrorCode`／`Log`。最終寫入表、覆寫範圍與能否重跑，需取得 SP 定義才能確認。 | ForecastRepository.SyncFCST2RollingAccount（`A/Areas/Sales.Fcst/Repository/ForecastRepository.cs`） |

## 既有文件與結構定義

- **Share Rate**：總覽與建置順序（`PortalAPI:Docs/ShareRate/README.md`）、來源及匯入／查詢規則（`PortalAPI:Docs/ShareRate/Base/README.md`）、品質與配合度欄位／DDL（`PortalAPI:Docs/ShareRate/Base/ShareRate_DB_Schema.md`）、計算、紀錄表與失敗邊界（`PortalAPI:Docs/ShareRate/Calculation/README.md`）。沿用原文件，不在此複製完整規則。`ShareRate_Result` 的外部產生流程與 DDL 尚未隨此 repository 保存；兩支計算 SP 的現存 SQL 為等待後結束的佔位邏輯，不代表正式計算已實作或部署。
- **PMForecast**：SDContext（`A/Areas/Sales.Fcst/Entity/SD/SDContext.cs`） 定義設定主從及預測主從關聯；預測頭檔 Entity（`A/Areas/Sales.Fcst/Entity/SD/PmForecast_ModelForecasts.cs`） 宣告 `Model_SYS_ID + WeekID + CountryCode` 唯一索引；Repository（`A/Areas/Sales.Fcst/Repository/PmForecastRepository.cs`） 的國別查詢與保存據此區隔。這是程式模型證據，不能證明現場索引或外鍵已套用。
- **認證 migrations**：DefaultDbContextModelSnapshot（`A/Migrations/DefaultDbContextModelSnapshot.cs`） 與目前兩組 migration 均屬於 `DefaultDbContext`，涵蓋認證資料；不是全部業務 DB 的建置或升級腳本。
- 其他 SP／View 的結果 Entity 與呼叫包裝可協助理解參數、回傳欄位，但不等於 DB 物件定義。本機未找到的定義不可由名稱、註解或 DTO 推導成已確認規則。

## 待確認項目

| 項目 | 已知線索與仍缺證據 |
| --- | --- |
| 外部程序與 View | 簽核、Forecast／Rolling、客戶庫存及各匯入流程可定位呼叫端；多數 SP、View 定義未隨此 repository 保存。其讀寫表、內部交易、跨 DB 相依、Trigger／排程及重跑影響，須核對實際定義與版本。 |
| 現場 schema 與部署 | Entity 的關聯、索引、欄位型別及現有 SQL 只代表程式模型／檔案內容。正式與測試的實際物件、約束、資源對應及部署進度，本次未連線確認。 |
| Share Rate 結果來源 | 既有文件已標示由外部流程產生；該流程的維護位置、實際排程及完整結果表定義仍待取得。 |
| CNOrder 歷史 ODBC 入口 | OrderRequestRepository.InsertOrderToTiptop（`A/Areas/Sales.CNOrder/Repository/OrderRequestRepository.cs`） 存在清除後重寫 `order_file` 的 ODBC 程式，但該方法內連線字串為空，本次在目前 C# 中只找到方法定義。不得列為已可用或已部署的傳送通道。 |
| 歷史需求與業務認可 | 相關 README 的外部需求／設計連結未在本次重新讀取；程式行為不代表現行 SOP 或業務已認可。 |

更新此導覽時只補會影響定位或判斷的差異，保留來源、核對日期及待確認限制；完整欄位、既有業務文件與個案 SQL 各留原維護位置。
