export const CANVAS = Object.freeze({ width: 1280, height: 720, centerX: 640 });

export const COLORS = Object.freeze({
  black: "#111111",
  dark: "#333333",
  gray: "#666666",
  line: "#D3D3D3",
  light: "#F3F3F3",
  orange: "#D35230",
  white: "#FFFFFF",
});

export const FONT = "Microsoft JhengHei";

export function addBox(slide, x, y, width, height, options = {}) {
  const geometry = options.geometry ?? "roundRect";
  const shape = slide.shapes.add({
    geometry,
    name: options.name,
    position: { left: x, top: y, width, height },
    fill: options.fill ?? COLORS.white,
    line: {
      style: "solid",
      fill: options.line ?? COLORS.black,
      width: options.lineWidth ?? 1.4,
    },
  });
  return shape;
}

export function addText(slide, value, x, y, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(value);
  shape.text.style = {
    fontFamily: options.fontFamily ?? FONT,
    fontSize: options.fontSize ?? 27,
    bold: options.bold ?? false,
    color: options.color ?? COLORS.black,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "middle",
  };
  return shape;
}

export function addRichText(slide, runs, x, y, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: options.name,
    position: { left: x, top: y, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text.style = {
    fontFamily: options.fontFamily ?? FONT,
    fontSize: options.fontSize ?? 27,
    bold: options.bold ?? false,
    color: options.color ?? COLORS.black,
    alignment: options.align ?? "left",
    verticalAlignment: options.valign ?? "middle",
  };
  shape.text = [{ runs }];
  return shape;
}

export function addLabel(slide, value, x, y, width, options = {}) {
  const height = options.height ?? 52;
  addBox(slide, x, y, width, height, {
    fill: options.fill ?? COLORS.white,
    line: options.line ?? COLORS.black,
    lineWidth: options.lineWidth ?? 1.3,
    name: options.boxName,
  });
  return addText(slide, value, x + 10, y + 3, width - 20, height - 6, {
    fontSize: options.fontSize ?? 27,
    bold: options.bold ?? true,
    color: options.color ?? COLORS.black,
    align: options.align ?? "center",
    name: options.textName,
  });
}

export function addArrowLabel(slide, x, y, options = {}) {
  return addText(slide, options.value ?? "→", x, y, options.width ?? 46, options.height ?? 46, {
    fontSize: options.fontSize ?? 40,
    bold: true,
    color: options.color ?? COLORS.orange,
    align: "center",
  });
}

export function addPageChrome(slide, { number, title, section }) {
  slide.background.fill = COLORS.white;
  addText(slide, title, 58, 26, 1164, 70, {
    fontSize: 43,
    bold: true,
    align: "left",
    name: "mode-b-title",
  });
}

export function addPageMeta(slide, { number, section }) {
  return addText(
    slide,
    `${section ?? "教學"} · ${String(number ?? 1).padStart(2, "0")}`,
    1030,
    676,
    170,
    24,
    { fontSize: 16, color: COLORS.gray, align: "right", name: "mode-b-page-meta" },
  );
}

export function addGroupFrame(slide, x, y, width, height, options = {}) {
  return addBox(slide, x, y, width, height, {
    fill: options.fill ?? COLORS.white,
    line: options.line ?? COLORS.black,
    lineWidth: options.lineWidth ?? 1.6,
    name: options.name,
  });
}

export function addFramedItem(slide, value, x, y, width, height, options = {}) {
  addBox(slide, x, y, width, height, {
    fill: options.fill ?? COLORS.light,
    line: options.line ?? COLORS.line,
    lineWidth: options.lineWidth ?? 1,
    name: options.boxName,
  });
  return addText(slide, value, x + 12, y + 4, width - 24, height - 8, {
    fontSize: options.fontSize ?? 27,
    bold: options.bold ?? false,
    color: options.color ?? COLORS.black,
    align: options.align ?? "center",
    name: options.textName,
  });
}

export function addTakeaway(slide, value, options = {}) {
  addBox(slide, 58, 642, 1164, 62, {
    fill: COLORS.white,
    line: COLORS.gray,
    lineWidth: 1.1,
    name: "mode-b-final-takeaway-bar",
  });
  addText(slide, "◎", 76, 650, 44, 44, {
    fontSize: 34,
    bold: true,
    color: COLORS.orange,
    align: "center",
    name: "mode-b-takeaway-marker",
  });
  const runs = Array.isArray(value) ? value : [{ run: String(value) }];
  addRichText(slide, runs, 130, 649, 850, 48, {
    fontSize: 28,
    bold: true,
    name: "mode-b-takeaway",
  });
  return addText(
    slide,
    `${options.section ?? "教學"} · ${String(options.number ?? 1).padStart(2, "0")}`,
    1010,
    658,
    190,
    30,
    { fontSize: 16, color: COLORS.gray, align: "right", name: "mode-b-page-meta" },
  );
}

export function centeredX(width, centerX = CANVAS.centerX) {
  return centerX - width / 2;
}

export function symmetricPair({ columnWidth, centerGap, centerX = CANVAS.centerX }) {
  return {
    leftX: centerX - centerGap / 2 - columnWidth,
    rightX: centerX + centerGap / 2,
  };
}

export function evenlySpacedRow({ count, itemWidth, left, right }) {
  if (!Number.isInteger(count) || count < 1) throw new Error("count must be a positive integer");
  if (count === 1) return [left + (right - left - itemWidth) / 2];
  const gap = (right - left - count * itemWidth) / (count - 1);
  if (gap < 0) throw new Error("row items do not fit between left and right bounds");
  return Array.from({ length: count }, (_, index) => left + index * (itemWidth + gap));
}

export function addSpeakerNotes(slide, { core, bridge, risk, next }) {
  slide.speakerNotes.textFrame.setText([
    `核心：${core}`,
    `橋接：${bridge}`,
    `風險：${risk}`,
    `下一步：${next}`,
  ]);
  slide.speakerNotes.setVisible(true);
}
