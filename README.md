# Skill Forge

透過同一個 GitHub 儲存庫安裝到 **Codex 與 Claude Code** 的技能市集。技能以外掛（plugin）為安裝單位，每個外掛共用一份 `SKILL.md`、參考文件及資源，另提供兩個平台各自的市集與外掛設定檔。

GitHub 儲存庫：[joyceowo/skill-forge](https://github.com/joyceowo/skill-forge)。市集顯示名稱為 **Skill Forge**，識別碼為 `skill-forge`。

## 已收錄的技能

| 外掛／技能 | 版本 | 用途 |
| --- | --- | --- |
| [sync-business-logic-docs](plugins/sync-business-logic-docs/README.md) | 1.1.0 | 從 C# 與 Git 歷史建立、稽核及增量同步業務邏輯 Markdown 文件。 |
| [code-atlas](plugins/code-atlas/README.md) | 1.0.0 | 將單一或多個 Git 專案整理成三層商業地圖、鎮民規則文件與可匯入的地圖 ZIP。 |
| [b2c-platform-tools](plugins/b2c-platform-tools/README.md) | 0.5.20 | 直接讀碼診斷系統問題，維護專案範圍與 Notion 位置；包含診斷與系統維護兩個 Skill。 另提供上線與測試通知及 Portal 公告流程。 |

## 平台支援

| 環境 | 安裝入口 | 技能內容 |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json` | 共用外掛內的 `skills/`。 |
| Claude Code | `.claude-plugin/marketplace.json` | 共用相同的 `skills/`，以 `/外掛名稱:技能名稱` 呼叫。 |
| Claude 網頁版／一般聊天 | 手動上傳單一技能 ZIP | 將 `skills/<技能名稱>/` 資料夾連同內容壓成 ZIP，再依 [Claude Skills 說明](https://support.claude.com/en/articles/12512180-use-skills-in-claude) 上傳；不使用以下 Claude Code CLI 指令。 |

各外掛的執行需求見其說明。B2C Platform Tools 的一般程式分析使用通用檔案工具，可選分析範圍檢查需要 PowerShell 7，不要求外部設定目錄，Notion 紀錄需要執行環境已連接可用的 Notion 工具與接收者自己的目的地。文件同步與 Code Atlas 使用檔案／Git 操作，`agents/openai.yaml` 提供 Codex 的顯示資訊與預設提示，核心流程位於共用的 `SKILL.md`。Claude 網頁版執行此技能仍需要提供原始碼與可存取的 Git 歷史；僅上傳 Skill 不會取得本機專案，因此程式碼同步工作建議使用 Claude Code。

## Code Atlas 安裝與使用

Code Atlas 的完整流程是 **Skill → 商業邏輯文件 → 地圖 ZIP → viewer 匯入 → 國家／城市／鄉鎮縮放**。此版本包含分析腳本、參考文件、離線 viewer 與 D3 授權；使用方式與 Python 套件需求見 [Code Atlas 說明](plugins/code-atlas/README.md)。

登錄市集並安裝 Code Atlas：

```powershell
# Codex
codex plugin marketplace add https://github.com/joyceowo/skill-forge.git --ref main
codex plugin add code-atlas@skill-forge
# Claude Code
claude plugin marketplace add https://github.com/joyceowo/skill-forge.git
claude plugin install code-atlas@skill-forge
```

從 GitHub 安裝必須等這個版本推送後才會取得；本機版本可先用以下方式載入（將路徑替換成自己的）：

```powershell
codex plugin marketplace add 'C:/path/to/skill-forge'
codex plugin add code-atlas@skill-forge
claude --plugin-dir 'C:/path/to/skill-forge/plugins/code-atlas'
```

在目標 Git 專案開啟新聊天後，請 Codex「使用 code-atlas 分析目前專案，產生商業邏輯文件並匯出地圖 ZIP」；Claude Code 使用 `/code-atlas:code-atlas` 加上相同要求。單一功能中的欄位或選項放在鎮民，商業流程、規則及程式證據是預設內容。

更新時，Codex 先執行 `codex plugin marketplace upgrade skill-forge`，再執行 `codex plugin add code-atlas@skill-forge`；Claude Code 先執行 `claude plugin marketplace update skill-forge`，再執行 `claude plugin update code-atlas@skill-forge`。本機市集直接讀取來源目錄；GitHub 市集更新讀取已推送的版本。完成後重新開啟工作階段。

## 從 GitHub 安裝

GitHub 安裝會取得遠端分支的內容。本機修改必須先提交並推送到 `main`，其他使用者才會取得新版；測試尚未發布的修改請見下方「本機驗證」。

### Codex

需要支援 `codex plugin` 的 Codex CLI。本專案建立時以 `codex-cli 0.160.0` 檢查指令格式。

在任何目錄執行以下指令，不必先手動複製本專案：

```powershell
codex plugin marketplace add https://github.com/joyceowo/skill-forge.git --ref main
codex plugin add sync-business-logic-docs@skill-forge
```

第一個指令從 GitHub 的 `main` 分支取得並登錄市集，第二個指令安裝其中的技能外掛。若儲存庫為私人儲存庫，使用者需具備 GitHub 存取權，並先設定 Git 驗證。

安裝後在 Codex 開啟新聊天，於技能選單搜尋 **Sync Business Logic Docs**，或輸入：

```text
請使用 sync-business-logic-docs，稽核這個 C# 專案的業務規則，並同步 docs/business/ 下的文件。
```

可用下列指令確認市集與外掛狀態：

```powershell
codex plugin marketplace list
codex plugin list
```

### Claude Code

需要已安裝且支援外掛的 Claude Code。在 PowerShell 或其他終端機執行：

```powershell
claude plugin marketplace add https://github.com/joyceowo/skill-forge.git
claude plugin install sync-business-logic-docs@skill-forge
```

第一個指令登錄市集，第二個指令安裝外掛。私人儲存庫同樣需要 GitHub 存取權與 Git 驗證。安裝後開啟 Claude Code 工作階段，輸入：

```text
/sync-business-logic-docs:sync-business-logic-docs 將 src/Order/ 的 C# 業務規則同步到 docs/business/order.md，先做完整覆蓋稽核。
```

也可以直接用自然語言要求使用 `sync-business-logic-docs`。在 Claude Code 的互動對話中，可用 `/plugin` 瀏覽市集外掛，或輸入：

```text
/plugin marketplace add joyceowo/skill-forge
/plugin install sync-business-logic-docs@skill-forge
```

終端機的 `claude plugin list` 可確認安裝狀態。指令與市集格式依據 [Claude Code 官方文件](https://code.claude.com/docs/en/plugin-marketplaces)。

## 更新已安裝的技能

### Codex

```powershell
codex plugin marketplace upgrade skill-forge
codex plugin add sync-business-logic-docs@skill-forge
```

先更新 GitHub 市集快照，再安裝該快照中的外掛版本，最後開啟新聊天。

### Claude Code

```powershell
claude plugin marketplace update skill-forge
claude plugin update sync-business-logic-docs@skill-forge
```

更新後開啟新的 Claude Code 工作階段。兩個平台的安裝與更新各自管理；更新其中一個平台不會自動更新另一個。

## 目錄結構

```text
skill-forge/
├── .agents/plugins/marketplace.json
├── .claude-plugin/marketplace.json
├── README.md
├── scripts/validate-marketplace.mjs
└── plugins/
    └── sync-business-logic-docs/
        ├── .codex-plugin/plugin.json
        ├── .claude-plugin/plugin.json
        ├── README.md
        └── skills/sync-business-logic-docs/
            ├── SKILL.md
            ├── agents/openai.yaml
            ├── assets/
            │   ├── business-logic-map.yaml
            │   └── business-logic-state.yaml
            └── references/
                ├── coverage-audit.md
                └── examples.md
```

兩個市集的來源路徑都相對於儲存庫根目錄。Codex 使用 `source: { "source": "local", "path": "./plugins/sync-business-logic-docs" }`，Claude 使用 `source: "./plugins/sync-business-logic-docs"`。兩者指向同一個外掛目錄，不能直接互換市集 JSON。

## 本機驗證

在儲存庫根目錄使用 Node.js 22 或更新版本執行：

```powershell
node scripts/validate-marketplace.mjs
```

這個檢查會確認兩邊市集收錄相同外掛、來源路徑存在且位於套件內、外掛名稱與版本等共用欄位一致，以及共用技能入口存在。它是儲存庫一致性檢查，不取代平台完整格式驗證或實際使用測試。

有安裝 Claude Code 的環境，再執行官方驗證與本機載入：

```powershell
claude plugin validate .
claude plugin validate ./plugins/sync-business-logic-docs
claude --plugin-dir ./plugins/sync-business-logic-docs
```

最後一個指令啟動 Claude Code 並載入本機外掛，可確認上述 `/sync-business-logic-docs:sync-business-logic-docs` 指令是否出現。此開發方式不需要先發布到 GitHub。

## 維護與擴充

1. 新增 `plugins/<外掛名稱>/`，在 `.codex-plugin/plugin.json` 與 `.claude-plugin/plugin.json` 分別提供設定。兩份 manifest 的 `name`、`version`、`description`、`author`、`skills`、`repository`、`homepage`、`keywords` 保持一致；Codex 的 `interface` 留在 Codex manifest。
2. 將共用技能放入 `skills/<技能名稱>/SKILL.md`，包含 YAML frontmatter 的 `name` 與 `description`；參考文件及資源一起放在技能資料夾內。
3. 在兩個市集的 `plugins` 陣列尾端加入對應外掛。Codex 項目保留 `source`、`policy.installation`、`policy.authentication` 與 `category`；Claude 項目使用字串形式的本機 `source`。
4. 執行一致性檢查與平台驗證，確認安裝後能找到並使用技能。若新增 MCP、Hooks 或平台專屬工具，需要另外檢查兩邊的設定與執行能力。
5. 發布外掛更新時，同步更新兩份 manifest 的版本與本頁版本表，再提交並推送到 GitHub 的 `main` 分支。由兩個平台分別依上方指令更新並驗證。

請編輯此專案中的來源檔案；Codex 的安裝快取由安裝指令管理。這份技能目前是原始技能的完整副本，不會自動與個人技能目錄雙向同步。

分享市集時提供本儲存庫的 GitHub 連結，以及使用者所用平台的安裝指令。此儲存庫是可自行加入的市集，不代表已上架到任一平台的官方精選目錄。
