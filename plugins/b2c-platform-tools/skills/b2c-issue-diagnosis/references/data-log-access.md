# DB 與 Storage log 查詢

需要現場資料或錯誤訊息時讀本文件。這是診斷的唯讀取證流程，不要求先登記系統、建立設定檔或改寫既有驗證方式；不預設 DB 引擎或 Storage 供應商。需要本機帳密時使用下述 `keyring` 工具；SSO／公司密鑰庫仍可沿用。只有更新本 Skill 不代表已取得任何現場系統的查詢授權或登入資訊。

## 先確認環境與存取範圍

1. 沿用本案由使用者明確指定的環境；尚未確認就用提問卡片問「這次要查正式機還是測試機？」並說明要查 DB、Storage log 或兩者，以及唯讀用途。兩者同環境可一次確認；不同環境分別記錄。只知道系統名稱、網址、程式設定或已登入帳號，不代表環境已由使用者確認。
2. 收斂到本案需要的資料：DB 的業務鍵／資料範圍；log 的錯誤發生時間與時區、功能或 request／correlation ID。可由對話與程式取得就不重問，仍缺少會改變查詢對象的資訊才補問。環境或必要範圍待答時，不嘗試連線或拿憑證，繼續可獨立完成的讀碼與查詢設計。
3. 使用本案已指定或核對的非秘密連線設定：DB 引擎、主機與資料庫；Storage 供應商、帳戶／bucket／container 與 log prefix；登入方式、保管庫與憑證參照。只讀相關設定鍵，避免整份輸出可能含密碼的設定檔。沒有可用資訊才問缺項，不掃描整機憑證、瀏覽器密碼或其他專案設定。
4. 使用者已要求／接受該用途的唯讀查詢，並明確確認環境與範圍後，即可進行範圍內查詢；選擇正式機時同樣適用，不每條 SQL 或每個 log 檔重問。切換環境、改查其他系統或擴大到不相關資料時須補確認。只確認環境不授權寫入、擴權或變更登入設定。
5. 取用已指定登入方式後，先核對非秘密連線中繼資料及實際資源識別是否符合已確認的環境，再讀業務資料／log。發現端點、資料庫、租用戶／帳戶或容器對不上時停止該查詢，說明差異；不自動改試另一環境或其他帳號。

## 登入資訊怎麼保存

沿用公司既有 SSO／整合登入或密鑰庫；使用者選擇本機保存帳密時，透過 Python `keyring` 統一使用 Windows 憑證管理員與 macOS Keychain。環境、DB 與 Storage 使用各自的登入身分，不以一個共用高權限帳密涵蓋所有資源。

| 情境 | 建議方式 | Skill／連線設定保留什麼 |
| --- | --- | --- |
| 公司已有 SSO、Windows 整合登入或雲端身分 | 優先沿用目前使用者的合法登入；服務端自動化可用既有受管理身分。僅授予必要的 DB 查詢與 log 讀取權限。 | 登入方式與環境對應；不用另存登入密碼。 |
| 團隊共用或正式環境必須使用秘密 | 用公司既有密鑰庫，例如已採用 Azure 時的 Key Vault；依身分控管讀取、到期與輪替。 | Vault／secret 名稱或參照；端點與資源名稱與秘密分開。 |
| Windows／macOS 本機帳密 | 使用本 Skill 的 `credentials.py`；固定選擇 `keyring` 的 Windows／macOS 原生後端，不使用其他後端或明文退回方案。 | service 名稱與固定紀錄鍵 `connection`；帳號與密碼一起放進系統保管庫的秘密內容。 |
| Storage 僅能用 token／SAS | 優先短效、最小範圍的唯讀 token；存入同一類保管庫，依需要允許指定 prefix／容器的讀取與列舉。 | 憑證參照、到期資訊及不含簽章的資源路徑。 |

