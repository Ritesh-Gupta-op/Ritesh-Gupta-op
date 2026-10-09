"""Render the real contribution calendar as a self-contained dark SVG."""

import argparse
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


NS = "http://www.w3.org/2000/svg"
PALETTE = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")
ET.register_namespace("", NS)


def element(parent, tag, **attributes):
    return ET.SubElement(parent, f"{{{NS}}}{tag}", {
        key.replace("_", "-"): str(value) for key, value in attributes.items()
    })


def render(source, username):
    calendar = ET.fromstring(source)
    days = calendar.findall(f".//{{{NS}}}rect[@data-date]")
    if len(days) < 300:
        raise ValueError("The upstream response does not contain a yearly calendar")

    width = int(calendar.get("width")) + 48
    height = int(calendar.get("height")) + 92
    root = ET.Element(f"{{{NS}}}svg", {
        "width": str(width), "height": str(height),
        "viewBox": f"0 0 {width} {height}", "role": "img",
        "aria-labelledby": "title description",
    })
    element(root, "title", id="title").text = f"{username}'s contribution calendar"
    element(root, "desc", id="description").text = (
        "GitHub contribution activity over the last year. "
        "Brighter green dots represent higher activity."
    )
    element(root, "rect", x=0.5, y=0.5, width=width - 1, height=height - 1,
            rx=12, fill="#0d1117", stroke="#30363d")
    element(root, "text", x=24, y=30, fill="#c9d1d9",
            font_family="monospace", font_size=13).text = "/ contribution garden"
    element(root, "text", x=width - 24, y=30, fill="#8b949e",
            text_anchor="end", font_family="sans-serif", font_size=10).text = "LAST 12 MONTHS"

    grid = element(root, "g", transform="translate(24, 50)")
    for day in days:
        day_date = date.fromisoformat(day.get("data-date"))
        level = int(day.get("data-score"))
        if not 0 <= level < len(PALETTE):
            raise ValueError(f"Unexpected activity level: {level}")
        dot = element(grid, "circle", cx=int(day.get("x")) + 5,
                      cy=int(day.get("y")) + 5, r=4, fill=PALETTE[level],
                      data_date=day_date.isoformat(), data_level=level)
        element(dot, "title").text = f"{day_date.isoformat()}: activity level {level}/4"

    for label in calendar.findall(f".//{{{NS}}}text"):
        element(grid, "text", x=label.get("x"), y=label.get("y"),
                fill="#8b949e", font_family="sans-serif", font_size=9).text = label.text

    legend_y = height - 20
    element(root, "text", x=width - 151, y=legend_y + 3, fill="#8b949e",
            font_family="sans-serif", font_size=10).text = "Less"
    for level, color in enumerate(PALETTE):
        element(root, "circle", cx=width - 117 + level * 14,
                cy=legend_y, r=4, fill=color)
    element(root, "text", x=width - 48, y=legend_y + 3, fill="#8b949e",
            font_family="sans-serif", font_size=10).text = "More"

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="Ritesh-Gupta-op")
    parser.add_argument("--output", type=Path, default=Path("contributions-dark.svg"))
    args = parser.parse_args()

    request = Request(
        f"https://ghchart.rshah.org/39d353/{args.username}",
        headers={"User-Agent": "Mozilla/5.0 (GitHub profile calendar)"},
    )
    with urlopen(request, timeout=30) as response:
        svg = render(response.read(), args.username)
    # Only replace the last good calendar after the response is validated.
    args.output.write_bytes(svg)
    print(f"Updated {args.output}")


if __name__ == "__main__":
    main()
