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

# Collect all days
days = []
for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)

# Group by month
from collections import defaultdict
monthly = defaultdict(int)
for day in days:
    month = day["date"][:7]  # YYYY-MM
    monthly[month] += day["contributionCount"]

# Get last 12 months
sorted_months = sorted(monthly.keys())[-12:]
month_commits = [monthly[m] for m in sorted_months]
month_labels = [datetime.strptime(m, "%Y-%m").strftime("%b") for m in sorted_months]
max_commits = max(month_commits) if max(month_commits) > 0 else 1

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

# SVG dimensions
WIDTH = 900
HEIGHT = 300
GROUND_Y = 240
SKY_H = GROUND_Y
BUILDING_AREA_W = WIDTH - 40
NUM_MONTHS = len(sorted_months)
SLOT_W = BUILDING_AREA_W // NUM_MONTHS

rng = random.Random(42)

def make_building(x, w, h, commits, month_label, seed):
    r = random.Random(seed)
    bx = x + 4
    bw = w - 8
    by = GROUND_Y - h
    color_choices = [
        ("#1a2a3a", "#2a3f52", "#0d1c2a"),
        ("#1a1a2e", "#2a2a45", "#0d0d1e"),
        ("#0d2618", "#1a3d26", "#081a10"),
        ("#1e1a0d", "#332d14", "#141009"),
        ("#1a0d1a", "#2e1a2e", "#100810"),
    ]
    dark, mid, shadow = r.choice(color_choices)

    svg = ""

    # Main building body
    svg += f'<rect x="{bx}" y="{by}" width="{bw}" height="{h}" fill="{dark}"/>\n'
    # Side shadow
    svg += f'<rect x="{bx}" y="{by}" width="3" height="{h}" fill="{shadow}" opacity="0.6"/>\n'
    # Top highlight
    svg += f'<rect x="{bx}" y="{by}" width="{bw}" height="2" fill="{mid}"/>\n'

    # Antenna on taller buildings
    if h > 80 and r.random() > 0.4:
        ant_x = bx + bw // 2
        ant_h = r.randint(10, 25)
        svg += f'<rect x="{ant_x - 1}" y="{by - ant_h}" width="2" height="{ant_h}" fill="{mid}"/>\n'
        # blinking light on antenna
        svg += f'''<circle cx="{ant_x}" cy="{by - ant_h}" r="2" fill="#ff4444" opacity="0.9">
  <animate attributeName="opacity" values="0.9;0.1;0.9" dur="{r.uniform(0.8,2.0):.1f}s" repeatCount="indefinite"/>
</circle>\n'''

    # Water tower on some buildings
    if h > 100 and r.random() > 0.6:
        wt_x = bx + r.randint(4, bw - 12)
        svg += f'<rect x="{wt_x}" y="{by - 14}" width="8" height="10" fill="{mid}"/>\n'
        svg += f'<rect x="{wt_x - 1}" y="{by - 16}" width="10" height="3" fill="{mid}"/>\n'
        svg += f'<rect x="{wt_x + 2}" y="{by - 4}" width="2" height="6" fill="{shadow}"/>\n'
        svg += f'<rect x="{wt_x + 5}" y="{by - 4}" width="2" height="6" fill="{shadow}"/>\n'

    # Windows
    win_cols = max(1, (bw - 6) // 7)
    win_rows = max(1, (h - 10) // 10)
    for row in range(win_rows):
        for col in range(win_cols):
            wx = bx + 4 + col * 7
            wy = by + 6 + row * 10
            if wx + 4 > bx + bw - 2:
                continue
            lit = r.random()
            if commits == 0:
                win_color = "#0a0a12"
                win_opacity = "0.3"
                anim = ""
            elif lit < 0.55:
                # lit window
                win_colors = ["#ffe566", "#ffd700", "#fffacd", "#ffeaa0", "#00ffcc", "#66ccff"]
                wc = r.choice(win_colors)
                win_color = wc
                win_opacity = str(round(r.uniform(0.6, 0.95), 2))
                if r.random() > 0.7:
                    dur = round(r.uniform(2.0, 6.0), 1)
                    anim = f'<animate attributeName="opacity" values="{win_opacity};{round(float(win_opacity)*0.2,2)};{win_opacity}" dur="{dur}s" repeatCount="indefinite"/>'
                else:
                    anim = ""
            else:
                win_color = "#050508"
                win_opacity = "0.8"
                anim = ""
            svg += f'<rect x="{wx}" y="{wy}" width="4" height="5" fill="{win_color}" opacity="{win_opacity}">{anim}</rect>\n'

    # Month label
    label_y = GROUND_Y + 14
    svg += f'<text x="{x + w//2}" y="{label_y}" font-family="\'Courier New\', monospace" font-size="8" fill="#445566" text-anchor="middle">{month_label}</text>\n'

    return svg

# Stars
def make_stars(seed, count=120):
    r = random.Random(seed)
    svg = ""
    for _ in range(count):
        sx = r.uniform(0, WIDTH)
        sy = r.uniform(0, SKY_H * 0.85)
        size = r.uniform(0.5, 1.8)
        op = round(r.uniform(0.3, 0.9), 2)
        low = round(op * 0.2, 2)
        dur = round(r.uniform(1.5, 5.0), 1)
        svg += f'''<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{size:.1f}" fill="white" opacity="{op}">
  <animate attributeName="opacity" values="{op};{low};{op}" dur="{dur}s" repeatCount="indefinite"/>
</circle>\n'''
    return svg

# Moon
def make_moon():
    mx, my = 820, 45
    return f'''
<circle cx="{mx}" cy="{my}" r="22" fill="#fffde0" opacity="0.92"/>
<circle cx="{mx + 7}" cy="{my - 5}" r="18" fill="#0a0a18"/>
<circle cx="{mx}" cy="{my}" r="22" fill="none" stroke="#fffde0" stroke-width="1" opacity="0.3"/>
'''

# Ground / road
def make_ground():
    svg = ""
    # Ground
    svg += f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="{HEIGHT - GROUND_Y}" fill="#070710"/>\n'
    # Road
    svg += f'<rect x="0" y="{GROUND_Y + 8}" width="{WIDTH}" height="18" fill="#0d0d18"/>\n'
    # Road dashes
    for i in range(0, WIDTH, 28):
        svg += f'<rect x="{i}" y="{GROUND_Y + 16}" width="14" height="2" fill="#222233" opacity="0.8"/>\n'
    # Sidewalk
    svg += f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="8" fill="#0f0f1e"/>\n'
    # Reflection on ground
    svg += f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="4" fill="#1a1a3a" opacity="0.4"/>\n'
    return svg

# Moving cars
def make_cars():
    svg = ""
    cars = [
        {"color": "#ff4444", "speed": "8s", "y": GROUND_Y + 11, "w": 14, "h": 5},
        {"color": "#ffff44", "speed": "13s", "y": GROUND_Y + 17, "w": 12, "h": 4},
        {"color": "#4444ff", "speed": "18s", "y": GROUND_Y + 11, "w": 14, "h": 5},
    ]
    for i, car in enumerate(cars):
        cx = car["w"]
        cy = car["y"]
        cw = car["w"]
        ch = car["h"]
        # headlights
        svg += f'''<g opacity="0.9">
  <rect x="0" y="{cy}" width="{cw}" height="{ch}" fill="{car["color"]}">
    <animateTransform attributeName="transform" type="translate"
      from="-20 0" to="{WIDTH + 20} 0"
      dur="{car["speed"]}" repeatCount="indefinite" begin="{i * 2.5}s"/>
  </rect>
  <rect x="{cw - 3}" y="{cy + 1}" width="3" height="2" fill="#ffffaa" opacity="0.9">
    <animateTransform attributeName="transform" type="translate"
      from="-20 0" to="{WIDTH + 20} 0"
      dur="{car["speed"]}" repeatCount="indefinite" begin="{i * 2.5}s"/>
  </rect>
</g>\n'''
    return svg

# Pixel person walking
def make_walker():
    px = 60
    py = GROUND_Y - 8
    svg = f'''<g>
  <animateTransform attributeName="transform" type="translate"
    from="-10 0" to="{WIDTH + 10} 0"
    dur="20s" repeatCount="indefinite"/>
  <!-- body -->
  <rect x="{px}" y="{py}" width="4" height="6" fill="#00cc88"/>
  <!-- head -->
  <rect x="{px}" y="{py - 4}" width="4" height="4" fill="#ffcc99"/>
  <!-- legs alternating -->
  <rect x="{px}" y="{py + 6}" width="2" height="3" fill="#335577">
    <animate attributeName="height" values="3;1;3" dur="0.4s" repeatCount="indefinite"/>
  </rect>
  <rect x="{px + 2}" y="{py + 6}" width="2" height="3" fill="#335577">
    <animate attributeName="height" values="1;3;1" dur="0.4s" repeatCount="indefinite"/>
  </rect>
</g>'''
    return svg

timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}">
<!-- Pixel City Skyline — {timestamp} -->
<defs>
  <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" style="stop-color:#020208;stop-opacity:1"/>
    <stop offset="60%" style="stop-color:#050514;stop-opacity:1"/>
    <stop offset="100%" style="stop-color:#0a0a20;stop-opacity:1"/>
  </linearGradient>
  <filter id="cityGlow" x="-5%" y="-5%" width="110%" height="110%">
    <feGaussianBlur stdDeviation="1.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <!-- Scanlines -->
  <pattern id="scanlines" x="0" y="0" width="1" height="2" patternUnits="userSpaceOnUse">
    <rect width="1" height="1" fill="rgba(0,0,0,0.06)"/>
  </pattern>
</defs>

<!-- Sky -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#skyGrad)"/>

<!-- Stars -->
{make_stars(99)}

<!-- Moon -->
{make_moon()}

<!-- City glow on horizon -->
<ellipse cx="{WIDTH//2}" cy="{GROUND_Y}" rx="400" ry="30" fill="#001a33" opacity="0.5"/>

'''

# Buildings
for i, (label, commits) in enumerate(zip(month_labels, month_commits)):
    slot_x = 20 + i * SLOT_W
    # Height proportional to commits, min 20px, max 180px
    if commits == 0:
        bh = 15
    else:
        bh = int(20 + (commits / max_commits) * 160)
    # Vary building width slightly
    bw = SLOT_W
    svg += make_building(slot_x, bw, bh, commits, label, seed=i * 137 + 42)

# Ground, road, cars, walker
svg += make_ground()
svg += make_cars()
svg += make_walker()

# Stats overlay bottom right
svg += f'''
<!-- Stats -->
<text x="{WIDTH - 12}" y="{GROUND_Y - 10}" font-family="\'Courier New\', monospace" font-size="8" fill="#334455" text-anchor="end" opacity="0.8">{total} commits · {streak}d streak · {timestamp}</text>

<!-- Scanlines -->
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scanlines)" opacity="0.5"/>

<!-- Pixel border -->
<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="none" stroke="#0d1a2a" stroke-width="3"/>
</svg>'''

os.makedirs("dist", exist_ok=True)
with open("dist/city.svg", "w") as f:
    f.write(svg)

print(f"Done! {NUM_MONTHS} buildings, {total} total commits, {streak} day streak.")
