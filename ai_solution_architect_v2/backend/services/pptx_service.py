"""
pptx_service.py

Python wrapper that calls generate_pptx.js via subprocess.
Accepts the full architecture JSON dict and returns the .pptx as bytes.

The JS generator (generate_pptx.js) uses:
  - drawioGenerator.js  — converts architecture.components + .connections → draw.io XML
  - drawioRenderer.js   — renders draw.io XML → PNG via local Puppeteer (no external API)

No Mermaid dependency remains.
"""

import io
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from lxml import etree

# Resolve the JS script path relative to this file
_SCRIPT_DIR     = Path(__file__).parent / "pptx_gen"
_JS_SCRIPT      = _SCRIPT_DIR / "generate_pptx.js"
_TITLE_SLIDES   = _SCRIPT_DIR / "title_slides.pptx"
_CLOSING_SLIDES = _SCRIPT_DIR / "closing_slides.pptx"
_NODE_BIN       = "node"

# OOXML namespaces
_RELS_NS   = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT_NS     = "http://schemas.openxmlformats.org/package/2006/content-types"
_P_NS      = "http://schemas.openxmlformats.org/presentationml/2006/main"
_R_NS      = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_REL_SLIDE  = f"{_R_NS}/slide"
_REL_MASTER = f"{_R_NS}/slideMaster"

# Directories under ppt/ whose files receive a per-guest prefix to avoid conflicts
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

# Directory-name tokens that appear as the second-to-last segment in .rels Targets,
# e.g. Target="../media/image1.png" → parent dir token = "media"
_ASSET_DIRNAMES = frozenset({
    "slides", "media", "slideLayouts", "slideMasters",
    "theme", "fonts", "diagrams", "charts", "embeddings",
})


# ── ZIP helpers ───────────────────────────────────────────────────────────────

def _read_zip(data: bytes) -> dict:
    out = {}
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        for name in zf.namelist():
            out[name] = zf.read(name)
    return out


def _prefix_filename(path: str, prefix: str) -> str:
    """Add `prefix` to the filename (last) component of `path`."""
    dir_part, sep, filename = path.rpartition("/")
    return f"{dir_part}{sep}{prefix}{filename}"


def _prefix_rels_targets(rels_bytes: bytes, prefix: str) -> bytes:
    """
    In a .rels XML file, prefix the filename of every Target whose
    parent directory token is a known PPTX asset directory.

    Example:  Target="../media/image1.png"  →  Target="../media/g1_image1.png"
    """
    try:
        root = etree.fromstring(rels_bytes)
    except Exception:
        return rels_bytes

    for rel in root:
        if rel.get("TargetMode") == "External":
            continue
        target = rel.get("Target", "")
        parts = target.replace("\\", "/").split("/")
        # Need at least "parent_dir/filename" (len >= 2)
        if len(parts) >= 2 and parts[-2].lstrip(".") in _ASSET_DIRNAMES:
            parts[-1] = prefix + parts[-1]
            rel.set("Target", "/".join(parts))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _remap_rels_ids(rels_bytes: bytes, id_map: dict) -> tuple:
    """
    Remap relationship IDs in a .rels file to avoid conflicts.
    Returns (updated_rels_bytes, old_to_new_id_mapping).
    
    id_map should be {old_rid: new_rid} for IDs to remap.
    """
    try:
        root = etree.fromstring(rels_bytes)
    except Exception:
        return rels_bytes, {}
    
    actual_remaps = {}
    for rel in root:
        old_id = rel.get("Id", "")
        if old_id in id_map:
            new_id = id_map[old_id]
            rel.set("Id", new_id)
            actual_remaps[old_id] = new_id
    
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), actual_remaps


def _remap_xml_rid_references(xml_bytes: bytes, rid_map: dict) -> bytes:
    """
    Update all r:embed, r:link, r:id attribute values in XML to use remapped rIds.
    """
    if not rid_map:
        return xml_bytes
    
    try:
        root = etree.fromstring(xml_bytes)
        
        # Define namespace for relationships
        r_ns = _R_NS
        
        # Find all elements with r:embed, r:link, or r:id attributes
        for elem in root.iter():
            for attr_name in [f"{{{r_ns}}}embed", f"{{{r_ns}}}link", f"{{{r_ns}}}id"]:
                old_val = elem.get(attr_name)
                if old_val and old_val in rid_map:
                    elem.set(attr_name, rid_map[old_val])
        
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    except Exception:
        return xml_bytes



