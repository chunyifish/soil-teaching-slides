import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


EMU_PER_IN = 914400
SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
OUT_W = 1600
OUT_H = 900
SX = OUT_W / (SLIDE_W_IN * EMU_PER_IN)
SY = OUT_H / (SLIDE_H_IN * EMU_PER_IN)

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def px(v, axis="x"):
    return int(round(int(v) * (SX if axis == "x" else SY)))


def color_from_hex(value, default=(17, 17, 17)):
    if not value:
        return default
    value = value.strip("#")
    if len(value) != 6:
        return default
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def find_font():
    candidates = [
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\msjhbd.ttc",
        r"C:\Windows\Fonts\mingliu.ttc",
        r"C:\Windows\Fonts\arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


FONT_PATH = find_font()


def get_font(pt, bold=False):
    size = max(8, int(round(pt * OUT_H / 720)))
    if FONT_PATH:
        try:
            return ImageFont.truetype(FONT_PATH, size=size, index=0)
        except Exception:
            pass
    return ImageFont.load_default()


def line_color(sppr):
    ln = sppr.find("a:ln", NS)
    if ln is None:
        return None, 0
    nofill = ln.find("a:noFill", NS)
    if nofill is not None:
        return None, 0
    srgb = ln.find(".//a:srgbClr", NS)
    w = int(ln.attrib.get("w", "12700"))
    return color_from_hex(srgb.attrib.get("val") if srgb is not None else None, (130, 130, 130)), max(1, int(w / 12700 * 2))


def fill_color(sppr):
    nofill = sppr.find("a:noFill", NS)
    if nofill is not None:
        return None
    srgb = sppr.find(".//a:solidFill/a:srgbClr", NS)
    if srgb is None:
        return None
    return color_from_hex(srgb.attrib.get("val"), (255, 255, 255))


def shape_type(sppr):
    geom = sppr.find("a:prstGeom", NS)
    return geom.attrib.get("prst", "rect") if geom is not None else "rect"


def xfrm_rect(sppr):
    xfrm = sppr.find("a:xfrm", NS)
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    return (
        px(off.attrib["x"], "x"),
        px(off.attrib["y"], "y"),
        px(int(off.attrib["x"]) + int(ext.attrib["cx"]), "x"),
        px(int(off.attrib["y"]) + int(ext.attrib["cy"]), "y"),
    )


def collect_runs(sp):
    runs = []
    for p in sp.findall(".//a:p", NS):
        text = "".join(t.text or "" for t in p.findall(".//a:t", NS)).strip()
        if not text:
            continue
        rpr = p.find(".//a:rPr", NS)
        pt = 16
        bold = False
        color = (17, 17, 17)
        if rpr is not None:
            if "sz" in rpr.attrib:
                pt = int(rpr.attrib["sz"]) / 100
            bold = rpr.attrib.get("b") == "1"
            srgb = rpr.find(".//a:srgbClr", NS)
            if srgb is not None:
                color = color_from_hex(srgb.attrib.get("val"), color)
        ppr = p.find("a:pPr", NS)
        align = ppr.attrib.get("algn", "ctr") if ppr is not None else "ctr"
        runs.append((text, pt, bold, color, align))
    return runs


def draw_centered_text(draw, box, runs):
    if not runs:
        return
    x1, y1, x2, y2 = box
    line_heights = []
    prepared = []
    for text, pt, bold, color, align in runs:
        font = get_font(pt, bold)
        bbox = draw.textbbox((0, 0), text, font=font)
        h = bbox[3] - bbox[1]
        w = bbox[2] - bbox[0]
        line_heights.append(h + 4)
        prepared.append((text, font, color, align, w, h))
    total_h = sum(line_heights)
    y = y1 + (y2 - y1 - total_h) / 2
    for idx, (text, font, color, align, w, h) in enumerate(prepared):
        if align == "l":
            x = x1 + 12
        elif align == "r":
            x = x2 - w - 12
        else:
            x = x1 + (x2 - x1 - w) / 2
        draw.text((x, y), text, font=font, fill=color)
        y += line_heights[idx]


def draw_shape(draw, sp):
    sppr = sp.find("p:spPr", NS)
    if sppr is None:
        return
    box = xfrm_rect(sppr)
    fill = fill_color(sppr)
    outline, width = line_color(sppr)
    typ = shape_type(sppr)
    if typ == "ellipse":
        if fill:
            draw.ellipse(box, fill=fill)
        if outline and width:
            draw.ellipse(box, outline=outline, width=width)
    elif typ == "roundRect":
        radius = max(8, int((box[3] - box[1]) * 0.18))
        if fill:
            draw.rounded_rectangle(box, radius=radius, fill=fill)
        if outline and width:
            draw.rounded_rectangle(box, radius=radius, outline=outline, width=width)
    else:
        if fill:
            draw.rectangle(box, fill=fill)
        if outline and width:
            draw.rectangle(box, outline=outline, width=width)
    draw_centered_text(draw, box, collect_runs(sp))


def draw_line(draw, cxn):
    sppr = cxn.find("p:spPr", NS)
    if sppr is None:
        return
    box = xfrm_rect(sppr)
    color, width = line_color(sppr)
    if not color:
        return
    x1, y1, x2, y2 = box
    xfrm = sppr.find("a:xfrm", NS)
    if xfrm is not None:
        if xfrm.attrib.get("flipH") == "1":
            x1, x2 = x2, x1
        if xfrm.attrib.get("flipV") == "1":
            y1, y2 = y2, y1
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    ln = sppr.find("a:ln", NS)
    if ln is not None and ln.find("a:headEnd", NS) is not None:
        angle = math.atan2(y2 - y1, x2 - x1)
        size = max(8, width * 5)
        pts = [
            (x2, y2),
            (x2 - size * math.cos(angle - 0.45), y2 - size * math.sin(angle - 0.45)),
            (x2 - size * math.cos(angle + 0.45), y2 - size * math.sin(angle + 0.45)),
        ]
        draw.polygon(pts, fill=color)


def slide_sort_key(name):
    m = re.search(r"slide(\d+)\.xml$", name)
    return int(m.group(1)) if m else 0


def render(pptx, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pptx) as z:
        slide_names = sorted(
            [n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=slide_sort_key,
        )
        for idx, name in enumerate(slide_names, 1):
            root = ET.fromstring(z.read(name))
            img = Image.new("RGB", (OUT_W, OUT_H), "white")
            draw = ImageDraw.Draw(img)
            tree = root.find(".//p:spTree", NS)
            for child in list(tree):
                if child.tag.endswith("}sp"):
                    draw_shape(draw, child)
                elif child.tag.endswith("}cxnSp"):
                    draw_line(draw, child)
            img.save(out_dir / f"slide-{idx:02d}.png")
    return len(slide_names)


if __name__ == "__main__":
    pptx = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    count = render(pptx, out_dir)
    print(f"rendered {count} slides to {out_dir}")
