"""
pptx_service.py

Portable PowerPoint generation and native-template assembly service.

Key behavior:
- Node/PptxGenJS generates content PPTX.
- PowerPoint COM optionally imports title/content/closing decks.
- A permanent copy is saved to a machine-specific output folder.
- The API still receives bytes and can return a browser download normally.

Environment variables:
    PPTX_WORK_DIR
        Optional PowerPoint staging root.
        Example: D:\\DocuFlow\\pptx_work

    PPTX_OUTPUT_DIR
        Optional permanent generated-PPTX output directory.
        Example: D:\\DocuFlow\\generated_pptx

    PPTX_KEEP_DEBUG_FILES
        Optional. Set to "1", "true", or "yes" to retain assembly inputs:
        base.pptx, content.pptx, final.pptx and PowerShell script.
"""

import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
import zipfile
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from lxml import etree


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).parent / "pptx_gen"
_JS_SCRIPT = _SCRIPT_DIR / "generate_pptx.js"
_TITLE_SLIDES = _SCRIPT_DIR / "title_slides.pptx"
_CLOSING_SLIDES = _SCRIPT_DIR / "closing_slides.pptx"
_NODE_BIN = "node"


# ---------------------------------------------------------------------------
# OOXML namespaces
# ---------------------------------------------------------------------------

_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_REL_SLIDE = f"{_R_NS}/slide"
_REL_MASTER = f"{_R_NS}/slideMaster"

_ASSET_DIRS = frozenset({
    "ppt/slides",
    "ppt/media",
    "ppt/slideLayouts",
    "ppt/slideMasters",
    "ppt/theme",
    "ppt/fonts",
    "ppt/diagrams",
    "ppt/charts",
    "ppt/embeddings",
})

_ASSET_DIRNAMES = frozenset({
    "slides",
    "media",
    "slideLayouts",
    "slideMasters",
    "theme",
    "fonts",
    "diagrams",
    "charts",
    "embeddings",
})


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------

def _truthy_env(name: str) -> bool:
    """Read a conventional boolean environment variable."""
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _ensure_writable_directory(path: Path) -> Path:
    """
    Create a directory and verify that the current backend process can write
    to it. Returns a resolved path or raises an exception.
    """
    path = path.expanduser()
    path.mkdir(parents=True, exist_ok=True)

    probe_file = path / f".docuflow_probe_{uuid.uuid4().hex}.tmp"
    probe_file.write_text("ok", encoding="utf-8")
    probe_file.unlink(missing_ok=True)

    return path.resolve()


def _get_local_app_data() -> Optional[Path]:
    """Return LOCALAPPDATA when available on Windows."""
    value = os.getenv("LOCALAPPDATA", "").strip()
    return Path(value).expanduser() if value else None


def _get_user_profile() -> Optional[Path]:
    """Return USERPROFILE when available on Windows."""
    value = os.getenv("USERPROFILE", "").strip()
    return Path(value).expanduser() if value else None


def _get_pptx_work_root() -> Path:
    """
    Resolve a machine-specific writable staging root for temporary PowerPoint
    assembly files.

    Priority:
    1. PPTX_WORK_DIR
    2. LOCALAPPDATA\\DocuFlow\\pptx_work
    3. Python system temporary directory
    """
    configured_dir = os.getenv("PPTX_WORK_DIR", "").strip()

    candidates = []

    if configured_dir:
        candidates.append(Path(configured_dir))

    local_app_data = _get_local_app_data()
    if local_app_data is not None:
        candidates.append(local_app_data / "DocuFlow" / "pptx_work")

    candidates.append(Path(tempfile.gettempdir()) / "DocuFlow" / "pptx_work")
    candidates.append(Path(tempfile.gettempdir()))

    errors = []

    for candidate in candidates:
        try:
            resolved = _ensure_writable_directory(candidate)
            print(f"[pptx_service] PPTX work root: {resolved}")
            return resolved
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    raise RuntimeError(
        "Unable to create a writable PowerPoint work directory. "
        + " | ".join(errors)
    )


