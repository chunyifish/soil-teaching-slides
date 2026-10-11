#!/usr/bin/env python3
"""Validate package integrity and the editable-object contract for SOIL Mode B PPTX decks."""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"p": P_NS, "a": A_NS, "m": M_NS, "r": R_NS, "rel": REL_NS, "ct": CT_NS}
NEGATIVE_EXTENT = re.compile(rb"\b(?:cx|cy)=\"-\d+\"")
RAW_LATEX = re.compile(
    r"\\(?:frac|dfrac|tfrac|sqrt|sum|int|prod|lim|log|ln|alpha|beta|gamma|delta|theta|lambda|pi|infty|times|cdot|begin|end)\b"
)
ASCII_PPTX_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.pptx$", re.IGNORECASE)


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


def _source_part_from_rels(rel_name: str) -> str:
    if rel_name == "_rels/.rels":
        return ""
    path = PurePosixPath(rel_name)
    if path.parent.name != "_rels" or not path.name.endswith(".rels"):
        return ""
    return str(path.parent.parent / path.name[:-5])


def _resolve_target(source_part: str, target: str) -> str | None:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    target_path = unquote(parsed.path)
    if target_path.startswith("/"):
        resolved = posixpath.normpath(target_path.lstrip("/"))
    else:
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target_path))
    return resolved if resolved != "." else ""