def _get_slide_paths(files: dict) -> list:
    """Return ordered list of slide ZIP-paths from a PPTX file-dict."""
    prs_rels_bytes = files.get("ppt/_rels/presentation.xml.rels", b"")
    prs_bytes      = files.get("ppt/presentation.xml", b"")
    if not prs_rels_bytes or not prs_bytes:
        return []

    try:
        rels_root = etree.fromstring(prs_rels_bytes)
    except Exception:
        return []

    rid_to_path = {}
    for rel in rels_root:
        if rel.get("Type") == _REL_SLIDE and rel.get("TargetMode", "") != "External":
            target = rel.get("Target", "")
            rid_to_path[rel.get("Id")] = "ppt/" + target.lstrip("/")

    try:
        prs_root = etree.fromstring(prs_bytes)
    except Exception:
        return list(rid_to_path.values())

    sld_id_lst = prs_root.find(f"{{{_P_NS}}}sldIdLst")
    if sld_id_lst is None:
        return list(rid_to_path.values())

    return [rid_to_path[sld.get(f"{{{_R_NS}}}id")]
            for sld in sld_id_lst
            if sld.get(f"{{{_R_NS}}}id") in rid_to_path]


def _get_master_paths(files: dict) -> list:
    """Return list of slide-master ZIP-paths referenced by a PPTX file-dict."""
    prs_rels_bytes = files.get("ppt/_rels/presentation.xml.rels", b"")
    if not prs_rels_bytes:
        return []
    try:
        rels_root = etree.fromstring(prs_rels_bytes)
    except Exception:
        return []
    return [
        "ppt/" + rel.get("Target", "").lstrip("/")
        for rel in rels_root
        if rel.get("Type") == _REL_MASTER and rel.get("TargetMode", "") != "External"
    ]


def _rewrite_xml_asset_refs(xml_bytes: bytes, prefix: str) -> bytes:
    """
    Rewrite asset paths in XML body to use the given prefix.
    Handles embedded references like ../media/image.png → ../media/g1_image.png
    This is applied to slide masters and layouts to fix broken references.
    """
    try:
        # Convert bytes to string for regex operations
        xml_str = xml_bytes.decode('utf-8', errors='replace')
        
        # Replace relative asset paths with prefixed versions
        # Patterns: ../media/xxx, ../fonts/xxx, ../theme/xxx, ../diagrams/xxx, etc.
        asset_patterns = ["media", "fonts", "theme", "diagrams", "charts", "embeddings"]
        for asset_type in asset_patterns:
            # Match ../ + asset_type + / + filename
            pattern = rf'(\.\./(?:{asset_type})/)([^"/\\\s]+)'
            xml_str = re.sub(pattern, r'\1' + prefix + r'\2', xml_str)
        
        return xml_str.encode('utf-8')
    except Exception:
        # If something fails, return original bytes
        return xml_bytes


def _ct_map(files: dict) -> dict:
    """Return {'/partname': 'content-type'} from [Content_Types].xml."""
    ct_bytes = files.get("[Content_Types].xml", b"")
    if not ct_bytes:
        return {}
    try:
        root = etree.fromstring(ct_bytes)
    except Exception:
        return {}
    return {
        "/" + el.get("PartName", "").lstrip("/"): el.get("ContentType", "")
        for el in root
        if el.get("PartName") and el.get("ContentType")
    }


def _get_pptx_slide_dimensions(pptx_path: Path) -> dict:
    """
    Extract slide dimensions (cx, cy in EMUs) from a PPTX file.
    Returns dict with 'cx' and 'cy' keys, or empty dict if extraction fails.
    """
    if not pptx_path.exists():
        return {}
    
    try:
        files = _read_zip(pptx_path.read_bytes())
        prs_bytes = files.get("ppt/presentation.xml", b"")
        if not prs_bytes:
            return {}
        
        root = etree.fromstring(prs_bytes)
        sld_sz = root.find(f"{{{_P_NS}}}sldSz")
        if sld_sz is not None:
            cx = sld_sz.get("cx")
            cy = sld_sz.get("cy")
            if cx and cy:
                return {"cx": int(cx), "cy": int(cy)}
    except Exception:
        pass
    
    return {}