def _get_pptx_output_root() -> Path:
    """
    Resolve a permanent output folder for generated PPTX files.

    Priority:
    1. PPTX_OUTPUT_DIR
    2. USERPROFILE\\Downloads\\DocuFlow_PPTX
    3. LOCALAPPDATA\\DocuFlow\\generated_pptx
    4. Current working directory\\generated_pptx

    This folder is persistent. It is NOT deleted after generation.
    """
    configured_dir = os.getenv("PPTX_OUTPUT_DIR", "").strip()

    candidates = []

    if configured_dir:
        candidates.append(Path(configured_dir))

    user_profile = _get_user_profile()
    if user_profile is not None:
        candidates.append(user_profile / "Downloads" / "DocuFlow_PPTX")

    local_app_data = _get_local_app_data()
    if local_app_data is not None:
        candidates.append(local_app_data / "DocuFlow" / "generated_pptx")

    candidates.append(Path.cwd() / "generated_pptx")

    errors = []

    for candidate in candidates:
        try:
            resolved = _ensure_writable_directory(candidate)
            print(f"[pptx_service] Persistent PPTX output root: {resolved}")
            return resolved
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")

    raise RuntimeError(
        "Unable to create a writable persistent PPTX output directory. "
        + " | ".join(errors)
    )


def _safe_filename_part(value: str, fallback: str = "presentation") -> str:
    """
    Convert a string to a Windows-safe filename fragment.
    """
    value = str(value or "").strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value)
    value = re.sub(r"\s+", "_", value)
    value = value.strip(" ._")

    if not value:
        return fallback

    return value[:80]


def _extract_output_label(architecture_json: dict) -> str:
    """
    Select a useful output filename prefix from known input fields.
    """
    if not isinstance(architecture_json, dict):
        return "docuflow_presentation"

    candidates = [
        architecture_json.get("project_name"),
        architecture_json.get("projectName"),
        architecture_json.get("title"),
        architecture_json.get("name"),
        architecture_json.get("document_title"),
        architecture_json.get("documentTitle"),
    ]

    for candidate in candidates:
        if candidate and str(candidate).strip():
            return _safe_filename_part(str(candidate))

    return "docuflow_presentation"


def _persist_generated_pptx(pptx_bytes: bytes, architecture_json: dict) -> Path:
    """
    Persist an output copy outside TemporaryDirectory.

    The returned PPTX bytes are still used by FastAPI for browser downloads,
    while this creates a physical copy that remains on disk after request
    completion.
    """
    if not pptx_bytes:
        raise RuntimeError("Cannot persist an empty PPTX payload.")

    output_root = _get_pptx_output_root()
    output_label = _extract_output_label(architecture_json)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:8]

    output_path = output_root / (
        f"{output_label}_{timestamp}_{unique_suffix}.pptx"
    )

    output_path.write_bytes(pptx_bytes)

    if not output_path.exists():
        raise RuntimeError(
            f"PPTX persistence failed; file was not created: {output_path}"
        )

    if output_path.stat().st_size <= 0:
        raise RuntimeError(
            f"PPTX persistence failed; file is empty: {output_path}"
        )

    print(
        f"[pptx_service] Persistent PPTX saved: {output_path} "
        f"({output_path.stat().st_size:,} bytes)"
    )

    return output_path


def _copy_debug_file(source: Path, debug_dir: Path, target_name: str) -> None:
    """
    Best-effort debug file copy. Never masks the original generation failure.
    """
    try:
        if source.exists():
            debug_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, debug_dir / target_name)
    except Exception as exc:
        print(
            f"[pptx_service] Warning: could not preserve debug file "
            f"'{source}': {exc}"
        )


# ---------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------

def _safe_xml_root(xml_bytes: bytes):
    parser = etree.XMLParser(
        recover=True,
        remove_blank_text=True,
        huge_tree=True,
    )
    return etree.fromstring(xml_bytes, parser=parser)


def _xml_to_bytes(root) -> bytes:
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=False,
        pretty_print=False,
    )


def _read_zip(data: bytes) -> dict:
    out = {}

    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        for name in zf.namelist():
            out[name] = zf.read(name)

    return out


def _prefix_filename(path: str, prefix: str) -> str:
    dir_part, sep, filename = path.rpartition("/")
    return f"{dir_part}{sep}{prefix}{filename}"


def _prefix_rels_targets(rels_bytes: bytes, prefix: str) -> bytes:
    try:
        root = _safe_xml_root(rels_bytes)
    except Exception:
        return rels_bytes

    for rel in root:
        if rel.get("TargetMode") == "External":
            continue

        target = rel.get("Target", "")
        parts = target.replace("\\", "/").split("/")

        if len(parts) >= 2 and parts[-2].lstrip(".") in _ASSET_DIRNAMES:
            parts[-1] = prefix + parts[-1]
            rel.set("Target", "/".join(parts))

    return _xml_to_bytes(root)


