# 高解析度截圖

**每 1 CSS px 至少 2 個像素的要求及下方放大分塊流程僅適用於 Claude。** 通知以 860 px 欄寬顯示，Claude 使用 2 倍原圖維持文字與標註清晰度。

Codex 與其他非 Claude 宿主使用工具輸出的原生截圖，以文字及操作欄位清楚可讀為準，不因未達 2 倍而要求分塊、切換瀏覽器或補圖。標註仍使用共用腳本，`scale` 填入實際的「存檔寬度 ÷ 網頁 CSS 寬度」，不可將 1 倍原圖直接宣告為 2 倍。

## Claude：先量測，再決定擷取方式

1. 依 SKILL 第 3 步拉寬網頁、收合 MENU，確認可視寬度大於 1000 CSS px。
2. 以 JavaScript 讀取 `innerWidth`、`innerHeight`，再擷取一張完整可視範圍並讀取存檔的像素寬度。
3. 計算 `存檔寬度 ÷ innerWidth`：
   - **2 以上**：直接使用該截圖，免分塊。
   - **低於 2**：截圖工具已縮小畫面，例如 Claude 桌面版內部瀏覽器固定輸出 800 px 寬。改用下方的放大分塊擷取。
   - 工具無法執行 JavaScript 或存出原檔時，請使用者用 Chrome DevTools 的 `Capture screenshot`（DPR 2），或 Win+Shift+S 擷取含頁首的畫面。

禁止用放大圖片或 AI 放大補足解析度；放大只會把模糊的像素拉大，AI 放大還可能改寫中文字。

## Claude：放大分塊擷取

對 `html` 元素套用 CSS `transform: scale()`。版面寬度不變，瀏覽器以較大比例重新繪製文字與線條，每次只截一塊，再拼接成 2 倍原圖。

1. **產生計畫。** `--viewport` 為 `innerWidth`x`innerHeight`，`--output` 為截圖工具輸出的像素尺寸，`--region` 為要保留的頁面範圍（從左上角起算，含系統頁首，單位 CSS px）。

   ```text
   python <skill>/scripts/annotate_screenshot.py plan --viewport 1060x934 --output 800x705 --region 1060x530
   ```

   計畫列出 `transform`、`setup_js`、每塊的 `js` 與拼接座標，以及 `restore_js`。倍率公式為 `2 × innerWidth ÷ 輸出寬度`。
2. **依序擷取。** 執行一次 `setup_js`；每塊先執行該塊 `js`，**等待至少 1.5 秒**再截圖，以工具的完整輸出尺寸存成無損 PNG，檔名使用計畫的 `file`。不可用縮小預覽代替存檔，縮小預覽的存檔也會變小。
3. **逐塊核對。** 畫面重繪可能比截圖慢，導致某塊截到上一塊的內容。比對每塊應出現的區域；`render` 遇到完全相同的兩塊會提出警告，非空白區域須重截。
4. **一定還原。** 完成或中途失敗都執行 `restore_js`，確認網頁恢復原狀。此操作只改變顯示，不送出資料；畫面在擷取期間會放大閃動。

限制：展開中的原生下拉選單、滑鼠懸停提示、固定位置浮層可能無法正確呈現。需要這些狀態時，改請使用者以 DevTools 或 Win+Shift+S 擷取。

## 標註與輸出

各宿主共用標註腳本。Claude 分塊時，把計畫的 `size`、`tiles` 與標註寫成 JSON，交給 `render` 拼接並標註。使用單張原生截圖時，改用 `"image": "raw.png"` 取代 `tiles` 與 `size`，並將 `scale` 設為實際原圖倍率；下例的 `2` 只代表 2 倍原圖。

```json
{
  "scale": 2,
  "size": [2120, 1060],
  "tiles": [{"file": "tile-r0-c0.png", "x": 0, "y": 0}],
  "crop": [0, 0, 1060, 530],
  "marks": [
    {"n": 1, "target": [440, 174, 620, 235], "side": "above", "line_y": 124, "text": "點選匯入本週 Forecast 範本"},
    {"n": 2, "target": [334, 353, 624, 391], "side": "right", "pad": [4, 2.5], "stroke": 2, "text": "選擇與範本相同的國家"},
    {"n": 3, "target": [34, 477, 79, 507], "side": "right", "text": "點選匯入"}
  ]
}
```

```text
python <skill>/scripts/annotate_screenshot.py render --input <spec.json> --output <step>.png
```

- `target` 為操作目標的左、上、右、下，單位是頁面 CSS px；可用 `getBoundingClientRect()` 量測，內嵌框架須加上框架本身的位移。
- `side` 決定圓點與說明文字的位置：`right`、`left`，或兩側沒有空間時用 `above`、`below`（與框左緣對齊，可用 `line_y` 指定該行中心）。
- 相鄰目標間距小於 8 CSS px 時，用 `pad` 縮小上下留白並設 `stroke` 為 2；框線互相接觸時腳本會停止。
- 選填 `crop`（CSS px）、`color`（整份或單點，最多三色），以及非 Windows 環境的 `--font <bold.ttf>`。
- 輸出的 PNG 直接放入通知 JSON；產生器會把寬度超過 1720 px 的圖縮成 1720 px，HTML 與 PDF 共用同一張圖。
