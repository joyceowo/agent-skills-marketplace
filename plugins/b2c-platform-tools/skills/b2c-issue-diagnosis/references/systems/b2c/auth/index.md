# 登入、跨站與切換身分

[核對範圍與路徑縮寫](../index.md)。關鍵字：登入、跨站、切換身分。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/Login/README.md`、`V/src/pages/Login_Loading/README.md`、`V/src/pages/ChangeUser/README.md`。 |
| 前端／封裝 | `V/src/pages/Login`、`V/src/pages/Login_Loading`、`V/src/pages/ChangeUser`；`V/src/api/oauth.js`、`V/src/api/common/auth.js` |
| 後端 | 先看 Portal 的 `Portal:Portal_Net5/Controllers/HomeController.cs`；Token 發行另看 `A/Controllers/AuthorizationController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

網站登入與 API Token 入口分開追查，見 [登入與身分共用機制](../shared-mechanisms.md)。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