def _remap_rels_ids(rels_bytes: bytes, id_map: dict):
    try:
        root = _safe_xml_root(rels_bytes)
    except Exception:
        return rels_bytes, {}

    actual_remaps = {}

    for rel in root:
        old_id = rel.get("Id", "")

        if old_id in id_map:
            new_id = id_map[old_id]
            rel.set("Id", new_id)
            actual_remaps[old_id] = new_id

    return _xml_to_bytes(root), actual_remaps


def _remap_xml_rid_references(xml_bytes: bytes, rid_map: dict) -> bytes:
    if not rid_map:
        return xml_bytes

    try:
        root = _safe_xml_root(xml_bytes)

        for elem in root.iter():
            for attr_name in [
                f"{{{_R_NS}}}embed",
                f"{{{_R_NS}}}link",
                f"{{{_R_NS}}}id",
            ]:
                old_val = elem.get(attr_name)

                if old_val and old_val in rid_map:
                    elem.set(attr_name, rid_map[old_val])

        return _xml_to_bytes(root)

    except Exception:
        return xml_bytes


def _get_slide_paths(files: dict) -> list:
    prs_rels_bytes = files.get("ppt/_rels/presentation.xml.rels", b"")
    prs_bytes = files.get("ppt/presentation.xml", b"")

    if not prs_rels_bytes or not prs_bytes:
        return []

    try:
        rels_root = _safe_xml_root(prs_rels_bytes)
    except Exception:
        return []

    rid_to_path = {}

    for rel in rels_root:
        if rel.get("Type") == _REL_SLIDE and rel.get("TargetMode", "") != "External":
            target = rel.get("Target", "")
            rid_to_path[rel.get("Id")] = "ppt/" + target.lstrip("/")

    try:
        prs_root = _safe_xml_root(prs_bytes)
    except Exception:
        return list(rid_to_path.values())

    sld_id_lst = prs_root.find(f"{{{_P_NS}}}sldIdLst")

    if sld_id_lst is None:
        return list(rid_to_path.values())

    return [
        rid_to_path[sld.get(f"{{{_R_NS}}}id")]
        for sld in sld_id_lst
        if sld.get(f"{{{_R_NS}}}id") in rid_to_path
    ]


def _get_master_paths(files: dict) -> list:
    prs_rels_bytes = files.get("ppt/_rels/presentation.xml.rels", b"")

    if not prs_rels_bytes:
        return []

    try:
        rels_root = _safe_xml_root(prs_rels_bytes)
    except Exception:
        return []

    return [
        "ppt/" + rel.get("Target", "").lstrip("/")
        for rel in rels_root
        if rel.get("Type") == _REL_MASTER
        and rel.get("TargetMode", "") != "External"
    ]


def _ct_map(files: dict) -> dict:
    ct_bytes = files.get("[Content_Types].xml", b"")

    if not ct_bytes:
        return {}

    try:
        root = _safe_xml_root(ct_bytes)
    except Exception:
        return {}

    return {
        "/" + el.get("PartName", "").lstrip("/"): el.get("ContentType", "")
        for el in root
        if el.get("PartName") and el.get("ContentType")
    }


def _ensure_content_type_entry(
    ct_el,
    part_name: str,
    content_type: str,
) -> None:
    """Ensure a content type Override exists for a package part."""
    part_name = "/" + part_name.lstrip("/")

    for el in ct_el:
        if el.get("PartName") == part_name:
            return

    etree.SubElement(
        ct_el,
        f"{{{_CT_NS}}}Override",
        attrib={
            "PartName": part_name,
            "ContentType": content_type,
        },
    )


def _ensure_content_types_order(ct_el) -> None:
    """
    OOXML content types require Default items before Override items.
    """
    defaults = []
    overrides = []

    for el in list(ct_el):
        tag = el.tag.split("}", 1)[1] if "}" in el.tag else el.tag

        if tag == "Default":
            defaults.append(el)
        elif tag == "Override":
            overrides.append(el)

    if not defaults or not overrides:
        return

    for el in list(ct_el):
        ct_el.remove(el)

    for el in defaults:
        ct_el.append(el)

    for el in overrides:
        ct_el.append(el)


