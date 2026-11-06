# 診斷回覆格式
先辨識系統、查閱 Notion，再核對提供的程式碼，回覆操作問題、程式 Bug 或功能需求的判斷與解法；有工作卡時附連結。不要求 commit 或版本對照；系統參考只補充背景與定位資訊。

報告 Schema 用於需要結構化輸出時的驗證，不要求每個問題都另存 JSON。個案工作紀錄以 Notion 為主，MD 只補充必要背景與無法直接從程式取得的約定，不逐案複製實作；SQL 與測試資料保留 Git。Notion 排版及人工結案方式依 [Notion 工作追蹤](notion-workflow.md)，不重複產生個案交付／驗收文件。

以下供診斷時檢查資訊是否完整，依本案需要選用，不要求逐欄填寫。Notion 工作卡採 [Notion 工作追蹤](notion-workflow.md) 的簡潔寫法，不照抄分類代碼、保留語或不適用欄位。

以下是按需選用的資訊，不是固定章節或回覆順序；以簡潔、清楚、容易閱讀為原則，依內容選擇文字、條列、步驟、表格或圖表：
- 系統：名稱（system_id）
- 分類／影響：classification／impact_scope
- 結論與解法：直接說明如何處理、操作步驟或修改方案及預期結果；推測必須明講
- 預期／實際：依問題需要描述；缺少資料會影響判斷時，寫明具體缺項及用途。功能需求不強填實際故障或重現結果
- 證據：本次已實際讀取的程式片段、附件檔名或工作區路徑／方法；背景文件只作輔助，標示 CONFIRMED 或 HYPOTHESIS。未執行時不說已重現，不聲稱來源已部署。
- 處理：可執行步驟、是否需要修改、是否已有授權
- 驗證：實際執行與結果；Notion 工作卡的待辦只列在最上方 checkbox，明細不另寫尚待執行或未完成。不可把設定檢查當作業務修復驗證
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
| SQL 檔案 | 可點擊的實際絕對路徑、各檔用途、正確執行順序；Notion 中的執行狀態只列在最上方 checkbox；註解與自訂提示預設繁體中文 |
| 環境與前提 | 測試資料庫／測試 API、先套 DB 再啟動新版程式等必要順序；未知的位址、帳號與測試資料標示須替換 |
| 設定位置 | 設定的畫面／API，或資料表、篩選鍵、欄位及有效值；檔案設定列檔案／環境與欄位，區分本次修改與沿用前提，不能只列設定名稱 |
| 使用者驗收 | API 方法與路徑或指令、實際輸入、預期結果；錯誤輸入、重傳或資料隔離案例依需求選擇 |
| 通過判準 | 可觀察的回傳欄位、匯出值或唯讀查詢結果；不只寫「確認正常」 |
| 驗證與待辦 | 已執行的自動測試與結果列於驗證明細；本案所需 SQL Server／真實 Excel／實際 API 驗收的待辦及完成狀態只列在最上方 checkbox，不在明細重述 |
| 呈現方式 | 依內容選擇短段落、條列、步驟、表格或圖表；複雜關係可用流程圖，不為套格式增加章節或圖表 |

涉及資料隔離時，使用不同範圍的測試資料，驗證更新其中一組不影響其他組；具體鍵值、操作與預期結果依當次程式及需求決定。

完整 JSON 沿用既有 Schema：SQL 與驗收文件路徑、操作及預期結果記入 `solution_steps`，執行證據記入 `test_results`；`user_reply` 同樣保留 SQL 路徑及核心驗收方式。`changed_files` 記錄核准範圍內的業務程式檔，交付文件另於 `solution_steps` 列出，不藉此擴大程式寫入權限。
