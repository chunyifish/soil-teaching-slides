# NotebookLM Slide Deck Reference

Use this reference only for Mode C. NotebookLM produces a fast visual draft; it does not replace Mode A when exact wording or one-prompt-per-slide control is required.

## Mode Boundary

- Modes A and C share the old `黑白手繪教學圖解風` v2.1 visual system.
- Read `soil-handdrawn-style-v2.yaml` and `handdrawn-soil-style.md` before generating.
- Keep A/C page furniture: white background, black-and-white hand-drawn line art, sparse orange accents, medium-gray `#6B6B6B` page-number block, one consistently styled approved section label, Microsoft-JhengHei-like Traditional Chinese typography, framed teaching structure, and bottom takeaway bar with a thin light-gray `#D9D9D9` border.
- Never import Mode B's 32 pt title, one-line large-text layout, bottom-right metadata, or no-fixed-footer rule.

## Current Tool Sequence

Use the NotebookLM MCP tools in this order:

1. `notebook_create`: create a clean notebook for a serious deck attempt.
2. `source_add`: add one consolidated text source with `source_type: text` and wait for processing.
3. `studio_create`: create `artifact_type: slide_deck` with conservative parameters.
4. `studio_status`: poll until the artifact is completed or failed.
5. `download_artifact`: download `slide_deck_format: pptx`; also download `pdf` when available.
6. `studio_revise`: revise isolated slide defects only; it creates a new artifact, so poll and download again.

If authentication fails, run `nlm login`. Do not claim generation succeeded from a notebook URL or a queued status.

## Consolidated Source Contract

Create one source containing all of the following:

- Confirmed slide count and page order
- Exact Traditional Chinese title for every slide
- One teaching point and learner task per slide
- SOIL page role and visual structure per slide
- Required short labels and exact bottom takeaway per slide
- Full contents of `soil-handdrawn-style-v2.yaml`
- Explicit instruction to use Taiwan Traditional Chinese throughout
- Explicit instruction to keep white or near-white backgrounds
- Explicit instruction to use the shared old A/C page furniture
- Explicit instruction to use exactly one approved section label per slide and keep its position, size, weight, spacing, baseline, and orange underline consistent across the deck
- Explicit instruction that every visible character, including illustration labels, must resemble Microsoft JhengHei
- Explicit prohibition on black or near-black page-number blocks, dark takeaway borders, English page furniture, English placeholder text, beige paper textures, dark backgrounds, gradients, and Mode B styling

Use one clean consolidated source because conflicting source history causes language and style drift. Do not stack multiple corrective sources in a contaminated notebook.

## Studio Parameters

Start conservatively:

```yaml
artifact_type: slide_deck
slide_format: detailed_deck
slide_length: default
```

Put hard language, page-count, and visual constraints in the source. Add `custom_prompt`, `language`, or `visual_style` only when needed and supported by the active tool schema.

## Quality Control

After download:

- Confirm the PPTX exists and is non-empty.
- Confirm slide count against the approved plan.
- Inspect media count; NotebookLM decks are commonly image/media-based.
- Render slides or extract media and create a contact sheet.
- Check Taiwan Traditional Chinese, Microsoft-JhengHei-like typography throughout, title fidelity, pure white background, black-and-white line art, sparse orange emphasis, medium-gray page-number blocks, consistent single section labels, and bottom takeaway bars with light-gray borders.
- Download PDF too when available for easy review.
- Report any paraphrasing, renamed titles, missing takeaways, unexpected slide count, or style drift.

Use `studio_revise` when only a few slides fail. When the whole deck drifts into English, beige backgrounds, or a different visual system, create a clean notebook and regenerate from one corrected consolidated source.

## Known Limits

- NotebookLM may paraphrase approved wording or rename the artifact.
- It may change the requested slide count.
- It may satisfy the language constraint while drifting visually, or satisfy the visual constraint while drifting into English.
- Output is generally not a fully editable native-object PowerPoint deck.
- Mode C is therefore a reviewable visual draft, not an exact-fidelity final deck.