def _scale_slide_xml(
    slide_xml_bytes: bytes,
    scale_x: float,
    scale_y: float,
) -> bytes:
    """
    Scale shape positions only in actual slide XML.

    Do not apply this to masters or layouts because those relationship graphs
    can be invalidated by arbitrary XML modification.
    """
    try:
        root = _safe_xml_root(slide_xml_bytes)

        ns = {
            "p": _P_NS,
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }

        xfrm_nodes = []
        xfrm_nodes.extend(root.findall(".//p:sp//a:xfrm", ns))
        xfrm_nodes.extend(root.findall(".//p:pic//a:xfrm", ns))
        xfrm_nodes.extend(root.findall(".//p:graphicFrame//a:xfrm", ns))

        for xfrm in xfrm_nodes:
            off = xfrm.find("a:off", ns)

            if off is not None:
                x = int(off.get("x", 0))
                y = int(off.get("y", 0))

                off.set("x", str(int(x * scale_x)))
                off.set("y", str(int(y * scale_y)))

            ext = xfrm.find("a:ext", ns)

            if ext is not None:
                cx = int(ext.get("cx", 0))
                cy = int(ext.get("cy", 0))

                ext.set("cx", str(int(cx * scale_x)))
                ext.set("cy", str(int(cy * scale_y)))

        return _xml_to_bytes(root)

    except Exception as exc:
        print(
            f"[pptx_service] Warning: Could not scale slide XML: {exc}"
        )
        return slide_xml_bytes


# ---------------------------------------------------------------------------
# Optional ZIP merge implementation
# ---------------------------------------------------------------------------

