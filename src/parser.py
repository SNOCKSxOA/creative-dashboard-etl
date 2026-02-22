"""
Naming Convention Parser

Parses SNOCKS Meta Ads naming convention into structured fields.
Supports 3 schemas based on Creative Source.

The first 7 fields are always present and identical across all schemas:
  1. Product
  2. Creative ID
  3. Content Type
  4. Adtype
  5. Creative Cluster
  6. In/Ex
  7. Creative Source

From position 8 onward, fields depend on the schema.
"""

from typing import Optional

# Creative Source values that map to each schema
SCHEMA_1_SOURCES = {
    "Katrin", "Claudio", "Katrin+Claudio",
    "CFC", "CFK", "CFS", "CFZ", "CFP", "IN", "CFF", "CFN",
}

SCHEMA_2_SOURCES = {
    "MT", "SM", "CreativeTeam", "DCO", "TeamPaid",
    "MIT", "M28", "Other", "addictive", "stronger",
}


def detect_schema(creative_source: str) -> int:
    """Detect which naming schema to use based on creative_source."""
    if creative_source in SCHEMA_1_SOURCES:
        return 1
    # Also check partial matches for Schema 1 (e.g., "Katrin" in "Katrin+Claudio")
    if any(s in creative_source for s in ["Katrin"]):
        return 1
    if creative_source in SCHEMA_2_SOURCES:
        return 2
    return 3


def parse_ad_name(ad_name: str) -> dict:
    """
    Parse an ad name string into structured fields.
    
    Returns a dict with all parsed fields. Fields that couldn't be 
    extracted are set to None. Parse warnings are collected in 'parse_errors'.
    """
    result = {
        # Core fields
        "product": None,
        "creative_id": None,
        "content_type": None,
        "adtype": None,
        "creative_cluster": None,
        "in_ex": None,
        "creative_source": None,
        "schema_version": 3,
        
        # Schema 1 optional fields
        "pl_eg_sp": None,
        "color": None,
        "element": None,
        "cr_kuerzel": None,
        "creative_tag": None,
        "format_video": None,
        "format_foto": None,
        "hook": None,
        "text_kuerzel": None,
        "visual": None,
        "angle": None,
        "gender": None,
        "test_ids": None,
        "launch_year_week": None,
        "original_creative_id": None,
        "additional_infos": None,
        "free_text": None,
        "is_ai": False,
        "ad_group_number": None,
        
        # Schema 2 additional fields
        "color_freitext_pl": None,
        "visual_ct": None,
        "creator_cluster": None,
        "text_edit": None,
        "text_align": None,
        "image_type": None,
        "copy_cluster": None,
        "zusatzfeld": None,
        
        # Meta
        "raw_suffix": None,
        "parse_errors": [],
    }

    if not ad_name or not ad_name.strip():
        result["parse_errors"].append("Empty ad name")
        return result

    parts = ad_name.split("_")

    # We need at least 7 parts for the core fields
    if len(parts) < 7:
        result["parse_errors"].append(f"Only {len(parts)} segments, expected at least 7")
        # Try to extract what we can
        fields = ["product", "creative_id", "content_type", "adtype", "creative_cluster", "in_ex", "creative_source"]
        for i, field in enumerate(fields):
            if i < len(parts):
                result[field] = parts[i]
        result["raw_suffix"] = "_".join(parts[min(len(parts), 7):]) if len(parts) > 7 else None
        return result

    # Extract core fields (positions 1-7)
    result["product"] = parts[0]
    result["creative_id"] = parts[1]
    result["content_type"] = parts[2]
    result["adtype"] = parts[3]
    result["creative_cluster"] = parts[4]
    result["in_ex"] = parts[5]
    result["creative_source"] = parts[6]

    # Detect schema
    schema = detect_schema(result["creative_source"])
    result["schema_version"] = schema

    # Remaining parts after core fields
    remaining = parts[7:]

    if not remaining:
        return result

    if schema == 1:
        result = _parse_schema_1(result, remaining)
    elif schema == 2:
        result = _parse_schema_2(result, remaining)
    else:
        result = _parse_schema_3(result, remaining)

    return result


