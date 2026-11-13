# 範例測試入口

[核對範圍與路徑縮寫](../index.md)。關鍵字：Sample.Test、範例測試入口。

| 定位項目 | 來源 |
| --- | --- |
| 前端／呼叫者 | 本次未在 Vue 找到對應路由呼叫；外部呼叫者、選單與啟用狀態待確認。 |
| 後端 | `A/Areas/Sample.Test/Controllers/CRUDController.cs:TestGet`／`TestPost`／`SendMail`：範例測試入口，不自行執行。 |
| 定位狀態 | 僅後端入口；呼叫者待確認；入口核對不代表操作或部署驗收。 |

此為定位用的範例入口；未授權時不執行 TestPost 或 SendMail。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
