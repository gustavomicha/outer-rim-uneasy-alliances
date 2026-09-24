"""Extract cards from the Uneasy Alliances PDF and bundle them into a single playable HTML file.

Usage: python build/build.py   (needs pymupdf + pillow)
"""
import base64
import io
import json
import pathlib

import pymupdf
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF = ROOT / "Uneasy Alliances - Outer Rim Cooperative (V2.2.01).pdf"
RULEBOOK = ROOT / "sw07_outerrim_rulebook_v2-compressed.pdf"
FONTS = ROOT / "build" / "assets" / "fonts"
# (template, output): the rulebook-styled app, and the original dark version kept as a backup
# (template, output). build/app_classic.html holds the earlier dark theme; add it here to build it too.
TARGETS = [
    (ROOT / "build" / "app.html", ROOT / "index.html"),
]

CARD_DPI = 150
SHEET_DPI = 150
QUALITY = 72

# 3x3 card grid on every card page (points)
GX = [36, 216, 396, 576]
GY = [36, 276, 516, 756]

doc = pymupdf.open(PDF)


def pixmap(page_no, rect, dpi):
    pix = doc[page_no - 1].get_pixmap(dpi=dpi, clip=pymupdf.Rect(*rect))
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def encode(im):
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=QUALITY, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def render(page_no, rect, dpi):
    return encode(pixmap(page_no, rect, dpi))


def cell_rect(r, c, inset=1.0):
    return (GX[c] + inset, GY[r] + inset, GX[c + 1] - inset, GY[r + 1] - inset)


def cell(page_no, r, c):
    return render(page_no, cell_rect(r, c), CARD_DPI)


def jabba_crew_fix():
    """The Jabba half of this event card says "Resolve card #148" (Erskin Semaj), but the Gammorean
    it describes is Jubnuck, #143. Replace the printed 8 with a 3 glyph taken from another card."""
    im = pixmap(26, cell_rect(2, 1), CARD_DPI)
    src = pixmap(28, cell_rect(0, 2), CARD_DPI)  # "You may spend 3,000 credits..."
    x0, y0, x1, y1 = 248, 452, 265, 477  # box around the "8"
    for y in range(y0, y1 + 1):  # wipe the 8 with the background just to its right
        bg = im.getpixel((x1 + 6, y))
        for x in range(x0, x1 + 1):
            im.putpixel((x, y), bg)
    glyph = src.crop((172, 196, 182, 212)).convert("L")  # the "3" (stops before the comma)
    glyph = glyph.resize((10, 15), Image.LANCZOS)  # match the "Resolve card" type size
    lo, hi = glyph.getextrema()
    ink = Image.new("RGB", glyph.size, (15, 15, 15))
    # ignore the faint paper texture so only the digit itself is pasted
    alpha = glyph.point(lambda v: int(min(255, max(0, hi - v - 30) * 255 / max(1, (hi - lo - 30) * 0.8))))
    im.paste(ink, (248, 455), alpha)
    return encode(im)


images = {}

# ---------------------------------------------------------------- scenarios
SCEN = [
    # id, name, stars, A page, position(0=top,1=bottom)
    ("jabba", "Only Jabba Would Be So Bold", 2, 5, 0),
    ("valarian", "Settling a Score with a Hutt", 4, 5, 1),
    ("ryloth", "Strangling the Ryloth Rebellion", 1, 7, 0),
    ("lothal", "Stamping Out a Rebel Cell on Lothal", 2, 7, 1),
    ("hope", "The Rebellion's Shining Hope", 1, 9, 0),
    ("naboo", "A Consuming Light on Naboo", 3, 9, 1),
    ("sunrise", "A Red Sunrise on Ryloth", 4, 11, 0),
    ("crimson", "A Rising Star in Crimson Dawn", 3, 11, 1),
]
# numbered encounter cards for each scenario's 4 jobs, and the crew card its events reference
SCEN_NUMS = {
    "jabba": [101, 102, 103, 104, 143], "valarian": [105, 106, 107, 108, 144],
    "ryloth": [111, 112, 113, 114, 145], "lothal": [115, 116, 117, 118, 146],
    "hope": [121, 122, 123, 124, 148], "naboo": [125, 126, 127, 128, 147],
    "sunrise": [131, 132, 133, 134, 142], "crimson": [135, 136, 137, 138, 141],
}


