---
name: python-pptx-deck-building
description: "Programmatically design premium PPTX slide decks using python-pptx when available."
license: MIT
platforms: [linux, macos, windows]
---

# python-pptx Slide Deck Generation

## Trigger Guidance
Use this skill whenever `python-pptx` is verified as installed in the active environment during a slide creation task. Writing layout scripts in pure Python via `python-pptx` offers high programmatic control, robust table creation, slide master/layout leverage, and complete safety from XML parsing corruptions.

---

## Architecture of a Premium Slide (16:9 widescreen)

Default widescreen parameters in `python-pptx` are configured as:
- **Slide Width**: 13.333" (`Inches(13.333)`)
- **Slide Height**: 7.5" (`Inches(7.5)`)
- **Standard Margins**: 0.8" left/right margin limits (width is 11.7" for visual elements).

---

## Quick-Start Template Structure

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Theme configuration
    FONT_HEAD = "Georgia"
    FONT_BODY = "Calibri"
    COLOR_BG_DARK = RGBColor(15, 23, 42)
    COLOR_BG_LIGHT = RGBColor(248, 250, 252)
    
    blank_layout = prs.slide_layouts[6]
    
    # Add a blank slide
    slide = prs.slides.add_slide(blank_layout)
    
    # Establish Background
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = COLOR_BG_LIGHT
```

---

## Design Design Patterns

### 1. Visual Card Containers (Side-by-Side Comparison)
Create distinct visual groups ("cards") using rounded rectangles or outlined rectangles paired with solid accent borders on the left or top. This avoids plain black bullet lines.

```python
# Card background box
card_left = Inches(0.8)
card_top = Inches(1.8)
card_width = Inches(5.5)
card_height = Inches(4.8)

card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_left, card_top, card_width, card_height)
card.fill.solid()
card.fill.fore_color.rgb = RGBColor(255, 255, 255) # Clear White
card.line.color.rgb = RGBColor(226, 232, 240)    # Soft Slate boundary

# 0.1"-wide Top/Left Accent Bar
accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, card_left, card_top, Inches(0.1), card_height)
accent.fill.solid()
accent.fill.fore_color.rgb = RGBColor(14, 165, 233) # Accent Cyan
accent.line.fill.background()
```

### 2. Stat Cards (Big Number + Label)

For data-heavy slides, use individual card shapes with a large number and smaller label. Place them in a grid row.

```python
def add_stat_card(slide, left, top, width, height, number, label, num_color=RGBColor(225, 6, 0)):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(30, 41, 59)
    card.line.fill.background()
    tb_num = slide.shapes.add_textbox(left, top, width, Inches(1.0))
    tb_num.word_wrap = True
    p = tb_num.text_frame.paragraphs[0]
    p.text = str(number)
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = num_color
    p.alignment = PP_ALIGN.CENTER
    tb_lbl = slide.shapes.add_textbox(left, top + Inches(0.9), width, Inches(0.5))
    tb_lbl.word_wrap = True
    p = tb_lbl.text_frame.paragraphs[0]
    p.text = label
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(203, 213, 225)
    p.alignment = PP_ALIGN.CENTER
```

### 3. Image Embedding

Add images while maintaining aspect ratio. Use `add_picture` with width or height (not both) to auto-scale.

```python
def add_image_safe(slide, path, left, top, width=None, height=None):
    if not os.path.exists(path):
        return None
    if width and height:
        return slide.shapes.add_picture(path, left, top, width, height)
    elif width:
        return slide.shapes.add_picture(path, left, top, width=width)
    elif height:
        return slide.shapes.add_picture(path, left, top, height=height)
    return slide.shapes.add_picture(path, left, top)
```

### 4. Accent Bar (Thin Colored Stripe)

Use RECTANGLE shapes as thin border accents (top/bottom of slide, left edge of cards).

```python
def add_accent_bar(slide, left, top, width, height, color=RGBColor(225, 6, 0)):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()
    return bar
