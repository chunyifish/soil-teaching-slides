# SOIL Teaching Slides Skill

把教學材料轉成 SOIL 結構的逐頁企劃與簡報成品，支援：

- A：圖像式 PPTX
- B：可編輯 PPTX
- C：NotebookLM 視覺草稿
- D：離線 HTML 簡報

Mode D 支援高資訊量表格的投影字級、內容精簡與依序揭示。所有模式都會先產生文字版逐頁企劃，經使用者確認後才建立最終簡報。

## 安裝

### 建議方式：請 Codex 安裝

在 Codex 開新 task，貼上：

```text
請使用 skill-installer，從 GitHub repo chunyifish/soil-teaching-slides 的 soil-teaching-slides 路徑安裝 skill。
```

安裝完成後，重新啟動 Codex 或開啟新的 task，讓 Codex 重新載入 skills。

### 手動安裝

```powershell
git clone https://github.com/chunyifish/soil-teaching-slides.git
$skillDestination = "$env:USERPROFILE\.codex\skills\soil-teaching-slides"
if (Test-Path -LiteralPath $skillDestination) {
  throw "Skill already exists: $skillDestination"
}
Copy-Item -LiteralPath '.\soil-teaching-slides\soil-teaching-slides' -Destination $skillDestination -Recurse
```

## 使用方式

在 prompt 中直接指定 skill，並貼上教材或提供檔案：

```text
$soil-teaching-slides 請把這份教材做成 12 頁可編輯 PPTX。
```

```text
$soil-teaching-slides 請做成離線 HTML 簡報。表格資訊量大，請優先精簡文字、保持投影字級，並讓各列依序出現。
```

工作流程：

1. Codex 先提供文字版逐頁教學企劃。
2. 確認頁數、順序、標題、學習者任務與輸出模式。
3. 回覆「確認」後，Codex 才建立 PPTX、NotebookLM 草稿或 HTML 成品。
4. Codex 依輸出模式執行版面、溢位、互動或列印驗證。

## 授權

本 repo 採雙重授權，授權邊界如下：

### MIT License：程式與可執行範本

下列內容採 [MIT License](LICENSE)：

- `soil-teaching-slides/scripts/`
- `soil-teaching-slides/assets/html-deck-template/`
- `soil-teaching-slides/agents/openai.yaml`

允許私人、教學及商業使用、修改與散布，但必須保留著作權與 MIT 授權聲明。

### CC BY-NC-SA 4.0：SOIL 教學內容

下列內容採 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE-CONTENT.md)：

- `soil-teaching-slides/SKILL.md`
- `soil-teaching-slides/references/`
- `soil-teaching-slides/assets/mode-b-approved-reference.pptx`
- 本 README 中的原創說明文字

這些內容可在非商業情境分享與改作，但必須標示作者、註明修改，並以相同授權分享改作版本。商業使用請先取得著作權人另外授權。

使用本 skill 產生的原創簡報不會自動被要求採用上述授權；但若成品直接重製本 repo 中受授權保護的提示詞、教材文字、參考內容或範例資產，相關部分仍受原授權規範。

完整作者、引用及非官方改作聲明請見 [NOTICE.md](NOTICE.md)。

## 建議引用

```text
李俊儀（2026）。SOIL Teaching Slides Skill（v1.0.0）。
https://github.com/chunyifish/soil-teaching-slides
```

若曾修改內容，請同時標示「本版本已修改，非原始官方版本」。

## Repo 結構

```text
soil-teaching-slides/
├── LICENSE
├── LICENSE-CONTENT.md
├── NOTICE.md
├── README.md
└── soil-teaching-slides/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

## 免責聲明

本專案按現狀提供，不保證適用於所有課程、學習者或技術環境。AI 生成內容仍應由使用者依教材、著作權、教學目標與實際情境進行檢查。
