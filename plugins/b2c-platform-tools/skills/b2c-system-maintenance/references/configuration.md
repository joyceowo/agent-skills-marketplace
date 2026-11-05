# 系統參考與可選範圍檢查

系統參考與分析範圍供當次查找及核對，不是登記或啟用程序，不要求外部本機設定目錄。診斷的 Notion 目的地依 [Portal 與其他系統的位置規則](../../b2c-issue-diagnosis/references/systems/b2c-portal/notion.md)；參考文件不取代實際授權或 Notion 權限。

## 可選範圍物件

一般問答／開發不需要 JSON。需要機械檢查時，scripts/IssueAssistant.ps1 接受明確的 -WorkspaceRoot 及記憶體中的 -ScopeJson，格式見 [scope.schema.json](../../b2c-issue-diagnosis/references/schemas/scope.schema.json)。只有以下欄位：

| 欄位 | 用途 |
| --- | --- |
| system_id／system_name | 本次已辨識的目標，用於報告核對，無須事先登記。 |
| read_paths | 本次相關程式，包含必要的共用檔；須已存在。 |
| write_paths | 本次必要的專屬修改候選；可包含新檔，須在可讀範圍內。 |
| docs_paths | 本次必要文件，未知用 []。 |
| shared_dependencies | 已識別的共用相依；可讀，工具拒絕寫入。 |

路徑相對於目標工作區。專屬檔案與共用相依混在同一資料夾時，列明專屬可寫檔，不把父目錄整體列為可寫。新增測試可在現有測試目錄列出新檔候選；未存在的 read_paths 不會通過檢查。

Validate 不帶 ScopeJson 時只檢查工作區，不授予檔案權限；CheckPath 需要當次分析範圍，寫入另需 -Authorized 表示已取得的實際授權。ValidateReport 比對報告的目標、證據、變更與驗證聲明；未辨識系統只能表達 UNKNOWN／NEEDS_INFO，不能藉此放寬讀寫。

共用改動仍由診斷流程分析其他呼叫者與授權，不能靠修改範圍物件規避限制。工具不讀外部設定、不管理系統清單或啟用狀態，也不查詢／寫入 Notion。工具變更執行 scripts/tests/Run-Tests.ps1。
