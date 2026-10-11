import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { addText, addGroupFrame, COLORS } from "../scripts/editable_b_style_helpers.mjs";
import { addLatexFormula } from "../scripts/editable_b_formula_helpers.mjs";

const runtimeModules = process.env.RUNTIME_NODE_MODULES;
if (!runtimeModules) throw new Error("Set RUNTIME_NODE_MODULES to the bundled presentation dependency directory.");
const artifactToolPath = path.join(runtimeModules, "@oai", "artifact-tool", "dist", "artifact_tool.mjs");
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactToolPath).href);
const outDir = path.resolve(process.argv[2] ?? "work/mode-b-regression");
const casePath = path.resolve(process.argv[3] ?? "tests/b_mode_formula_cases.json");
await fs.mkdir(outDir, { recursive: true });
const formulaCases = JSON.parse(await fs.readFile(casePath, "utf8")).cases;

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function title(slide, text, page) {
  slide.background.fill = COLORS.white;
  addText(slide, text, 56, 26, 1168, 68, { fontSize: 42, bold: true, name: `b-quality-title-${page}` });
  addText(slide, `B 模式回歸 · ${String(page).padStart(2, "0")}`, 1030, 675, 190, 24, {
    fontSize: 16, color: COLORS.gray, align: "right", name: `b-quality-meta-${page}`,
  });
}

function addSquare(slide, x, y, size, name, line = COLORS.black) {
  return slide.shapes.add({
    geometry: "rect", name,
    position: { left: x, top: y, width: size, height: size },
    fill: COLORS.white, line: { style: "solid", fill: line, width: 3 },
  });
}

function addTriangle(slide, x, y, size, name, fill = COLORS.black) {
  return slide.shapes.add({
    geometry: "triangle", name,
    position: { left: x, top: y, width: size, height: size },
    fill, line: { style: "solid", fill: fill, width: 1 },
  });
}

function notes(slide, core, bridge, risk, next, latex = null) {
  const lines = [`核心：${core}`, `橋接：${bridge}`, `風險：${risk}`, `下一步：${next}`];
  if (latex) lines.push(`公式來源 LaTeX：${latex}`);
  slide.speakerNotes.textFrame.setText(lines);
  slide.speakerNotes.setVisible(true);
}

function addFormulaSlide({ page, heading, latex, id, explanation, fontSize = 48 }) {
  const slide = presentation.slides.add();
  title(slide, heading, page);
  const formula = addLatexFormula(slide, latex, { left: 110, top: 220, width: 1060, height: 250 }, {
    name: `formula-${id}`, fontSize, minFontSize: 27, color: COLORS.black,
  });
  addText(slide, explanation, 130, 520, 1020, 62, { fontSize: 30, color: COLORS.dark, align: "center" });
  notes(slide, explanation, "對照上一頁的觀察或模型。", "只讀符號而沒有對應量。", "請用同一關係解釋新例子。", latex);
  return { slide, formula };
}

// 1. A familiar geometric comparison: when a square is scaled down, area and perimeter both fall.
{
  const slide = presentation.slides.add(); title(slide, "一般正方形縮小：面積與周長都變小", 1);
  addSquare(slide, 190, 190, 180, "square-large");
  addSquare(slide, 720, 245, 90, "square-small", COLORS.orange);
  addText(slide, "邊長 4\n面積 16\n周長 16", 170, 410, 220, 126, { fontSize: 30, align: "center" });
  addText(slide, "邊長 2\n面積 4\n周長 8", 655, 410, 220, 126, { fontSize: 30, align: "center", color: COLORS.orange });
  addText(slide, "→", 505, 255, 88, 70, { fontSize: 54, bold: true, align: "center", color: COLORS.orange });
  notes(slide, "確認邊長縮小一半時的面積與周長。", "從熟悉的正方形開始。", "把面積和周長混為同一種量。", "提出挖洞後邊界如何變化。");
}

// 2. Optional cognitive-conflict example, paired with the evidence that resolves it.
{
  const slide = presentation.slides.add(); title(slide, "預測與證據：挖掉一塊後，全部邊界是多少？", 2);
  addSquare(slide, 200, 190, 220, "outer-square");
  slide.shapes.add({ geometry: "rect", name: "removed-center-hole", position: { left: 282, top: 272, width: 56, height: 56 }, fill: COLORS.white, line: { style: "solid", fill: COLORS.orange, width: 3 } });
  addGroupFrame(slide, 590, 175, 475, 355, { line: COLORS.line, lineWidth: 2, name: "evidence-frame" });
  addText(slide, "面積：16 → 15", 630, 230, 400, 66, { fontSize: 42, bold: true, align: "center" });
  addText(slide, "原外框周長：16", 630, 320, 400, 54, { fontSize: 30, align: "center" });
  addText(slide, "新增內框：4", 630, 380, 400, 54, { fontSize: 30, color: COLORS.orange, align: "center" });
  addText(slide, "全部邊界：16 + 4 = 20", 630, 445, 400, 56, { fontSize: 31, bold: true, color: COLORS.orange, align: "center" });
  notes(slide, "先收集預測，再用內外邊界的計數檢驗。", "從等比例縮小轉向改變邊界的操作。", "只計算外框。", "將同一比較方法用在重複挖空。", "P_{all}=P_{outer}+P_{hole}");
}