```

### 5. Rich Multi-Line Text Box

One text box with multiple styled paragraphs instead of stacking separate boxes.

```python
def add_rich_textbox(slide, left, top, width, height, lines):
    """lines = list of (text, font_size, bold, color, align) tuples"""
    tb = slide.shapes.add_textbox(left, top, width, height)
    tb.word_wrap = True
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    for i, (text, size, bold, color, align) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.alignment = align
        p.space_after = Pt(4)
    return tb
```

### 7. Image Download with Fallback

When embedding web images, download them locally first, then embed. Use `requests` with a `User-Agent` header to avoid 403s. Cache downloads so re-runs reuse already-downloaded files.

**CRITICAL: Image format.** python-pptx only supports BMP, GIF, JPEG, PNG, TIFF, and WMF. Many web sources serve WEBP (Wikimedia, modern CDNs). Always use Pillow to decode and save as JPEG — this handles WEBP-to-JPEG conversion transparently.

```python
import os, requests
from io import BytesIO
from PIL import Image as PILImage
from pathlib import Path

IMG_DIR = Path("ppt_images")
IMG_DIR.mkdir(exist_ok=True)

def download_image(url, filename):
    """Download + convert any format to JPEG for python-pptx compatibility."""
    filepath = IMG_DIR / filename
    if filepath.exists():
        return str(filepath)
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/jpeg,image/png,image/*,*/*;q=0.8"
        })
        if resp.status_code == 200:
            buf = BytesIO(resp.content)
            img = PILImage.open(buf)
            img = img.convert("RGB")  # strips RGBA/Palette modes
            img.save(filepath, "JPEG", quality=90)
            return str(filepath)
        return None
    except Exception:
        return None
```

**Sourcing reliable image URLs** — Unsplash photo IDs change and Wikimedia often returns WEBP. Use Serper API (`/images` endpoint) to search Google Images and get verified URLs from known archives (Britannica, Incredible India, Wikimedia JPEG variants, official tourism sites):

```bash
SERPER_API_KEY="..." python ./scripts/search.py images \
  "Red Fort Delhi high quality photo" --gl in --num 5
# Pick URLs from the response — prefer Britannica, Unsplash,
# Incredible India (scene7.com), or booking.com for hotels
```

Preferred image sources (JPEG, reliable):
| Source | URL pattern | Reliability |
|--------|------------|-------------|
| Unsplash | `images.unsplash.com/photo-...?fm=jpg&q=80&w=1600` | High (use `fm=jpg` query param) |
| Britannica | `cdn.britannica.com/.../...jpg` | Very high |
| Incredible India | `s7ap1.scene7.com/is/image/incredibleindia/...` | Very high |
| Wikimedia JPEG | `upload.wikimedia.org/wikipedia/commons/...` | Good (but may serve WEBP — Pillow handles it) |
| Tripadvisor | `dynamic-media-cdn.tripadvisor.com/media/photo-o/...` | Good |
| Official tourism | `*.incredibleindia.org`, `akshardham.com` | Very high |

```python
# Usage pattern
IMAGES = {
    "red_fort": "https://images.unsplash.com/photo-XXXX?fm=jpg&q=80&w=1600",
    "hotel": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/XXXX.jpg",
}
img_paths = {}
for key, url in IMAGES.items():
    img_paths[key] = download_image(url, f"{key}.jpg")
