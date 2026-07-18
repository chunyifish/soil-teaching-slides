# Hand-Drawn SOIL Teaching Slide Style

Use this compact reference for Modes A and C. Both modes share the old visual template. `soil-handdrawn-style-v2.yaml` is the canonical source of truth; this file translates it into quick operational guidance. Mode B is independent and must not inherit these rules.

This style is based on the user's confirmed `黑白手繪教學圖解風` YAML v2.1.

## Core Look

- 16:9 landscape teaching slide.
- Pure white or near-white background.
- Top-left medium-gray square page-number block, `#6B6B6B`, with large white digits such as `01`; never use a black or near-black fill.
- Put exactly one approved Traditional Chinese course/section label immediately to the right of the page marker. Do not concatenate key labels or invent a new label.
- Keep the page-number block, section-label baseline, font size, weight, spacing, and short orange underline identical on every slide. Use one fixed underline length and thickness across the deck.
- Huge bold black Traditional Chinese title across the upper center.
- Central teaching diagram built from black-and-white hand-drawn line art.
- Pencil sketch texture, clean gray hatching, and teaching-handbook/manual feeling.
- Orange is the only strong accent and should stay under 10% of the page.
- Use orange arrows to show flow, transformation, cause/effect, or decision paths.
- Use orange circular number markers such as `1`, `2`, `3` for sequence or key steps.
- Use black frames, rounded manual-like boxes, labels, checklists, worksheet panels, or page tabs to chunk information.
- Bottom takeaway box: large white rounded rectangle with a thin light-gray `#D9D9D9` outline; never use a black or dark-gray border.
- Bottom takeaway has an orange lightbulb, target, check, or guiding icon on the left.
- Bottom takeaway text is large and bold; highlight only one key word or phrase in orange when possible.
- Make every visible character resemble Microsoft JhengHei, including tiny illustration labels. Do not allow handwritten, calligraphic, serif, or English placeholder text inside diagrams.

## Illustration Language

- Prefer black-and-white sketch objects and simple teaching scenes.
- Acceptable objects: teacher, student, AI machine, laptop, book, worksheet, lamp, board, cards, gears, checklist, table, pathway, notebook, folder, form, stamp, magnifying glass, clipboard.
- Draw figures as clean line art with light hatching, not realistic photos.
- Use friendly instructional drawings, not corporate stock illustration.
- Keep the visual relationship obvious at thumbnail size.
- Each page should feel like one teaching diagram, not a generic infographic.
- Use concrete objects as metaphors for abstract teaching ideas.

## Layout Decision Rule

Do not copy a reference image layout. Use the SOIL slide plan to choose the layout:

- Comparison: left-right or top-bottom contrast cards.
- Process: connected steps, orange arrows, or numbered stations.
- Hierarchy: layers, tabs, tree structure, or nested frames.
- System: central concept with simple surrounding links.
- Checklist: clipboard, manual page, or form with check marks.
- Matrix: simplify if image2 must render text directly; prefer large cards plus a transfer arrow over dense small cells.
- Summary: four-item checklist, convergence map, or action list.

Priority order:

1. SOIL page role and structure type
2. Current teaching task
3. Information relationship
4. Visual style consistency
5. Decoration

## Direct Traditional Chinese Text With Image2

Use direct-generated Traditional Chinese when the user explicitly asks for text to be in the image, asks for ChatGPT Image 2/image2 complete slide images, or chooses Mode A and does not request editable/native text.

- Keep on-slide text short, large, and already approved in the slide plan.
- Include only: page number, section label, title, key labels, and bottom takeaway.
- Quote exact text in prompts and say `all visible text must be directly rendered in the image`.
- By default, request typography that visually resembles Microsoft JhengHei: clean bold Traditional Chinese sans-serif, upright strokes, high legibility, and no calligraphy. This is a visual instruction to image2, not a claim that the installed Microsoft font is embedded.
- Keep the text inside the generated image for Mode A. Do not switch to PowerPoint text overlays unless the user explicitly requests editable or typographically exact text.
- Avoid dense paragraphs, small annotations, and full data tables.
- For difficult slides, reduce text before regenerating rather than adding more prompt instructions.
- Regenerate slides with obvious title errors, wrong page numbers, unreadable labels, or style drift.
- Tell the user if some small text may not be character-perfect because image2 direct text is probabilistic.

## Prompt Pattern

Use a compact prompt shape:

```text
Use case: scientific-educational
Asset type: complete 16:9 presentation slide image, slide <N> of <TOTAL>
Style name: 黑白手繪教學圖解風
Primary request: Create a complete Traditional Chinese teaching slide. All visible text must be directly rendered in the image.
Visual style: white background, black-and-white hand-drawn line art, pencil sketch texture, grayscale shadows, teaching handbook style, medium-gray #6B6B6B page-number block, thin light-gray #D9D9D9 takeaway border, black structural frames, small #FF5A00 orange accents only for <specific use>.
Typography: every visible character must visually resemble Microsoft JhengHei; clean Traditional Chinese sans-serif, upright strokes, high legibility, no calligraphy, no serif, and no English placeholder text.
Header consistency: use one approved section label only; keep page marker size, label position, label font size and weight, spacing, baseline, and short orange underline identical across all slides.
Layout role: <SOIL page role>; structure: <SOIL visual structure>.
Composition: <one concise description tied to the teaching relationship>.
Text must be Traditional Chinese and legible:
Page number:「<NN>」
Section label:「<label>」
Title:「<title>」
Labels:「...」
Bottom reminder:「<takeaway>」
Constraints: exact Traditional Chinese text, large readable text, no extra text, no watermark, no logo, no photorealistic style, no colorful illustration, orange under 10%, no black page-number block, no dark takeaway border, no inconsistent header geometry.
```

## Avoid

- Photos.
- Dark backgrounds.
- Gradient or decorative backgrounds.
- Generic business templates.
- Dense card grids.
- Tiny labels.
- Full prose pages.
- Random icons that do not teach the relationship.
- English titles unless the user explicitly requests English.
- Large orange fills or multi-color palettes.
