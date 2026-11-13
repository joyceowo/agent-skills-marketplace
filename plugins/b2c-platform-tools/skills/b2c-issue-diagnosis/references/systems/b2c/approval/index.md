# 簽核流程與 PDF

[核對範圍與路徑縮寫](../index.md)。關鍵字：簽核、流程、PDF。

| 定位項目 | 來源 |
| --- | --- |
| 既有文件 | `V/src/pages/Process_Confirm/README.md`、`V/src/pages/PageToPdf/README.md`。 |
| 前端／封裝 | `V/src/pages/Process_Confirm`、`V/src/pages/PageToPdf`；`V/src/api/processSign.js` |
| 後端 | `A/Areas/Digital.Process/Controllers/ConfirmController.cs`；另經 Portal 的 `Portal:Portal_Net5/Controllers/ProcessController.cs`／`Portal:Portal_Net5/Controllers/PdfController.cs`。 |
| 定位狀態 | 已定位前後端入口；入口核對不代表操作或部署驗收。 |

簽核前後處理、UserID 與檔案／PDF 請按實際呼叫追查，見 [API 中介對照](../entry-map.md#經-portal-中介的請求)。

## 既有需求來源

README 的需求資料夾已核對：[簽核元件規劃 v1（UI & SQL）](https://docs.google.com/presentation/d/1FoQCRGNm8DX3l4mU-U_OycFFSJP4PQxynAB3UgMPTdQ/edit?usp=drivesdk) 第 8–16 頁為設定 UI，第 28／34 頁為簽核與 Portal 中介 API；[v2](https://docs.google.com/presentation/d/1TibDjtBeb4bJ9eXi5C-y0sIvS-Z7ZKZo-jPwwlGcZgY/edit?usp=drivesdk) 第 13–14 頁為前後處理與簽核類別。2026-11-13 讀取文字；屬歷史設計，不代表全部已實作／部署。

其他 API 按封裝及 Controller 直接追查；共用登入、附件與資料轉換按需讀 [共用機制](../shared-mechanisms.md)。