def _zip_merge_pptx(pptx_bytes_list: list) -> bytes:
    """
    Low-level ZIP merge implementation.

    This is intentionally retained for compatibility/debugging, but production
    generation uses _merge_with_templates(), which delegates slide import to
    PowerPoint and avoids manual cross-presentation master/layout wiring.
    """
    if not pptx_bytes_list:
        return b""

    out = _read_zip(pptx_bytes_list[0])

    prs_el = _safe_xml_root(out["ppt/presentation.xml"])
    prs_rels = _safe_xml_root(out["ppt/_rels/presentation.xml.rels"])
    ct_el = _safe_xml_root(out["[Content_Types].xml"])

    base_sld_sz = prs_el.find(f"{{{_P_NS}}}sldSz")
    base_dims = None

    if base_sld_sz is not None:
        base_cx = int(base_sld_sz.get("cx", 0))
        base_cy = int(base_sld_sz.get("cy", 0))

        if base_cx > 0 and base_cy > 0:
            base_dims = {
                "cx": base_cx,
                "cy": base_cy,
            }

    sld_id_lst = prs_el.find(f"{{{_P_NS}}}sldIdLst")

    if sld_id_lst is None:
        sld_id_lst = etree.SubElement(
            prs_el,
            f"{{{_P_NS}}}sldIdLst",
        )

    sld_master_id_lst = prs_el.find(f"{{{_P_NS}}}sldMasterIdLst")

    max_sld_id = 255

    for sld in sld_id_lst:
        try:
            max_sld_id = max(max_sld_id, int(sld.get("id", 0)))
        except Exception:
            pass

    max_rid = 0

    for rel in prs_rels:
        match = re.match(r"rId(\d+)", rel.get("Id", ""))

        if match:
            max_rid = max(max_rid, int(match.group(1)))

    max_master_id = 2147483647

    if sld_master_id_lst is not None:
        for sm in sld_master_id_lst:
            try:
                max_master_id = max(
                    max_master_id,
                    int(sm.get("id", 0)),
                )
            except Exception:
                pass

    for src_idx, src_bytes in enumerate(pptx_bytes_list[1:], 1):
        src = _read_zip(src_bytes)
        prefix = f"g{src_idx}_"
        src_ct = _ct_map(src)

        scale_x = 1.0
        scale_y = 1.0

        if base_dims:
            src_prs_bytes = src.get("ppt/presentation.xml", b"")

            if src_prs_bytes:
                try:
                    src_prs_el = _safe_xml_root(src_prs_bytes)
                    src_sld_sz = src_prs_el.find(f"{{{_P_NS}}}sldSz")

                    if src_sld_sz is not None:
                        src_cx = int(src_sld_sz.get("cx", 0))
                        src_cy = int(src_sld_sz.get("cy", 0))

                        if src_cx > 0 and src_cy > 0:
                            scale_x = base_dims["cx"] / src_cx
                            scale_y = base_dims["cy"] / src_cy

                except Exception:
                    pass

        for src_path, data in src.items():
            path_dir = src_path.rpartition("/")[0]
            effective_dir = (
                path_dir.replace("/_rels", "")
                if "/_rels" in path_dir
                else path_dir
            )

            if effective_dir not in _ASSET_DIRS:
                continue

            new_path = _prefix_filename(src_path, prefix)

            if src_path.endswith(".rels"):
                data = _prefix_rels_targets(data, prefix)

            elif (
                src_path.endswith(".xml")
                and (scale_x != 1.0 or scale_y != 1.0)
                and src_path.startswith("ppt/slides/")
                and "/_rels/" not in src_path
            ):
                data = _scale_slide_xml(data, scale_x, scale_y)

            out[new_path] = data

            if "/" + src_path in src_ct:
                _ensure_content_type_entry(
                    ct_el,
                    "/" + new_path,
                    src_ct["/" + src_path],
                )

        for slide_path in _get_slide_paths(src):
            new_slide_path = _prefix_filename(slide_path, prefix)

            if new_slide_path not in out:
                continue

            max_rid += 1
            new_rid = f"rId{max_rid}"

            etree.SubElement(
                prs_rels,
                f"{{{_RELS_NS}}}Relationship",
                attrib={
                    "Id": new_rid,
                    "Type": _REL_SLIDE,
                    "Target": new_slide_path[len("ppt/"):],
                },
            )

            max_sld_id += 1

            slide_id_el = etree.SubElement(
                sld_id_lst,
                f"{{{_P_NS}}}sldId",
            )
            slide_id_el.set("id", str(max_sld_id))
            slide_id_el.set(f"{{{_R_NS}}}id", new_rid)

        if sld_master_id_lst is not None:
            for master_path in _get_master_paths(src):
                new_master_path = _prefix_filename(master_path, prefix)

                if new_master_path not in out:
                    continue

                max_rid += 1
                master_rid = f"rId{max_rid}"

                etree.SubElement(
                    prs_rels,
                    f"{{{_RELS_NS}}}Relationship",
                    attrib={
                        "Id": master_rid,
                        "Type": _REL_MASTER,
                        "Target": new_master_path[len("ppt/"):],
                    },
                )

                max_master_id += 1

                master_id_el = etree.SubElement(
                    sld_master_id_lst,
                    f"{{{_P_NS}}}sldMasterId",
                )
                master_id_el.set("id", str(max_master_id))
                master_id_el.set(f"{{{_R_NS}}}id", master_rid)

    out["ppt/presentation.xml"] = _xml_to_bytes(prs_el)
    out["ppt/_rels/presentation.xml.rels"] = _xml_to_bytes(prs_rels)

    _ensure_content_types_order(ct_el)
    out["[Content_Types].xml"] = _xml_to_bytes(ct_el)

    print(
        f"[pptx_service] ZIP merged {len(pptx_bytes_list)} presentations; "
        f"max_rid={max_rid}, max_sld_id={max_sld_id}"
    )

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        allowZip64=True,
    ) as zf:
        for name, data in out.items():
            zf.writestr(name, data)

    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Native PowerPoint template assembly
# ---------------------------------------------------------------------------