```

**Key design decisions:**
- Always use Pillow for download — handles WEBP, AVIF, and palette-mode images transparently
- Prefer `fm=jpg` param on Unsplash URLs to force JPEG
- Cache in `ppt_images/` folder — deleting it forces clean re-download
- Accept header hints servers to return JPEG over WEBP when available

### 8. Multi-Day Itinerary Slide Factory

For repetitive day-by-day content (travel plans, course schedules, sprint plans), use a factory function that takes a structured tuple and produces consistent slides:

```python
def slide_day(prs, day, title, activities, meals, notes, accent_color, img_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # ... consistent layout with accent bar, card layout, image on right
    return slide

# Data as tuples
days = [
    (1, "Day Title", ["Activity 1", "Activity 2"], ["Meal tip"], ["Note"], COLOR_ACCENT),
    ...
]
for d in days:
    slide_day(prs, *d, img_path=img_paths.get("some_key"))
```

**Pattern benefits:**
- One layout change propagates across all days
- Each day is a data tuple — easy to reorder or edit
- Consistent visual rhythm across slides

### 9. Full-Width Comparison Tables
Widescreen designs benefit heavily from clean, multi-column tables. Space them to utilize the full 11.7" layout frame.

```python
table_shape = slide.shapes.add_table(number_of_rows, 4, Inches(0.8), Inches(1.8), Inches(11.7), Inches(5.0))
table = table_shape.table

# Set Column Widths Programmatically to fill the table bounds perfectly
table.columns[0].width = Inches(1.5)
table.columns[1].width = Inches(3.4)
table.columns[2].width = Inches(3.4)
table.columns[3].width = Inches(3.4)
```

To update programmatic styles (stripping or background changes), iterate and cell-edit:
```python
def style_cell(cell, text, bg_rgb, font_size, is_bold=False, is_italic=False, text_rgb=RGBColor(15,23,42), align=PP_ALIGN.LEFT):
    cell.fill.solid()
    cell.fill.fore_color.rgb = bg_rgb
    cell.text_frame.text = "" # Clear default
    p = cell.text_frame.paragraphs[0]
    p.alignment = align
    p.text = text
    p.font.name = "Calibri"
    p.font.size = Pt(font_size)
    p.font.bold = is_bold
    p.font.italic = is_italic
    p.font.color.rgb = text_rgb
```

---

## Common Pitfalls

1. **Text Overflow in Small Cards**: Text frames nested inside shapes don't auto-wrap accurately. Always define a dedicated text box (`add_textbox`) slightly offset within your visual bounds, and set `word_wrap = True`.
2. **Ignoring Margins**: Never stretch main text blocks or comparison layouts closer than `0.5"` to the screen rim. Keep header titles consistently aligned at `X = Inches(0.8)`.
3. **Low Color Contrast**: When writing dark text on light cards, ensure boundaries or highlights are visually clear. If utilizing a dark theme slides sandwich, use high-contrast text shades like pure white `RGBColor(255, 255, 255)` or light pastel color tones.
4. **MSO_SHAPE.ROUNDED_RECTANGLE is preferred over plain RECTANGLE** for card backgrounds — it looks more polished. Just call `add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, ...)`. Avoid manipulating the XML `prstGeom` element with `qn()` — lxml namespace lookups (`nsmap.get('a', None)`) can return None and cause a TypeError on some shape elements.
5. **Import `MSO_ANCHOR` from `pptx.enum.text`** when using `anchor` parameter on text frames. Missing it is a common NameError.
6. **`add_picture` with both width and height** can distort images. Pass only width or only height to let python-pptx auto-scale the other dimension proportionally.
7. **Table row index off-by-one**: A table with `N+1` rows (1 header + N data) has valid indices 0 through N. A total row is at index `N`, not `N+1`. Using `len(items)` as the total row index is correct; `len(items)+1` is out of range.
8. **Web image URLs go 404**: Unsplash photo IDs change over time. Always use `download_image()` with a cache-and-fallback pattern. Never assume a URL will resolve at runtime. Check `os.path.exists()` before `add_picture`. Use `add_image_safe()` that returns `None` on failure rather than crashing the whole deck.
9. **WEBP format unsupported by python-pptx**: Many sites (Wikimedia, Oberoi, Unsplash with `fm=webp`) serve WEBP images. `python-pptx` cannot embed WEBP. Always route downloads through Pillow: `PILImage.open(BytesIO(resp.content)).convert("RGB").save(path, "JPEG")`. This handles WEBP, AVIF, palette-mode, and RGBA transparently.
10. **Tuple unpacking in row data**: When iterating data rows for multi-column tables, match the tuple length exactly to the columns. A 4-column table needs 4-item tuples. If you later add a column, don't forget to update the unpack — Python won't warn you, it'll just crash at runtime. Prefer named tuples or dicts for complex rows.
