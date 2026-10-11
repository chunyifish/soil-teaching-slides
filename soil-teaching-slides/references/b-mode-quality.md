# SOIL Teaching Skill — B Mode Quality Enhancement

This document applies only to **Mode B: Editable PPTX**. Keep the existing A/B/C names, plan-confirmation workflow, and SOIL planning interface. It does not change Mode A's image-first pipeline or Mode C's offline HTML renderer.

`../assets/mode-b-approved-reference.pptx` remains the visual layout benchmark. `../assets/Fractal_Editable.pptx` is a quality case for teaching progression and the coordination of diagrams, data, text, and formulas. Learn from the case's decisions; do not reproduce its 18-page sequence or assume its formula implementation is the most maintainable one.

## 1. Design the learning path

Before laying out slides, identify:

- the learning goal and the knowledge structure students must understand;
- the audience's likely prior knowledge;
- a plausible intuition, misconception, or missing connection that could obstruct learning;
- the evidence, comparison, or reasoning that would help learners revise or extend that understanding;
- a new situation in which learners can use the idea.

Use SOIL's existing four processes—**選取、組織、整合、遷移**—and principles—**明確、關聯、結構、脈絡**. Preserve the existing SOIL-1/2/3 planning stages and their confirmation gate, including SOIL-2's **動機、注意、行動** rhythm where it fits. Show where the chosen sequence serves the four processes and four principles in the page plan. Choose the sequence to fit the subject and learner; do not turn the following options into a mandatory script.

Apply the checks inside the current planning stages:

- **SOIL-1 概念定位：** name the learner's starting knowledge, likely intuition or misconception, essential evidence, and intended transfer alongside the core concept and supporting concepts.
- **SOIL-2 教學脈絡定位：** choose a learning path that fits the material, and explain how observation, prediction, evidence, and formalization will be sequenced when those moves help. Cognitive conflict is available but optional.
- **SOIL-3 逐頁架構：** make the learner's task, visible evidence, knowledge relationship, and bridge between pages explicit while keeping one main teaching job per page.

When pedagogically suitable, a sequence may:

1. activate relevant prior knowledge;
2. ask learners to predict, compare, or explain before giving the answer;
3. present an observation, counterexample, data point, or other evidence;
4. connect concrete representations to the underlying relationship;
5. name and formalize the concept, including symbols or equations;
6. give learners a new case to explain or solve.

**Cognitive conflict is optional.** Use it only when the subject contains a useful expectation/evidence gap and the later evidence resolves it. Do not invent a misconception or surprise solely to create drama. A direct explanation, worked example, inquiry, classification, or other sequence may be more appropriate.

For each page, keep the existing plan fields and add the learner's starting idea, the observable task/evidence, and the bridge to the next page when they clarify the teaching logic. Give each page one main teaching job. Prefer showing relationships before naming an abstract symbol when that order helps understanding.

## 2. Choose a visual structure from the knowledge relationship

Retain the existing B-mode system: 16:9 canvas; white background; black text; gray structure; sparse muted-orange emphasis; native editable text and shapes; large readable type; one teaching focus per page. Keep diagrams, data, and formulas in the same visual field when that makes their relationship clear.

Choose representations according to the material:

- comparison → aligned contrast;
- sequence → ordered steps or a process;
- cause and effect → connected causal structure;
- classification → hierarchy or grouped categories;
- quantitative change → geometric model, table, or chart;
- derivation → short visible steps paired with the relevant diagram or data.

Use the existing `editable-pptx-layout.md` tokens and helpers. Do not copy the case deck's page layouts. Maintain enough spacing for labels and formulas; split a long derivation across steps or pages instead of shrinking it until it is hard to read.

## 3. Formula source and rendering policy

Represent each authored mathematical or scientific expression as a **standard LaTeX string** in the slide source. Do not type LaTeX commands into a visible text box. Keep the source available in the authoring data or speaker notes when a formula needs later revision.

### Preferred representation order