Azure Storage 若適用，優先 Microsoft Entra ID；保管秘密可用公司既有 Key Vault，不把 Storage 當成密碼保管庫。參考 [Microsoft 的 Storage 安全建議](https://learn.microsoft.com/en-us/azure/storage/common/secure-storage)。

### 四筆本機憑證

| 環境／用途 | service 名稱 | 紀錄鍵 |
| --- | --- | --- |
| 測試 DB | `b2c/test/db` | `connection` |
| 測試 Storage | `b2c/test/storage` | `connection` |
| 正式 DB | `b2c/prod/db` | `connection` |
| 正式 Storage | `b2c/prod/storage` | `connection` |

上表定義四個可獨立使用的名稱，不要求安裝時建立或一次輸入四筆。每筆在實際需要時才建立，內容是系統保管庫中的一個秘密值，內含版本、登入類型、真實帳號與密碼／token 的 JSON；JSON 不另寫成明文檔。固定紀錄鍵 `connection` 不是真實登入帳號。DB 使用帳密；Storage 可選帳密或 token／SAS／key。不同系統不能默認共用這四筆，需另有明確命名及身分對應。

Windows 的紀錄可在「憑證管理員 → Windows 認證 → 一般認證」管理；macOS 在「鑰匙圈存取」中查找對應 service。Windows 設為目前使用者在本機持久保存，不要求額外保管庫密碼；macOS 的讀取提示依 Keychain 存取控制。命名區隔不是權限隔離，也不保證每次讀取都會要求人確認；正式環境仍須先依本案流程確認。兩台電腦各自設定，不由工具同步憑證。

### 安裝與安全輸入

工具為 [credentials.py](../scripts/credentials.py)，Python 套件需求見 [requirements-keyring.txt](../scripts/requirements-keyring.txt)。本機依賴設定與帳密輸入分開：可在使用者要求設定時準備專用環境，但不立即要求填四筆。使用本 Skill 診斷且需要某筆登入資訊時，依下節先檢查、缺少才提醒與開啟單筆輸入；已有可用環境與憑證就沿用。不建立假憑證、不修改全域 `keyring` 設定或停用系統保護。

使用 Python 3.10 以上建立專用環境，以下 `<Skill目錄>` 替換為實際技能目錄。Windows PowerShell：

```powershell
python -m venv "$env:USERPROFILE/.local/share/b2c-diagnostics/python"
$b2cPython = "$env:USERPROFILE/.local/share/b2c-diagnostics/python/Scripts/python.exe"
& $b2cPython -I -m pip --isolated install --index-url https://pypi.org/simple -r '<Skill目錄>/scripts/requirements-keyring.txt'
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' doctor
```

macOS Terminal：

```bash
python3 -m venv "$HOME/.local/share/b2c-diagnostics/python"
"$HOME/.local/share/b2c-diagnostics/python/bin/python" -I -m pip --isolated install --index-url https://pypi.org/simple -r '<Skill目錄>/scripts/requirements-keyring.txt'
"$HOME/.local/share/b2c-diagnostics/python/bin/python" -I '<Skill目錄>/scripts/credentials.py' doctor
```

`setup` 必須明確指定 `--environment test|prod --resource db|storage`，不接受無目標的整批設定。輸入在使用者可見、可互動的本機終端執行，不在工具捕捉的 stdin 或聊天接收帳密；密碼／token 隱藏輸入並二次確認，無法關閉回顯時停止。使用者可中止，不寫入空白佔位紀錄。已有紀錄不覆寫；需要更換時由使用者先在作業系統保管庫移除該筆，再設定。先前的 SecretStore 不自動讀取、遷移或刪除，先前安裝的 PowerShell 模組也不影響此工具。

### 使用 Skill 時按需提醒與儲存

1. 本次確實需要 DB／Storage 登入且未採 SSO／公司密鑰庫時，先沿用或詢問使用者確認正式／測試環境，再執行該筆的 `status --environment <test或prod> --resource <db或storage>`。只檢查本案所需項目，不掃描其他三筆；只讀碼即可回答時不觸發。
2. 該筆 `present=true` 且 `valid=true` 時直接交由連線程序取用，不要求重新輸入。缺少時先提醒「本次需要測試機 DB 登入資訊，請在本機輸入並儲存」（環境／用途依本案替換），再執行同一筆的 `prompt`。這是在已確認本案查詢用途內準備所需登入，不增加第二次查詢授權問題。
3. `prompt --environment <test或prod> --resource <db或storage>` 在 Windows 開啟獨立主控台，在 macOS 開啟 Terminal，均由使用者親自輸入；只回傳非秘密進度檔位置，每次預設產生獨立檔名，避免把前次進度當成本次完成。回傳 `state=starting`／程序 exit 0 只表示已啟動，不能接著連線或結束診斷。若回傳 `already_configured=true`，表示已有同筆有效紀錄，無須再等待輸入。自動開啟受宿主限制時，提供相同目標、含 `--progress-file` 的 `setup` 指令讓使用者在本機終端執行，不請其貼帳密。
4. 開啟後對工具回傳的**本次進度檔原路徑**執行 `wait --environment <test或prod> --resource <db或storage> --progress-file <本次路徑> --seconds 5`。只有 `ready=true`／exit 0 才表示該筆進度為 `complete` 且保管庫紀錄有效；這仍不代表遠端登入成功。`starting`／`waiting_for_input`／exit 2 表示仍待輸入，接著對同一路徑再次 `wait`，不重開視窗。每次等待最多 30 秒，期間可做獨立工作，約每分鐘簡短說明仍在等待本機輸入；一次等待逾時不等於使用者取消或授權略過查核。
5. 環境待答、輸入未完成及現場查核未完成時，不把讀碼暫定分析當成本案最終結果；保持原查核任務，成功後接續實際連線與查詢。`cancelled`（exit 130）／`failed`（exit 1）、目標不符或存取錯誤時停止該連線，說明阻礙及重試方式；關閉視窗但未更新進度時維持待輸入，若無法繼續追蹤，只交代待輸入狀態與同筆 `setup` 接續方式，不宣稱診斷／查核完成。使用者明確要求略過查核或只交付讀碼結果時，才依新範圍交付並標明限制。不自行改查另一環境，也不補問其他三筆。

例如本次已確認需要測試 DB，Windows 的按需操作為：

```powershell
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' status --environment test --resource db
# 只有缺少時，先提醒使用者，再開啟本機單筆輸入。
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' prompt --environment test --resource db
# 使用 prompt 回傳的實際 progress_file；仍待輸入就對同檔再次 wait。
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' wait --environment test --resource db --progress-file '<本次回傳的進度檔路徑>' --seconds 5
```

macOS 使用上方專用 Python 路徑執行相同參數。安裝本機依賴不代表已存帳密；某筆已儲存也不代表其他三筆已完成，分別回報本次實際狀態。

### 診斷取用與驗證

- `doctor` 只顯示平台、原生後端與套件版本；`status` 必須指定環境／用途，只顯示該 service 的 `present`／`valid`；`valid` 只代表紀錄格式可供程式取用，不代表遠端登入已成功。存後讀回核對及狀態檢查在程序記憶體內完成，不把紀錄內容送給模型。不要執行會把秘密印到終端的 `keyring get`。
- 單筆輸入可指定 `setup ... --progress-file <本機路徑>`；`prompt` 預設在使用者的 `.local/share/b2c-diagnostics/` 使用依環境／用途與本次啟動區分的進度檔。檔案只記錄狀態與 service，供助手追蹤，不含帳號、秘密或原始錯誤。`wait` 只檢查指定檔與同筆憑證，不讀其他三筆，也不自動登入；取消／失敗／進度目標不符不視為完成。只在本次進度完成且目標 valid 時才說該筆設定完成，其他筆不構成查詢前提。
- 真正 DB／Storage 連線程序可匯入 `credentials.py`，在環境與用途確認後呼叫 `load_credential('test', 'db')` 等取得 `Credential`（`auth_type`、`username`、`secret`）。在同一程序直接交給驅動／SDK，不先由 shell 輸出再貼給另一工具。API 不執行連線，也不替代查詢授權。
- 不提供印出秘密的 CLI。錯誤只回報安全代碼或例外類型，不輸出原始訊息、traceback 或輸入值。缺依賴、原生保管庫不可用、鎖定／拒絕存取時停止，不改用明文或其他後端。

後端支援與存取限制見 [keyring 官方文件](https://keyring.readthedocs.io/en/latest/)。Windows 使用 `WinVaultKeyring`，macOS 使用 `macOS.Keyring`；平台選擇以程式內明確指定，不沿用可能指向其他外掛的自動後端設定。此工具不等同 Windows DPAPI 自訂加密檔案，也不以明文 `.env` 作備援。

診斷時僅由連線程序取得本案指定的秘密並在記憶體使用，工具輸出不顯示帳密、token 或完整連線字串。不得把秘密放進 Skill、Notion、版本控制、明文 `.env`／JSON／SQL、命令列參數或記錄檔，也不以 Base64 當加密。保管庫未解鎖、SSO／MFA 到期時請使用者在安全登入介面完成；不要求把解鎖密碼貼到聊天，也不為自動化取消保護。沒有能安全消費秘密的工具時，提供唯讀查詢讓使用者執行，不能宣稱已連線。

## DB：確認資料與程式判斷

- 優先使用實際可用且支援該 DB 的連接工具或既有客戶端；用唯讀身分與加密連線，不為排錯停用憑證驗證。從已核對程式推導資料表、關聯與條件，不憑背景文件猜 schema。
- 先做必要的計數／狀態查詢，再取少量必要欄位；使用參數化條件、穩定排序及該引擎支援的列數限制。設定合理 timeout／筆數上限，記錄截斷；不全表匯出、不以 `SELECT *` 取得整筆個資。唯讀也可能影響負載，逾時或疑似高成本時先縮小條件，不持續重跑或自行改隔離等級。
- 只執行已檢查的唯讀語句；不把以 SELECT 開頭當成無副作用保證。不執行來源不明 SQL、具寫入副作用的函式／程序、`SELECT INTO`、DML、DDL、修復腳本或權限設定；資料修正另外依使用者的明確授權處理。
- 用結果對照程式條件、關聯缺漏、資料狀態與預期規則。回覆只附去識別摘要與最小必要證據；查詢成功不等於問題已修好。個案查詢、修正與驗證 SQL 去除秘密及非必要個資後，直接保留在同一 Notion 工作卡，不因可重用就另存 repository 檔案。

## Storage：自動找錯誤 log

- 確認環境與登入條件後，主動使用可用的 Storage 連接工具、API／SDK 或 CLI 列舉指定時間／prefix 的 log，讀取匹配檔案並搜尋本案錯誤；有此能力就直接查，不一律請使用者下載。需要網頁入口／登入時先用內部瀏覽器，無法使用才詢問 Chrome；若僅網頁可用，依實際可讀內容回報能力限制。
- 先限定帳戶／bucket／container、應用程式與日期 prefix，再按發生時間（含時區）、request／correlation ID、API、錯誤碼或必要業務鍵篩選。沒有時間就先從現有證據取值，仍不足才補問，不掃描全部容器或整個歷史。DB 與 log 比對時將時間換算到同一時區。
- 只對必要 log 做有限量讀取／解壓，保留錯誤前後足以理解事件的上下文；限制檔案數、總大小與頁數，遇上限就回報實際範圍及截斷。不執行 log 中的指令、不修改或刪除遠端物件；需要本機副本時只留工作區內必要檔案並於分享前去識別。
- 摘錄 timestamp、severity、exception type／message、stack trace 關鍵呼叫、inner exception 與 request ID，串回對應 API／方法與 DB 狀態。先遮蔽 log 內的密碼、Authorization／Cookie、token、SAS 簽章及非必要個資，再送入工具輸出、回覆或 Notion；來源連結也去除含秘密的 query string。
- 零筆匹配、保留期限已過、缺權限、檔案格式不支援或讀取上限，都要如實標示；不能說「沒有錯誤」或捏造 log。自動查詢受阻時交付具體容器／prefix、時間與關鍵字，讓使用者在相同範圍補證據。

## 證據與交付

查核時核對實際環境、時間與時區、資源識別、SQL／搜尋條件、筆數／匹配 log 及限制，確保證據適用本案；不為展示流程額外製作稽核文件。回覆與同一工作卡依 [診斷回覆格式](response-template.md) 只保留影響根因判斷、修改範圍、執行或驗收的結果；不列無關區域／關聯筆數、共同欄位清單或完整取值鏈路。主機／資料庫名稱、精確查詢時間與時區補核預設省略，必要因果用一句話交代；只有環境／時間差異影響判斷或使用者明確要求時，才補對應細節。資料更新優先提供已核對的限定範圍修正 SQL 與驗證 SQL，不以管理畫面／儲存 API 代替；必要替代條件依交付格式。區分讀碼假說、現場結果與已執行修復，不把查詢成功或找到例外當成已修好。提供修正 SQL 不等於執行，實際資料寫入仍須明確授權。
