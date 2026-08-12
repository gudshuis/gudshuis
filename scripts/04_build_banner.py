"""Assemble the full banner: terminal window, VISUAL.MAP orbit panel,
SYSTEM.INFO readout, LIVE badge, and handle pill.

VISUAL.MAP previously held a dithered self-portrait that crossfaded with
a small logo loop; that panel now embeds the static engineering-orbit.svg
skills graphic instead, clipped to the same frame.

Usage: python 04_build_banner.py --mode dark|light --out banner-dark.svg
"""
import argparse
import base64
import mimetypes
import os

WIDTH, HEIGHT = 1180, 610
PORTRAIT_BOX = (40, 90, 448, 560)  # x0,y0,x1,y1 inside the window

PALETTE = {
    "dark": {
        "bg": "#0A101F",
        "window": "#0d1117",
        "border": "#30363d",
        "portrait": "#39D353",
        "portrait_bg": "#0A101F",
        "chrome": "#39D353",
        "chrome2": "#2EA043",
        "accent": "#2EA043",
        "text": "#c9d1d9",
        "label": "#39d353",
        "muted": "#30363d",
    },
    "light": {
        "bg": "#FFFFFF",
        "window": "#f6f8fa",
        "border": "#d0d7de",
        "portrait": "#15803D",
        "portrait_bg": "#FFFFFF",
        "chrome": "#15803D",
        "chrome2": "#15803D",
        "accent": "#15803D",
        "text": "#24292f",
        "label": "#15803D",
        "muted": "#d0d7de",
    },
}

FIELDS = [
    ("Subject", "Arun Malve"),
    ("Role", "AI / Cloud / Platform / DevSecOps Engineer"),
    ("Origin", "London, UK"),
    ("Education", "Master's (Advanced Computers)"),
    ("Status", "Building + Learning + Shipping"),
    ("ToolChain", "kubectl - Terraform - VS Code - Git"),
    ("Core.Lang", "Python - Bash - PowerShell - YAML"),
    ("Core.IaC", "Terraform - Pulumi - Ansible"),
    ("Core.CI/CD", "GitHub Actions - Azure DevOps - ArgoCD"),
    ("Core.Infra", "Kubernetes - Docker - Proxmox - Istio"),
    ("Core.AI", "MCP - RAG - LLM Agents - Claude"),
    ("Grid.Mail", "arundilse@gmail.com"),
    ("Grid.LinkedIn", "/in/arunmalve"),
    ("Grid.YouTube", "@gudshuis"),
    ("Grid.Instagram", "@malve_"),
    ("Grid.Medium", "@gudshuis"),
]

HANDLE = "@gudshuis"

ROW_FONT = 17
HEADER_FONT = 16
ROW_SPACING = 28
CHAR_W = ROW_FONT * 0.521  # approx monospace advance ratio


def data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        mime = "image/svg+xml" if path.endswith(".svg") else "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_orbit_panel(box) -> str:
    x0, y0, x1, y1 = box
    box_w, box_h = x1 - x0, y1 - y0
    uri = data_uri("assets/engineering-orbit.svg")
    return (
        f'<clipPath id="orbitClip"><rect x="{x0}" y="{y0}" width="{box_w}" '
        f'height="{box_h}" rx="6"/></clipPath>'
        f'<image x="{x0}" y="{y0}" width="{box_w}" height="{box_h}" '
        f'href="{uri}" preserveAspectRatio="xMidYMid slice" '
        f'clip-path="url(#orbitClip)"/>'
    )


