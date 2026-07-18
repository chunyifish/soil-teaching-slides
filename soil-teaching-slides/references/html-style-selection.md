# Mode D Content-Driven Style Selection

Use an explicit user style as the source of truth. When no style is specified, select exactly one deck-level style family from the content. Do not mix or average families.

## Selection Order

Judge in this order:

1. Communication purpose
2. Learner task
3. Dominant information relationship
4. Presentation setting
5. Visual tone

Record the selected family and a one-sentence reason in the Phase 1 style brief.

## Style Families

### Narrative / Conviction

Choose for speeches, beliefs, reflective essays, stories, manifestos, and identity-oriented teaching.

- Large statements and generous whitespace
- Strong pacing between slides
- One visual metaphor or restrained shape system
- Minimal labels and restrained motion
- Avoid dense grids and dashboard styling

### Structured Teaching

Choose for concept explanation, knowledge organization, course instruction, procedures, and misconception correction.

- Clear frames, groups, hierarchy, comparisons, and processes
- Stable title and content zones
- One accent color for signaling
- Diagrams built with HTML/CSS/SVG
- Avoid decorative illustration that does not teach the relationship

### Workshop Facilitation

Choose for discussion, hands-on work, reflection prompts, group activities, and classroom practice.

- Prominent task instruction
- Clear sequence, time or material cues only when supplied
- Response frames, prompts, and action states
- High projection readability
- Avoid adding unrequested timers, scoring, or interaction logic

### Research / Evidence

Choose for reports, data, literature, findings, argumentation, and evidence comparison.

- Charts, tables, citations, and claims take priority
- Neutral palette and restrained decoration
- Visible units, labels, sources, and uncertainty
- Use native SVG or HTML where practical
- Avoid turning evidence into generic card grids

### Hand-Drawn Teaching

Choose when the user asks for a hand-drawn SOIL look or the content strongly benefits from concrete teaching metaphors.

- White background, black line language, gray texture, sparse accent color
- Editable HTML labels around local illustrations or inline SVG
- Use the A/C YAML only when the user explicitly asks D to match that old visual family
- Do not automatically inherit A/C page furniture or fixed takeaway bar

## Tie-Breaking

When two families seem plausible, choose the family that best supports the dominant learner task. Prefer the more restrained family when visual complexity would not improve understanding. Surface a genuine conflict instead of blending incompatible patterns.

## Style Brief Fields

Include:

- Family
- One-sentence rationale
- Background and palette direction
- Typography direction
- Motion level: none, subtle, or instructional
- Image policy: none, optional, or required
- Repeated page furniture, if any