def _parse_schema_1(result: dict, remaining: list[str]) -> dict:
    """
    Parse Schema 1 (internal creation) optional fields.
    
    Order: PL/EG/SP, Color, Element, CR-Kürzel, CreativeTag,
           FormatVideo|FormatFoto, Hook, Text, Visual, Angle,
           Gender, TestIDs, LaunchWeek, OriginalCreativeID,
           AdditionalInfos, FreeText, AI, AdGroupNumber
    
    Since many fields are optional and we can't always reliably distinguish
    them by position alone, we store the raw suffix as fallback and do
    best-effort sequential parsing.
    """
    result["raw_suffix"] = "_".join(remaining)
    content_type = (result.get("content_type") or "").lower()
    
    idx = 0
    
    # PL/EG/SP (may start with PL-, EG, SP)
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val.startswith(("PL-", "PL", "EG", "SP")):
            result["pl_eg_sp"] = val
            idx += 1
    
    # Color
    if idx < len(remaining) and remaining[idx]:
        result["color"] = remaining[idx]
        idx += 1
    
    # Element (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["element"] = remaining[idx]
        idx += 1
    
    # CR-Kürzel
    if idx < len(remaining) and remaining[idx]:
        result["cr_kuerzel"] = remaining[idx]
        idx += 1
    
    # Creative Tag (spaces removed in naming convention)
    if idx < len(remaining) and remaining[idx]:
        result["creative_tag"] = remaining[idx]
        idx += 1
    
    # Format (Video or Foto, depending on content_type)
    if idx < len(remaining) and remaining[idx]:
        if content_type != "image":
            result["format_video"] = remaining[idx]
        else:
            result["format_foto"] = remaining[idx]
        idx += 1
    
    # Hook (only for non-Image)
    if content_type != "image" and idx < len(remaining) and remaining[idx]:
        result["hook"] = remaining[idx]
        idx += 1
    
    # Text Kürzel (only for non-Image)
    if content_type != "image" and idx < len(remaining) and remaining[idx]:
        result["text_kuerzel"] = remaining[idx]
        idx += 1
    
    # Visual (only for non-Image)
    if content_type != "image" and idx < len(remaining) and remaining[idx]:
        result["visual"] = remaining[idx]
        idx += 1
    
    # Angle
    if idx < len(remaining) and remaining[idx]:
        result["angle"] = remaining[idx]
        idx += 1
    
    # Gender
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val in ("M", "F", "D", "U"):
            result["gender"] = val
            idx += 1
    
    # Test IDs
    if idx < len(remaining) and remaining[idx]:
        result["test_ids"] = remaining[idx]
        idx += 1
    
    # Launch Year + Week
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val and val != "#ERROR!":
            result["launch_year_week"] = val
        idx += 1
    
    # Original Creative ID
    if idx < len(remaining) and remaining[idx]:
        result["original_creative_id"] = remaining[idx]
        idx += 1
    
    # Additional Infos / Schema M ID
    if idx < len(remaining) and remaining[idx]:
        result["additional_infos"] = remaining[idx]
        idx += 1
    
    # Free Text
    if idx < len(remaining) and remaining[idx]:
        result["free_text"] = remaining[idx]
        idx += 1
    
    # Check for AI flag anywhere in remaining parts
    if "AI" in remaining:
        result["is_ai"] = True
    
    # Ad Group Number (often last)
    if idx < len(remaining) and remaining[idx]:
        result["ad_group_number"] = remaining[idx]
        idx += 1

    return result


def _parse_schema_2(result: dict, remaining: list[str]) -> dict:
    """
    Parse Schema 2 (external agencies) optional fields.
    
    Order: PL/EG/SP(-Color), TestIDs, VisualCT, CreatorCluster,
           Gender, TextEdit, TextAlign, ImageType, CopyCluster,
           Element, LaunchWeek, OriginalCreativeID, AdditionalInfos,
           Zusatzfeld, FreeText, AdGroupNumber
    """
    result["raw_suffix"] = "_".join(remaining)
    
    idx = 0
    
    # PL/EG/SP (may include color via hyphen: PL-SOC-Rot)
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val.startswith(("PL-", "PL", "EG", "SP")):
            # Check for color suffix via hyphen
            if "-" in val:
                parts_hyphen = val.split("-")
                if len(parts_hyphen) >= 3:
                    result["pl_eg_sp"] = "-".join(parts_hyphen[:2])
                    result["color"] = "-".join(parts_hyphen[2:])
                else:
                    result["pl_eg_sp"] = val
            else:
                result["pl_eg_sp"] = val
            idx += 1
    
    # Test IDs
    if idx < len(remaining) and remaining[idx]:
        result["test_ids"] = remaining[idx]
        idx += 1
    
    # Visual CT (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["visual_ct"] = remaining[idx]
        idx += 1
    
    # Creator Cluster (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["creator_cluster"] = remaining[idx]
        idx += 1
    
    # Gender
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val in ("M", "F", "D", "U"):
            result["gender"] = val
            idx += 1
    
    # Text Edit (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["text_edit"] = remaining[idx]
        idx += 1
    
    # Text Align (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["text_align"] = remaining[idx]
        idx += 1
    
    # Image Type (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["image_type"] = remaining[idx]
        idx += 1
    
    # Copy Cluster
    if idx < len(remaining) and remaining[idx]:
        result["copy_cluster"] = remaining[idx]
        idx += 1
    
    # Element (Kürzel)
    if idx < len(remaining) and remaining[idx]:
        result["element"] = remaining[idx]
        idx += 1
    
    # Launch Year + Week
    if idx < len(remaining) and remaining[idx]:
        val = remaining[idx]
        if val and val != "#ERROR!":
            result["launch_year_week"] = val
        idx += 1
    
    # Original Creative ID
    if idx < len(remaining) and remaining[idx]:
        result["original_creative_id"] = remaining[idx]
        idx += 1
    
    # Additional Infos
    if idx < len(remaining) and remaining[idx]:
        result["additional_infos"] = remaining[idx]
        idx += 1
    
    # Zusatzfeld
    if idx < len(remaining) and remaining[idx]:
        result["zusatzfeld"] = remaining[idx]
        idx += 1
    
    # Free Text
    if idx < len(remaining) and remaining[idx]:
        result["free_text"] = remaining[idx]
        idx += 1
    
    # Ad Group Number
    if idx < len(remaining) and remaining[idx]:
        result["ad_group_number"] = remaining[idx]
        idx += 1

    return result


def _parse_schema_3(result: dict, remaining: list[str]) -> dict:
    """
    Parse Schema 3 (fallback / minimal).
    Only PL/EG/SP and TestIDs after core fields.
    """
    result["raw_suffix"] = "_".join(remaining)
    
    idx = 0
    
    # PL/EG/SP
    if idx < len(remaining) and remaining[idx]:
        result["pl_eg_sp"] = remaining[idx]
        idx += 1
    
    # Test IDs
    if idx < len(remaining) and remaining[idx]:
        result["test_ids"] = remaining[idx]
        idx += 1

    return result
