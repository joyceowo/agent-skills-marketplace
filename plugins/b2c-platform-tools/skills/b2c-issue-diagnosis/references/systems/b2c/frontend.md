# B2C 前端 Portal

預設來源讀 [system.json](system.json) 的 `repositories.frontend`；來源由使用者確認。本機目錄依 [初始化與路徑解析](../../common/initialization.md) 的 `--system b2c --role frontend` 取得。

核對版本與縮寫見 [索引](index.md)，遵循目標路徑適用的 AGENTS.md。環境／啟動問題查 `Portal:README.md`；需要找頁面或需求文件時查 [功能索引](functions.md)，已有檔案或 API 線索則直接追查。外部需求文件僅讀本案相關部分。

| 要找的內容 | 位置 |
| --- | --- |
| Vue 多頁與實際輸出網址 | `V/vue.config.js` 的 `pages`／`entry`／`filename`；頁面從 `V/src/pages/<頁面>/main.js` 開始，頁內 router 再追 `router.js`。 |
| 畫面、事件、傳值 | `V/src/pages/<頁面>/App.vue`、`view/`、`components/`；Vuex 另見 `V/src/store_*/`、`V/src/stores/`。各頁結構以實際檔案為準。 |
| 請求與後端入口 | `V/src/api/`；按 [入口對照](entry-map.md) 區分 Portal 中介與 PortalAPI，不以同名檔案推定呼叫關係。 |
| 共享問題 | [共用機制](shared-mechanisms.md)：動態選單、登入、axios、附件、i18n。 |
| 執行環境 | 已核對 `V/package.json` 為 Vue 2／Vue CLI 4；Portal 的 `Portal_Net5/Portal.csproj` 使用 `netcoreapp3.1`。安裝／建置入口依根 README、`V/.nvmrc`、package scripts，不在索引重寫完整手冊。 |

目前 `V/src/pages/<頁面>` 存在不代表已納入建置；是否輸出看 `vue.config.js`，是否出現在使用者選單另由 API／權限決定。另有 `Portal/website.publishproj`（TargetFrameworkVersion v4.6.1 的網站發佈專案）；現行 `Portal:Portal_Net5.sln` 只引用 `Portal_Net5/Portal.csproj`。已區分專案用途，舊發佈專案是否另有部署仍未確認；`wwwroot/` 靜態內容與 Vue 原始碼分開看。

測試／本機網址已可從 `Portal:README.md`「環境網址」定位：前端測試入口 `https://gigabyte-b2c-portal-net5-testing.azurewebsites.net/index.html`；`V/src/pages/SalesTQM/README.md` 留有 API 測試 Swagger `https://gigabyte-b2c-portalapi-net5-testing.azurewebsites.net/swagger/index.html`；本機為 `http://localhost:9000/login.html` 配合 `https://localhost:5001`。這是文件中的候選入口，未驗證線上可用性或部署版本，不能據此選 DB 環境。

涉及畫面與後端結果差異時，沿同一 API 追到後端，不僅憑名稱推定對應模組。需要讀後端時才補後端路徑。未讀程式／未操作頁面時，不宣稱已核對前端實作或重現。
