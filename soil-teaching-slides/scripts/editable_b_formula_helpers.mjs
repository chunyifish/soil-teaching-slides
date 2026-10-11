import { COLORS, FONT } from "./editable_b_style_helpers.mjs";

const GREEK = Object.freeze({
  alpha: "α", beta: "β", gamma: "γ", delta: "δ", epsilon: "ε",
  theta: "θ", lambda: "λ", mu: "μ", pi: "π", rho: "ρ", sigma: "σ",
  phi: "φ", omega: "ω", Gamma: "Γ", Delta: "Δ", Theta: "Θ",
  Lambda: "Λ", Pi: "Π", Sigma: "Σ", Phi: "Φ", Omega: "Ω",
});

const SYMBOLS = Object.freeze({
  infty: "∞", times: "×", cdot: "·", pm: "±", mp: "∓", neq: "≠",
  le: "≤", leq: "≤", ge: "≥", geq: "≥", approx: "≈", equiv: "≡",
  to: "→", rightarrow: "→", leftarrow: "←", leftrightarrow: "↔",
  Rightarrow: "⇒", Leftrightarrow: "⇔", rightleftharpoons: "⇌",
  partial: "∂", nabla: "∇", forall: "∀", exists: "∃", in: "∈",
  notin: "∉", cup: "∪", cap: "∩", emptyset: "∅", degree: "°",
  up: "↑", down: "↓",
});

const TEXT_OPERATORS = new Set(["log", "ln", "sin", "cos", "tan", "lim", "max", "min"]);
const LARGE_OPERATORS = Object.freeze({ sum: "∑", int: "∫", prod: "∏" });
const WIDE_MATH_GLYPHS = new Set(["∞", "→", "←", "↔", "⇒", "⇔", "⇌", "≤", "≥", "≈", "≡", "∅", "∇"]);

function macroAt(source, index) {
  let end = index + 1;
  if (/[A-Za-z]/.test(source[end] ?? "")) {
    while (/[A-Za-z]/.test(source[end] ?? "")) end += 1;
  } else if (end < source.length) {
    end += 1;
  }
  return { name: source.slice(index + 1, end), end };
}

function groupAt(source, index) {
  while (/\s/.test(source[index] ?? "")) index += 1;
  if (source[index] !== "{") throw new Error(`Expected a braced LaTeX group at character ${index}.`);
  let depth = 1;
  let end = index + 1;
  while (end < source.length && depth > 0) {
    if (source[end] === "\\") {
      end = macroAt(source, end).end;
      continue;
    }
    if (source[end] === "{") depth += 1;
    else if (source[end] === "}") depth -= 1;
    end += 1;
  }
  if (depth !== 0) throw new Error(`Unclosed LaTeX group beginning at character ${index}.`);
  return { value: source.slice(index + 1, end - 1), end };
}

function operandAt(source, index) {
  while (/\s/.test(source[index] ?? "")) index += 1;
  if (source[index] === "{") return groupAt(source, index);
  if (source[index] === "\\") {
    const macro = macroAt(source, index);
    if (source[macro.end] === "{") {
      const group = groupAt(source, macro.end);
      return { value: source.slice(index, group.end), end: group.end };
    }
    return { value: source.slice(index, macro.end), end: macro.end };
  }
  if (index >= source.length) throw new Error("Missing superscript or subscript value.");
  return { value: source[index], end: index + 1 };
}

function addScript(nodes, kind, value) {
  const base = nodes.pop();
  if (!base) throw new Error(`LaTeX ${kind} script has no base expression.`);
  if (base.type === "script") {
    if (base[kind]) throw new Error(`Repeated ${kind} script is not supported in the same group.`);
    base[kind] = value;
    nodes.push(base);
    return;
  }
  if (base.type === "largeOperator" || base.type === "limit") {
    if (base[kind]) throw new Error(`Repeated ${kind} limit is not supported.`);
    base[kind] = value;
    nodes.push(base);
    return;
  }
  nodes.push({ type: "script", base, [kind]: value });
}

