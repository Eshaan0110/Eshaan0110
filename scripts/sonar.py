import requests
import os
import math
import random
from datetime import datetime

USERNAME = "Eshaan0110"
TOKEN = os.environ["GITHUB_TOKEN"]

query = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

headers = {"Authorization": f"Bearer {TOKEN}"}
response = requests.post(
    "https://api.github.com/graphql",
    json={"query": query, "variables": {"login": USERNAME}},
    headers=headers
)
data = response.json()
weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
total = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

days = []
for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)

active_days = [d for d in days if d["contributionCount"] > 0]
max_commits = max((d["contributionCount"] for d in active_days), default=1)

# Current streak
streak = 0
today = datetime.utcnow().date()
for day in reversed(days):
    d = datetime.strptime(day["date"], "%Y-%m-%d").date()
    if d > today:
        continue
    if day["contributionCount"] > 0:
        streak += 1
    else:
        break

# Place each active day as a ping on the radar
# Days spread across the full circle, radius = normalized commit count
WIDTH = 520
HEIGHT = 520
CX = WIDTH // 2
CY = HEIGHT // 2
R = 210  # radar radius

pings = []
total_days = len(days)
for i, day in enumerate(days):
    if day["contributionCount"] == 0:
        continue
    angle = (i / total_days) * 2 * math.pi - math.pi / 2
    norm = day["contributionCount"] / max_commits
    # Scatter radius between 60% and 95% of R based on commit count
    radius = R * (0.35 + norm * 0.60)
    # Slight random jitter per day for organic feel
    rng = random.Random(day["date"])
    jitter_r = rng.uniform(-8, 8)
    jitter_a = rng.uniform(-0.04, 0.04)
    final_r = max(20, radius + jitter_r)
    final_a = angle + jitter_a
    x = CX + final_r * math.cos(final_a)
    y = CY + final_r * math.sin(final_a)
    count = day["contributionCount"]
    dot_size = round(1.5 + (count / max_commits) * 4.5, 2)
    # Color intensity
    if count >= max_commits * 0.75:
        color = "#00ff88"
        glow = "glow_bright"
    elif count >= max_commits * 0.4:
        color = "#00cc66"
        glow = "glow_mid"
    else:
        color = "#009944"
        glow = "glow_dim"
    # sweep angle for this ping (in degrees, for CSS animation delay)
    sweep_deg = round(math.degrees(angle + math.pi / 2) % 360, 1)
    pings.append((x, y, dot_size, color, glow, sweep_deg, count, day["date"]))

timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}">
<!-- Sonar Contribution Radar — {timestamp} -->
<defs>
  <!-- Deep dark background gradient -->
  <radialGradient id="bgGrad" cx="50%" cy="50%" r="50%">
    <stop offset="0%" style="stop-color:#001a0e;stop-opacity:1"/>
    <stop offset="70%" style="stop-color:#000d07;stop-opacity:1"/>
    <stop offset="100%" style="stop-color:#000000;stop-opacity:1"/>
  </radialGradient>

  <!-- Radar sweep gradient -->
  <radialGradient id="sweepGrad" cx="50%" cy="50%" r="50%">
    <stop offset="0%" style="stop-color:#00ff66;stop-opacity:0.18"/>
    <stop offset="100%" style="stop-color:#00ff66;stop-opacity:0"/>
  </radialGradient>

  <!-- Clip to circle -->
  <clipPath id="radarClip">
    <circle cx="{CX}" cy="{CY}" r="{R}"/>
  </clipPath>

  <!-- Glow filters -->
  <filter id="glow_bright" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow_mid" x="-80%" y="-80%" width="260%" height="260%">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow_dim" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="1.2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="screenGlow" x="-10%" y="-10%" width="120%" height="120%">
    <feGaussianBlur stdDeviation="8" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="textGlow">
    <feGaussianBlur stdDeviation="2" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>

  <!-- Scanline texture -->
  <pattern id="scanlines" x="0" y="0" width="2" height="2" patternUnits="userSpaceOnUse">
    <rect width="2" height="1" fill="rgba(0,0,0,0.08)"/>
  </pattern>
</defs>

<!-- Outer bezel -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="#000"/>
<circle cx="{CX}" cy="{CY}" r="{R + 22}" fill="#0a0a0a" stroke="#003322" stroke-width="3"/>
<circle cx="{CX}" cy="{CY}" r="{R + 14}" fill="#050f09" stroke="#004433" stroke-width="2"/>
<circle cx="{CX}" cy="{CY}" r="{R + 6}" fill="#000d07" stroke="#005544" stroke-width="1.5"/>

<!-- Radar background -->
<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#bgGrad)"/>