def _scale_slide_xml(slide_xml_bytes: bytes, scale_x: float, scale_y: float) -> bytes:
    """
    Scale all shape positions and dimensions in a slide XML by the given factors.
    Modifies all p:sp (shape), p:grpSp (group shape), p:cxnSp (connector) elements.
    """
    try:
        root = etree.fromstring(slide_xml_bytes)
        
        # Define namespaces
        ns = {
            "p": _P_NS,
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }
        
        # Find all transform elements (contains position and size)
        for xfrm in root.findall(".//a:xfrm", ns):
            # xfrm/a:off has x, y attributes (in EMUs)
            off = xfrm.find("a:off", ns)
            if off is not None:
                x = int(off.get("x", 0))
                y = int(off.get("y", 0))
                off.set("x", str(int(x * scale_x)))
                off.set("y", str(int(y * scale_y)))
            
            # xfrm/a:ext has cx, cy attributes (width, height in EMUs)
            ext = xfrm.find("a:ext", ns)
            if ext is not None:
                cx = int(ext.get("cx", 0))
                cy = int(ext.get("cy", 0))
                ext.set("cx", str(int(cx * scale_x)))
                ext.set("cy", str(int(cy * scale_y)))
        
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    except Exception as e:
        print(f"[pptx_service] Warning: Could not scale slide XML: {e}")
        return slide_xml_bytes



# ── Core ZIP-level merge ──────────────────────────────────────────────────────

