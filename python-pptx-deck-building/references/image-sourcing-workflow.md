# Image Sourcing for PPT Decks

## Serper Image Search Workflow

Use Serper API (`/images` endpoint) to find valid, JPEG-compatible image URLs instead of guessing Unsplash IDs.

```bash
export SERPER_API_KEY="<key>"
python ~/AppData/Local/hermes/skills/search/serper-web-search/scripts/search.py images \
  "Red Fort Delhi high quality photo" --gl in --num 5
```

### Response → Pick JPEG URLs

Parse the JSON: each result has `imageUrl`. Prefer URLs from these domains (proven JPEG-compatible):

| Domain | Notes |
|--------|-------|
| `images.unsplash.com/photo-...?fm=jpg` | Add `fm=jpg` to force JPEG |
| `cdn.britannica.com/.../*.jpg` | Always JPEG |
| `s7ap1.scene7.com/is/image/incredibleindia/...` | Incredible India tourism site |
| `upload.wikimedia.org/wikipedia/commons/...*.jpg` | May serve WEBP despite .jpg - Pillow handles it |
| `dynamic-media-cdn.tripadvisor.com/media/photo-o/...` | Tripadvisor media |
| `cf.bstatic.com/xdata/images/hotel/...*.jpg` | Booking.com hotel images |
| `akshardham.com/.../*.jpg` | Official temple site |
| `assets.cntraveller.in/...` | Condé Nast Traveller India |

### What to Avoid

- `media.istockphoto.com` — blocked by referrer on programmatic download
- `media.gettyimages.com` — often 400/403 without auth cookies
- `i.pinimg.com` — low resolution
- `*.alamy.com/*` — watermarked

## Reliable Keywords by Subject

| Subject | Query |
|---------|-------|
| Red Fort | `Red Fort Delhi India high quality photo` |
| India Gate | `India Gate New Delhi landmark photo` |
| Qutub Minar | `Qutub Minar Delhi tower monument` |
| Taj Mahal | `Taj Mahal Agra India high quality photo` |
| Humayun's Tomb | `Humayun Tomb Delhi India high quality photo` |
| Lotus Temple | `Lotus Temple New Delhi Bahai` |
| Akshardham | `Akshardham temple Delhi Swaminarayan` |
| Street food | `Delhi street food chaat golgappa` |
| Hauz Khas | `Hauz Khas Village Delhi India` |
| Luxury hotel | `luxury hotel Oberoi Delhi India` |

## Fallback Strategy

1. Serper → pick JPEG URLs from trusted domains
2. Test-download each with requests + Pillow
3. Any that fail → Serper with alternate query
4. Last resort: omit image from that slide (add_image_safe returns None, slide renders fine)