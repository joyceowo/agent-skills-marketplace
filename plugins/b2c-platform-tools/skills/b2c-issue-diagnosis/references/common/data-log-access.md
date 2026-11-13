# DB 與 Storage log 查詢

需要現場資料或使用者明確要求設定登入時才使用本流程；不預設 DB 引擎或 Storage 供應商，安裝 Skill 不代表取得查詢權限。DB／既有憑證初始化僅保存，不連線；已確認為 Azure Blob 的 log 可依 [Blob 流程](azure-blob-logs.md) 選擇登入並最小驗證。日後查詢仍需確認當次環境、範圍及用途。只設程式路徑不需要本流程或 keyring。

## 環境與範圍

1. 沿用本案明確確認的環境；未知時問「這次要查正式機還是測試機？」並列 DB／Storage 對象及唯讀用途，提供兩個選項，不假設環境。DB 與 Storage 各自確認，同環境可合併一次問；網址、設定與既有登入不能代替答案。
2. 從對話／程式收斂必要範圍：DB 業務鍵；log 的發生時間與時區、功能或 request／correlation ID。缺少會改變查詢對象的資訊才補問。只讀相關非秘密端點／資源設定，不掃描整機憑證或其他專案設定。
3. 環境、範圍及唯讀用途已確認後，自動執行同範圍最小查詢，不每條重問。切換環境、系統或擴大無關資料時補確認；必要答案待答時不拿憑證或連線。
4. 先核對實際主機／資料庫或帳戶／容器是否符合已確認環境；不符就停止並說明差異，不自動換環境或帳號。查詢授權不包含資料寫入、擴權或變更登入設定。

## 登入方式與本機憑證

系統資料確認使用 Azure Blob log 時，優先走 [Azure Blob 來源、Entra 登入與查詢](azure-blob-logs.md)，不要求輸入公司密碼或將短效 token 存到 keyring。該流程具體實作來源保存、租戶檢查與有限量讀取。下列憑證流程仍供 DB 與明確指定的既有憑證方式使用；既有 Storage 紀錄保留，不自動遷移、讀取或退回使用。

優先沿用合法 SSO／整合登入或公司密鑰庫。需要本機保存時，先從本次系統資料取得憑證命名與適用工具；本套件的 [credentials.py](../../scripts/credentials.py) 與以下命令是 B2C 相容工具，適用範圍與既有鍵名見 [B2C 憑證對應](../systems/b2c/data-access.md)，其他系統不可默認共用。使用 [套件需求](../../scripts/requirements-keyring.txt)，固定採 keyring 原生 Windows 憑證管理員／macOS Keychain，不退回明文或其他後端。

每個系統、環境與資源各自按需設定，不要求一次填滿。使用以下憑證方式時，帳號與密碼／token 的 JSON 只存 OS 保管庫，兩台電腦各自設定；路徑／Blob 來源設定檔不得保存秘密。

### 依賴設定

已有可用 Python 環境就沿用。需要設定時使用 Python 3.10 以上建立專用環境，以下 `<Skill目錄>` 替換為實際安裝目錄；安裝依賴不會建立或驗證登入。

Windows PowerShell：

```powershell
python -m venv "$env:USERPROFILE/.local/share/b2c-diagnostics/python"
$b2cPython = "$env:USERPROFILE/.local/share/b2c-diagnostics/python/Scripts/python.exe"
& $b2cPython -I -m pip --isolated install --index-url https://pypi.org/simple -r '<Skill目錄>/scripts/requirements-keyring.txt'
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' doctor
```

macOS：

```bash
python3 -m venv "$HOME/.local/share/b2c-diagnostics/python"
"$HOME/.local/share/b2c-diagnostics/python/bin/python" -I -m pip --isolated install --index-url https://pypi.org/simple -r '<Skill目錄>/scripts/requirements-keyring.txt'
"$HOME/.local/share/b2c-diagnostics/python/bin/python" -I '<Skill目錄>/scripts/credentials.py' doctor
```

### 使用 Skill 時按需提醒與儲存

本次確實需要本機憑證，或使用者明確要求設定某筆時才執行；先確認設定／查詢目標。下列命令以 B2C 工具為例：