def _zip_merge_pptx(pptx_bytes_list: list) -> bytes:
    """
    Merge multiple PPTX files at the ZIP level.

    Strategy
    --------
    • The FIRST PPTX is the structural base.  Its entire ZIP contents, including
      slides, layouts, masters, media, theme and fonts, are kept byte-for-byte
      untouched.  This is the "as-is" guarantee for template slides.

    • Every SUBSEQUENT PPTX has its asset files (slides, layouts, masters, media,
      theme, fonts …) copied into the output under a unique filename prefix
      ("g1_", "g2_", …).  Their .rels files are rewritten so every Target that
      points into an asset directory also uses the same prefix.  No conflicts
      with the base or with each other can occur.

    • presentation.xml (slide-id list) and presentation.xml.rels are updated to
      register the new slides (and their masters).

    • [Content_Types].xml is updated with Override entries for the new parts.
    """
    if not pptx_bytes_list:
        return b""

    # ── Phase 1: load base (first PPTX, kept as-is) ─────────────────────────
    out = _read_zip(pptx_bytes_list[0])

    prs_el   = etree.fromstring(out["ppt/presentation.xml"])
    prs_rels = etree.fromstring(out["ppt/_rels/presentation.xml.rels"])
    ct_el    = etree.fromstring(out["[Content_Types].xml"])

    # Extract base dimensions for later scaling
    base_sld_sz = prs_el.find(f"{{{_P_NS}}}sldSz")
    base_dims = None
    if base_sld_sz is not None:
        base_cx = int(base_sld_sz.get("cx", 0))
        base_cy = int(base_sld_sz.get("cy", 0))
        if base_cx > 0 and base_cy > 0:
            base_dims = {"cx": base_cx, "cy": base_cy}

    sld_id_lst = prs_el.find(f"{{{_P_NS}}}sldIdLst")
    if sld_id_lst is None:
        sld_id_lst = etree.SubElement(prs_el, f"{{{_P_NS}}}sldIdLst")

    sld_master_id_lst = prs_el.find(f"{{{_P_NS}}}sldMasterIdLst")

    # Max sldId used so far
    max_sld_id = 255
    for sld in sld_id_lst:
        try:
            max_sld_id = max(max_sld_id, int(sld.get("id", 0)))
        except (ValueError, TypeError):
            pass

    # Max rId used so far in presentation.xml.rels
    max_rid = 0
    for rel in prs_rels:
        m = re.match(r"rId(\d+)", rel.get("Id", ""))
        if m:
            max_rid = max(max_rid, int(m.group(1)))

    # Max sldMasterId used so far
    max_master_id = 2147483647
    if sld_master_id_lst is not None:
        for sm in sld_master_id_lst:
            try:
                max_master_id = max(max_master_id, int(sm.get("id", 0)))
            except (ValueError, TypeError):
                pass

    # Set of PartNames already in [Content_Types].xml
    ct_parts = {el.get("PartName", "") for el in ct_el}

    # ── Phase 2: append each guest PPTX ─────────────────────────────────────
    for src_idx, src_bytes in enumerate(pptx_bytes_list[1:], 1):
        src    = _read_zip(src_bytes)
        pfx    = f"g{src_idx}_"          # e.g. "g1_", "g2_"
        src_ct = _ct_map(src)

        # Extract dimensions from source and calculate scale factors if needed
        scale_x = 1.0
        scale_y = 1.0
        if base_dims:
            src_prs_bytes = src.get("ppt/presentation.xml", b"")
            if src_prs_bytes:
                try:
                    src_prs_el = etree.fromstring(src_prs_bytes)
                    src_sld_sz = src_prs_el.find(f"{{{_P_NS}}}sldSz")
                    if src_sld_sz is not None:
                        src_cx = int(src_sld_sz.get("cx", 0))
                        src_cy = int(src_sld_sz.get("cy", 0))
                        if src_cx > 0 and src_cy > 0:
                            scale_x = base_dims["cx"] / src_cx
                            scale_y = base_dims["cy"] / src_cy
                            if abs(scale_x - 1.0) > 0.01 or abs(scale_y - 1.0) > 0.01:
                                print(f"[pptx_service] Source {src_idx} size mismatch: "
                                      f"scaling by {scale_x:.3f}x{scale_y:.3f} to match base")
                except Exception:
                    pass

        # Build rId mapping for this source's master/layout .rels files
        # to avoid conflicts when multiple guests have same rIds
        rid_mapping = {}  # maps rels_path -> {old_rid: new_rid}
        for src_path in src:
            if (src_path.startswith("ppt/slideMasters/_rels/") or 
                src_path.startswith("ppt/slideLayouts/_rels/")) and src_path.endswith(".xml.rels"):
                try:
                    rels_root = etree.fromstring(src[src_path])
                    path_map = {}
                    for rel in rels_root:
                        old_rid = rel.get("Id", "")
                        if old_rid.startswith("rId"):
                            max_rid += 1
                            new_rid = f"rId{max_rid}"
                            path_map[old_rid] = new_rid
                    if path_map:
                        rid_mapping[src_path] = path_map
                        print(f"[pptx_service] Remapped {len(path_map)} rIds in {src_path} "
                              f"(source {src_idx}) to avoid conflicts")
                except Exception as e:
                    print(f"[pptx_service] Warning: Could not remap rIds in {src_path}: {e}")

        # Copy every asset file from guest to output, with prefix on the filename
        for src_path, data in src.items():
            path_dir = src_path.rpartition("/")[0]
            eff_dir  = path_dir.replace("/_rels", "") if "/_rels" in path_dir else path_dir
            if eff_dir not in _ASSET_DIRS:
                continue  # skip non-asset files (presentation.xml, docProps, etc.)

            new_path = _prefix_filename(src_path, pfx)
            
            # Rewrite .rels Target attributes to use the same prefix
            if src_path.endswith(".rels"):
                data = _prefix_rels_targets(data, pfx)
                # If this is a master/layout .rels, apply rId remapping
                if src_path in rid_mapping:
                    data, _ = _remap_rels_ids(data, rid_mapping[src_path])
            
            # For XML files: apply scaling and/or rId remapping as needed
            elif src_path.endswith(".xml"):
                # Scale slide and layout/master XML if dimensions differ from base
                if (scale_x != 1.0 or scale_y != 1.0):
                    if (src_path.startswith("ppt/slides/") or 
                        src_path.startswith("ppt/slideLayouts/") or 
                        src_path.startswith("ppt/slideMasters/")):
                        data = _scale_slide_xml(data, scale_x, scale_y)
                
                # Update rId references in master/layout XML to use remapped IDs
                if src_path.startswith("ppt/slideMasters/") or src_path.startswith("ppt/slideLayouts/"):
                    # Construct the path to the corresponding .rels file
                    dir_part, _, filename = src_path.rpartition("/")
                    rels_path = f"{dir_part}/_rels/{filename}.rels"
                    if rels_path in rid_mapping:
                        data = _remap_xml_rid_references(data, rid_mapping[rels_path])
            
            
            out[new_path] = data

            # Register in [Content_Types].xml if needed
            abs_new = "/" + new_path
            if "/" + src_path in src_ct and abs_new not in ct_parts:
                etree.SubElement(ct_el, f"{{{_CT_NS}}}Override", attrib={
                    "PartName": abs_new,
                    "ContentType": src_ct["/" + src_path],
                })
                ct_parts.add(abs_new)

        # Register slides in presentation.xml + presentation.xml.rels
        for slide_path in _get_slide_paths(src):
            new_slide_path = _prefix_filename(slide_path, pfx)
            if new_slide_path not in out:
                print(f"[pptx_service] WARNING: {new_slide_path} missing after copy")
                continue

            max_rid += 1
            new_rid = f"rId{max_rid}"
            rel_target = new_slide_path[len("ppt/"):]   # relative to ppt/

            etree.SubElement(prs_rels, f"{{{_RELS_NS}}}Relationship", attrib={
                "Id":     new_rid,
                "Type":   _REL_SLIDE,
                "Target": rel_target,
            })
            max_sld_id += 1
            sld_el = etree.SubElement(sld_id_lst, f"{{{_P_NS}}}sldId")
            sld_el.set("id", str(max_sld_id))
            sld_el.set(f"{{{_R_NS}}}id", new_rid)

        # Register slide masters so PowerPoint fully acknowledges them
        if sld_master_id_lst is not None:
            for master_path in _get_master_paths(src):
                new_master_path = _prefix_filename(master_path, pfx)
                if new_master_path not in out:
                    continue
                max_rid += 1
                m_rid = f"rId{max_rid}"
                rel_master_target = new_master_path[len("ppt/"):]

                etree.SubElement(prs_rels, f"{{{_RELS_NS}}}Relationship", attrib={
                    "Id":     m_rid,
                    "Type":   _REL_MASTER,
                    "Target": rel_master_target,
                })
                max_master_id += 1
                sm_el = etree.SubElement(sld_master_id_lst, f"{{{_P_NS}}}sldMasterId")
                sm_el.set("id", str(max_master_id))
                sm_el.set(f"{{{_R_NS}}}id", m_rid)

        print(f"[pptx_service] Appended {len(_get_slide_paths(src))} slide(s) "
              f"from source {src_idx} (prefix={pfx})")

    # ── Phase 3: write back modified XML ────────────────────────────────────
    _X = {"xml_declaration": True, "encoding": "UTF-8", "standalone": True}
    out["ppt/presentation.xml"]            = etree.tostring(prs_el,   **_X)
    out["ppt/_rels/presentation.xml.rels"] = etree.tostring(prs_rels, **_X)
    out["[Content_Types].xml"]             = etree.tostring(ct_el,    **_X)

    # ── Phase 4: write output ZIP ────────────────────────────────────────────
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in out.items():
            zf.writestr(name, data)
    return buf.getvalue()


