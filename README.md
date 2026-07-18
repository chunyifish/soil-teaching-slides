# SOIL Teaching Slides Skill

把教學材料轉成 SOIL 結構的逐頁企劃與簡報成品，支援：

- A：圖像式 PPTX
- B：可編輯 PPTX
- C：NotebookLM 視覺草稿
- D：離線 HTML 簡報

Mode D 支援高資訊量表格的投影字級、內容精簡與依序揭示。所有模式都會先產生文字版逐頁企劃，經使用者確認後才建立最終簡報。

## 在另一台電腦安裝

### 建議方式：請 Codex 安裝

在另一台電腦登入可存取此 private repo 的 GitHub 帳號，然後在 Codex 開新 task，貼上：

```text
請使用 skill-installer，從 GitHub repo chunyifish/soil-teaching-slides 的 soil-teaching-slides 路徑安裝 skill。
```

安裝完成後，在下一個 task 使用 `$soil-teaching-slides`。

### 手動安裝

先確認 Git 已登入可存取此 repo 的 GitHub 帳號：

```powershell
git clone https://github.com/chunyifish/soil-teaching-slides.git
$skillDestination = "$env:USERPROFILE\.codex\skills\soil-teaching-slides"
if (Test-Path -LiteralPath $skillDestination) {
  throw "Skill already exists: $skillDestination"
}
Copy-Item -LiteralPath '.\soil-teaching-slides\soil-teaching-slides' -Destination $skillDestination -Recurse
```

重新啟動 Codex，或開啟新的 task，讓 Codex 重新載入 skills。

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
4. Codex 會依輸出模式執行版面、溢位、互動或列印驗證。

## Repo 結構

```text
soil-teaching-slides/
├── README.md
└── soil-teaching-slides/
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```