const byId = new Map(formulaCases.map((item) => [item.id, item]));
const generated = [];
generated.push(addFormulaSlide({ page: 3, id: "fraction", heading: "分數：分子與分母的關係", latex: byId.get("fraction").latex, explanation: "分數由可編輯的分子、分數線與分母組成。", fontSize: 60 }));
generated.push(addFormulaSlide({ page: 4, id: "powers-indices", heading: "指數與上下標", latex: byId.get("powers-indices").latex, explanation: "每一步保留四分之三，初始面積記為 A₀。", fontSize: 50 }));
generated.push(addFormulaSlide({ page: 5, id: "root", heading: "根號與指數", latex: byId.get("root").latex, explanation: "根號與平方項可在同一式中保持清楚層次。", fontSize: 54 }));
generated.push(addFormulaSlide({ page: 6, id: "limit", heading: "極限：重複操作後會趨近哪裡？", latex: byId.get("limit").latex, explanation: "n 增加時，(3/4)ⁿ 趨近 0。", fontSize: 48 }));
generated.push(addFormulaSlide({ page: 7, id: "logarithm", heading: "對數與維度", latex: byId.get("logarithm").latex, explanation: "縮放倍率與相似部分數共同決定維度。", fontSize: 54 }));
generated.push(addFormulaSlide({ page: 8, id: "aligned-greek", heading: "多行推導與希臘字母", latex: byId.get("aligned").latex, explanation: "三行以等號對齊，包含希臘字母。", fontSize: 39 }));
generated.push(addFormulaSlide({ page: 9, id: "sum-integral", heading: "求和與積分符號", latex: byId.get("sum-integral").latex, explanation: "上下界要和求和、積分符號保持對應。", fontSize: 46 }));
generated.push(addFormulaSlide({ page: 10, id: "chemistry", heading: "化學式的上下標與反應箭頭", latex: byId.get("chemistry").latex, explanation: "原子數用下標表示，反應方向由箭頭標示。", fontSize: 48 }));

// 9. The diagram, numerical evidence, and equation share one visible structure.
{
  const slide = presentation.slides.add(); title(slide, "圖形、數據與公式對應同一個縮放關係", 11);
  addTriangle(slide, 170, 190, 210, "whole-triangle");
  addTriangle(slide, 550, 205, 100, "part-triangle-1");
  addTriangle(slide, 655, 205, 100, "part-triangle-2");
  addTriangle(slide, 602, 312, 100, "part-triangle-3");
  addText(slide, "邊長縮小：1/2\n相似部分：3 個", 140, 440, 270, 90, { fontSize: 29, align: "center" });
  addText(slide, "→", 424, 260, 90, 60, { fontSize: 48, bold: true, color: COLORS.orange, align: "center" });
  addLatexFormula(slide, byId.get("logarithm").latex, { left: 790, top: 220, width: 360, height: 130 }, { name: "formula-geometry-link", fontSize: 47, color: COLORS.orange });
  addText(slide, "D ≈ 1.585", 820, 405, 310, 60, { fontSize: 40, bold: true, align: "center", color: COLORS.orange });
  notes(slide, "把幾何份數與縮放倍率代入同一公式。", "先看三個保留部分，再命名符號。", "公式脫離圖形關係。", "以新的縮放例題檢驗遷移。", byId.get("logarithm").latex);
}

for (const [index, slide] of presentation.slides.items.entries()) {
  const blob = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(outDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await blob.arrayBuffer()));
}

const pptxPath = path.join(outDir, "B_Mode_Quality_Regression.pptx");
await (await PresentationFile.exportPptx(presentation)).save(pptxPath);
const manifest = {
  title: "SOIL Teaching Skill - B Mode Quality Regression",
  slides: presentation.slides.items.length,
  formulas: generated.map(({ formula }) => ({ source: formula.source, objectPrefix: formula.objectPrefix, objectCount: formula.objectCount, fontSize: formula.fontSize })),
  testCases: formulaCases.map(({ id, latex, features }) => ({ id, latex, features })),
  pptx: pptxPath,
  renderer: "@oai/artifact-tool in-memory slide PNG export; PPTX is separately rendered in PowerPoint/LibreOffice for QA",
};
await fs.writeFile(path.join(outDir, "regression-manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
console.log(JSON.stringify(manifest, null, 2));
