#!/usr/bin/env python3
"""Validate the structural contract for SOIL Mode B editable PPTX decks."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS = {"p": P_NS, "a": A_NS}
NEGATIVE_EXTENT = re.compile(rb"\b(?:cx|cy)=\"-\d+\"")


def _xml(zf: zipfile.ZipFile, name: str) -> ET.Element:
    return ET.fromstring(zf.read(name))


def _text(shape: ET.Element) -> str:
    return "".join(node.text or "" for node in shape.findall(".//a:t", NS)).strip()


def _solid_rgb(parent: ET.Element | None) -> str | None:
    if parent is None:
        return None
    node = parent.find("a:solidFill/a:srgbClr", NS)
    return node.get("val", "").upper() if node is not None else None


def _no_fill(parent: ET.Element | None) -> bool:
    return parent is not None and parent.find("a:noFill", NS) is not None


def inspect_pptx(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        slide_names = sorted(
            name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        notes_names = sorted(
            name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
        )
        media_names = [name for name in names if name.startswith("ppt/media/") and not name.endswith("/")]

        negative_extents = 0
        for name in names:
            if name.endswith(".xml"):
                negative_extents += len(NEGATIVE_EXTENT.findall(zf.read(name)))

        empty_invisible = 0
        white_masks = 0
        fixed_takeaway_bars = 0
        for slide_name in slide_names:
            root = _xml(zf, slide_name)
            for shape in root.findall(".//p:sp", NS):
                c_nv_pr = shape.find("p:nvSpPr/p:cNvPr", NS)
                shape_name = c_nv_pr.get("name", "") if c_nv_pr is not None else ""
                if shape_name in {"mode-b-final-takeaway-bar", "takeaway-frame"}:
                    fixed_takeaway_bars += 1
                if _text(shape):
                    continue
                sp_pr = shape.find("p:spPr", NS)
                line = sp_pr.find("a:ln", NS) if sp_pr is not None else None
                fill_none = _no_fill(sp_pr)
                line_none = line is None or _no_fill(line) or line.get("w") == "0"
                if fill_none and line_none:
                    empty_invisible += 1
                    continue

                fill_rgb = _solid_rgb(sp_pr)
                line_rgb = _solid_rgb(line)
                if fill_rgb == "FFFFFF" and (line_none or line_rgb == "FFFFFF"):
                    white_masks += 1

        return {
            "slides": len(slide_names),
            "media": len(media_names),
            "notes": len(notes_names),
            "negative_extents": negative_extents,
            "empty_invisible": empty_invisible,
            "white_masks": white_masks,
            "fixed_takeaway_bars": fixed_takeaway_bars,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--expected-slides", type=int)
    parser.add_argument("--allow-media", action="store_true")
    parser.add_argument("--forbid-fixed-takeaway", action="store_true")
    parser.add_argument("--notes", choices=("all", "any", "none"), default="all")
    args = parser.parse_args()

    if not args.pptx.is_file():
        parser.error(f"PPTX not found: {args.pptx}")

    try:
        result = inspect_pptx(args.pptx)
    except (zipfile.BadZipFile, ET.ParseError, KeyError) as exc:
        print(f"FAIL: cannot inspect PPTX: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    if args.expected_slides is not None and result["slides"] != args.expected_slides:
        failures.append(f"slides={result['slides']} expected={args.expected_slides}")
    if not args.allow_media and result["media"] != 0:
        failures.append(f"media={result['media']} expected=0")
    if args.notes == "all" and result["notes"] != result["slides"]:
        failures.append(f"notes={result['notes']} expected={result['slides']}")
    if args.notes == "any" and result["notes"] == 0:
        failures.append("notes=0 expected at least 1")
    if args.notes == "none" and result["notes"] != 0:
        failures.append(f"notes={result['notes']} expected=0")
    for key in ("negative_extents", "empty_invisible", "white_masks"):
        if result[key] != 0:
            failures.append(f"{key}={result[key]} expected=0")
    if args.forbid_fixed_takeaway and result["fixed_takeaway_bars"] != 0:
        failures.append(f"fixed_takeaway_bars={result['fixed_takeaway_bars']} expected=0")

    summary = " ".join(f"{key}={value}" for key, value in result.items())
    if failures:
        print(f"FAIL: {summary}")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
