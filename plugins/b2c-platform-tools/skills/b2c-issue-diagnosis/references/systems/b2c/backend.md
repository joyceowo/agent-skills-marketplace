# B2C 後端 PortalAPI

預設來源讀 [system.json](system.json) 的 `repositories.backend`；來源由使用者確認。本機目錄依 [初始化與路徑解析](../../common/initialization.md) 的 `--system b2c --role backend` 取得。

核對版本與縮寫見 [索引](index.md)。找功能／文件時查 [功能索引](functions.md)，需對照 API 時查 [入口對照](entry-map.md)；已有 Controller 線索可直接依注入介面追 Service、Repository、Model／Entity 與直接相依。

| 要找的內容 | 位置 |
| --- | --- |
| 啟動、共用註冊 | `A/Program.cs` → `A/Providers/StarupProvider.cs`（檔名如此）、`OpenIddictProvider.cs`、`DependencyInjectionProvider.cs`、`DbContextExtensions.cs`；詳見 [共用機制](shared-mechanisms.md)。 |
| 功能 API | `A/Areas/<Area>/Controllers/`，路由可能來自同目錄 Base Controller；Area 目錄的點號不一定等於 URL 斜線。全域 Token／檔案入口另在 `A/Controllers/`。 |
| 邏輯與資料 | 對應 Area 的 `Service/`、`Repository/`、`Model/`、`Entity/`、`Profiles/`；依引用定位，不假設每區都有全部目錄或相同模式。 |
| 已有業務說明 | 按 [功能索引](functions.md) 連到原文件，例如 `PortalAPI:Docs/ShareRate/README.md` 及其 Base／Calculation 文件；根 README 仍為範本，不是完整專案規格。 |
| 編譯與測試入口 | `A/PortalAPI.csproj` 目前為 `net8.0`；`PortalAPI:PortalAPI.Tests/PortalAPI.Tests.csproj`。本次未執行業務測試或啟動 API。 |

前後端分別檢查 Git 狀態與實際變更；Portal 也有自己的 `Portal_Net5/Controllers/`／`Service/PortalAPI.cs` 中介，不把它當成這裡的後端根目錄。

設定程式路徑不需要 DB 帳密；只有需要現場資料時才依 [資料存取](../../common/data-log-access.md) 確認環境及取用對應憑證。不以初始化為由啟動可能連正式資料的 API。