def build_info_panel(pal: dict, panel_box) -> str:
    x0, y0, x1, y1 = panel_box
    panel_w = x1 - x0
    parts = [f'<text x="{x0}" y="{y0}" font-size="{HEADER_FONT}" fill="{pal["label"]}" '
             f'font-family="SFMono-Regular, Consolas, monospace" font-weight="600">SYSTEM.INFO</text>']
    parts.append(f'<line x1="{x0}" y1="{y0+8}" x2="{x1}" y2="{y0+8}" stroke="{pal["muted"]}"/>')

    top = y0 + 62
    for i, (label, value) in enumerate(FIELDS):
        y = top + i * ROW_SPACING
        label_w = len(label) * CHAR_W * 0.62
        value_w_est = min(len(value) * CHAR_W * 0.62, panel_w * 0.62)
        label_end = x0 + label_w + 4
        value_start = x1 - value_w_est
        esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;")
        parts.append(
            f'<text x="{x0}" y="{y}" font-size="{ROW_FONT}" fill="{pal["label"]}" '
            f'font-family="SFMono-Regular, Consolas, monospace">{esc(label)}</text>'
        )
        if value_start > label_end + 6:
            parts.append(
                f'<line x1="{label_end:.1f}" y1="{y-4}" x2="{value_start-6:.1f}" y2="{y-4}" '
                f'stroke="{pal["muted"]}" stroke-dasharray="1,3"/>'
            )
        # Same font-family/size/weight as the label — no textLength squeeze,
        # which was distorting/dimming the glyphs on some SVG renderers.
        parts.append(
            f'<text x="{x1}" y="{y}" font-size="{ROW_FONT}" fill="{pal["text"]}" '
            f'font-family="SFMono-Regular, Consolas, monospace" '
            f'text-anchor="end">{esc(value)}</text>'
        )
    return "\n".join(parts)


def build_banner(mode: str) -> str:
    pal = PALETTE[mode]

    orbit_svg = build_orbit_panel(PORTRAIT_BOX)

    info_panel_box = (500, 60, WIDTH - 40, HEIGHT - 40)
    info_svg = build_info_panel(pal, info_panel_box)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">',
        f'<rect width="100%" height="100%" rx="14" fill="{pal["window"]}" '
        f'stroke="{pal["border"]}" stroke-width="1.5"/>',
        # title bar
        f'<rect x="0" y="0" width="{WIDTH}" height="44" rx="14" fill="{pal["window"]}"/>',
        f'<rect x="0" y="30" width="{WIDTH}" height="14" fill="{pal["window"]}"/>',
        f'<line x1="0" y1="44" x2="{WIDTH}" y2="44" stroke="{pal["border"]}"/>',
        f'<circle cx="26" cy="22" r="6" fill="#ff5f56"/>',
        f'<circle cx="46" cy="22" r="6" fill="#ffbd2e"/>',
        f'<circle cx="66" cy="22" r="6" fill="#27c93f"/>',
        f'<text x="{WIDTH/2}" y="27" font-size="13" fill="{pal["text"]}" '
        f'font-family="SFMono-Regular, Consolas, monospace" text-anchor="middle">'
        f'profile.sh --live</text>',
        # portrait frame
        f'<rect x="{PORTRAIT_BOX[0]-4}" y="{PORTRAIT_BOX[1]-4}" '
        f'width="{PORTRAIT_BOX[2]-PORTRAIT_BOX[0]+8}" height="{PORTRAIT_BOX[3]-PORTRAIT_BOX[1]+8}" '
        f'rx="8" fill="{pal["portrait_bg"]}" stroke="{pal["chrome"]}" stroke-width="1.5"/>',
        f'<text x="{PORTRAIT_BOX[0]}" y="{PORTRAIT_BOX[1]-14}" font-size="{HEADER_FONT}" '
        f'fill="{pal["chrome"]}" font-family="SFMono-Regular, Consolas, monospace" '
        f'font-weight="600">VISUAL.MAP</text>',
        orbit_svg,
        # LIVE badge
        f'<circle cx="{WIDTH-150}" cy="66" r="4" fill="#ef4444">'
        f'<animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/>'
        f'</circle>',
        f'<text x="{WIDTH-140}" y="70" font-size="12" fill="#ef4444" '
        f'font-family="SFMono-Regular, Consolas, monospace" font-weight="600">LIVE</text>',
        # handle pill
        f'<rect x="{WIDTH-40-11*CHAR_W}" y="80" width="{11*CHAR_W+20:.1f}" height="24" rx="12" '
        f'fill="{pal["accent"]}" opacity="0.15" stroke="{pal["accent"]}"/>',
        f'<text x="{WIDTH-40-11*CHAR_W/2-10:.1f}" y="96" font-size="13" fill="{pal["accent"]}" '
        f'font-family="SFMono-Regular, Consolas, monospace" text-anchor="middle" '
        f'font-weight="600">{HANDLE}</text>',
        info_svg,
        "</svg>",
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dark", "light"], required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    svg = build_banner(args.mode)
    with open(args.out, "w") as f:
        f.write(svg)
    size_kb = os.path.getsize(args.out) / 1024
    print(f"wrote {args.out} ({size_kb:.0f} KB)")
