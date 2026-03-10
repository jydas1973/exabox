# PPTX Generator Skill

Generate professional, on-brand presentations and LinkedIn carousels using `python-pptx`. The skill produces `.pptx` files compatible with PowerPoint, Google Slides, and Keynote.

---

## Prerequisites

- [`uv`](https://docs.astral.sh/uv/) must be installed (the skill runs python-pptx via `uv run`)
- No manual Python setup needed — `uv` handles dependencies automatically

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## How the Brand System Works

The skill is **brand-driven**. All styling (colors, fonts, assets) lives in a brand config folder:

```
skills/pptx-generator/brands/{brand-name}/
  brand.json          ← Colors (hex) and fonts
  config.json         ← Output directory and generation settings
  brand-system.md     ← Visual design principles
  tone-of-voice.md    ← Writing style and vocabulary
  assets/             ← Logo, icons
```

**Existing brands:**

| Brand | Description | Output Directory |
|-------|-------------|-----------------|
| `dynamous` | Dark aesthetic, AI education content | `Dynamous/Content-Ideation/Presentations` |

To see all brands:
```
Glob: .claude/skills/pptx-generator/brands/*/brand.json
```

---

## Use Cases

### Use Case 1 — Generate slides from an existing brand

Use this when a brand is already configured.

**Sample prompt:**
```
Generate a 15-slide presentation for brand "dynamous" about the topic of
AI Agents in Enterprise. Use the content from /path/to/content.md as the
source material. Save the output to the default output directory.
```

---

### Use Case 2 — Extract style from a sample PPTX and generate new slides

Use this when you want Claude to extract colors/fonts from an existing presentation
and create a new brand, then generate slides in that style from a content file.

#### Step 1 — Create a brand from your sample PPTX

```
I have a sample PPTX at /path/to/sample.pptx.

Please:
1. Read it using python-pptx and extract:
   - Background color and alternate background color
   - Primary text color and secondary text color
   - Accent / highlight colors (up to 3)
   - Heading font and body font
   - Any recurring visual style or design patterns
2. Create a new brand called "my-brand" in:
   .claude/skills/pptx-generator/brands/my-brand/
   with brand.json, config.json, brand-system.md, and tone-of-voice.md
   populated from the values you extracted.
3. Set the output directory in config.json to: output/my-brand
```

#### Step 2 — Generate the new PPTX from a content file

```
Generate a 15-slide presentation for brand "my-brand" using the content
in /path/to/content.md.

Structure the deck as:
- 1 title slide
- 2–3 section breaks
- Body slides using the most visual layouts (cards, stats, columns)
- 1 closing slide

Save the output to output/my-brand/.
```

#### Combined prompt (one shot)

```
I want to generate a new PPTX presentation.

Style source:  /path/to/sample.pptx
  → Read this file with python-pptx, extract the color palette and fonts,
    and create a new brand called "my-brand" in:
    .claude/skills/pptx-generator/brands/my-brand/
    (brand.json, config.json, brand-system.md, tone-of-voice.md)

Content source: /path/to/content.md
  → Read this file and use it as the source material for all slide content.

Then generate a 15-slide presentation for brand "my-brand" using that content.
Output directory: output/my-brand/
```

---

### Use Case 3 — Generate a LinkedIn Carousel

Carousels are square (1:1) multi-page PDFs for LinkedIn. They are 5–10 slides, mobile-readable.

**Sample prompt:**
```
Create a LinkedIn carousel for brand "dynamous" about the topic:
"5 mistakes engineers make when adopting AI agents"

Structure: hook slide → 5 numbered-point slides → CTA slide
Export as PDF to output/dynamous/
```

---

### Use Case 4 — Edit an existing PPTX

**Sample prompt:**
```
Edit the existing PPTX at /path/to/existing.pptx:
- Update the title on slide 1 to "New Title"
- Replace the bullet points on slide 3 with the content below:
  [your new content]
- Change the accent color throughout to #3B82F6

Save the modified file to output/my-brand/updated.pptx
  (do not overwrite the original)
```

---

### Use Case 5 — Add or update a layout template (cookbook)

**Sample prompt:**
```
Create a new cookbook layout called "timeline-slide" that shows 4–6 events
on a horizontal timeline. Add it to:
  .claude/skills/pptx-generator/cookbook/timeline-slide.py

Include full frontmatter (purpose, best_for, avoid_when, max_items, instructions)
and generate a test slide using the "dynamous" brand to verify it renders correctly.
```

---

## Available Layouts

### Presentation layouts (16:9)

| Layout file | Best for |
|-------------|----------|
| `title-slide` | Opening slide |
| `section-break-slide` | Dividers between sections |
| `closing-slide` | Final CTA / thank you |
| `content-slide` | Linear text / bullets (use sparingly — last resort) |
| `multi-card-slide` | 3–5 equal features, steps, or items |
| `floating-cards-slide` | Exactly 3 featured concepts with depth |
| `two-column-slide` | Side-by-side comparisons |
| `stats-slide` | 2–4 big metrics or KPIs |
| `circular-hero-slide` | Central concept with surrounding items |
| `giant-focus-slide` | 1–3 words of dramatic emphasis |
| `bold-diagonal-slide` | High-energy, urgent, or warning content |
| `quote-slide` | Powerful quote with attribution |
| `chart-slide` | Data visualisation (pie, bar, line, doughnut) |
| `code-slide` | Code snippets with syntax-style formatting |
| `image-caption-slide` | Screenshot or photo with caption |
| `corner-anchor-slide` | Content anchored to a corner with bold accent |

### Carousel layouts (1:1 square, LinkedIn)

| Layout file | Best for |
|-------------|----------|
| `hook-slide` | First slide — scroll stopper |
| `single-point-slide` | One key insight with explanation |
| `numbered-point-slide` | Listicle items with a big number |
| `quote-slide` | Social proof or key insight |
| `cta-slide` | Last slide — call to action |

To preview all presentation layouts at once:
```bash
uv run .claude/skills/pptx-generator/generate-cookbook-preview.py
# Opens: cookbook-preview.pptx
```

---

## Brand File Reference

### `brand.json` — Colors and fonts

```json
{
  "name": "Brand Name",
  "colors": {
    "background":         "07090F",
    "background_alt":     "080A13",
    "text":               "FAFAFA",
    "text_secondary":     "CCCCCC",
    "accent":             "3B82F6",
    "accent_secondary":   "60A5FA",
    "accent_tertiary":    "0EA5E9",
    "code_bg":            "0A0C12",
    "card_bg":            "0D1117",
    "card_bg_alt":        "161B22"
  },
  "fonts": {
    "heading": "Inter",
    "body":    "Inter",
    "code":    "JetBrains Mono"
  },
  "assets": {
    "logo": "assets/logo.png"
  }
}
```

> All color values are hex **without** the `#` prefix.

### `config.json` — Output settings

```json
{
  "output": {
    "directory":  "output/my-brand",
    "naming":     "{name}-{date}",
    "keep_parts": false
  },
  "generation": {
    "slides_per_batch": 5,
    "auto_combine":     true,
    "open_after_generate": false
  },
  "defaults": {
    "slide_width_inches":  13.333,
    "slide_height_inches": 7.5
  }
}
```

---

## How Generation Works

1. **Brand discovery** — reads `brand.json`, `config.json`, and markdown files
2. **Layout discovery** — reads frontmatter from all `cookbook/*.py` files
3. **Slide planning** — creates a plan table (layout, title, content) before generating
4. **Batch generation** — generates max 5 slides per batch, validates each batch
5. **Combine** — merges all part files into one final PPTX
6. **Clean up** — deletes part files (only final file remains)

### Output naming

| Config value | Resolves to |
|---|---|
| `{name}` | Presentation name from your prompt |
| `{brand}` | Brand folder name |
| `{date}` | Current date (YYYY-MM-DD) |

Final file: `output/{brand}/{name}-final.pptx`

---

## Tips

- **Be specific about slide count** — "15 slides" gets better results than "a presentation"
- **Mention structure** — tell Claude if you want section breaks, an intro, a closing slide, etc.
- **Content files** — markdown, plain text, and structured notes all work well as input
- **Variety** — the skill enforces visual layout variety (content-slide capped at 25% of slides)
- **Carousels** — always specify the topic and desired CTA so the last slide is purposeful
- **Logo** — place your logo PNG at `brands/{brand-name}/assets/logo.png` before generating