<!-- Grid rings -->
'''

for ring in [0.25, 0.5, 0.75, 1.0]:
    r_val = R * ring
    opacity = 0.12 if ring < 1.0 else 0.25
    svg += f'<circle cx="{CX}" cy="{CY}" r="{r_val:.1f}" fill="none" stroke="#00ff66" stroke-width="0.8" opacity="{opacity}"/>\n'

# Cross hairs
svg += f'''
<line x1="{CX}" y1="{CY - R}" x2="{CX}" y2="{CY + R}" stroke="#00ff66" stroke-width="0.6" opacity="0.15"/>
<line x1="{CX - R}" y1="{CY}" x2="{CX + R}" y2="{CY}" stroke="#00ff66" stroke-width="0.6" opacity="0.15"/>
<line x1="{CX - R*0.707:.1f}" y1="{CY - R*0.707:.1f}" x2="{CX + R*0.707:.1f}" y2="{CY + R*0.707:.1f}" stroke="#00ff66" stroke-width="0.4" opacity="0.08"/>
<line x1="{CX + R*0.707:.1f}" y1="{CY - R*0.707:.1f}" x2="{CX - R*0.707:.1f}" y2="{CY + R*0.707:.1f}" stroke="#00ff66" stroke-width="0.4" opacity="0.08"/>
'''

# Ping dots with fade animation
svg += '\n<!-- Contribution pings -->\n'
SWEEP_DURATION = 6  # seconds per full rotation

for (x, y, size, color, glow, sweep_deg, count, date) in pings:
    # Each dot fades in when sweep passes it, then slowly decays
    delay = round((sweep_deg / 360) * SWEEP_DURATION, 2)
    fade_dur = round(SWEEP_DURATION * 0.85, 2)
    # Outer halo
    svg += f'''<circle cx="{x:.1f}" cy="{y:.1f}" r="{size*2:.1f}" fill="{color}" opacity="0" clip-path="url(#radarClip)" filter="url(#{glow})">
  <animate attributeName="opacity" values="0;0.18;0" dur="{SWEEP_DURATION}s" begin="{delay}s" repeatCount="indefinite"/>
</circle>
'''
    # Core dot
    svg += f'''<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{color}" opacity="0" clip-path="url(#radarClip)" filter="url(#{glow})">
  <animate attributeName="opacity" values="0;0.9;0.4;0" dur="{SWEEP_DURATION}s" begin="{delay}s" repeatCount="indefinite"/>
</circle>
'''

# Sweep arm — rotates full 360 every SWEEP_DURATION seconds
svg += f'''
<!-- Sweep arm -->
<g clip-path="url(#radarClip)">
  <g transform-origin="{CX} {CY}">
    <animateTransform attributeName="transform" type="rotate"
      from="0 {CX} {CY}" to="360 {CX} {CY}"
      dur="{SWEEP_DURATION}s" repeatCount="indefinite"/>
    <!-- Trailing glow wedge -->
    <path d="M{CX},{CY} L{CX},{CY - R} A{R},{R} 0 0,1 {CX + R*math.sin(math.radians(25)):.1f},{CY - R*math.cos(math.radians(25)):.1f} Z"
      fill="url(#sweepGrad)" opacity="0.7"/>
    <!-- Sweep line -->
    <line x1="{CX}" y1="{CY}" x2="{CX}" y2="{CY - R}"
      stroke="#00ff66" stroke-width="1.5" opacity="0.9"/>
    <!-- Sweep tip glow -->
    <circle cx="{CX}" cy="{CY - R + 4}" r="3" fill="#00ff88" opacity="0.6" filter="url(#glow_bright)"/>
  </g>
</g>

<!-- Center dot -->
<circle cx="{CX}" cy="{CY}" r="4" fill="#00ff66" filter="url(#glow_bright)" opacity="0.9"/>
<circle cx="{CX}" cy="{CY}" r="2" fill="#ffffff" opacity="0.8"/>

<!-- Scanlines overlay -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scanlines)" opacity="0.4"/>

<!-- Outer ring border -->
<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#00ff66" stroke-width="1.5" opacity="0.4"/>
'''

# Degree labels
for deg, label in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
    angle_rad = math.radians(deg - 90)
    lx = CX + (R + 16) * math.cos(angle_rad)
    ly = CY + (R + 16) * math.sin(angle_rad)
    svg += f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="monospace" font-size="10" fill="#00aa44" opacity="0.6" text-anchor="middle" dominant-baseline="middle">{label}</text>\n'

# Stats text
svg += f'''
<!-- Stats readout -->
<text x="18" y="30" font-family="\'Courier New\', monospace" font-size="9" fill="#00ff66" opacity="0.7" filter="url(#textGlow)">SONAR ACTIVE</text>
<text x="18" y="44" font-family="\'Courier New\', monospace" font-size="8" fill="#00cc55" opacity="0.55">USER: {USERNAME}</text>
<text x="18" y="57" font-family="\'Courier New\', monospace" font-size="8" fill="#00cc55" opacity="0.55">COMMITS: {total}</text>
<text x="18" y="70" font-family="\'Courier New\', monospace" font-size="8" fill="#00cc55" opacity="0.55">STREAK: {streak}d</text>
<text x="18" y="83" font-family="\'Courier New\', monospace" font-size="8" fill="#00cc55" opacity="0.55">PINGS: {len(pings)}</text>

<!-- Bottom timestamp -->
<text x="{WIDTH - 10}" y="{HEIGHT - 10}" font-family="\'Courier New\', monospace" font-size="7" fill="#004422" opacity="0.5" text-anchor="end">{timestamp}</text>

<!-- Blinking cursor -->
<rect x="18" y="90" width="6" height="9" fill="#00ff66" opacity="0.7">
  <animate attributeName="opacity" values="0.7;0;0.7" dur="1s" repeatCount="indefinite"/>
</rect>

</svg>'''

os.makedirs("dist", exist_ok=True)
with open("dist/sonar.svg", "w") as f:
    f.write(svg)

print(f"Done! {len(pings)} pings, {streak} day streak, {total} total commits.")
