# B2C 上線／測試通知

從 Notion 頁面或貼上的文字產生一份可離線開啟的 HTML，內含 Outlook 郵件主旨和正文的複製按鈕，以及 `Document.pdf` 下載。上線通知可依授權建立 Portal 公告。

## 安裝與使用

依 [Skill Forge 安裝說明](../../README.md#從-github-安裝) 登錄市集。新版推送後，已登錄的使用者先更新市集，再安裝通知外掛。

```powershell
# Codex
codex plugin marketplace upgrade skill-forge
codex plugin add b2c-notice@skill-forge

# Claude Code
claude plugin marketplace update skill-forge
claude plugin install b2c-notice@skill-forge
```

安裝後開啟新工作階段。在 Codex 可輸入「使用 b2c-release-test-notice，根據以下內容製作測試通知」。Claude Code 可用 `/b2c-notice:b2c-release-test-notice`。

Claude 會用聊天文字確認上線日期與標題。有可用的提問卡片時，會用卡片確認語言、截圖和公告。

先前安裝 `b2c-release-test-notice@skill-forge` 的使用者，請依上方指令安裝新識別碼 `b2c-notice@skill-forge`。市集更新後，舊外掛如仍列在已安裝清單，可從該清單移除。

原先透過 `b2c-platform-tools` 使用通知的使用者，可在安裝此外掛後，將原外掛更新至 0.6.0。兩個外掛可分別安裝。

### 從本機載入

在 Skill Forge 儲存庫根目錄執行。Codex 指令適用於尚未登錄同名市集的環境。Claude Code 可直接載入外掛目錄。

```powershell
codex plugin marketplace add (Get-Location).Path
codex plugin add b2c-notice@skill-forge

claude --plugin-dir ./plugins/b2c-notice
```

## 執行需求

HTML 產生器需要 Python、Pillow、ReportLab、pypdf 及支援通知語言的字型。讀取 Notion 頁面需要 Notion 連線，登入截圖或建立 Portal 公告時需有對應站點的存取權。完整流程見 [技能說明](skills/b2c-release-test-notice/SKILL.md)。
