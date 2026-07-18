#!/usr/bin/env python3
"""Build a 16:9 PPTX from generated backgrounds plus editable text overlays.

The input JSON contains slides with a background image and editable text boxes.
Coordinates are in PowerPoint inches on a 13.333 x 7.5 widescreen slide.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


EMU_PER_INCH = 914400
SLIDE_W_IN = 13.333333
SLIDE_H_IN = 7.5
SLIDE_W = int(SLIDE_W_IN * EMU_PER_INCH)
SLIDE_H = int(SLIDE_H_IN * EMU_PER_INCH)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def emu(value: float) -> int:
    return int(float(value) * EMU_PER_INCH)


def clean_hex(value: str, default: str = "17201D") -> str:
    raw = str(value or default).strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in raw):
        return default
    return raw.upper()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def rels_xml(items) -> str:
    rows = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    rows.extend(items)
    rows.append("</Relationships>")
    return "\n".join(rows)


def text_box_xml(item: dict, shape_id: int) -> str:
    text = escape(str(item.get("text", "")))
    x = emu(item.get("x", 0))
    y = emu(item.get("y", 0))
    w = emu(item.get("w", 4))
    h = emu(item.get("h", 1))
    font_size = int(float(item.get("font_size", 24)) * 100)
    color = clean_hex(item.get("color", "17201D"))
    bold = ' b="1"' if item.get("bold") else ""
    italic = ' i="1"' if item.get("italic") else ""
    align = str(item.get("align", "l")).lower()
    align_map = {"left": "l", "center": "ctr", "right": "r", "l": "l", "ctr": "ctr", "r": "r"}
    anchor = str(item.get("valign", "top")).lower()
    anchor_map = {"top": "t", "middle": "ctr", "center": "ctr", "bottom": "b", "t": "t", "ctr": "ctr", "b": "b"}
    typeface = escape(str(item.get("font", "Aptos")))
    name = escape(str(item.get("name", f"Text {shape_id}")))
    return f'''
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody>
        <a:bodyPr wrap="square" anchor="{anchor_map.get(anchor, "t")}"><a:spAutoFit/></a:bodyPr>
        <a:lstStyle/>
        <a:p><a:pPr algn="{align_map.get(align, "l")}"/><a:r><a:rPr lang="zh-TW" sz="{font_size}"{bold}{italic}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{typeface}"/><a:ea typeface="{typeface}"/></a:rPr><a:t>{text}</a:t></a:r><a:endParaRPr lang="zh-TW" sz="{font_size}"/></a:p>
      </p:txBody>
    </p:sp>'''


def build_package(spec: dict, spec_dir: Path, out: Path) -> None:
    slides = spec.get("slides") or []
    if not slides:
        raise SystemExit("Spec must contain a non-empty slides array.")

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        media_dir = tmp / "ppt" / "media"
        slides_dir = tmp / "ppt" / "slides"
        slide_rels_dir = slides_dir / "_rels"
        ppt_rels_dir = tmp / "ppt" / "_rels"
        root_rels_dir = tmp / "_rels"

        media_names = []
        for index, slide in enumerate(slides, start=1):
            bg = Path(slide.get("background", ""))
            bg_path = bg if bg.is_absolute() else spec_dir / bg
            if not bg_path.exists():
                raise SystemExit(f"Missing background image for slide {index}: {bg_path}")
            if bg_path.suffix.lower() not in IMAGE_EXTS:
                raise SystemExit(f"Unsupported image extension: {bg_path}")
            if bg_path.stat().st_size <= 0:
                raise SystemExit(f"Background image is empty: {bg_path}")
            media_name = f"background{index}{bg_path.suffix.lower()}"
            media_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(bg_path, media_dir / media_name)
            media_names.append(media_name)

        content_rows = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Default Extension="png" ContentType="image/png"/>',
            '<Default Extension="jpg" ContentType="image/jpeg"/>',
            '<Default Extension="jpeg" ContentType="image/jpeg"/>',
            '<Default Extension="webp" ContentType="image/webp"/>',
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        ]
        for index in range(1, len(slides) + 1):
            content_rows.append(
                f'<Override PartName="/ppt/slides/slide{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            )
        content_rows.append("</Types>")
        write(tmp / "[Content_Types].xml", "\n".join(content_rows))

        write(
            root_rels_dir / ".rels",
            rels_xml(
                [
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
                ]
            ),
        )

        slide_ids = []
        presentation_rels = [
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
        ]
        for index in range(1, len(slides) + 1):
            rid = index + 1
            slide_ids.append(f'<p:sldId id="{255 + index}" r:id="rId{rid}"/>')
            presentation_rels.append(
                f'<Relationship Id="rId{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{index}.xml"/>'
            )
        write(ppt_rels_dir / "presentation.xml.rels", rels_xml(presentation_rels))

        write(
            tmp / "ppt" / "presentation.xml",
            f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst>{''.join(slide_ids)}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>''',
        )

        write(
            tmp / "ppt" / "slideMasters" / "slideMaster1.xml",
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>''',
        )
        write(
            tmp / "ppt" / "slideMasters" / "_rels" / "slideMaster1.xml.rels",
            rels_xml(
                [
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>',
                    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>',
                ]
            ),
        )
        write(
            tmp / "ppt" / "slideLayouts" / "slideLayout1.xml",
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>''',
        )
        write(
            tmp / "ppt" / "slideLayouts" / "_rels" / "slideLayout1.xml.rels",
            rels_xml(
                [
                    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
                ]
            ),
        )
        write(
            tmp / "ppt" / "theme" / "theme1.xml",
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="SOIL Background Text Theme"><a:themeElements><a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F1F1F"/></a:dk2><a:lt2><a:srgbClr val="F2F2F2"/></a:lt2><a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>''',
        )

        for index, slide in enumerate(slides, start=1):
            media_name = media_names[index - 1]
            text_xml = "\n".join(text_box_xml(item, shape_id) for shape_id, item in enumerate(slide.get("texts", []), start=3))
            write(
                slides_dir / f"slide{index}.xml",
                f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    <p:pic>
      <p:nvPicPr><p:cNvPr id="2" name="{escape(media_name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
    {text_xml}
  </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>''',
            )
            write(
                slide_rels_dir / f"slide{index}.xml.rels",
                rels_xml(
                    [
                        f'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{escape(media_name)}"/>',
                        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>',
                    ]
                ),
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in tmp.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(tmp).as_posix())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="JSON spec with slides, backgrounds, and text boxes.")
    parser.add_argument("--out", required=True, help="Output PPTX path.")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = json.loads(spec_path.read_text(encoding="utf-8-sig"))
    out = Path(args.out)
    build_package(spec, spec_path.parent, out)
    print(f"Wrote {out} with {len(spec.get('slides', []))} slide(s), {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