function parseSequence(source) {
  const nodes = [];
  for (let i = 0; i < source.length;) {
    const char = source[i];
    if (/\s/.test(char)) {
      let end = i + 1;
      while (/\s/.test(source[end] ?? "")) end += 1;
      nodes.push({ type: "space", count: Math.min(2, end - i) });
      i = end;
      continue;
    }
    if (char === "^") {
      const operand = operandAt(source, i + 1);
      addScript(nodes, "sup", parseSequence(operand.value));
      i = operand.end;
      continue;
    }
    if (char === "_") {
      const operand = operandAt(source, i + 1);
      addScript(nodes, "sub", parseSequence(operand.value));
      i = operand.end;
      continue;
    }
    if (char === "{") {
      const group = groupAt(source, i);
      nodes.push(...parseSequence(group.value));
      i = group.end;
      continue;
    }
    if (char === "}") throw new Error(`Unexpected closing brace at character ${i}.`);
    if (char !== "\\") {
      nodes.push({ type: "text", value: char });
      i += 1;
      continue;
    }

    const { name, end } = macroAt(source, i);
    i = end;
    if (name === "frac" || name === "dfrac" || name === "tfrac") {
      const numerator = groupAt(source, i);
      const denominator = groupAt(source, numerator.end);
      nodes.push({ type: "fraction", numerator: parseSequence(numerator.value), denominator: parseSequence(denominator.value) });
      i = denominator.end;
    } else if (name === "sqrt") {
      const radicand = groupAt(source, i);
      nodes.push({ type: "root", radicand: parseSequence(radicand.value) });
      i = radicand.end;
    } else if (["text", "mathrm", "operatorname", "mathbf", "mathit", "textsf", "textrm"].includes(name)) {
      const group = groupAt(source, i);
      nodes.push(...parseSequence(group.value));
      i = group.end;
    } else if (name === "," || name === ";" || name === ":" || name === "quad" || name === "qquad") {
      nodes.push({ type: "space", count: name === "qquad" ? 4 : name === "quad" ? 3 : name === "," ? 0.6 : 1 });
    } else if (["!", "displaystyle", "textstyle", "limits", "nolimits", "left", "right"].includes(name)) {
      // These change TeX spacing or delimiters, not the visible math content here.
    } else if (GREEK[name]) {
      nodes.push({ type: "text", value: GREEK[name] });
    } else if (SYMBOLS[name]) {
      nodes.push({ type: "text", value: SYMBOLS[name] });
    } else if (TEXT_OPERATORS.has(name)) {
      nodes.push({ type: name === "lim" ? "limit" : "text", value: name });
    } else if (LARGE_OPERATORS[name]) {
      nodes.push({ type: "largeOperator", value: LARGE_OPERATORS[name].trim() });
    } else if (name === "end") {
      throw new Error("Unmatched LaTeX \\end; use a supported aligned environment or split the expression.");
    } else if (name === "begin") {
      throw new Error("Nested LaTeX environments are not supported by the editable formula helper.");
    } else {
      throw new Error(`Unsupported LaTeX command \\${name}; compose with editable primitives or use the disclosed fallback.`);
    }
  }
  return mergeTextNodes(nodes);
}

function mergeTextNodes(nodes) {
  const result = [];
  for (const node of nodes) {
    const last = result[result.length - 1];
    if (node.type === "text" && last?.type === "text") last.value += node.value;
    else result.push(node);
  }
  return result;
}

