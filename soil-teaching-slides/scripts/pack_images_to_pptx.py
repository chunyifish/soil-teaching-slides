#!/usr/bin/env python3
"""Pack 16:9 slide images into a PPTX, one full-slide image per slide.

This script uses only the Python standard library. It creates a minimal
PowerPoint package with each input image filling a widescreen slide.
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


SLIDE_W = 13_333_500
SLIDE_H = 7_500_000
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def natural_key(path: Path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def content_type(path: Path) -> str:
    if path.suffix.lower() == ".webp":
        return "image/webp"
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


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


def build_package(images: list[Path], out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        media_dir = tmp / "ppt" / "media"
        slides_dir = tmp / "ppt" / "slides"
        slide_rels_dir = slides_dir / "_rels"
        ppt_rels_dir = tmp / "ppt" / "_rels"
        root_rels_dir = tmp / "_rels"
        theme_dir = tmp / "ppt" / "theme"

        media_names = []
        for index, image in enumerate(images, start=1):
            ext = image.suffix.lower()
            media_name = f"image{index}{ext}"
            target = media_dir / media_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image, target)
            media_names.append(media_name)

        defaults = {
            "rels": "application/vnd.openxmlformats-package.relationships+xml",
            "xml": "application/xml",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
        }
        content_rows = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        ]
        for ext, ctype in defaults.items():
            content_rows.append(f'<Default Extension="{ext}" ContentType="{ctype}"/>')
        content_rows.extend(
            [
                '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
                '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
                '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
                '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
            ]
        )
        for index in range(1, len(images) + 1):
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
        for index in range(1, len(images) + 1):
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
  <p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
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
            theme_dir / "theme1.xml",
            '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="SOIL Image Theme"><a:themeElements><a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1><a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="1F1F1F"/></a:dk2><a:lt2><a:srgbClr val="F2F2F2"/></a:lt2><a:accent1><a:srgbClr val="4472C4"/></a:accent1><a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3><a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5><a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Office"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme><a:fmtScheme name="Office"><a:fillStyleLst/><a:lnStyleLst/><a:effectStyleLst/><a:bgFillStyleLst/></a:fmtScheme></a:themeElements></a:theme>''',
        )

        for index, media_name in enumerate(media_names, start=1):
            escaped_name = escape(media_name)
            write(
                slides_dir / f"slide{index}.xml",
                f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    <p:pic>
      <p:nvPicPr><p:cNvPr id="2" name="{escaped_name}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{SLIDE_W}" cy="{SLIDE_H}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>
  </p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>''',
            )
            write(
                slide_rels_dir / f"slide{index}.xml.rels",
                rels_xml(
                    [
                        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/%s"/>'
                        % escaped_name,
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
    parser.add_argument("--images-dir", required=True, help="Directory containing slide images.")
    parser.add_argument("--out", required=True, help="Output PPTX path.")
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    out = Path(args.out)
    images = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS],
        key=natural_key,
    )
    if not images:
        raise SystemExit(f"No slide images found in {images_dir}")
    for image in images:
        if image.stat().st_size <= 0:
            raise SystemExit(f"Image is empty: {image}")

    build_package(images, out)
    size = os.path.getsize(out)
    print(f"Wrote {out} with {len(images)} slide(s), {size} bytes")


if __name__ == "__main__":
    main()
