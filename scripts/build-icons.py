from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

TILE = """<svg xmlns="http://www.w3.org/2000/svg" width="130" height="130" viewBox="0 0 130 130" font-family="Tahoma, Verdana, Segoe UI, sans-serif">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2f7de1"/><stop offset="1" stop-color="#6fb2f2"/>
    </linearGradient>
    <filter id="s"><feDropShadow dx="1" dy="1" stdDeviation="0.6" flood-color="#000" flood-opacity=".8"/></filter>
  </defs>
  <rect width="130" height="130" fill="url(#sky)"/>
  <path d="M0 112q40-18 80-6t50-2v26H0z" fill="#3f9b3a"/>
  <g transform="translate(33 18)" filter="url(#s)">{art}</g>
  <text x="65" y="104" font-size="12" fill="#fff" text-anchor="middle" filter="url(#s)">{label}</text>
</svg>
"""

ICONS = {
    "icon-uncached": ("Uncached",
        '<rect width="64" height="64" rx="12" fill="#f5c518"/>'
        '<path d="M18 20h28M22 20l3 30h14l3-30M28 14h8" stroke="#14140f" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
    "icon-core": ("uncached-core",
        '<path d="M32 2l28 14v32L32 62 4 48V16z" fill="#c97a3a" stroke="#5b3010" stroke-width="2"/>'
        '<path d="M4 16l28 14 28-14M32 30v32" stroke="#5b3010" stroke-width="2" fill="none"/>'
        '<text x="44" y="50" font-size="14" font-weight="bold" fill="#fff" text-anchor="middle">rs</text>'),
    "icon-desktop": ("uncached-desktop",
        '<rect x="2" y="4" width="60" height="42" rx="4" fill="#dfe6ef" stroke="#2b3a55" stroke-width="2"/>'
        '<rect x="8" y="10" width="48" height="30" fill="#14140f"/>'
        '<rect x="12" y="15" width="22" height="5" fill="#f5c518"/><rect x="12" y="24" width="36" height="3" fill="#f5f3e8"/>'
        '<rect x="12" y="31" width="28" height="3" fill="#f5f3e8"/>'
        '<path d="M24 46h16l3 10H21z" fill="#9aa7b8"/><rect x="16" y="56" width="32" height="4" rx="2" fill="#2b3a55"/>'),
    "icon-website": ("uncached.app",
        '<circle cx="32" cy="32" r="28" fill="#3b8fe0" stroke="#0b3f8a" stroke-width="2"/>'
        '<path d="M10 22c10 4 14 0 20 6s-4 12 4 16 4 12 0 14M40 6c-4 8 6 10 2 18s10 6 16 2" fill="#4caf50" stroke="#2e7d32" stroke-width="1.5"/>'
        '<ellipse cx="32" cy="32" rx="12" ry="28" fill="none" stroke="#fff" stroke-opacity=".5"/>'),
    "icon-portfolio": ("natanviana.dev",
        '<path d="M2 14h22l6 6h32v38H2z" fill="#f2c94c" stroke="#a6801a" stroke-width="2"/>'
        '<rect x="2" y="24" width="60" height="34" fill="#f7d96b" stroke="#a6801a" stroke-width="2"/>'
        '<text x="32" y="48" font-size="15" font-weight="bold" fill="#6b4f00" text-anchor="middle">&lt;/&gt;</text>'),
    "icon-ri7": ("RI7 Consultoria",
        '<rect x="4" y="18" width="56" height="40" rx="5" fill="#7a4b2a" stroke="#3d220f" stroke-width="2"/>'
        '<path d="M22 18v-6h20v6" stroke="#3d220f" stroke-width="4" fill="none"/>'
        '<rect x="4" y="32" width="56" height="4" fill="#3d220f"/><rect x="28" y="29" width="8" height="10" rx="1" fill="#e6c27a"/>'),
}

for name, (label, art) in ICONS.items():
    (OUT / f"{name}.svg").write_text(TILE.format(label=label, art=art))
