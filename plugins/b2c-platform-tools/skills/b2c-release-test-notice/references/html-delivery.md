# HTML 交付方式

將已核對的內容寫成一份 UTF-8 JSON，再呼叫 `scripts/render_notice.py`。可用宿主的文件/PDF Python 環境；腳本需要 `Pillow`、`reportlab`、`pypdf`。Windows 預設使用微軟正黑體，其他環境可傳入支援繁體中文的 TrueType 字型。優先使用可用的內附工具，無須公開上傳截圖。

```text
python <skill>/scripts/render_notice.py --input <notice.json> --output <通知名稱>.html
```

非 Windows 或需指定字型時加上 `--font <regular.ttf> --bold-font <bold.ttf>`。輸入 JSON 和截圖是工作素材；交付路徑只需 HTML。截圖路徑相對於輸入 JSON 所在目錄，也可給本機絕對路徑。

```json
{
  "type": "release",
  "language": "zh-Hant",
  "title": "訂單查詢新增交貨區間",
  "highlight": "2026/11/06",
  "blocks": [
    {"kind": "paragraph", "text": "訂單查詢已於 2026/11/06 上線交貨區間篩選。"},
    {"kind": "heading", "text": "本次更新重點"},
    {"kind": "bullet", "text": "可依預計交貨起訖日篩選訂單。"},
    {"kind": "image", "path": "filter.png", "alt": "訂單查詢的交貨區間欄位", "caption": "圖 1｜設定交貨區間"}
  ]
}
```

`type` 可用 `release` 或 `test`。依提問卡片選擇填寫 `language` 為 `zh-Hant`（繁體中文）、`en`（英文）或 `bilingual`（中英雙語）。既有輸入未含 `language` 時沿用繁體中文。單語將該語言的標題寫入 `title`，雙語將中文標題寫入 `title`、英文標題寫入 `title_en`，並在同一個 `blocks` 陣列先放中文正文，再放英文正文。產生器會自動附上各語言對應的通知類型。請在輸入中提供已整理好的文字，產生器依內容排版。

`highlight` 選填，僅標色正文中相同的文字，不代表日期或部署狀態已確認。文字段落支援 `heading`、`paragraph`、`bullet`、`emphasis`。圖片支援 PNG、JPEG，`alt` 必填，`caption` 選填。無截圖就省略圖片區塊。使用文字欄位，不在輸入中塞 HTML 或 JavaScript。

版面特別保留 Outlook 貼上修正：正文使用單層 `width="100%"` 表格；表格本身不設 `align` 或 `float`，靠左設定放在儲存格及文字。每列使用 inline 字型、字級、顏色、行距、內距和背景，圖片指定尺寸及替代文字。複製結果為郵件正文，避免工具列、外層容器和腳本進入郵件。傳統 Outlook 貼上時選「保留來源格式」，在原信表格外的空白段落貼上。

產生器會重新讀取內嵌 PDF，比對正文和圖文順序。對成品另檢查 PDF 分頁、截圖與文字是否被截斷；可用本機暫存檔渲染檢查，最終只交付 HTML。瀏覽器遇到同名下載檔可能自行附加編號。