def sheet_circles(page_no, pos):
    y0 = 0 if pos == 0 else 395
    out = []
    for dr in doc[page_no - 1].get_drawings():
        r = dr["rect"]
        kinds = "".join(it[0] for it in dr["items"])
        if kinds.count("c") >= 4 and 15 < r.width < 40 and abs(r.width - r.height) < 3:
            if y0 <= r.y0 < y0 + 395:
                out.append((r.x0, r.y0, r.width))
    out.sort(key=lambda t: (round(t[1] / 8), t[0]))
    return [
        {"x": round(x / 612 * 100, 3), "y": round((y - y0) / 395 * 100, 3), "w": round(w / 612 * 100, 3)}
        for x, y, w in out
    ]


scenarios = []
for sid, name, stars, page, pos in SCEN:
    rect = (0, 0 if pos == 0 else 395, 612, 395 if pos == 0 else 791)
    for side, pg in (("A", page), ("B", page + 1)):
        images[f"S-{sid}-{side}"] = render(pg, rect, SHEET_DPI)
    ca, cb = sheet_circles(page, pos), sheet_circles(page + 1, pos)
    print(f"{name}: circles A={len(ca)} B={len(cb)}")
    scenarios.append({"id": sid, "name": name, "stars": stars, "circlesA": ca, "circlesB": cb, "nums": SCEN_NUMS[sid]})

SHEETS = json.loads((ROOT / "build" / "scenarios.json").read_text())
for s in scenarios:
    sheet = SHEETS[s["id"]]
    a_slots = sum(2 if r["slots"] == "AB" else r["slots"] for r in sheet["A"]["rows"])
    assert a_slots == len(s["circlesA"]), (s["id"], a_slots, len(s["circlesA"]))
    assert len(s["circlesB"]) == 4, s["id"]
    s["sheet"] = sheet