function parseRows(latex) {
  const start = String.raw`\begin{aligned}`;
  const end = String.raw`\end{aligned}`;
  let source = latex.trim();
  if (source.startsWith(start) && source.endsWith(end)) {
    source = source.slice(start.length, -end.length);
  } else if (/\\begin\{/.test(source) || /\\end\{/.test(source)) {
    throw new Error("Only the aligned LaTeX environment is supported for multi-line formulas.");
  }
  return source.split(String.raw`\\`).map((row) => row.replaceAll("&", "").trim()).filter(Boolean).map(parseSequence);
}

function textWidth(value, fontSize) {
  let units = 0;
  for (const char of value) {
    if (/\s/.test(char)) units += 0.32;
    else if (/^[\u2E80-\u9FFF]$/u.test(char)) units += 1;
    else if (WIDE_MATH_GLYPHS.has(char)) units += 1.15;
    else if (/^[α-ωΓ-Ω]$/u.test(char)) units += 0.78;
    else if (/^[il.,:;!'|]$/.test(char)) units += 0.34;
    else if (/^[mw@%]$/.test(char)) units += 0.86;
    else if (/^[MW]$/.test(char)) units += 0.9;
    else if (/^[A-Z]$/.test(char)) units += 0.7;
    else units += 0.61;
  }
  return Math.max(fontSize * 0.28, units * fontSize);
}

function dimensions(nodes, fontSize) {
  const entries = nodes.map((node) => dimension(node, fontSize));
  return {
    width: entries.reduce((sum, item) => sum + item.width, 0),
    ascent: Math.max(fontSize * 0.78, ...entries.map((item) => item.ascent)),
    descent: Math.max(fontSize * 0.24, ...entries.map((item) => item.descent)),
  };
}

function dimension(node, fontSize) {
  const line = fontSize * 1.08;
  if (node.type === "space") return { width: fontSize * 0.28 * node.count, ascent: 0, descent: 0 };
  if (node.type === "text") return { width: textWidth(node.value, fontSize), ascent: fontSize * 0.8, descent: fontSize * 0.24 };
  if (node.type === "fraction") {
    const n = dimensions(node.numerator, fontSize * 0.72);
    const d = dimensions(node.denominator, fontSize * 0.72);
    return { width: Math.max(n.width, d.width) + fontSize * 0.34, ascent: n.ascent + n.descent + fontSize * 0.19, descent: d.ascent + d.descent + fontSize * 0.19 };
  }
  if (node.type === "root") {
    const r = dimensions(node.radicand, fontSize * 0.92);
    return { width: fontSize * 0.76 + r.width + fontSize * 0.08, ascent: Math.max(fontSize * 0.94, r.ascent + r.descent + fontSize * 0.12), descent: r.descent };
  }
  if (node.type === "script") {
    const base = dimension(node.base, fontSize);
    const sup = node.sup ? dimensions(node.sup, fontSize * 0.62) : null;
    const sub = node.sub ? dimensions(node.sub, fontSize * 0.62) : null;
    return {
      width: base.width + Math.max(sup?.width ?? 0, sub?.width ?? 0),
      ascent: Math.max(base.ascent, sup ? base.ascent * 0.72 + sup.ascent + sup.descent * 0.3 : 0),
      descent: Math.max(base.descent, sub ? base.descent + sub.ascent + sub.descent * 0.42 : 0),
    };
  }
  if (node.type === "limit" || node.type === "largeOperator") {
    const base = textWidth(node.value, fontSize);
    const sup = node.sup ? dimensions(node.sup, fontSize * 0.58) : null;
    const sub = node.sub ? dimensions(node.sub, fontSize * 0.58) : null;
    return {
      width: Math.max(base, sup?.width ?? 0, sub?.width ?? 0) + fontSize * 0.12,
      ascent: fontSize * 0.8 + (sup ? sup.ascent + sup.descent * 0.55 : 0),
      descent: fontSize * 0.24 + (sub ? sub.ascent + sub.descent * 0.55 : 0),
    };
  }
  return { width: line, ascent: fontSize * 0.8, descent: fontSize * 0.24 };
}

function makeText(slide, value, x, top, width, height, options, counter) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name: `${options.name ?? "b-formula"}-part-${counter.value++}`,
    position: { left: x, top, width: Math.max(1, width), height: Math.max(1, height) },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontFamily: options.fontFamily ?? FONT,
    fontSize: options.fontSize,
    color: options.color ?? COLORS.black,
    alignment: "center",
    verticalAlignment: "middle",
  };
  shape.text.insets = 0;
}

function makeRule(slide, x, y, width, thickness, options, counter) {
  slide.shapes.add({
    geometry: "rect",
    name: `${options.name ?? "b-formula"}-rule-${counter.value++}`,
    position: { left: x, top: y, width: Math.max(1, width), height: Math.max(1, thickness) },
    fill: options.color ?? COLORS.black,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function drawSequence(slide, nodes, x, baseline, fontSize, options, counter) {
  let cursor = x;
  for (const node of nodes) {
    const d = dimension(node, fontSize);
    if (node.type === "space") {
      cursor += d.width;
    } else if (node.type === "text") {
      makeText(slide, node.value, cursor, baseline - d.ascent, d.width + 2, d.ascent + d.descent, { ...options, fontSize }, counter);
      cursor += d.width;
    } else if (node.type === "fraction") {
      const small = fontSize * 0.72;
      const n = dimensions(node.numerator, small);
      const den = dimensions(node.denominator, small);
      const pad = (d.width - Math.max(n.width, den.width)) / 2;
      const gap = fontSize * 0.11;
      drawSequence(slide, node.numerator, cursor + pad + (Math.max(n.width, den.width) - n.width) / 2, baseline - gap - n.descent, small, options, counter);
      makeRule(slide, cursor + 1, baseline, d.width - 2, Math.max(1.5, fontSize * 0.045), options, counter);
      drawSequence(slide, node.denominator, cursor + pad + (Math.max(n.width, den.width) - den.width) / 2, baseline + gap + den.ascent, small, options, counter);
      cursor += d.width;
    } else if (node.type === "root") {
      const radicalWidth = fontSize * 0.76;
      const radFs = fontSize * 0.92;
      const rad = dimensions(node.radicand, radFs);
      makeText(slide, "√", cursor, baseline - fontSize * 0.95, radicalWidth, fontSize * 1.24, { ...options, fontSize: fontSize * 1.16 }, counter);
      makeRule(slide, cursor + radicalWidth * 0.78, baseline - rad.ascent - fontSize * 0.05, rad.width + 2, Math.max(1.5, fontSize * 0.045), options, counter);
      drawSequence(slide, node.radicand, cursor + radicalWidth, baseline, radFs, options, counter);
      cursor += d.width;
    } else if (node.type === "script") {
      const base = dimension(node.base, fontSize);
      drawSequence(slide, [node.base], cursor, baseline, fontSize, options, counter);
      const scriptFs = fontSize * 0.62;
      if (node.sup) {
        const sd = dimensions(node.sup, scriptFs);
        drawSequence(slide, node.sup, cursor + base.width, baseline - base.ascent * 0.72 - sd.descent, scriptFs, options, counter);
      }
      if (node.sub) {
        const sd = dimensions(node.sub, scriptFs);
        drawSequence(slide, node.sub, cursor + base.width, baseline + base.descent + sd.ascent * 0.64, scriptFs, options, counter);
      }
      cursor += d.width;
    } else if (node.type === "limit" || node.type === "largeOperator") {
      const baseWidth = textWidth(node.value, fontSize);
      const baseX = cursor + (d.width - baseWidth) / 2;
      makeText(slide, node.value, baseX, baseline - fontSize * 0.8, baseWidth + 2, fontSize * 1.06, { ...options, fontSize }, counter);
      if (node.sup) {
        const sd = dimensions(node.sup, fontSize * 0.58);
        drawSequence(slide, node.sup, cursor + (d.width - sd.width) / 2, baseline - fontSize * 0.8 - sd.ascent - sd.descent * 0.4, fontSize * 0.58, options, counter);
      }
      if (node.sub) {
        const sd = dimensions(node.sub, fontSize * 0.58);
        drawSequence(slide, node.sub, cursor + (d.width - sd.width) / 2, baseline + fontSize * 0.24 + sd.ascent + 4, fontSize * 0.58, options, counter);
      }
      cursor += d.width;
    }
  }
}

/**
 * Lay out a documented LaTeX subset as individually editable PowerPoint text and shapes.
 * Returns the exact source and the generated object prefix for an authoring manifest.
 */
export function addLatexFormula(slide, latex, box, options = {}) {
  if (typeof latex !== "string" || !latex.trim()) throw new TypeError("latex must be a non-empty standard LaTeX string.");
  const rows = parseRows(latex);
  const requestedSize = options.fontSize ?? 40;
  const minSize = options.minFontSize ?? 27;
  const gap = options.rowGap ?? requestedSize * 0.28;
  const measureRows = (size) => rows.map((row) => dimensions(row, size));
  const rowMetrics = measureRows(requestedSize);
  const naturalWidth = Math.max(...rowMetrics.map((row) => row.width));
  const naturalHeight = rowMetrics.reduce((sum, row) => sum + row.ascent + row.descent, 0) + gap * (rows.length - 1);
  const scale = Math.min(1, box.width / Math.max(1, naturalWidth), box.height / Math.max(1, naturalHeight));
  const fontSize = requestedSize * scale;
  if (fontSize < minSize) {
    throw new Error(`Formula needs about ${Math.ceil(fontSize)} px in this box; enlarge the box or split the derivation (minimum ${minSize} px).`);
  }
  const metrics = measureRows(fontSize);
  const totalHeight = metrics.reduce((sum, row) => sum + row.ascent + row.descent, 0) + gap * scale * (rows.length - 1);
  let baseline = box.top + (box.height - totalHeight) / 2 + metrics[0].ascent;
  const counter = { value: 1 };
  const baseOptions = { ...options, fontSize, name: options.name ?? "b-formula" };
  const formulaCenter = box.left + box.width / 2;

  rows.forEach((row, index) => {
    const rowMetrics = metrics[index];
    const eqIndex = row.findIndex((node) => node.type === "text" && node.value.includes("="));
    let rowX;
    if (rows.length > 1 && eqIndex >= 0) {
      const prefixWidth = dimensions(row.slice(0, eqIndex), fontSize).width;
      const maxPrefix = Math.max(...rows.map((candidate) => {
        const candidateEq = candidate.findIndex((node) => node.type === "text" && node.value.includes("="));
        return candidateEq < 0 ? 0 : dimensions(candidate.slice(0, candidateEq), fontSize).width;
      }));
      rowX = formulaCenter - maxPrefix + (maxPrefix - prefixWidth);
    } else {
      rowX = formulaCenter - rowMetrics.width / 2;
    }
    drawSequence(slide, row, rowX, baseline, fontSize, baseOptions, counter);
    baseline += rowMetrics.ascent + rowMetrics.descent + gap * scale;
  });

  return { source: latex, objectPrefix: baseOptions.name, objectCount: counter.value - 1, fontSize };
}

export function parseLatexForEditableLayout(latex) {
  return parseRows(latex);
}

export const EDITABLE_FORMULA_MACROS = Object.freeze({
  greek: Object.keys(GREEK),
  operators: [...Object.keys(SYMBOLS), ...Object.keys(LARGE_OPERATORS), ...TEXT_OPERATORS],
  structures: ["frac", "sqrt", "superscript", "subscript", "aligned"],
});
