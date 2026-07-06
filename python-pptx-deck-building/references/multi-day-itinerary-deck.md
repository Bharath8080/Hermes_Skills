# Multi-Day Itinerary PPT — Reference Implementation

## Scope
This reference captures the approach used to build a 20-slide New Delhi travel plan deck (July 2026). The same pattern adapts to any multi-day itinerary, schedule, or agenda presentation.

## Deck Architecture

| Layer | Count | Purpose |
|-------|-------|---------|
| Splash slides | 1 | Title |
| Summary slides | 3 | Overview, Flight, Hotels |
| Content slides | 10 | Day-by-day itinerary (Days 1-10) |
| Thematic slides | 4 | Places, Food, Budget, Tips |
| Closing | 1 | Thank You |

## Slide Layout Pattern

```
┌─────────────────────────────────────────────────────┐
│  Accent bar (6px, colored per topic)                │
│  DAY 1  (small, accent color)                       │
│  Title (large, white)                               │
│  ── thin accent underline ──                        │
│  ┌─────────────────────┐  ┌──────────────────────┐  │
│  │ ITINERARY            │  │  [IMAGE]             │  │
│  │ ▸ Activity 1         │  │                      │  │
│  │ ▸ Activity 2         │  │  (right side,        │  │
│  │ ▸ Activity 3         │  │   4"×5.3"            │  │
│  ├─────────────────────┤  │                      │  │
│  │ MEALS & NOTES        │  │                      │  │
│  │ 🍽 Meal suggestion   │  │                      │  │
│  │ 💡 Pro tip           │  │                      │  │
│  └─────────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Color Theme

| Role | RGB | Used For |
|------|-----|----------|
| Background | (15, 23, 42) | Slide base |
| Card BG | (30, 41, 59) | Content cards |
| Card border | (51, 65, 85) | Card outlines |
| Accent 1 | (234, 179, 8) | Gold — hotels, food |
| Accent 2 | (14, 165, 233) | Sky — flights, transport |
| Accent 3 | (239, 68, 68) | Red — day trips, warnings |
| Accent 4 | (34, 197, 94) | Green — budget, meals |
| Body text | (203, 213, 225) | Light gray on dark |
| Muted text | (148, 163, 184) | Notes, secondary info |

## Data Flow

```python
# 1. Define images as URL dict
IMAGES = {"key": "https://unsplash.com/photo-XXXX?w=1600&q=80"}

# 2. Download all (cached), some may be None
img_paths = download_all_images()

# 3. Define day data as tuples
days = [
    (1, "Title", ["Activity 1", "Activity 2"], ["Meal"], ["Note"], COLOR_ACCENT),
    ...
]

# 4. Build slides via factory function
for d in days:
    slide_itinerary_day(prs, *d, img_path=img_paths.get("key"))

# 5. Add thematic slides, save
prs.save("output.pptx")
```

## Image Download Strategy

- **Source**: Unsplash direct URLs with `?w=1600&q=80` for quality
- **Cache**: `ppt_images/` folder — existing files are reused
- **Failure**: Returns `None`; `add_image_safe()` checks `os.path.exists()` before insertion
- **Cleanup**: Delete `ppt_images/` to force re-download

## Tables — Indexing Rule

For a table with `N+1` rows (1 header + N data items):
- `table.cell(0, j)` — header row
- `table.cell(i, j)` for `i in range(1, N+1)` — data rows
- **Total row** at index `N` (NOT `N+1`)

```python
n = len(items)
table = slide.shapes.add_table(n + 1, cols, ...)  # +1 for header
# data rows at 1..N
# total row at index N
style_cell(table.cell(n, 0), "TOTAL", ...)  # correct
```

## Verification

After generation, validate with:
```python
from pptx import Presentation
prs = Presentation("file.pptx")
print(f"Slides: {len(prs.slides)}")
imgs = sum(1 for s in prs.slides for sh in s.shapes if sh.shape_type == 13)
print(f"Images: {imgs}")
```

## Real Example
Full code at `C:\Users\homeu\golang\create_delhi_trip_ppt.py` — 20-slide New Delhi 10-day travel plan with 13 embedded images, 3 hotel cards, budget table, food guide, and tips section.