def handshake_icon():
    """The black handshake from the co-op event card back, as a transparent PNG mask."""
    im = pixmap(13, cell_rect(0, 0), CARD_DPI * 2).convert("L")
    box = im.point(lambda v: 255 if v < 110 else 0).getbbox()
    glyph = im.crop(box)
    glyph = glyph.resize((glyph.width // 2, glyph.height // 2), Image.LANCZOS)
    mask = Image.new("LA", glyph.size, 0)
    mask.putalpha(glyph.point(lambda v: max(0, min(255, (200 - v) * 2))))
    buf = io.BytesIO()
    mask.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------- co-op event deck
images["BACK-event"] = cell(13, 0, 0)
events = []
for page in (14, 16, 18, 20, 22, 24):
    for r in range(3):
        for c in range(3):
            cid = f"E{len(events) + 1:02d}"
            images[cid] = cell(page, r, c)
            events.append({"id": cid, "kind": "event"})

T = {  # thematic cards: (top half scenario, bottom half scenario)
    26: [[("ryloth", "hope")] * 3, [("lothal", "jabba")] * 3,
         [("lothal", "jabba"), ("lothal", "jabba"), ("crimson", "naboo")]],
    28: [[("crimson", "naboo")] * 3, [("crimson", "naboo")] * 3, [("valarian", "sunrise")] * 3],
    30: [[("valarian", "sunrise")] * 3, [("valarian", "sunrise")] * 3],
}
for page, rows in T.items():
    for r, row in enumerate(rows):
        for c, (top, bottom) in enumerate(row):
            cid = f"E{len(events) + 1:02d}"
            images[cid] = jabba_crew_fix() if (page, r, c) == (26, 2, 1) else cell(page, r, c)
            events.append({"id": cid, "kind": "event", "top": top, "bottom": bottom})

for s in scenarios:
    n = sum(1 for e in events if s["id"] in (e.get("top"), e.get("bottom")))
    assert n == 2 * s["stars"] + 1, (s["name"], n)

# ---------------------------------------------------------------- numbered deck
N = {
    30: [None, None, [101, 102, 103]],
    32: [[106, 105, 104], [111, 108, 107], [114, 113, 112]],
    34: [[115, 116, 117], [118, 121, 122], [123, 124, 125]],
    36: [[136, 135, 134], [133, 132, 131], [128, 127, 126]],
    38: [[137, 138, 109], [110, 119, 120], [129, 130, 139]],
    40: [[None, None, 109], [110, 119, 120], [129, 130, 139]],
    42: [[140, 141, 142], [143, 144, 145], [146, 147, 148]],
    44: [[140, None, None], None, None],
}
numbered = []
for page, rows in N.items():
    for r, row in enumerate(rows):
        for c, num in enumerate(row or []):
            if num is None:
                continue
            copy = sum(1 for x in numbered if x["num"] == num)
            cid = f"N{num}{'ab'[copy]}"
            images[cid] = cell(page, r, c)
            numbered.append({"id": cid, "kind": "num", "num": num})
assert sorted({x["num"] for x in numbered}) == list(range(101, 149))

# ---------------------------------------------------------------- co-op job market
images["BACK-job"] = cell(43, 0, 0)
jobs = []
for r, c in [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:
    cid = f"J{len(jobs) + 1}"
    images[cid] = cell(44, r, c)
    jobs.append({"id": cid, "kind": "job"})

# ---------------------------------------------------------------- rulebook look: page frame + fonts
def rulebook_frame():
    """The metal page frame image behind page 2 of the Unfinished Business rulebook."""
    rb = pymupdf.open(RULEBOOK)
    info = max(rb[1].get_image_info(xrefs=True), key=lambda i: pymupdf.Rect(i["bbox"]).get_area())
    pix = pymupdf.Pixmap(rb, info["xref"])
    if pix.n - pix.alpha > 3:
        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=82, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


def favicon():
    """Tab icon: the four-pointed fame star over a starfield."""
    svg = (ROOT / "build" / "assets" / "favicon.svg").read_bytes()
    return "data:image/svg+xml;base64," + base64.b64encode(svg).decode()


def app_icon(size=180, ss=4):
    """The same icon as a PNG for 'add to home screen'. Drawn here rather than converted from the
    SVG, because the SVG converter drops gradients."""
    from PIL import ImageDraw, ImageOps

    n = size * ss
    space = ImageOps.colorize(Image.radial_gradient("L").resize((n, n)), (40, 64, 95), (7, 12, 22))
    corners = Image.new("L", (n, n), 0)
    ImageDraw.Draw(corners).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 0.2), fill=255)
    icon = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    icon.paste(space, (0, 0), corners)

    draw = ImageDraw.Draw(icon)
    for x, y, r, a in [(17, 20, 1.5, 230), (80, 16, 1.1, 180), (86, 45, 1.6, 215), (14, 62, 1.2, 165),
                       (30, 85, 1.5, 205), (70, 82, 1.1, 155), (52, 12, 1.0, 130)]:
        x, y, r = x / 100 * n, y / 100 * n, r / 100 * n
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(219, 231, 245, a))

    def bezier(p0, c0, c1, p1, steps=40):
        for i in range(steps):
            t = i / steps
            u = 1 - t
            yield tuple((u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d) / 100 * n
                        for a, b, c, d in zip(p0, c0, c1, p1))

    tips = [(50, 8), (92, 50), (50, 92), (8, 50)]
    ctrl = [((54.5, 37), (62, 45.5)), ((62, 54.5), (54.5, 63)), ((45.5, 63), (38, 54.5)), ((38, 45.5), (45.5, 37))]
    points = []
    for i, (c0, c1) in enumerate(ctrl):
        points += list(bezier(tips[i], c0, c1, tips[(i + 1) % 4]))

    gold = Image.new("RGBA", (n, n))
    gd = ImageDraw.Draw(gold)
    for y in range(n):  # top-to-bottom gold gradient
        t = y / n
        gd.line([(0, y), (n, y)], fill=(int(255 - 79 * t), int(234 - 107 * t), int(169 - 146 * t), 255))
    star = Image.new("L", (n, n), 0)
    ImageDraw.Draw(star).polygon(points, fill=255)
    icon.paste(gold, (0, 0), star)
    draw.line(points + [points[0]], fill=(109, 77, 10, 255), width=max(2, int(n * 0.014)), joint="curve")

    buf = io.BytesIO()
    icon.resize((size, size), Image.LANCZOS).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


