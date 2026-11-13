# B2C 共用機制定位

依問題只讀相關一列；路徑縮寫與核對版本見 [索引](index.md)。以下為程式已核對的定位線索，不代表已實測或業務規則已確認；只記影響追查的差異。

| 問題／關鍵字 | 優先入口 | 判斷線索 |
| --- | --- | --- |
| 網址打開錯頁、找不到 router | `V/vue.config.js` 的 `pages`、`entry`、`filename`；對應 `V/src/pages/<頁面>/main.js`／`router.js` | Vue 2 多頁建置；頁面內可再用 Vue Router，不能只找一份全站 router。 |
| 選單缺少、點擊開錯、iframe | `V/src/pages/Main/App.vue`、`V/src/components/layout/menuItem.vue` → `V/src/api/commonApi.js:GetMenuList` → `A/Areas/Digital.System/Controllers/ProgramController.cs`／`Service/ProgramService.cs`／`Repository/ProgramRepository.cs` | 選單由 API 取得，含使用者、節點與權限／快取處理；`public/menu.json` 不足以證明目前選單。實際權限資料未查。 |
| 登入失效、重導、切換身分 | `V/src/api/common/auth.js`、`authInterceptor.js`、`loginRedirect.js`、`loginState.js`、`V/src/api/oauth.js` → `Portal:Portal_Net5/Controllers/HomeController.cs`／`Provider/TokenHeaderMiddleware.cs` | `/CheckLogin` 以 HTTP 200／401 區分；首檢後有成功狀態快取。跨站身分另經 `/auth/ensure-user-context`；不要把網路錯誤直接判為登入失效。 |
| API Token／401／403 | `A/Program.cs` → `A/Providers/OpenIddictProvider.cs`、`RequireAuthenticationExtensions.cs`、`A/Controllers/AuthorizationController.cs` | 與 Portal Cookie／Session 入口分開追；授權方案依實際 endpoint 設定核對，不由頁面有權限推定所有 API 行為。 |
| 傳值空白、陣列、查不到資料 | `V/src/api/common/instance.js`；各 `V/src/api/*.js` | 共用 instance 會移除空字串／null／undefined 查詢值，處理陣列序列化並補空 POST body。其他封裝另建 axios，須先看頁面實際用哪一個。 |
| 畫面錯誤訊息與後端不同 | 各 API 封裝的 `codeMap`、`V/src/api/common/instance.js` → `A/Providers/ApiResponseProvider.cs`、`StarupProvider.cs` | 部分舊封裝會將 `StatusCode` 改成文字；HTTP 狀態與業務 `StatusCode` 分開看。共用 instance 的 2016 會嘗試下載錯誤檔，不等於成功。 |
| UserID 傳了卻變更、身分資料不符 | Portal 中介 Controller／`Portal:Portal_Net5/Service/Infrastructure/CommonFunction.cs`；`A/Providers/UserIdActionFilterProvider.cs` | Portal 可由 Session 補身分；PortalAPI 的全域 filter 也可能依登入者及管理員判斷覆寫 `UserID`。以當次入口核對，不直接信任畫面送值。 |
| 上傳太大、批次部分失敗、附件消失 | `V/src/utils/uploadBatch.mjs`、`V/src/api/portalFileApi.js`、`portalEditerFileApi.js` → `A/Controllers/PortalFileController.cs`／`A/Service/PortalFileService.cs` | 有請求大小檢查、分批與部分失敗處理；不能把某一批完成當全部完成。模組 Excel 匯入可能走自己的 Controller 或 Portal 中介。 |
| Excel／下載檔／Storage | `V/src/module/common.js:exportFileHandler`；`A/Service/ICommonExcel.cs`／`Infrastructure/CommonExcel.cs`、`ICommonStorage.cs`／`Infrastructure/CommonStorageAzure.cs`／`CommonStorageLocalFile.cs` | Storage 實作由 `A/Providers/StarupProvider.cs` 選擇；下載也有不同入口，從實際 wrapper／回傳 `FilePath` 查，不猜遠端帳戶。 |
| 共用下拉、產品線、幣別 | `V/src/api/commonApi.js` → `A/Areas/Digital.Common/Controllers/CommonController.cs`；模組自己的 `CommonController` | 同名 Common 屬不同 Area，先核對完整 API 路徑。 |
| 服務實作、DB Context、連線選錯 | `A/Program.cs`、`A/Providers/DependencyInjectionProvider.cs`、`DbContextExtensions.cs`；模組 `Entity/`、`Model/`、`Profiles/` | Service／Repository 有命名與介面自動 DI；Context 可用 Attribute 指定連線名稱，否則依 Context 名稱取得。只定位設定鍵，不保存帳密或連線字串。 |
| 例外、log、請求關聯 | `A/Providers/LogMiddlewareProvider.cs`、`A/Program.cs`；兩專案的 `Portal_Net5/nlog*.config`／`PortalAPI_Net5/nlog*.config` | Blob 來源候選、日期格式與 ActivityId 截短集中見 [資料來源](data-access.md#blob-log)。預設 File 寫 `Log/${log-fullpath}.log`、歸檔上限 2000 檔；檔數不代表 Blob 保留天數，實際部署與保留政策仍待確認。 |
| 翻譯缺字、顯示語系 | `Portal:docs/agents/i18n.md` → `V/src/i18n.js`、`V/public/locales/` | 先依專案既有 i18n 文件定位，避免只改單一頁面文案。 |

跨模組修改前辨識其他呼叫者；本表只協助定位，不授予共用邏輯修改、資料更新或部署權限。
