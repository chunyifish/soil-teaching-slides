#!/usr/bin/env python3
"""Run the Mode B formula and PPTX regression suite without installing dependencies."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
SCRIPTS = ROOT / "scripts"


def run(command: list[str], *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    output = (result.stdout + result.stderr).strip()
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{output}")
    if output:
        print(output)
    return output


def find_soffice() -> str | None:
    explicit = os.environ.get("SOFFICE")
    if explicit and Path(explicit).is_file():
        return explicit
    discovered = shutil.which("soffice")
    if discovered:
        return discovered
    for candidate in (Path(r"C:\Program Files\LibreOffice\program\soffice.com"), Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.com")):
        if candidate.is_file():
            return str(candidate)
    return None


def render_with_libreoffice(soffice: str, pptx: Path, output_dir: Path) -> dict[str, object]:
    profile = output_dir / "lo-profile"
    profile.mkdir(parents=True, exist_ok=True)
    pdf = output_dir / f"{pptx.stem}_LibreOffice.pdf"
    profile_uri = profile.resolve().as_uri()
    run([soffice, "--headless", f"-env:UserInstallation={profile_uri}", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx)])
    produced_pdf = output_dir / f"{pptx.stem}.pdf"
    if not produced_pdf.is_file():
        raise RuntimeError("LibreOffice returned success but did not create the PPTX render PDF.")
    produced_pdf.replace(pdf)

    try:
        import pypdfium2 as pdfium
    except ImportError:
        return {"application": "LibreOffice", "pdf": str(pdf), "page_count": None, "contact_sheet": None, "images": [], "detail": "PDF created; pypdfium2 unavailable for PNG conversion."}

    document = pdfium.PdfDocument(pdf)
    frames_dir = output_dir / "libreoffice-frames"
    frames_dir.mkdir(exist_ok=True)
    tiles: list[Image.Image] = []
    image_paths: list[str] = []
    for index in range(len(document)):
        image = document[index].render(scale=1.5).to_pil().convert("RGB")
        image_path = frames_dir / f"slide-{index + 1:02d}.png"
        image.save(image_path)
        image_paths.append(str(image_path))
        thumbnail = image.copy()
        thumbnail.thumbnail((480, 270))
        tile = Image.new("RGB", (500, 300), "white")
        tile.paste(thumbnail, ((500 - thumbnail.width) // 2, 10))
        ImageDraw.Draw(tile).text((12, 278), f"Slide {index + 1:02d}", fill="black")
        tiles.append(tile)
    columns = min(5, max(1, len(tiles)))
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 500, rows * 300), (232, 232, 232))
    for index, tile in enumerate(tiles):
        sheet.paste(tile, ((index % columns) * 500, (index // columns) * 300))
    contact = output_dir / "B_Mode_Quality_Regression_contact.png"
    sheet.save(contact)
    return {"application": "LibreOffice", "pdf": str(pdf), "page_count": len(document), "contact_sheet": str(contact), "images": image_paths}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--runtime-node", default=os.environ.get("RUNTIME_NODE") or shutil.which("node"))
    parser.add_argument("--runtime-node-modules", default=os.environ.get("RUNTIME_NODE_MODULES"))
    parser.add_argument("--python", default=os.environ.get("RUNTIME_PYTHON") or sys.executable)
    parser.add_argument("--skip-libreoffice", action="store_true", help="Keep artifact-tool PNG rendering only.")
    args = parser.parse_args()

    if not args.runtime_node or not Path(args.runtime_node).is_file():
        parser.error("Node.js was not found; load the bundled workspace dependencies or pass --runtime-node.")
    if not args.runtime_node_modules or not (Path(args.runtime_node_modules) / "@oai" / "artifact-tool" / "dist" / "artifact_tool.mjs").is_file():
        parser.error("Set RUNTIME_NODE_MODULES to the bundled workspace dependency directory or pass --runtime-node-modules.")

    if args.output_dir:
        output_dir = args.output_dir.resolve()
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        output_dir = Path.cwd() / "work" / f"b-mode-quality-regression-{stamp}"
    if output_dir.exists() and any(output_dir.iterdir()):
        parser.error(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["RUNTIME_NODE_MODULES"] = str(Path(args.runtime_node_modules).resolve())
    cases = TESTS / "b_mode_formula_cases.json"
    run([args.runtime_node, str(TESTS / "check_b_mode_formula_cases.mjs"), str(cases)], env=environment)
    run([args.runtime_node, str(TESTS / "generate_b_mode_regression.mjs"), str(output_dir), str(cases)], env=environment)

    deck = output_dir / "B_Mode_Quality_Regression.pptx"
    validator = SCRIPTS / "validate_editable_b_pptx.py"
    run([args.python, str(validator), str(ROOT / "assets" / "Fractal_Editable.pptx"), "--expected-slides", "18", "--quality-reference", "--allow-media"])
    validation = run([args.python, str(validator), str(deck), "--expected-slides", "11", "--require-editable", "--require-ascii-filename", "--forbid-fixed-takeaway"])

    manifest = json.loads((output_dir / "regression-manifest.json").read_text(encoding="utf-8"))
    pngs = sorted(output_dir.glob("slide-*.png"))
    if len(pngs) != 11:
        raise RuntimeError(f"artifact-tool created {len(pngs)} preview PNGs; expected 11.")
    if manifest["slides"] != 11 or len(manifest["testCases"]) != 9:
        raise RuntimeError("Regression manifest did not preserve the expected slide and formula-case counts.")
    if not manifest["formulas"] or any(item["objectCount"] < 3 for item in manifest["formulas"]):
        raise RuntimeError("A formula did not produce the expected editable component objects.")

    rendering: dict[str, object] = {"application": "@oai/artifact-tool", "png_count": len(pngs), "contact_sheet": None}
    if not args.skip_libreoffice:
        soffice = find_soffice()
        if soffice:
            rendering = render_with_libreoffice(soffice, deck, output_dir)
            if rendering["page_count"] is not None and rendering["page_count"] != 11:
                raise RuntimeError(f"LibreOffice rendered {rendering['page_count']} PDF pages; expected 11.")
        else:
            rendering["detail"] = "LibreOffice not installed; only artifact-tool slide PNGs were generated."

    report = {
        "result": "PASS",
        "reference": {"path": str(ROOT / "assets" / "Fractal_Editable.pptx"), "expected_slides": 18},
        "regression_deck": str(deck),
        "formula_case_count": len(manifest["testCases"]),
        "formula_objects": manifest["formulas"],
        "validation": validation,
        "rendering": rendering,
        "microsoft_powerpoint": "not tested by this script; record a separate read-only application check",
    }
    report_path = output_dir / "B_Mode_Quality_QA.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"result": report["result"], "deck": report["regression_deck"], "formula_cases": report["formula_case_count"], "rendering": rendering, "report": str(report_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
