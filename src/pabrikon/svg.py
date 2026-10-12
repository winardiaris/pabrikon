from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(frozen=True)
class SvgCheck:
    error: str | None = None
    has_viewbox: bool = False


def parse_svg(path: Path) -> ET.ElementTree:
    """Parse an SVG document while blocking external entity resolution."""
    # Python's bundled expat (>= 2.4.1) limits entity expansion, and
    # ElementTree never fetches external entities.
    return ET.parse(path)


def check_svg(path: Path) -> SvgCheck:
    """Check SVG readability and report whether a scalable viewBox is present."""
    try:
        root = parse_svg(path).getroot()
    except ET.ParseError as exc:
        return SvgCheck(error=f"invalid SVG XML: {exc}")
    if root.tag == "svg":
        return SvgCheck(error=f'root <svg> element is missing xmlns="{SVG_NS}"')
    if root.tag != f"{{{SVG_NS}}}svg":
        return SvgCheck(error=f"root element is {root.tag!r}, not an SVG <svg> element")
    return SvgCheck(has_viewbox="viewBox" in root.attrib)
