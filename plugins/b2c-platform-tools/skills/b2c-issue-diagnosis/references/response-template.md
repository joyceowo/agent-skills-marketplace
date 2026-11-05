# 診斷回覆格式
先讀提供的程式碼，回覆操作問題、程式 Bug 或功能需求的判斷與解法。不要求 commit 或版本對照；[PMForecast 參考索引](systems/pmforecast/knowledge.md) 只補充背景與定位資訊。

報告 Schema 用於需要結構化輸出時的驗證，不要求每個問題都另存 JSON。個案工作紀錄以 Notion 為主，MD 只補充必要背景與無法直接從程式取得的約定，不逐案複製實作；SQL 與測試資料保留 Git。Notion 排版及人工結案方式依 [Notion 工作追蹤](notion-workflow.md)，不重複產生個案交付／驗收文件。

一般對話依下列順序簡短回覆，不必為每個欄位另開段落：
- 系統：名稱（system_id）
- 分類／影響：classification／impact_scope
- 結論與解法：直接說明如何處理、操作步驟或修改方案及預期結果；推測必須明講
- 預期／實際：各自描述；未提供寫「尚未提供」
- 證據：本次已實際讀取的程式片段、附件檔名或工作區路徑／方法；背景文件只作輔助，標示 CONFIRMED 或 HYPOTHESIS。未執行時不說已重現，不聲稱來源已部署。
- 處理：可執行步驟、是否需要修改、是否已有授權
- 驗證：實際執行、結果、未執行原因；不可把設定檢查當作業務修復驗證
- 狀態：ANSWERED／NEEDS_INFO／PROPOSED_FIX／FIXED／OUT_OF_SCOPE
- 待補：會改變判斷的最少資料

只有需要結構化交付且已連接 repository 時，才使用本 Skill 的 [diagnosis.schema.json](schemas/diagnosis.schema.json) 與 `scripts/IssueAssistant.ps1 -WorkspaceRoot <目標工作區> -ScopeJson <本次分析的範圍JSON> -Action ValidateReport -ReportPath <工作區內相對路徑>`。工具與命令見 [程式碼診斷與修復](repository-workflow.md)。[示範 fixture](../scripts/tests/fixtures/demo-diagnosis.json) 僅供合約測試，不是實際個案證據。一般對話或 Notion 工作卡不強制產生 JSON。

只提供片段時直接以文字交付，不因片段無法通過 repository 報告路徑檢查而停止分析。

完整 JSON 不知道的文字欄寫「尚未確認」，未知清單用 []。尚無法辨識系統時 system_id、system_name 用空字串，classification=UNKNOWN、status=NEEDS_INFO，補問目標資訊；只有實際越出可存取／授權範圍才用 OUT_OF_SCOPE。未收錄系統不構成 OUT_OF_SCOPE。
尚未重現的程式風險用 PROPOSED_FIX／NEEDS_INFO，不能 FIXED。Test-Json 及輔助工具只能檢查格式與範圍，測試文字是否真實及根因是否正確仍由診斷者核對。

## 涉及程式／資料庫變更的交付

最終回答除了結論與已執行測試，應直接包含可執行的核心驗收步驟。依變更需要補充下列資訊，不將單純問答膨脹成部署清單：

| 交付項目 | 應提供的內容 |
| --- | --- |
| SQL 檔案 | 可點擊的實際絕對路徑、各檔用途、已執行／未執行、正確執行順序；註解與自訂提示預設繁體中文 |
| 環境與前提 | 測試資料庫／測試 API、先套 DB 再啟動新版程式等必要順序；未知的位址、帳號與測試資料標示須替換 |
| 使用者驗收 | API 方法與路徑或指令、實際輸入、預期結果；錯誤輸入、重傳或資料隔離案例依需求選擇 |
| 通過判準 | 可觀察的回傳欄位、匯出值或唯讀查詢結果；不只寫「確認正常」 |
| 尚未驗證 | 分開列出已通過的自動測試，以及尚未執行的 SQL Server／真實 Excel／實際 API 驗收 |
| 圖與表 | 多情境用表格；跨層流程依需要加精簡 Mermaid 圖；簡單操作不強制畫圖 |

例如 PMForecast 的 CountryCode 隔離驗收：同一機種／週別，以空白、IN、BR 分別上傳 10、20、30；重傳 IN=40 後，三角度匯出應為 10、40、30。這是合成驗收資料，不是正式業務預測。

完整 JSON 沿用既有 Schema：SQL 與驗收文件路徑、操作及預期結果記入 `solution_steps`，執行證據記入 `test_results`；`user_reply` 同樣保留 SQL 路徑及核心驗收方式。`changed_files` 記錄核准範圍內的業務程式檔，交付文件另於 `solution_steps` 列出，不藉此擴大程式寫入權限。