1. Use native Office Math (OMML) only when the authoring path produces it without unsafe package surgery and the regression deck opens and renders correctly in both PowerPoint and the available fallback renderer.
2. Otherwise use editable PowerPoint text and shapes: text for symbols and terms, and lines/shapes for fraction bars, radicals, grouping, and alignment. The current supported helper is `scripts/editable_b_formula_helpers.mjs`; it converts the documented LaTeX subset into native editable objects and rejects unsupported syntax instead of exposing raw source.
3. Use SVG/vector or a high-resolution image only when the expression cannot be represented correctly and readably with the preceding approaches. Mark that formula as non-text-editable in the QA report. Do not flatten a whole slide to solve one equation.

Do not inject hand-authored OMML into the PPTX merely to claim native equation editability. A formula that makes the package unreliable is not an acceptable tradeoff.

The supported helper covers fractions; roots; powers and indices; limits; logarithms; sums and integrals with bounds; common Greek letters and operators; and aligned multi-line expressions. It uses ordinary text boxes and simple line shapes, so each element can be selected and edited. If parsing fails, shorten or split the derivation, compose it from the documented primitives, or use the disclosed fallback path.

### Formula layout rules

- Place a formula next to the diagram, measurement, or data row it explains; use matching labels and values.
- Reveal a derivation in readable steps. Highlight a variable, value, or relationship only when it advances the reasoning.
- Keep fractions, indices, roots, and bounds inside the slide and away from overlapping graphics.
- Never display raw LaTeX, a missing-glyph box, or a command name as if it were mathematics.
- Check the rendered expression at full slide size. Automated text scans cannot prove that a symbol's meaning or visual form is correct.

## 4. Output and compatibility

- Write a new deliverable; preserve source and approved files.
- Use a short descriptive ASCII filename, for example `Fractal_Editable.pptx`, `SOIL_Math_Lesson.pptx`, or `Science_Lesson.pptx`.
- Export with the existing `@oai/artifact-tool` workflow. Avoid hand-building or casually repacking an OOXML archive.
- Run `scripts/validate_editable_b_pptx.py` on the final exported file. The validator checks ZIP integrity and CRCs, XML parsing, package relationships, slide references, slide bounds, editable content, visible raw-LaTeX remnants, and the existing Mode B object-hygiene rules.
- Render every slide from the final PPTX to PDF or images and inspect each full-size slide plus a contact sheet. Fix clipping, overflow, overlap, mismatched figure/formula labels, and font substitutions.
- Record the renderer. If Microsoft PowerPoint is available, open the final file read-only there and confirm it opens without repair. If it is unavailable, use LibreOffice and label PowerPoint compatibility **not tested**. Do not equate package validation or LibreOffice success with PowerPoint validation.

## 5. Regression suite and report

Run:

```powershell
python scripts/test_editable_b_quality.py
```

The suite checks the LaTeX cases in `tests/b_mode_formula_cases.json`, verifies that formulas become editable native shapes without visible source commands, validates the supplied 18-page quality case, and generates a small editable regression deck covering geometric comparison, a question/evidence teaching sequence, formula/diagram alignment, Chinese text, fractions, powers and indices, roots, limits, logarithms, multi-line equations, Greek letters, sums, integrals, and chemical subscripts/reaction arrows. It is intentionally smaller than the 18-page case.

On Windows with Microsoft PowerPoint installed, run `powershell -ExecutionPolicy Bypass -File tests/powerpoint_smoke_test.ps1 -PptxPath <final.pptx> -OutputDirectory <empty-qa-folder> -TestEditability`. The execution-policy bypass applies only to that PowerShell process and does not change the machine's policy. The script opens the final deck read-only, exports every slide through PowerPoint, then optionally changes and restores one formula text object in a disposable copy without saving. PowerPoint's automation API requires a visible application window; close it after the check. If PowerPoint is not available, mark the item untested and retain the LibreOffice result separately.

For a deck QA report, record:

- package/ZIP/XML/relationship checks and the validator result;
- slide count and native editable object summary;
- formula cases exercised and any non-editable fallback;
- renderer and full-size slide review result;
- whether Microsoft PowerPoint opened the file (yes/no/not tested);
- any compatibility item that remains unverified.

Passing the automated suite does not replace full-size visual inspection or actual PowerPoint testing.