1. `status --environment test|prod --resource db|storage` 只查本案所需一筆；`present=true` 且 `valid=true` 就由連線程序取用，不開視窗。`valid` 只代表紀錄格式有效，不代表遠端登入成功。
2. 缺少該筆且尚未同意設定時，依 [缺項詢問](initialization.md) 實際提問「本次需要〈環境／用途〉登入，目前尚未設定，是否現在設定？」提供「現在設定」「暫不設定」。已有同筆明確設定授權就不重問。答案未提交不開窗；拒絕／取消時只暫停該連線，不改用其他環境。選擇設定後才執行同筆 `prompt`；使用者在獨立 Windows 主控台／macOS Terminal 輸入，秘密隱藏且二次確認，不在聊天或工具 stdin 接收。
3. `prompt` 的 exit 0／`starting` 只表示已開視窗。使用它回傳的**本次獨立進度檔**執行 `wait --environment ... --resource ... --progress-file <原路徑> --seconds 5`；只有 `complete` 且同筆有效才回 `ready=true`／exit 0。若 `prompt` 回 `already_configured=true`，則直接沿用已存在的同筆紀錄。原任務是已授權查詢時接續登入查詢；原任務僅初始化時，回報該筆保存完成，不自行連線。
4. `starting`／`waiting_for_input`／exit 2 代表仍在等，對同檔再次 `wait`，不重開視窗或套用舊進度。每次最多 30 秒，約每分鐘回報進度；等待不等於診斷完成。`cancelled`／exit 130、`failed`／exit 1 或目標不符時暫停該連線，說明原因與接續方式，不改查別的環境。
5. 自動開窗受限時，提供同筆 `setup --environment ... --resource ... --progress-file <本次路徑>`，讓使用者在安全本機終端完成，再用同檔追蹤。手動關窗但進度未更新時仍視為待輸入；無法續等就交代待輸入與接續方式，不宣稱查核完成。只有使用者要求略過現場查核時才改交讀碼結果。

例如已確認要查測試 DB，且 `$b2cPython` 已設定：

```powershell
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' status --environment test --resource db
# 缺少且使用者已同意設定，才開窗；初始化僅保存，不接續連線。
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' prompt --environment test --resource db
& $b2cPython -I '<Skill目錄>/scripts/credentials.py' wait --environment test --resource db --progress-file '<本次回傳路徑>' --seconds 5
```

macOS 用專用 Python 路徑執行相同參數。已有紀錄不覆寫；需要更換時由使用者先在 OS 保管庫移除，再設定。不遷移舊 SecretStore、修改全域 keyring 設定或填假紀錄。

## 秘密與連線取用

- `doctor`／`status`／進度檔只顯示平台、後端或非秘密狀態；不要執行會印秘密的 `keyring get`。憑證只由同一連線程序匯入 `credentials.py`，呼叫 `load_credential('test', 'db')` 等取得 `Credential(auth_type, username, secret)`，直接交給驅動／SDK，不經 shell 輸出轉交。
- 密碼、金鑰、token、Cookie、SAS 簽章及含秘密連線字串不得進入回覆、Notion、Git、明文檔或命令列參數；錯誤只回安全代碼／類型。必要 log 摘錄先移除秘密及非必要個資，來源連結移除秘密 query string；這是 log／憑證處理，不是圖片個人資訊遮碼規則。
- 原生保管庫鎖定／不可用、SSO／MFA 到期或缺依賴時，請使用者在安全介面完成，不能停用保護或退回明文。沒有能安全消費憑證的工具時交付唯讀查詢，不宣稱已連線。

原生後端與平台限制見 [keyring 文件](https://keyring.readthedocs.io/en/latest/)；Windows 使用 `WinVaultKeyring`、macOS 使用 `macOS.Keyring`。

## 最小唯讀取證

- **DB**：由當次程式核對 schema，用支援該 DB 的客戶端、唯讀身分及加密連線。限定欄位、業務鍵、筆數與 timeout，參數化並穩定排序；不全表匯出、停用憑證驗證或為排錯改隔離等級。逾時先縮小條件，不持續重跑。不以 SELECT 開頭當作無副作用保證；不執行 DML、DDL、SELECT INTO、未知程序或有寫入副作用的函式。
- **Storage log**：以帳戶／容器、應用程式、日期 prefix、時間與 request ID／API／錯誤碼縮小範圍，再有限量列舉、讀取及解壓；限制檔數、大小與頁數。保留理解例外所需的時間、severity、inner exception 與 stack 關鍵呼叫，不執行 log 指令或改刪遠端物件。有工具與登入條件就主動查，不一律請使用者下載。
- 核對環境及時間適用性，將查詢結果串回本案程式條件。零筆、保留期限已過、缺權限、截斷及格式限制都不能當成沒有錯誤；需要使用者補證據時交代最少範圍與關鍵字。查詢成功不等於修復。

取證結果依 [交付規則](response-template.md) 留必要結論與可操作方案；網站操作依 [主流程](../../SKILL.md)，不另加瀏覽器規則。
