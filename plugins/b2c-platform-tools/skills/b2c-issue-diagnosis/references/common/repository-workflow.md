# 程式碼診斷與修復

## 分析與實作

1. 需要本機程式時先依 [初始化與路徑解析](initialization.md) 定位本次系統與前／後端；缺少時實際詢問，不自動推算或下載。讀取該路徑適用的 AGENTS.md，依入口、符號與呼叫關係追查必要 Service、Repository、Model、驗證及設定。路徑設定不授予寫入權限。
2. 對照已確認工作卡的預期／歷史與當次程式；只有片段就說明可確定範圍，不假設已重現、部署或直接重做舊成果。隨附 [系統參考](../systems/index.md) 只協助定位。
3. 區分功能專屬檔、共用相依與無關模組，不將整個 Area 當成可寫範圍。共用改動先分析其他呼叫者與回歸影響，只有現有授權未涵蓋時才補確認。
4. 實作前檢查並保留既有 Git 異動，只改本案必要檔案。只問分析不改業務程式；明確要求修復就沿用授權。資料修正及檔案交付統一依 [交付規則](response-template.md#涉及程式資料庫變更的交付)。
5. 選擇現有且直接相關的隔離測試／編譯，檢查 diff；工具測試、業務實測與人工驗收分開。不要為驗證啟動可能連正式資料的 API、停止原程序或重做已通過的相同檢查。

## 回歸原因與 Git 證據

- 使用者問「以前正常、突然發生」或需要定位變更來源時，從相關入口／符號的 Git 歷史、blame 與提交差異追查，對照可取得的舊版本與目前程式；不要只憑提交標題判定原因，也不預設每案都要完整追 Git。
- 找到引入錯誤的提交時，將具體錯誤、該提交時間與可核對的 commit 連結整併進原診斷。時間格式依 [Notion 工作追蹤](notion-workflow.md#結構與進度)；連結使用已核對的 repository 與完整 commit ID。歷史不完整或找不到引入點時如實說明，不捏造日期或連結。
- 區分程式提交、正式部署、資料建立與本次觸發時間。Git 能證明某版本已存在錯誤，不代表該時刻已上線，也不能據此認定去年實際採用的操作流程；尚無現場證據的解釋標為推論。

## 交付收尾：分支與 Commit

- 有實際檔案異動時，先完成驗證、說明修改／測試結果、建議分支與提交範圍。已有 Commit／分支決定就沿用；只更新 Notion 或分析時不必詢問。
- 尚無決定時，實際使用宿主允許的提問卡片詢問「是否建立分支並 Commit 本次變更？」並列「建立分支並 Commit」「使用目前分支 Commit」「暫不提交」；沒有適用工具才用聊天，不能只說可協助提交。等待規則依 [主流程](../../SKILL.md#提問與等待)。
- 分支預設 `codex/`。提交只納入本案確認的差異，不用 `git add .`；同檔混有其他工作時按區塊處理，無法可靠分離才確認範圍。不捨棄其他變更。Commit 授權不包含推送、合併或部署，已明確授權的動作照既有決定執行。

## 可選檢查工具

需要機械檢查時才使用 PowerShell 7 的 `scripts/IssueAssistant.ps1`，不是讀碼或開發前提：

```powershell
./scripts/IssueAssistant.ps1 -WorkspaceRoot <目標工作區絕對路徑> -ScopeJson <本次範圍JSON> -Action Validate
./scripts/IssueAssistant.ps1 -WorkspaceRoot <目標工作區絕對路徑> -ScopeJson <本次範圍JSON> -Action CheckPath -Path <相對路徑> -Operation read
./scripts/IssueAssistant.ps1 -WorkspaceRoot <目標工作區絕對路徑> -ScopeJson <本次範圍JSON> -Action ValidateReport -ReportPath <已要求的報告相對路徑>
```

腳本路徑相對於本 Skill；`ScopeJson` 可在記憶體產生，契約見 [範圍檢查](../../../b2c-system-maintenance/references/configuration.md)。寫入檢查另需 `-Operation write -Authorized` 表示實際已有授權；參數不會授予權限。工具拒絕越界、symlink／junction 及共用檔寫入，不能代替影響分析。只有使用者要求報告時才準備 JSON，現有 [fixture](../../scripts/tests/fixtures/demo-diagnosis.json) 僅為合成測試資料。

變更工具時執行 `scripts/tests/Run-Tests.ps1`，Python 工具以 `python -I -m unittest discover -s '<診斷技能目錄>/scripts/tests' -p 'test_*.py'` 執行路徑與憑證測試；流程的語意檢查另見 [回歸情境](scenarios.md)，工具通過不等於實際系統端到端驗收。