# ── Public entry point ────────────────────────────────────────────────────────

def _merge_with_templates(content_bytes: bytes) -> bytes:
    """
    Prepend title_slides.pptx and append closing_slides.pptx to the
    content PPTX bytes using ZIP-level merging (no python-pptx object model).

    Title and closing slides are preserved exactly as they are in their source files.
    Content slides are appended with prefixed asset names to avoid any conflicts.
    """
    has_title   = _TITLE_SLIDES.exists()
    has_closing = _CLOSING_SLIDES.exists()

    if not has_title and not has_closing:
        print("[pptx_service] NOTE: no template files found — returning content only")
        return content_bytes

    parts = []
    if has_title:
        parts.append(_TITLE_SLIDES.read_bytes())
    parts.append(content_bytes)
    if has_closing:
        parts.append(_CLOSING_SLIDES.read_bytes())

    print(f"[pptx_service] ZIP-level merging {len(parts)} PPTX source(s)...")
    result = _zip_merge_pptx(parts)
    print("[pptx_service] Merge complete")
    return result




class PptxService:
    def generate(self, architecture_json: dict) -> bytes:
        """
        Takes the full architecture response dict, runs the Node.js generator,
        merges title + content + closing templates in Python (with XML-level scaling),
        and returns .pptx bytes.

        The architecture_json MUST contain architecture.components (with id/label)
        and architecture.connections for the draw.io diagram to render correctly.

        Raises RuntimeError if Node.js process fails.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path  = os.path.join(tmpdir, "input.json")
            output_path = os.path.join(tmpdir, "output.pptx")

            with open(input_path, "w", encoding="utf-8") as f:
                json.dump(architecture_json, f, ensure_ascii=False)

            result = subprocess.run(
                [_NODE_BIN, str(_JS_SCRIPT), input_path, output_path],
                capture_output=True,
                timeout=180,   # increased for Puppeteer startup time
                cwd=str(_SCRIPT_DIR),
            )

            # Decode output with UTF-8 and error handling (not CP1252)
            stdout_text = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
            stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""

            if result.returncode != 0:
                raise RuntimeError(
                    f"PPTX generation failed (exit {result.returncode}):\n"
                    f"STDOUT: {stdout_text}\nSTDERR: {stderr_text}"
                )

            if not os.path.exists(output_path):
                raise RuntimeError(
                    f"Node process exited 0 but output file not found.\n"
                    f"STDERR: {stderr_text}"
                )

            with open(output_path, "rb") as f:
                content_bytes = f.read()

        # Merge title + content + closing entirely in Python (no Node→Python subprocess)
        return _merge_with_templates(content_bytes)