def _merge_with_templates(content_bytes: bytes) -> bytes:
    """
    Assemble title, generated content, and closing decks using PowerPoint COM.

    PowerPoint's InsertFromFile is used because it rebuilds master/layout
    relationships more reliably than copying arbitrary XML parts between PPTX
    ZIP packages.

    Note:
    - InsertFromFile inserts AFTER the supplied index.
    - To append, use deck.Slides.Count, never deck.Slides.Count + 1.
    - PowerPoint COM expects MsoTriState values: msoFalse=0, msoTrue=-1.
    """
    if not _TITLE_SLIDES.exists() and not _CLOSING_SLIDES.exists():
        return content_bytes

    work_root = _get_pptx_work_root()
    keep_debug_files = _truthy_env("PPTX_KEEP_DEBUG_FILES")

    with tempfile.TemporaryDirectory(
        prefix="docuflow_pptx_",
        dir=str(work_root),
        ignore_cleanup_errors=True,
    ) as tmpdir:
        tmpdir_path = Path(tmpdir)

        content_path = tmpdir_path / "content.pptx"
        base_path = tmpdir_path / "base.pptx"
        intermediate_path = tmpdir_path / "assembled_intermediate.pptx"
        output_path = tmpdir_path / "final.pptx"
        script_path = tmpdir_path / "assemble_pptx.ps1"

        content_path.write_bytes(content_bytes)

        if _TITLE_SLIDES.exists():
            base_path.write_bytes(_TITLE_SLIDES.read_bytes())
        else:
            base_path.write_bytes(content_bytes)

        def ps_quote(value: Path) -> str:
            return "'" + str(value.resolve()).replace("'", "''") + "'"

        commands = [
            "$ErrorActionPreference = 'Stop'",
            "$ppt = $null",
            "$deck = $null",
            "",
            "# Microsoft.Office.Core.MsoTriState values",
            "$msoFalse = 0",
            "$msoTrue = -1",
            "",
            "# PowerPoint PpSaveAsFileType",
            "$ppSaveAsOpenXMLPresentation = 24",
            "",
            "function Invoke-PowerPointIdle {",
            "  param([int]$Milliseconds = 1500)",
            "  $deadline = (Get-Date).AddMilliseconds($Milliseconds)",
            "  while ((Get-Date) -lt $deadline) {",
            "    Start-Sleep -Milliseconds 100",
            "  }",
            "}",
            "",
            "function Insert-DeckSlides {",
            "  param(",
            "    [Parameter(Mandatory = $true)] $Presentation,",
            "    [Parameter(Mandatory = $true)] [string] $SourcePath,",
            "    [Parameter(Mandatory = $true)] [string] $Label",
            "  )",
            "",
            "  if (-not (Test-Path -LiteralPath $SourcePath)) {",
            '    throw "[$Label] Source presentation was not found: $SourcePath"',
            "  }",
            "",
            "  $beforeCount = [int]$Presentation.Slides.Count",
            '  Write-Host "[$Label] Importing into deck with $beforeCount slide(s)"',
            "",
            "  # Index = the slide after which imported slides are placed.",
            "  # 0 is valid for an empty deck; Count appends to a non-empty deck.",
            "  $insertAfterIndex = $beforeCount",
            "",
            "  [void]$Presentation.Slides.InsertFromFile(",
            "    $SourcePath,",
            "    $insertAfterIndex",
            "  )",
            "",
            "  Invoke-PowerPointIdle -Milliseconds 3000",
            "",
            "  $afterCount = [int]$Presentation.Slides.Count",
            "  if ($afterCount -le $beforeCount) {",
            '    throw "[$Label] No slides were inserted. Before=$beforeCount, After=$afterCount"',
            "  }",
            "",
            '  Write-Host "[$Label] Imported $($afterCount - $beforeCount) slide(s); total=$afterCount"',
            "}",
            "",
            "try {",
            "  $ppt = New-Object -ComObject PowerPoint.Application",
            "  $ppt.Visible = $msoTrue",
            "",
            f"  if (-not (Test-Path -LiteralPath {ps_quote(base_path)})) {{",
            '    throw "Base presentation was not found."',
            "  }",
            "",
            '  Write-Host "[base] Opening base presentation"',
            "",
            "# Open(FileName, ReadOnly, Untitled, WithWindow)",
            f"  $deck = $ppt.Presentations.Open({ps_quote(base_path)}, $msoFalse, $msoFalse, $msoTrue)",
            "",
            "  Invoke-PowerPointIdle -Milliseconds 2000",
            '  Write-Host "[base] Opened with $($deck.Slides.Count) slide(s)"',
            "",
        ]

        if _TITLE_SLIDES.exists():
            commands.extend([
                f"  Insert-DeckSlides -Presentation $deck -SourcePath {ps_quote(content_path)} -Label 'content'",
                "",
            ])

        if _CLOSING_SLIDES.exists():
            commands.extend([
                f"  Insert-DeckSlides -Presentation $deck -SourcePath {ps_quote(_CLOSING_SLIDES)} -Label 'closing'",
                "",
            ])

        commands.extend([
            "  Invoke-PowerPointIdle -Milliseconds 3000",
            "",
            "  if ($deck.Slides.Count -eq 0) {",
            '    throw "Cannot save an empty PowerPoint presentation."',
            "  }",
            "",
            f"  $intermediatePath = {ps_quote(intermediate_path)}",
            f"  $finalPath = {ps_quote(output_path)}",
            "",
            "  if (Test-Path -LiteralPath $intermediatePath) {",
            "    Remove-Item -LiteralPath $intermediatePath -Force",
            "  }",
            "",
            "  if (Test-Path -LiteralPath $finalPath) {",
            "    Remove-Item -LiteralPath $finalPath -Force",
            "  }",
            "",
            '  Write-Host "[save] Saving $($deck.Slides.Count) slide(s)"',
            "",
            "  try {",
            "    $deck.SaveAs($intermediatePath, $ppSaveAsOpenXMLPresentation)",
            "  }",
            "  catch {",
            "    $saveAsError = $_.Exception.Message",
            '    Write-Host "[save] SaveAs failed: $saveAsError"',
            '    Write-Host "[save] Attempting SaveCopyAs fallback"',
            "",
            "    try {",
            "      $deck.SaveCopyAs($intermediatePath, $ppSaveAsOpenXMLPresentation, $msoFalse)",
            "    }",
            "    catch {",
            '      throw "PowerPoint could not save the merged presentation. SaveAs error: $saveAsError | SaveCopyAs error: $($_.Exception.Message)"',
            "    }",
            "  }",
            "",
            "  Invoke-PowerPointIdle -Milliseconds 2500",
            "",
            "  if (-not (Test-Path -LiteralPath $intermediatePath)) {",
            '    throw "PowerPoint reported success but did not create the intermediate PPTX."',
            "  }",
            "",
            "  $savedSize = (Get-Item -LiteralPath $intermediatePath).Length",
            "  if ($savedSize -le 0) {",
            '    throw "PowerPoint created an empty intermediate PPTX."',
            "  }",
            "",
            "  Copy-Item -LiteralPath $intermediatePath -Destination $finalPath -Force",
            "",
            "  if (-not (Test-Path -LiteralPath $finalPath)) {",
            '    throw "Final PPTX was not created after successful intermediate save."',
            "  }",
            "",
            '  Write-Host "[save] Final PPTX created: $finalPath"',
            "}",
            "finally {",
            "  if ($deck -ne $null) {",
            "    try { $deck.Close() } catch { }",
            "    try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($deck) } catch { }",
            "  }",
            "",
            "  if ($ppt -ne $null) {",
            "    try { $ppt.Quit() } catch { }",
            "    try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($ppt) } catch { }",
            "  }",
            "",
            "  [GC]::Collect()",
            "  [GC]::WaitForPendingFinalizers()",
            "}",
        ])

        powershell_script = "\n".join(commands)
        script_path.write_text(
            powershell_script,
            encoding="utf-8-sig",
        )

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0 or not output_path.exists():
            if keep_debug_files:
                debug_root = _get_pptx_output_root() / "debug_failed_assembly"
                debug_run_dir = debug_root / (
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                    + "_"
                    + uuid.uuid4().hex[:8]
                )

                _copy_debug_file(base_path, debug_run_dir, "base.pptx")
                _copy_debug_file(content_path, debug_run_dir, "content.pptx")
                _copy_debug_file(
                    intermediate_path,
                    debug_run_dir,
                    "assembled_intermediate.pptx",
                )
                _copy_debug_file(output_path, debug_run_dir, "final.pptx")
                _copy_debug_file(script_path, debug_run_dir, "assemble_pptx.ps1")

                print(
                    f"[pptx_service] Debug assembly files preserved in: "
                    f"{debug_run_dir}"
                )

            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()

            details_parts = [
                "PowerPoint template assembly failed.",
            ]

            if stdout:
                details_parts.append(f"PowerShell stdout:\n{stdout}")

            if stderr:
                details_parts.append(f"PowerShell stderr:\n{stderr}")

            raise RuntimeError("\n\n".join(details_parts))

        if keep_debug_files:
            debug_root = _get_pptx_output_root() / "debug_successful_assembly"
            debug_run_dir = debug_root / (
                datetime.now().strftime("%Y%m%d_%H%M%S")
                + "_"
                + uuid.uuid4().hex[:8]
            )

            _copy_debug_file(base_path, debug_run_dir, "base.pptx")
            _copy_debug_file(content_path, debug_run_dir, "content.pptx")
            _copy_debug_file(
                intermediate_path,
                debug_run_dir,
                "assembled_intermediate.pptx",
            )
            _copy_debug_file(output_path, debug_run_dir, "final.pptx")
            _copy_debug_file(script_path, debug_run_dir, "assemble_pptx.ps1")

            print(
                f"[pptx_service] Debug assembly files preserved in: "
                f"{debug_run_dir}"
            )

        return output_path.read_bytes()


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------

