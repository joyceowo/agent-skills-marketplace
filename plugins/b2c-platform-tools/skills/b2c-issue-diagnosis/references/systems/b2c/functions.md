# B2C 功能與文件索引

已有檔案／API 線索可直接追查；需要定位時從下表讀本案模組的 `index.md`。版本與縮寫見 [系統索引](index.md)，完整 Method／路徑對照見 [入口對照](entry-map.md)。

已盤點模組使用相同的單一入口，連到既有文件與前後端程式；特殊規則只保留有依據的補充。未列功能仍可直接分析，索引不代表全部上線功能或業務驗收。

## 平台環境與共用資料

- 環境、啟動、建置：`Portal:README.md`，命令再核對 `V/package.json`／`V/vue.config.js`。
- 登入、選單、附件、資料轉換與 log：[共用機制](shared-mechanisms.md)。
- 多語系：`Portal:docs/agents/i18n.md`。
- 模組 README 多含歷史需求連結，完整度及部署適用性需依本案核對。

## 頁面與功能模組

| 功能／關鍵字 | 模組定位文件 | 入口狀態 |
| --- | --- | --- |
| 登入、跨站、切換身分 | [登入、跨站與切換身分](auth/index.md) | 已定位前後端入口 |
| 首頁、選單、待辦 | [首頁、選單與待辦](home/index.md) | 已定位前後端入口 |
| 公告 | [公告](announcement/index.md) | 已定位前後端入口 |
| 簽呈、Rebate、促銷；簽呈統計；促銷簽呈、PPRebate | [Rebate、促銷簽呈與統計](rebate-sign/index.md) | 已定位前後端入口 |
| 簽核、流程、PDF | [簽核流程與 PDF](approval/index.md) | 已定位前後端入口 |
| 簽核流程設定舊頁 | [簽核設定舊頁](approval-settings/index.md) | 原型頁；啟用狀態待確認 |
| 總部接單、申請、週次、報表、產能 | [總部接單與週次管理](hq-order/index.md) | 已定位前後端入口 |
| Forecast、區域、機種 | [Forecast 預測](forecast/index.md) | 已定位前後端入口 |
| Rolling、DCM、週次 | [Rolling／DCM](rolling/index.md) | 已定位前後端入口 |
| PM Forecast、國家角度 | [PMForecast](pmforecast/index.md) | 已定位前後端入口 |
| Forecast／Rolling 同步紀錄 | [Forecast／Rolling 同步紀錄](forecast-rolling-report/index.md) | 已定位前後端入口 |
| HQ 費用預算／業績目標 | [HQ 費用預算與業績目標](hq-target/index.md) | 已定位前後端入口 |
| MKT 明細 | [MKT 明細上傳](mkt-upload/index.md) | 已定位前後端入口 |
| 價格、MSRP、Credit Spreadsheet | [價格、MSRP 與 Credit Spreadsheet](price-management/index.md) | 已定位前後端入口 |
| 成品運輸、陸運 | [成品運輸與陸運](transport/index.md) | 已定位前後端入口 |
| TQM、呆滯、報表上傳 | [Sales TQM 與呆滯報表](tqm/index.md) | 已定位前後端入口 |
| 預估、Estimate、沖銷 | [預估與沖銷](estimate/index.md) | 已定位前後端入口 |
| 銷折、ECredit、群簽 | [ECredit 銷折與群簽](ecredit/index.md) | 已定位前後端入口 |
| 付款申請、Fee、差旅報銷 | [付款申請與差旅報銷](fee/index.md) | 已定位前後端入口 |
| Oracle 服務費轉 AP | [Oracle 服務費轉 AP](fee-oracle/index.md) | 歷史 Controller；現行服務待確認 |
| RMA 客服 | [RMA 客服](rma-service/index.md) | 已定位前後端入口 |
| RMA 費用 | [RMA 費用](rma-expenses/index.md) | 已定位前後端入口 |
| ELearning 匯入 | [ELearning 匯入](elearning/index.md) | 已定位前後端入口 |
| 美國 EDI／PO Ack、產品資料 | [美國 EDI、PO Ack 與產品資料](us-order/index.md) | 已定位前後端入口 |
| 品質、品牌配合度風險、Share Rate | [Share Rate 品質與品牌配合度](share-rate/index.md) | 已定位前後端入口 |
| Power BI／Tableau | [Power BI 與 Tableau](reporting/index.md) | 已定位前後端入口 |
| PVT 重量／物流 | [PVT 重量與物流外站](pvt-weight/index.md) | 外站連結；外部實作待確認 |

## 僅後端入口

以下尚未在目前 Vue 對上路由呼叫；外部呼叫者與啟用狀態待確認。

| Area／關鍵字 | 模組定位文件 |
| --- | --- |
| `Cust.Stock`／客戶庫存上傳 | [客戶庫存上傳](cust-stock/index.md) |
| `Sales.CNOrder`／中國訂單、客戶與產品 | [中國訂單、客戶與產品](cn-order/index.md) |
| `Global.FinEngine`／FinEngine 通知 | [FinEngine 通知](fin-engine/index.md) |
| `Sales.PMBottomPrice`／PM 底價匯入與傳送 | [PM 底價匯入與傳送](pm-bottom-price/index.md) |
| `Sample.Test`／範例測試入口 | [範例測試入口](sample-test/index.md) |

`Digital.Common` 的共用入口見共用機制；動態選單與外站使本表不能代表所有已上線系統。
