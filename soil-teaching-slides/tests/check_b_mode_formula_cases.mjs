import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseLatexForEditableLayout } from "../scripts/editable_b_formula_helpers.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const casesPath = path.resolve(process.argv[2] ?? path.join(here, "b_mode_formula_cases.json"));
const { cases } = JSON.parse(await fs.readFile(casesPath, "utf8"));

function flatten(value, output = []) {
  if (Array.isArray(value)) value.forEach((item) => flatten(item, output));
  else if (value && typeof value === "object") {
    output.push(value);
    for (const [key, child] of Object.entries(value)) {
      if (key !== "value" && typeof child !== "string") flatten(child, output);
    }
  }
  return output;
}

function hasFeature(nodes, feature) {
  const all = flatten(nodes);
  if (feature === "fraction") return all.some((node) => node.type === "fraction");
  if (feature === "root") return all.some((node) => node.type === "root");
  if (feature === "superscript") return all.some((node) => node.type === "script" && node.sup);
  if (feature === "subscript") return all.some((node) => node.type === "script" && node.sub);
  if (feature === "limit") return all.some((node) => node.type === "limit");
  if (feature === "logarithm") return all.some((node) => node.type === "text" && node.value === "log");
  if (feature === "multiline") return nodes.length > 1;
  if (feature === "greek") return all.some((node) => node.type === "text" && /[α-ωΓΔΘΛΠΣΦΩ]/u.test(node.value));
  if (feature === "sum") return all.some((node) => node.type === "largeOperator" && node.value === "∑");
  if (feature === "integral") return all.some((node) => node.type === "largeOperator" && node.value === "∫");
  if (feature === "bounds") return all.some((node) => node.type === "largeOperator" && node.sub && node.sup);
  if (feature === "infinity") return all.some((node) => node.type === "text" && node.value.includes("∞"));
  if (feature === "arrow") return all.some((node) => node.type === "text" && node.value.includes("→"));
  throw new Error(`No feature check is registered for: ${feature}`);
}

for (const item of cases) {
  const nodes = parseLatexForEditableLayout(item.latex);
  for (const feature of item.features) {
    if (!hasFeature(nodes, feature)) throw new Error(`${item.id}: missing parsed feature ${feature}`);
  }
  if (/\\(?:frac|sqrt|sum|int|lim|log|alpha|beta|gamma|begin|end)\b/.test(JSON.stringify(nodes))) {
    throw new Error(`${item.id}: LaTeX source command leaked into the rendered layout tree.`);
  }
}

let rejected = false;
try {
  parseLatexForEditableLayout(String.raw`\unknown{x}`);
} catch (error) {
  rejected = /Unsupported LaTeX command/.test(String(error));
}
if (!rejected) throw new Error("Unsupported LaTeX commands must fail clearly instead of appearing as raw source.");

console.log(`PASS: parsed ${cases.length} LaTeX cases; required structures and explicit unsupported-command rejection verified.`);