class PptxService:
    """
    Generate PPTX bytes for the API and persist a copy to a machine-resolved
    output directory for local inspection/download history.
    """

    def generate(
        self,
        architecture_json: dict,
        tracker: Optional[Any] = None,
    ) -> bytes:
        node_start = time.time()

        work_root = _get_pptx_work_root()

        with tempfile.TemporaryDirectory(
            prefix="docuflow_node_",
            dir=str(work_root),
            ignore_cleanup_errors=True,
        ) as tmpdir:
            tmpdir_path = Path(tmpdir)

            input_path = tmpdir_path / "input.json"
            node_output_path = tmpdir_path / "output.pptx"

            input_path.write_text(
                json.dumps(
                    architecture_json,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    _NODE_BIN,
                    str(_JS_SCRIPT),
                    str(input_path),
                    str(node_output_path),
                ],
                capture_output=True,
                timeout=180,
                cwd=str(_SCRIPT_DIR),
            )

            node_duration = time.time() - node_start

            stdout_text = (
                result.stdout.decode("utf-8", errors="replace")
                if result.stdout
                else ""
            )

            stderr_text = (
                result.stderr.decode("utf-8", errors="replace")
                if result.stderr
                else ""
            )

            if stdout_text.strip():
                print(f"[pptx_service Node stdout]:\n{stdout_text}")

            if stderr_text.strip():
                print(f"[pptx_service Node stderr]:\n{stderr_text}")

            if result.returncode != 0:
                raise RuntimeError(
                    f"PPTX generation failed (exit {result.returncode}):\n"
                    f"STDOUT:\n{stdout_text}\n"
                    f"STDERR:\n{stderr_text}"
                )

            if not node_output_path.exists():
                raise RuntimeError(
                    "Node process exited successfully but did not create "
                    f"the expected PPTX: {node_output_path}\n"
                    f"STDERR:\n{stderr_text}"
                )

            if node_output_path.stat().st_size <= 0:
                raise RuntimeError(
                    "Node process created an empty output PPTX: "
                    f"{node_output_path}"
                )

            if tracker is not None:
                try:
                    step1_match = re.search(
                        r"\[pptx-gen\] STEP 1 duration:\s*(\d+)\s*ms",
                        stderr_text,
                    )
                    step2_match = re.search(
                        r"\[pptx-gen\] STEP 2 duration:\s*(\d+)\s*ms",
                        stderr_text,
                    )

                    duration_xml = (
                        float(step1_match.group(1)) / 1000.0
                        if step1_match
                        else 0.0
                    )

                    duration_png = (
                        float(step2_match.group(1)) / 1000.0
                        if step2_match
                        else 0.0
                    )

                    tracker._phase_timers["diagram_generation"] = duration_xml
                    tracker._phase_timers["diagram_rendering"] = duration_png
                    tracker._phase_timers["pptx_generation"] = max(
                        0.0,
                        node_duration - duration_xml - duration_png,
                    )

                except Exception as timing_err:
                    print(
                        "[Metrics] Warning: failed to parse timing from "
                        f"JS stderr: {timing_err}"
                    )

            content_bytes = node_output_path.read_bytes()

            if _truthy_env("PPTX_KEEP_DEBUG_FILES"):
                debug_root = _get_pptx_output_root() / "debug_node_output"
                debug_dir = debug_root / (
                    datetime.now().strftime("%Y%m%d_%H%M%S")
                    + "_"
                    + uuid.uuid4().hex[:8]
                )
                _copy_debug_file(
                    node_output_path,
                    debug_dir,
                    "node_generated_content.pptx",
                )
                _copy_debug_file(
                    input_path,
                    debug_dir,
                    "generation_input.json",
                )

                print(
                    f"[pptx_service] Node debug files preserved in: "
                    f"{debug_dir}"
                )

        assembly_ctx = (
            tracker.phase("pptx_assembly")
            if tracker is not None
            else nullcontext()
        )

        with assembly_ctx:
            final_bytes = _merge_with_templates(content_bytes)

        persisted_path = _persist_generated_pptx(
            final_bytes,
            architecture_json,
        )

        print(
            f"[pptx_service] Generation completed successfully. "
            f"Persistent file: {persisted_path}"
        )

        return final_bytes