def inspect_pptx(path: Path) -> dict[str, object]:
    package_errors: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        name_counts = Counter(names)
        duplicate_entries = sum(count - 1 for count in name_counts.values() if count > 1)
        if duplicate_entries:
            package_errors.append(f"duplicate ZIP entries={duplicate_entries}")
        crc_failure = zf.testzip()
        if crc_failure:
            package_errors.append(f"ZIP CRC failure at {crc_failure}")

        required_parts = {"[Content_Types].xml", "ppt/presentation.xml", "ppt/_rels/presentation.xml.rels"}
        missing_required = sorted(required_parts - set(names))
        if missing_required:
            package_errors.append(f"missing required parts={','.join(missing_required)}")

        xml_roots: dict[str, ET.Element] = {}
        xml_errors: list[str] = []
        for name in names:
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                xml_roots[name] = _xml(zf, name)
            except (ET.ParseError, KeyError) as exc:
                xml_errors.append(f"{name}: {exc}")
        package_errors.extend(f"invalid XML {error}" for error in xml_errors)

        relationship_files = [name for name in names if name.endswith(".rels")]
        relation_targets: dict[str, dict[str, str | None]] = {}
        all_targets: set[str] = set()
        missing_targets: list[str] = []
        for rel_name in relationship_files:
            root = xml_roots.get(rel_name)
            if root is None:
                continue
            source_part = _source_part_from_rels(rel_name)
            ids: dict[str, str | None] = {}
            for rel in root.findall("rel:Relationship", NS):
                rel_id = rel.get("Id", "")
                target = rel.get("Target", "")
                resolved = None if rel.get("TargetMode") == "External" else _resolve_target(source_part, target)
                ids[rel_id] = resolved
                if resolved is None:
                    continue
                all_targets.add(resolved)
                if resolved not in name_counts:
                    missing_targets.append(f"{source_part or '[package root]'} -> {rel_id} -> {target}")
            relation_targets[source_part] = ids

        if missing_targets:
            package_errors.extend(f"missing relationship target {entry}" for entry in missing_targets)

        content_types = xml_roots.get("[Content_Types].xml")
        if content_types is not None:
            for override in content_types.findall("ct:Override", NS):
                part_name = unquote(override.get("PartName", "")).lstrip("/")
                if part_name and part_name not in name_counts:
                    package_errors.append(f"content-type override points to missing part {part_name}")

        # Check every relationship ID used by an XML part against that part's own .rels file.
        for source_part, root in xml_roots.items():
            if source_part.endswith(".rels"):
                continue
            ids = relation_targets.get(source_part, {})
            for element in root.iter():
                for attr in (f"{{{R_NS}}}id", f"{{{R_NS}}}embed", f"{{{R_NS}}}link"):
                    ref_id = element.get(attr)
                    if ref_id and ref_id not in ids:
                        package_errors.append(f"{source_part} uses unresolved relationship id {ref_id}")

        presentation = xml_roots.get("ppt/presentation.xml")
        presentation_rels = relation_targets.get("ppt/presentation.xml", {})
        slide_names = sorted(
            name for name in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
        )
        slide_order: list[str] = []
        if presentation is not None:
            for slide_id in presentation.findall(".//p:sldId", NS):
                rel_id = slide_id.get(f"{{{R_NS}}}id", "")
                target = presentation_rels.get(rel_id)
                if target is None:
                    package_errors.append(f"presentation slide reference {rel_id} has no internal relationship")
                else:
                    if target not in name_counts:
                        package_errors.append(f"presentation references missing slide {target}")
                    slide_order.append(target)
        if slide_order and len(slide_order) != len(slide_names):
            package_errors.append(f"presentation references {len(slide_order)} slides but package contains {len(slide_names)}")

        slide_size = presentation.find(".//p:sldSz", NS) if presentation is not None else None
        slide_width = int(slide_size.get("cx", "0")) if slide_size is not None else 0
        slide_height = int(slide_size.get("cy", "0")) if slide_size is not None else 0

        media_names = [name for name in names if name.startswith("ppt/media/") and not name.endswith("/")]
        orphan_media = sorted(set(media_names) - all_targets)
        negative_extents = 0
        for name in names:
            if name.endswith(".xml"):
                negative_extents += len(NEGATIVE_EXTENT.findall(zf.read(name)))

        empty_invisible = 0
        white_masks = 0
        fixed_takeaway_bars = 0
        out_of_bounds = 0
        editable_shapes = 0
        pictures = 0
        formula_parts = 0
        office_math_objects = 0
        raw_latex: list[str] = []
        per_slide_shapes: dict[str, int] = {}

        for slide_name in slide_order or slide_names:
            root = xml_roots.get(slide_name)
            if root is None:
                continue
            shapes = root.findall(".//p:sp", NS)
            editable_shapes += len(shapes)
            per_slide_shapes[slide_name] = len(shapes)
            pictures += len(root.findall(".//p:pic", NS))
            office_math_objects += len(root.findall(".//m:oMath", NS))

            for shape in shapes:
                shape_name_node = shape.find("p:nvSpPr/p:cNvPr", NS)
                shape_name = shape_name_node.get("name", "") if shape_name_node is not None else ""
                if shape_name.startswith("b-formula") or shape_name.startswith("formula-"):
                    formula_parts += 1
                if shape_name in {"mode-b-final-takeaway-bar", "takeaway-frame"}:
                    fixed_takeaway_bars += 1
                text = _text(shape)
                if text and RAW_LATEX.search(text):
                    raw_latex.append(f"{slide_name}: {text}")
                if text:
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

            if slide_width and slide_height:
                sp_tree = root.find(".//p:spTree", NS)
                if sp_tree is not None:
                    for item in list(sp_tree):
                        if item.tag.rsplit("}", 1)[-1] not in {"sp", "pic", "cxnSp", "graphicFrame"}:
                            continue
                        xfrm = item.find("p:xfrm", NS) if item.tag.endswith("graphicFrame") else item.find("p:spPr/a:xfrm", NS)
                        if xfrm is None:
                            continue
                        off, ext = xfrm.find("a:off", NS), xfrm.find("a:ext", NS)
                        if off is None or ext is None:
                            continue
                        x, y = int(off.get("x", "0")), int(off.get("y", "0"))
                        cx, cy = int(ext.get("cx", "0")), int(ext.get("cy", "0"))
                        if x < 0 or y < 0 or cx < 0 or cy < 0 or x + cx > slide_width or y + cy > slide_height:
                            out_of_bounds += 1

        return {
            "slides": len(slide_order) if slide_order else len(slide_names),
            "media": len(media_names),
            "orphan_media": len(orphan_media),
            "notes": len([name for name in names if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)]),
            "editable_shapes": editable_shapes,
            "pictures": pictures,
            "formula_parts": formula_parts,
            "office_math_objects": office_math_objects,
            "negative_extents": negative_extents,
            "out_of_bounds": out_of_bounds,
            "empty_invisible": empty_invisible,
            "white_masks": white_masks,
            "fixed_takeaway_bars": fixed_takeaway_bars,
            "duplicate_entries": duplicate_entries,
            "xml_errors": len(xml_errors),
            "package_errors": package_errors,
            "raw_latex": raw_latex,
            "per_slide_shapes": per_slide_shapes,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--expected-slides", type=int)
    parser.add_argument("--allow-media", action="store_true")
    parser.add_argument("--forbid-fixed-takeaway", action="store_true")
    parser.add_argument("--require-editable", action="store_true")
    parser.add_argument("--require-ascii-filename", action="store_true")
    parser.add_argument("--quality-reference", action="store_true", help="Skip visual object-hygiene rules for a supplied reference deck.")
    parser.add_argument("--notes", choices=("all", "any", "none"), default="all")
    args = parser.parse_args()

    if not args.pptx.is_file():
        parser.error(f"PPTX not found: {args.pptx}")
    if args.require_ascii_filename and (not args.pptx.name.isascii() or not ASCII_PPTX_NAME.fullmatch(args.pptx.name)):
        print(f"FAIL: filename={args.pptx.name!r} expected a short ASCII .pptx filename")
        return 1

    try:
        result = inspect_pptx(args.pptx)
    except (zipfile.BadZipFile, ET.ParseError, KeyError, OSError, RuntimeError, ValueError) as exc:
        print(f"FAIL: cannot inspect PPTX: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = list(result["package_errors"])
    if args.expected_slides is not None and result["slides"] != args.expected_slides:
        failures.append(f"slides={result['slides']} expected={args.expected_slides}")
    if not args.allow_media and result["media"] != 0:
        failures.append(f"media={result['media']} expected=0")
    if result["orphan_media"] != 0:
        failures.append(f"orphan_media={result['orphan_media']} expected=0")
    if args.notes == "all" and result["notes"] != result["slides"]:
        failures.append(f"notes={result['notes']} expected={result['slides']}")
    if args.notes == "any" and result["notes"] == 0:
        failures.append("notes=0 expected at least 1")
    if args.notes == "none" and result["notes"] != 0:
        failures.append(f"notes={result['notes']} expected=0")
    for key in ("negative_extents", "out_of_bounds"):
        if result[key] != 0:
            failures.append(f"{key}={result[key]} expected=0")
    if result["raw_latex"]:
        failures.append(f"visible_raw_latex={len(result['raw_latex'])} expected=0")
    if args.require_editable and (result["editable_shapes"] == 0 or result["pictures"] > 0):
        failures.append(f"editable_shapes={result['editable_shapes']} pictures={result['pictures']} expected editable native content without flattened slide images")
    if not args.quality_reference:
        for key in ("empty_invisible", "white_masks"):
            if result[key] != 0:
                failures.append(f"{key}={result[key]} expected=0")
    if args.forbid_fixed_takeaway and result["fixed_takeaway_bars"] != 0:
        failures.append(f"fixed_takeaway_bars={result['fixed_takeaway_bars']} expected=0")

    summary_keys = (
        "slides", "media", "notes", "editable_shapes", "pictures", "formula_parts",
        "office_math_objects", "negative_extents", "out_of_bounds", "empty_invisible",
        "white_masks", "duplicate_entries", "xml_errors",
    )
    summary = " ".join(f"{key}={result[key]}" for key in summary_keys)
    if failures:
        print(f"FAIL: {summary} package_errors={len(result['package_errors'])}")
        for failure in failures:
            print(f"- {failure}")
        for text in result["raw_latex"][:10]:
            print(f"- raw LaTeX: {text}")
        return 1
    print(f"PASS: {summary} package_errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
