# Mode B Approved Editable PPTX Layout

Use this reference whenever `soil-teaching-slides` produces Mode B. The approved system combines one-line large-text pages with framed-text comparison, process, and hierarchy pages. For teaching sequence, formulas, file reliability, and regression checks, also follow [`b-mode-quality.md`](b-mode-quality.md).

`../assets/mode-b-approved-reference.pptx` is the layout benchmark. Use it to judge hierarchy, spacing, alignment, framed-text density, and large-text treatment. `../assets/Fractal_Editable.pptx` is an additional quality case for learner progression and the integration of geometry, evidence, data, and formulas. Neither deck supplies fixed teaching content, wording, page order, or slide count. Do not assume the case deck's underlying formula construction is the preferred implementation.

## Editable Contract

- Build with the Presentations skill and `@oai/artifact-tool`.
- Keep titles, body text, labels, frames, lines, arrows, tables, diagrams, and page metadata as editable PowerPoint-native objects.
- Default to a pure-text deck. Add images only when the user explicitly requests them.
- Keep speaker notes on every slide.
- Do not flatten a slide into a full-slide bitmap.

## Canvas and Tokens

- Canvas: 1280 × 720, widescreen 16:9.
- Center line: `x = 640`.
- Background: white `#FFFFFF`.
- Primary text: near-black `#111111`.
- Supporting text: dark gray `#333333` or gray `#666666`.
- Structural line: light gray `#D3D3D3`.
- Quiet fill: `#F3F3F3` or lighter.
- Accent: muted orange `#D35230`.
- Font: Microsoft JhengHei (`Microsoft JhengHei`).

Use orange for one core concept, active step, or decisive frame. Do not use it as decoration.

## Type Hierarchy

`@oai/artifact-tool` uses CSS pixels. PowerPoint point size is approximately `px × 0.75`.

- Standard title: 32 PowerPoint pt (`fontSize: 43` px), bold, left-aligned, normally one line.
- Large-text statement, primary question, or conclusion: 48–72 pt (`fontSize: 64–96` px), bold.
- Framed-page main heading: 27–32 pt (`fontSize: 36–43` px).
- General label and supporting explanation: 20–23 pt (`fontSize: 27–31` px).
- Page metadata: 12 pt (`fontSize: 16` px), regular, gray.

Important information must be at least one visible size tier larger than supporting text.

## Large-Text Rule

- Default to one line for the main large-text statement.
- Use two lines only as a rare exception when the wording cannot be shortened without losing meaning.
- Never use more than two lines.
- Shorten the statement or split the idea across slides before shrinking the type merely to make it fit.
- The large statement itself is the slide's takeaway; do not repeat it in a fixed footer.

## Page Chrome and Conclusions

- Title box baseline: `x=58, y=26, w=1164, h=70`.
- Optional metadata: bottom right, gray `section · page`, 12 pt.
- Do not add a fixed takeaway footer by default.
- Put each slide's conclusion inside the content structure:
  - large-text page: the main statement;
  - comparison page: the contrast or decisive framed item;
  - process page: the active final step or an integrated summary frame;
  - hierarchy page: the top core question or conclusion frame.
- Use the helper's `addTakeaway(...)` only when the user explicitly requests a special bottom takeaway page.

## Framed-Text System

Frames are an instructional structure, not decoration. Use as many as needed when they clarify grouping, sequence, hierarchy, or comparison.

Create three visible levels:

1. Outer group frame: black or gray, about 1.4–1.8 px.
2. Inner item frame: light gray, about 1 px, optionally with a quiet fill.
3. One active frame: muted orange, about 2 px.

Keep frames aligned, use consistent corner treatment, and preserve generous internal padding. Do not make every frame orange, equally thick, or equally prominent.

Use `addGroupFrame(...)` for outer groups and `addFramedItem(...)` for repeated inner items when practical.

## Alignment and Symmetry

Calculate positions from the 640 px center line.

For a symmetric pair with column width `w` and center gap `g`:

- Left column `x = 640 - g/2 - w`.
- Right column `x = 640 + g/2`.

For an evenly spaced row between left and right margins:

- Gap is `(right - left - count × itemWidth) / (count - 1)`.
- Item `x = left + index × (itemWidth + gap)`.

Comparison columns, process rows, hierarchy branches, and summary frames must share aligned tops, consistent dimensions, and equal optical weight.

## Approved Page Structures

### Framed Comparison

- Use two equal outer group frames around the center line.
- Align group headings and repeated inner framed items.
- Use the center contrast mark or one decisive item as the teaching focus.
- Reserve orange for one side's decisive difference.

### Framed Process

- Use equal-width outer step frames in one calculated row.
- Place connectors or arrow labels behind or between the steps.
- Put supporting detail inside lighter inner frames.
- Highlight only the decisive final or active step in orange.
- If needed, place one summary frame inside the content area rather than using a footer.

### Framed Hierarchy

- Put one core question or conclusion frame above the child frames.
- Add relationship lines before nodes so the lines remain behind the frames.
- Give child frames equal widths and aligned internal items.
- Use orange on the core frame or one decisive child, not both.

### Large-Text Summary or Question

- Use one main statement, normally on one line.
- Keep generous white space around the statement.
- Use orange on one decisive phrase.
- Do not add a fixed takeaway footer or decorative underline.

## Object Hygiene

Every PowerPoint object must have a visible teaching or structural purpose.

Do not create empty text boxes, invisible placeholders, white cover masks, negative extents, duplicate cover shapes, or off-slide draft objects.

## Speaker Notes

When appropriate, include:

- `核心` — the concept the teacher must land.
- `橋接` — how to connect from the previous slide.
- `風險` — the likely learner misconception.
- `下一步` — the question or action that advances the lesson.

## Build and Review Workflow

1. Confirm the page-by-page text plan and Mode B choice.
2. Build with the Presentations skill and `@oai/artifact-tool`.
3. Reuse `../scripts/editable_b_style_helpers.mjs` for tokens, titles, metadata, framed items, center-line calculations, and notes.
4. Render every slide at 1280 × 720 and create a contact sheet.
5. Inspect each slide at full size.
6. Run the Presentations overflow test.
7. Run `../scripts/validate_editable_b_pptx.py`.
8. Correct alignment, hierarchy, wrapping, notes, or object-hygiene failures before delivery.

## Release Checklist

- [ ] Title is left-aligned and 32 PowerPoint pt.
- [ ] Large-text statement is one line by default and never more than two lines.
- [ ] Audience-facing teaching text is at least 20 PowerPoint pt.
- [ ] Framed pages distinguish outer frames, inner frames, and one orange focus.
- [ ] Comparison/process/hierarchy layouts are calculated and aligned.
- [ ] No fixed takeaway footer appears unless explicitly requested.
- [ ] Optional page metadata is small, gray, and bottom-right.
- [ ] `ppt/media` is zero unless images were explicitly requested.
- [ ] Every slide has speaker notes.
- [ ] Empty transparent objects, white cover masks, and negative extents are zero.
- [ ] All content remains editable.