FONT_FACES = [  # family, file, weight range, style
    ("Saira Condensed", "SairaCondensed-600.woff2", "600", "normal"),
    ("Saira Condensed", "SairaCondensed-700.woff2", "700", "normal"),
    ("Source Sans 3", "SourceSans3-var.woff2", "300 700", "normal"),
    ("Source Sans 3", "SourceSans3-400i.woff2", "400", "italic"),
    ("Montserrat", "Montserrat-var.woff2", "300 800", "normal"),
]


def font_css():
    out = []
    for family, file, weight, style in FONT_FACES:
        b64 = base64.b64encode((FONTS / file).read_bytes()).decode()
        out.append(f"@font-face {{ font-family: '{family}'; src: url(data:font/woff2;base64,{b64}) format('woff2'); "
                   f"font-weight: {weight}; font-style: {style}; font-display: block; }}")
    return "\n".join(out)


data = {"scenarios": scenarios, "events": events, "numbered": numbered, "jobs": jobs, "icons": {"handshake": handshake_icon()}}


def write_pwa_files(page_html):
    """A manifest, two icons and a service worker, so browsers offer to install the app and it
    keeps working offline. index.html on its own stays self-contained; these only add the install."""
    import hashlib
    for px in (192, 512):
        raw = base64.b64decode(app_icon(px, ss=2).split(",")[1])
        (ROOT / f"icon-{px}.png").write_bytes(raw)
    manifest = {
        "name": "Uneasy Alliances — Outer Rim Co-op",
        "short_name": "Uneasy Alliances",
        "description": "Playable version of the Uneasy Alliances fan-made cooperative expansion for Star Wars: Outer Rim.",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#101a2e",
        "theme_color": "#101a2e",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    (ROOT / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n")
    version = hashlib.sha256(page_html.encode()).hexdigest()[:12]
    sw = (ROOT / "build" / "assets" / "sw.js").read_text().replace("__CACHE__", f"uneasy-alliances-{version}")
    (ROOT / "sw.js").write_text(sw)
    print(f"-> manifest.webmanifest, sw.js (cache uneasy-alliances-{version}), icon-192.png, icon-512.png")
extras = {"/*__FONTS__*/": font_css(), "__FRAME__": rulebook_frame(),
          "__FAVICON__": favicon(), "__TOUCHICON__": app_icon()}
for template, out in TARGETS:
    html = template.read_text()
    html = html.replace("/*__DATA__*/null", json.dumps(data))
    html = html.replace("/*__IMAGES__*/null", json.dumps(images))
    for key, value in extras.items():
        html = html.replace(key, value)
    out.write_text(html)
    print(f"-> {out.name} {out.stat().st_size / 1e6:.1f} MB")
    if out.name == "index.html":
        write_pwa_files(html)
print(f"events={len(events)} numbered={len(numbered)} jobs={len(jobs)}")
