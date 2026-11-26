# B2C 資料來源與憑證對應

## Blob log

問題診斷用 Azure Blob log，優先依 [共用 Azure Blob 流程](../../common/azure-blob-logs.md) 用公司 Entra 帳號登入；非秘密來源由每位安裝者按環境保存，不把個人帳戶／租戶資源資訊寫入套件。此登入與 Portal 網站登入分開，登入不能自動取得新角色。

2026-11-13 已核對兩個 repository 的 NLog 候選：Testing／Develop 容器名 `testing-portal-logs`，Production／Staging 為 `portal-logs`；路徑為 `yyMMdd/<api-areas>.log`（變數 `log-fullpath`）。相同容器名不證明 Storage account 相同，亦不表示各部署真的沿用設定。初始化先核對實際 account、container、租戶 GUID 與環境，再採用；不把 Develop／Testing 或 Staging／Production 自動視為同一來源。

從已確認環境的 PortalAPI `nlog.<環境>.config` 解析 Blob target 的帳戶、容器及 `blobName`，展開日期和 API 路徑。若部署有覆寫，優先採用該環境的實際端點。只取定位欄位，避免輸出完整連線字串。

要確認登入租戶時，對該 Azure 公有雲帳戶下的目標 Blob URL 發送不帶憑證或 SAS、禁止重新導向的 HTTPS `HEAD`，指定 `x-ms-version: 2022-11-02`。從 `401` 的 `WWW-Authenticate: Bearer` 取出 `authorization_uri`，核對其為 `https://login.microsoftonline.com/<租戶 GUID>/oauth2/authorize`，再用該 GUID 核對已保存來源與 Entra 登入。網站登入租戶、訂閱顯示名稱與容器名稱都不足以識別 Storage 租戶；直接讀 Blob 無須使用者提供訂閱 ID。若端點未回有效 challenge，才請使用者提供此 Storage 的租戶 GUID。首次保存或更換來源及互動登入沿用共用流程。

日誌時間格式候選為 `yy-MM-dd HH:mm:ss`，未含時區；ActivityId 在 layout 只保留前 5 字元。查詢先用已確認日期的 `yyMMdd/` 與功能 prefix，再按短 ActivityId／API 收斂；需精確時間時另確認部署時區。Blob 生命周期與實際保留期限仍待環境確認，程式的檔案 archive 數量不代表 Blob 保留天數。

## DB 與既有 Storage 憑證

需要定位 DB 資料來源、關聯或副作用時，先讀 [DB 導覽](database.md)，再核對當次程式及定義；單純設定憑證不要求讀取，也不因此連線 DB。

依 [共用資料存取](../../common/data-log-access.md) 設定與取用；此資料僅適用 B2C，不授予查詢權限。[system.json](system.json) 的 `credential_namespace` 為 `b2c`，沿用既有鍵，不遷移或要求已設定的使用者重填。

| 環境／用途 | service | 紀錄鍵 |
| --- | --- | --- |
| 測試 DB | `b2c/test/db` | `connection` |
| 測試 Storage | `b2c/test/storage` | `connection` |
| 正式 DB | `b2c/prod/db` | `connection` |
| 正式 Storage | `b2c/prod/storage` | `connection` |

現有 [credentials.py](../../../scripts/credentials.py) 是 B2C 憑證工具，保留原有命令與鍵名。其他系統未提供自己的憑證對應與工具前，不能默認使用它或共用以上登入。

四筆獨立，按需設定；只設前後端路徑或走上述 Entra Blob 流程時不讀保管庫。帳密初始設定可在沒有程式路徑時進行，但只確認本次設定目標，不連線。既有 Storage 鍵保留相容，只有明確使用該憑證方式才取用，不作 Entra 失敗後的自動備援。服務名稱區隔不是權限隔離，亦不保證讀取時會再次要求人確認。

DB 主機／資料庫、Storage 帳戶／容器與測試網址仍須由當次非秘密設定及已確認環境核對；遠端 Git 網址不能證明環境。不在外掛保存個人帳密、含秘密連線字串或維護者私人的資源 ID。
