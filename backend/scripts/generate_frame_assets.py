import os
from pathlib import Path

FRAMES = {
    "frame-rectangular.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlare" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.08"/>
    </linearGradient>
    <linearGradient id="templeShade" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0f172a" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#334155" stop-opacity="0.4"/>
    </linearGradient>
  </defs>

  <!-- Left Temple Arm (perspective rear) -->
  <path d="M 125 105 L 45 80 Q 40 78 35 85 L 30 92 Q 38 88 52 92 L 125 120 Z" fill="url(#templeShade)"/>
  <!-- Right Temple Arm (perspective rear) -->
  <path d="M 675 105 L 755 80 Q 760 78 765 85 L 770 92 Q 762 88 748 92 L 675 120 Z" fill="url(#templeShade)"/>

  <!-- Left Lens Glare & Tint -->
  <rect x="142" y="94" width="186" height="114" rx="14" fill="url(#lensGlare)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>
  <!-- Right Lens Glare & Tint -->
  <rect x="472" y="94" width="186" height="114" rx="14" fill="url(#lensGlare)" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>

  <!-- Frame Body: Acetate Rectangular -->
  <!-- Left Rim Outer -->
  <rect x="125" y="82" width="220" height="138" rx="22" ry="22" fill="none" stroke="currentColor" stroke-width="16" stroke-linejoin="round"/>
  <!-- Right Rim Outer -->
  <rect x="455" y="82" width="220" height="138" rx="22" ry="22" fill="none" stroke="currentColor" stroke-width="16" stroke-linejoin="round"/>

  <!-- Bridge -->
  <path d="M 335 128 Q 400 112 465 128 Q 400 120 335 128 Z" fill="currentColor"/>
  <path d="M 345 130 Q 400 118 455 130" fill="none" stroke="currentColor" stroke-width="12" stroke-linecap="round"/>

  <!-- End-piece Silver Rivet Accents -->
  <circle cx="118" cy="98" r="2.5" fill="#e2e8f0"/>
  <circle cx="118" cy="108" r="2.5" fill="#e2e8f0"/>
  <circle cx="682" cy="98" r="2.5" fill="#e2e8f0"/>
  <circle cx="682" cy="108" r="2.5" fill="#e2e8f0"/>

  <!-- Nose Pads / Sculpted Acetate Saddles -->
  <path d="M 342 145 Q 352 165 348 185" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
  <path d="M 458 145 Q 448 165 452 185" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
</svg>""",

    "frame-round.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareRound" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.25"/>
      <stop offset="45%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.08"/>
    </linearGradient>
    <linearGradient id="metalWire" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.4"/>
      <stop offset="50%" stop-color="currentColor"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.3"/>
    </linearGradient>
  </defs>

  <!-- Left Temple Arm -->
  <path d="M 145 140 L 50 115 Q 42 112 38 120 L 32 128 Q 42 122 55 126 L 145 152 Z" fill="#475569" opacity="0.7"/>
  <!-- Right Temple Arm -->
  <path d="M 655 140 L 750 115 Q 758 112 762 120 L 768 128 Q 758 122 745 126 L 655 152 Z" fill="#475569" opacity="0.7"/>

  <!-- Left Lens Glare -->
  <circle cx="235" cy="150" r="82" fill="url(#lensGlareRound)"/>
  <!-- Right Lens Glare -->
  <circle cx="565" cy="150" r="82" fill="url(#lensGlareRound)"/>

  <!-- Left Circular Wire Rim -->
  <circle cx="235" cy="150" r="84" fill="none" stroke="currentColor" stroke-width="8"/>
  <circle cx="235" cy="150" r="88" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>

  <!-- Right Circular Wire Rim -->
  <circle cx="565" cy="150" r="84" fill="none" stroke="currentColor" stroke-width="8"/>
  <circle cx="565" cy="150" r="88" fill="none" stroke="rgba(255,255,255,0.2)" stroke-width="1.5"/>

  <!-- Arched Keyhole Bridge -->
  <path d="M 319 146 C 350 102 450 102 481 146" fill="none" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
  <path d="M 323 150 C 355 110 445 110 477 150" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>

  <!-- Silicone Nose Pads & Arms -->
  <path d="M 325 155 Q 345 168 340 182" fill="none" stroke="currentColor" stroke-width="3"/>
  <ellipse cx="342" cy="184" rx="5" ry="9" transform="rotate(-15 342 184)" fill="rgba(255,255,255,0.7)" stroke="#94a3b8" stroke-width="1.5"/>

  <path d="M 475 155 Q 455 168 460 182" fill="none" stroke="currentColor" stroke-width="3"/>
  <ellipse cx="458" cy="184" rx="5" ry="9" transform="rotate(15 458 184)" fill="rgba(255,255,255,0.7)" stroke="#94a3b8" stroke-width="1.5"/>
</svg>""",

    "frame-semi-rimless.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareSemi" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.06"/>
    </linearGradient>
  </defs>

  <!-- Temples -->
  <path d="M 125 108 L 45 85 L 35 95 L 125 120 Z" fill="#334155" opacity="0.6"/>
  <path d="M 675 108 L 755 85 L 765 95 L 675 120 Z" fill="#334155" opacity="0.6"/>

  <!-- Left Lens -->
  <path d="M 130 115 Q 130 200 160 215 Q 235 220 310 215 Q 340 200 340 115 Z" fill="url(#lensGlareSemi)"/>
  <!-- Right Lens -->
  <path d="M 460 115 Q 460 200 490 215 Q 565 220 640 215 Q 670 200 670 115 Z" fill="url(#lensGlareSemi)"/>

  <!-- Nylon Cord Lower Suspension (Thin line) -->
  <path d="M 130 118 Q 130 200 160 215 Q 235 220 310 215 Q 340 200 340 118" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,2"/>
  <path d="M 460 118 Q 460 200 490 215 Q 565 220 640 215 Q 670 200 670 118" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="3,2"/>

  <!-- Upper Titanium Brow Bar Left -->
  <path d="M 115 105 Q 235 90 345 110 L 342 122 Q 235 102 125 118 Z" fill="currentColor"/>
  <!-- Upper Titanium Brow Bar Right -->
  <path d="M 455 110 Q 565 90 685 105 L 675 118 Q 565 102 458 122 Z" fill="currentColor"/>

  <!-- Bridge -->
  <path d="M 338 112 Q 400 98 462 112 L 460 124 Q 400 110 340 124 Z" fill="currentColor"/>

  <!-- Nose Pads -->
  <ellipse cx="350" cy="155" rx="5" ry="9" fill="rgba(255,255,255,0.7)" stroke="#64748b" stroke-width="1"/>
  <ellipse cx="450" cy="155" rx="5" ry="9" fill="rgba(255,255,255,0.7)" stroke="#64748b" stroke-width="1"/>
</svg>""",

    "frame-square.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareSquare" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.2"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.06"/>
    </linearGradient>
  </defs>

  <!-- Left Temple -->
  <path d="M 125 95 L 40 70 L 35 82 L 125 110 Z" fill="#1e293b" opacity="0.8"/>
  <!-- Right Temple -->
  <path d="M 675 95 L 760 70 L 765 82 L 675 110 Z" fill="#1e293b" opacity="0.8"/>

  <!-- Left Lens Glare -->
  <rect x="142" y="86" width="186" height="136" rx="10" fill="url(#lensGlareSquare)"/>
  <!-- Right Lens Glare -->
  <rect x="472" y="86" width="186" height="136" rx="10" fill="url(#lensGlareSquare)"/>

  <!-- Square TR90 Frame Rims -->
  <rect x="125" y="72" width="220" height="164" rx="16" fill="none" stroke="currentColor" stroke-width="18" stroke-linejoin="round"/>
  <rect x="455" y="72" width="220" height="164" rx="16" fill="none" stroke="currentColor" stroke-width="18" stroke-linejoin="round"/>

  <!-- Solid Keyhole Bridge -->
  <path d="M 335 125 Q 400 110 465 125 Q 400 120 335 125 Z" fill="currentColor"/>
  <path d="M 345 124 Q 400 115 455 124" fill="none" stroke="currentColor" stroke-width="14" stroke-linecap="round"/>

  <!-- Sculpted Nose Saddles -->
  <path d="M 342 145 Q 355 170 348 198" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
  <path d="M 458 145 Q 445 170 452 198" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
</svg>""",

    "frame-rimless.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareRimless" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.3"/>
      <stop offset="35%" stop-color="#ffffff" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.12"/>
    </linearGradient>
  </defs>

  <!-- Left Temple Arm (ultra slim wire) -->
  <path d="M 125 145 L 45 125 L 35 132 L 125 152 Z" fill="#64748b" opacity="0.6"/>
  <!-- Right Temple Arm -->
  <path d="M 675 145 L 755 125 L 765 132 L 675 152 Z" fill="#64748b" opacity="0.6"/>

  <!-- Left Rimless Oval Lens Shape -->
  <ellipse cx="235" cy="150" rx="100" ry="62" fill="url(#lensGlareRimless)" stroke="rgba(255,255,255,0.6)" stroke-width="2"/>
  <ellipse cx="235" cy="150" rx="98" ry="60" fill="none" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>

  <!-- Right Rimless Oval Lens Shape -->
  <ellipse cx="565" cy="150" rx="100" ry="62" fill="url(#lensGlareRimless)" stroke="rgba(255,255,255,0.6)" stroke-width="2"/>
  <ellipse cx="565" cy="150" rx="98" ry="60" fill="none" stroke="rgba(148,163,184,0.4)" stroke-width="1"/>

  <!-- Bridge Arch Mount -->
  <path d="M 335 148 Q 400 128 465 148" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>

  <!-- Compression Bushing & Drill Screws on Bridge -->
  <circle cx="338" cy="148" r="4" fill="currentColor"/>
  <circle cx="338" cy="148" r="2" fill="#e2e8f0"/>
  <circle cx="462" cy="148" r="4" fill="currentColor"/>
  <circle cx="462" cy="148" r="2" fill="#e2e8f0"/>

  <!-- Temporal Lug Drill Screws -->
  <circle cx="137" cy="146" r="4" fill="currentColor"/>
  <circle cx="137" cy="146" r="2" fill="#e2e8f0"/>
  <circle cx="663" cy="146" r="4" fill="currentColor"/>
  <circle cx="663" cy="146" r="2" fill="#e2e8f0"/>

  <!-- Nose Pads -->
  <ellipse cx="348" cy="172" rx="4.5" ry="8.5" fill="rgba(255,255,255,0.8)" stroke="#94a3b8" stroke-width="1"/>
  <ellipse cx="452" cy="172" rx="4.5" ry="8.5" fill="rgba(255,255,255,0.8)" stroke="#94a3b8" stroke-width="1"/>
</svg>""",

    "frame-aviator.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareAviator" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.25"/>
      <stop offset="45%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.1"/>
    </linearGradient>
  </defs>

  <!-- Temples -->
  <path d="M 130 115 L 45 92 L 35 100 L 130 125 Z" fill="#475569" opacity="0.6"/>
  <path d="M 670 115 L 755 92 L 765 100 L 670 125 Z" fill="#475569" opacity="0.6"/>

  <!-- Teardrop Lens Shapes -->
  <!-- Left Teardrop -->
  <path d="M 150 105 Q 240 95 320 105 Q 345 145 330 195 Q 290 230 220 225 Q 140 215 130 160 Q 130 125 150 105 Z" fill="url(#lensGlareAviator)"/>
  <!-- Right Teardrop -->
  <path d="M 650 105 Q 560 95 480 105 Q 455 145 470 195 Q 510 230 580 225 Q 660 215 670 160 Q 670 125 650 105 Z" fill="url(#lensGlareAviator)"/>

  <!-- Left Wire Teardrop Rim -->
  <path d="M 150 105 Q 240 95 320 105 Q 345 145 330 195 Q 290 230 220 225 Q 140 215 130 160 Q 130 125 150 105 Z" fill="none" stroke="currentColor" stroke-width="7"/>
  <!-- Right Wire Teardrop Rim -->
  <path d="M 650 105 Q 560 95 480 105 Q 455 145 470 195 Q 510 230 580 225 Q 660 215 670 160 Q 670 125 650 105 Z" fill="none" stroke="currentColor" stroke-width="7"/>

  <!-- Top Sweat Bar / Brow Bar (Distinctive Aviator Feature) -->
  <path d="M 215 92 Q 400 86 585 92" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>

  <!-- Lower Curved Bridge -->
  <path d="M 320 120 Q 400 108 480 120" fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round"/>

  <!-- Nose Pads -->
  <ellipse cx="340" cy="165" rx="5" ry="10" transform="rotate(-15 340 165)" fill="rgba(255,255,255,0.7)" stroke="#64748b" stroke-width="1.5"/>
  <ellipse cx="460" cy="165" rx="5" ry="10" transform="rotate(15 460 165)" fill="rgba(255,255,255,0.7)" stroke="#64748b" stroke-width="1.5"/>
</svg>""",

    "frame-wayfarer.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareWayfarer" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#0284c7" stop-opacity="0.08"/>
    </linearGradient>
  </defs>

  <!-- Chunky Temples -->
  <path d="M 120 100 L 40 75 Q 30 72 25 80 L 20 90 L 120 122 Z" fill="#0f172a" opacity="0.85"/>
  <path d="M 680 100 L 760 75 Q 770 72 775 80 L 780 90 L 680 122 Z" fill="#0f172a" opacity="0.85"/>

  <!-- Trapezoid Lenses (slight downward taper) -->
  <path d="M 142 95 L 328 100 L 310 205 Q 235 215 160 205 Z" fill="url(#lensGlareWayfarer)"/>
  <path d="M 472 100 L 658 95 L 640 205 Q 565 215 490 205 Z" fill="url(#lensGlareWayfarer)"/>

  <!-- Left Wayfarer Rim -->
  <path d="M 120 85 L 340 92 L 320 220 Q 235 230 145 220 Z" fill="none" stroke="currentColor" stroke-width="18" stroke-linejoin="round"/>
  <!-- Right Wayfarer Rim -->
  <path d="M 460 92 L 680 85 L 655 220 Q 565 230 480 220 Z" fill="none" stroke="currentColor" stroke-width="18" stroke-linejoin="round"/>

  <!-- Bridge -->
  <path d="M 335 118 Q 400 105 465 118 Q 400 114 335 118 Z" fill="currentColor"/>
  <path d="M 340 120 Q 400 110 460 120" fill="none" stroke="currentColor" stroke-width="14" stroke-linecap="round"/>

  <!-- Signature Horizontal Silver Diamond Studs -->
  <ellipse cx="116" cy="98" rx="6" ry="3.5" fill="#e2e8f0"/>
  <ellipse cx="684" cy="98" rx="6" ry="3.5" fill="#e2e8f0"/>

  <!-- Acetate Nose Saddles -->
  <path d="M 338 140 Q 350 165 344 190" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
  <path d="M 462 140 Q 450 165 456 190" fill="none" stroke="currentColor" stroke-width="10" stroke-linecap="round"/>
</svg>""",

    "frame-cat-eye.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <defs>
    <linearGradient id="lensGlareCatEye" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.25"/>
      <stop offset="40%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#e11d48" stop-opacity="0.08"/>
    </linearGradient>
  </defs>

  <!-- Sleek Temples -->
  <path d="M 115 88 L 40 65 L 32 75 L 115 105 Z" fill="#881337" opacity="0.7"/>
  <path d="M 685 88 L 760 65 L 768 75 L 685 105 Z" fill="#881337" opacity="0.7"/>

  <!-- Left Upswept Cat-Eye Lens -->
  <path d="M 130 92 Q 225 105 325 118 Q 330 185 285 210 Q 215 220 155 200 Q 120 155 130 92 Z" fill="url(#lensGlareCatEye)"/>
  <!-- Right Upswept Cat-Eye Lens -->
  <path d="M 670 92 Q 575 105 475 118 Q 470 185 515 210 Q 585 220 645 200 Q 680 155 670 92 Z" fill="url(#lensGlareCatEye)"/>

  <!-- Left Cat-Eye Winged Rim -->
  <path d="M 110 75 Q 225 95 335 112 Q 345 195 290 225 Q 215 235 145 212 Q 105 160 110 75 Z" fill="none" stroke="currentColor" stroke-width="16" stroke-linejoin="round"/>
  <!-- Right Cat-Eye Winged Rim -->
  <path d="M 690 75 Q 575 95 465 112 Q 455 195 510 225 Q 585 235 655 212 Q 695 160 690 75 Z" fill="none" stroke="currentColor" stroke-width="16" stroke-linejoin="round"/>

  <!-- Bridge -->
  <path d="M 330 120 Q 400 108 470 120 Q 400 114 330 120 Z" fill="currentColor"/>
  <path d="M 335 122 Q 400 112 465 122" fill="none" stroke="currentColor" stroke-width="12" stroke-linecap="round"/>

  <!-- Nose Pads -->
  <path d="M 338 140 Q 348 165 342 188" fill="none" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
  <path d="M 462 140 Q 452 165 458 188" fill="none" stroke="currentColor" stroke-width="9" stroke-linecap="round"/>
</svg>"""
}

def generate_assets():
    base_dirs = [
        Path("apps/web/public/assets/frames"),
        Path("backend/app/static/frames"),
    ]
    for d in base_dirs:
        d.mkdir(parents=True, exist_ok=True)
        for filename, content in FRAMES.items():
            file_path = d / filename
            file_path.write_text(content.strip(), encoding="utf-8")
            print(f"Generated: {file_path}")

if __name__ == "__main__":
    generate_assets()

