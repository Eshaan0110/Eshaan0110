import requests
import os
import math
import random
from datetime import datetime, timedelta
from collections import defaultdict

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

streak = 0
today = datetime.now().date()
for day in reversed(days):
    d = datetime.strptime(day["date"], "%Y-%m-%d").date()
    if d > today:
        continue
    if day["contributionCount"] > 0:
        streak += 1
    else:
        break

monthly = defaultdict(list)
for day in days:
    monthly[day["date"][:7]].append(day)
months = sorted(monthly.keys())[-7:]

WIDTH = 900
HEIGHT = 340
GROUND_Y = 258
ROAD_Y = GROUND_Y + 8
ROAD_H = 22
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

defs = f'''<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" style="stop-color:#0f0225"/>
    <stop offset="30%" style="stop-color:#3d0860"/>
    <stop offset="58%" style="stop-color:#7a1060"/>
    <stop offset="78%" style="stop-color:#c43a1a"/>
    <stop offset="100%" style="stop-color:#e8720a;stop-opacity:0.7"/>
  </linearGradient>
  <radialGradient id="sunGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" style="stop-color:#fff0a0;stop-opacity:1"/>
    <stop offset="35%" style="stop-color:#ff9900;stop-opacity:0.7"/>
    <stop offset="100%" style="stop-color:#660000;stop-opacity:0"/>
  </radialGradient>
  <radialGradient id="sunCore" cx="50%" cy="50%" r="50%">
    <stop offset="0%" style="stop-color:#ffffff"/>
    <stop offset="45%" style="stop-color:#ffe566"/>
    <stop offset="100%" style="stop-color:#ff8800"/>
  </radialGradient>
  <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" style="stop-color:#080118"/>
    <stop offset="100%" style="stop-color:#03000c"/>
  </linearGradient>
  <radialGradient id="lampGlow" cx="50%" cy="0%" r="100%">
    <stop offset="0%" style="stop-color:#ffee88;stop-opacity:0.5"/>
    <stop offset="100%" style="stop-color:#ff8800;stop-opacity:0"/>
  </radialGradient>
  <filter id="winglow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="1.3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="lampfilter" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="3" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <pattern id="scanlines" x="0" y="0" width="1" height="2" patternUnits="userSpaceOnUse">
    <rect width="1" height="1" fill="rgba(0,0,0,0.04)"/>
  </pattern>
</defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#sky)"/>'''

SUN_X, SUN_Y = 450, 135
sun = f'''<circle cx="{SUN_X}" cy="{SUN_Y}" r="120" fill="url(#sunGlow)" opacity="0.4"/>
<circle cx="{SUN_X}" cy="{SUN_Y}" r="40" fill="url(#sunCore)" opacity="0.97"/>
<rect x="{SUN_X-40}" y="{SUN_Y-2}" width="80" height="5" fill="#0f0225" opacity="0.2"/>
<rect x="{SUN_X-40}" y="{SUN_Y+8}" width="80" height="3" fill="#0f0225" opacity="0.15"/>
<rect x="{SUN_X-40}" y="{SUN_Y-10}" width="80" height="3" fill="#0f0225" opacity="0.15"/>'''

bg = ""
rng0 = random.Random(55)
for bx in range(0, WIDTH, 14):
    bh = rng0.randint(15, 50)
    bg += f'<rect x="{bx}" y="{GROUND_Y-bh}" width="12" height="{bh}" fill="#1e0640" opacity="0.25"/>\n'

stars = ""
rng1 = random.Random(77)
for _ in range(55):
    sx = rng1.uniform(0, WIDTH); sy = rng1.uniform(0, GROUND_Y*0.4)
    sr = rng1.uniform(0.3, 1.2); op = round(rng1.uniform(0.1, 0.5), 2)
    lo = round(op*0.1, 2); dur = round(rng1.uniform(2, 5), 1)
    stars += f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{sr:.1f}" fill="white" opacity="{op}"><animate attributeName="opacity" values="{op};{lo};{op}" dur="{dur}s" repeatCount="indefinite"/></circle>\n'

COLS = 5; ROWS = 6
WIN_W = 10; WIN_H = 8
WIN_GAP_X = 5; WIN_GAP_Y = 5
PAD_X = 10; PAD_BOT = 10
BW = PAD_X*2 + COLS*WIN_W + (COLS-1)*WIN_GAP_X
NUM = len(months)
TOTAL_GAP = WIDTH - NUM*BW
GAP = TOTAL_GAP // (NUM+1)

max_total = max(sum(d["contributionCount"] for d in monthly[m]) for m in months)

buildings = ""
lamp_positions = []

for i, m in enumerate(months):
    month_days = monthly[m]
    month_total = sum(d["contributionCount"] for d in month_days)
    norm = month_total / max_total if max_total > 0 else 0.1
    base_h = PAD_BOT + ROWS*WIN_H + (ROWS-1)*WIN_GAP_Y + 16
    extra_h = int(math.log1p(norm * 8) / math.log1p(8) * 100)
    bh = base_h + extra_h
    bx = GAP + i*(BW + GAP)
    by = GROUND_Y - bh
    cx = bx + BW//2

    buildings += f'<rect x="{bx}" y="{by}" width="{BW}" height="{bh}" fill="#08011a"/>\n'
    buildings += f'<rect x="{bx}" y="{by}" width="3" height="{bh}" fill="#180438" opacity="0.6"/>\n'
    buildings += f'<rect x="{bx+BW-3}" y="{by}" width="3" height="{bh}" fill="#030008" opacity="0.8"/>\n'
    buildings += f'<rect x="{bx-2}" y="{by}" width="{BW+4}" height="4" fill="#1a0440"/>\n'
    buildings += f'<rect x="{bx+8}" y="{by-6}" width="12" height="6" fill="#110330"/>\n'
    buildings += f'<rect x="{bx+BW-20}" y="{by-5}" width="10" height="5" fill="#110330"/>\n'
    buildings += f'<rect x="{cx-1}" y="{by-16}" width="2" height="12" fill="#1a0440"/>\n'
    buildings += f'<circle cx="{cx}" cy="{by-16}" r="2" fill="#ff3333" opacity="0.9"><animate attributeName="opacity" values="0.9;0.1;0.9" dur="1.1s" repeatCount="indefinite"/></circle>\n'

    win_start_y = by + bh - PAD_BOT - ROWS*WIN_H - (ROWS-1)*WIN_GAP_Y
    rng = random.Random(hash(m))
    for idx, day in enumerate(month_days[:30]):
        col = idx % COLS; row = idx // COLS
        wx = bx + PAD_X + col*(WIN_W + WIN_GAP_X)
        wy = win_start_y + row*(WIN_H + WIN_GAP_Y)
        count = day["contributionCount"]
        if count == 0:
            wc, op, anim = "#06010f", "0.7", ""
        elif count >= 6:
            wc = "#ffe566"; op = str(round(rng.uniform(0.85,1.0),2))
            dur = round(rng.uniform(1.0,2.5),1); lo = round(float(op)*0.3,2)
            anim = f'<animate attributeName="opacity" values="{op};{lo};{op}" dur="{dur}s" repeatCount="indefinite"/>'
        elif count >= 3:
            wc = "#ff9944"; op = str(round(rng.uniform(0.65,0.88),2))
            dur = round(rng.uniform(2.0,4.0),1); lo = round(float(op)*0.2,2)
            anim = f'<animate attributeName="opacity" values="{op};{lo};{op}" dur="{dur}s" repeatCount="indefinite"/>'
        else:
            wc = "#cc44aa"; op = str(round(rng.uniform(0.4,0.65),2)); anim = ""
        buildings += f'<rect x="{wx}" y="{wy}" width="{WIN_W}" height="{WIN_H}" fill="{wc}" opacity="{op}" filter="url(#winglow)">{anim}</rect>\n'

    label = datetime.strptime(m, "%Y-%m").strftime("%b")
    buildings += f'<text x="{cx}" y="{GROUND_Y+30}" font-family="\'Courier New\', monospace" font-size="8" fill="#cc88ff" opacity="0.8" text-anchor="middle">{label}</text>\n'
    lamp_positions.append(bx + BW + GAP//2)

ground = f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="{HEIGHT-GROUND_Y}" fill="url(#groundGrad)"/>\n'
ground += f'<rect x="0" y="{GROUND_Y}" width="{WIDTH}" height="8" fill="#0d0228"/>\n'
ground += f'<rect x="0" y="{ROAD_Y}" width="{WIDTH}" height="{ROAD_H}" fill="#0a0118"/>\n'
ground += f'<rect x="0" y="{ROAD_Y}" width="{WIDTH}" height="2" fill="#1a0440" opacity="0.5"/>\n'
ground += f'<rect x="0" y="{ROAD_Y+ROAD_H}" width="{WIDTH}" height="2" fill="#1a0440" opacity="0.4"/>\n'
for dx in range(0, WIDTH, 30):
    ground += f'<rect x="{dx}" y="{ROAD_Y+ROAD_H//2-1}" width="18" height="2" fill="#1a0335" opacity="0.6"/>\n'
ground += f'<ellipse cx="{WIDTH//2}" cy="{GROUND_Y+4}" rx="440" ry="8" fill="#ff6600" opacity="0.04"/>\n'

lamps = ""
for lx in lamp_positions[:-1]:
    ly = GROUND_Y
    lamps += f'<rect x="{lx-1}" y="{ly-32}" width="2" height="32" fill="#1a0440"/>\n'
    lamps += f'<rect x="{lx-1}" y="{ly-32}" width="8" height="2" fill="#1a0440"/>\n'
    lamps += f'<rect x="{lx+4}" y="{ly-35}" width="8" height="5" fill="#2a0855"/>\n'
    lamps += f'<ellipse cx="{lx+8}" cy="{ly-30}" rx="14" ry="18" fill="url(#lampGlow)" filter="url(#lampfilter)" opacity="0.7"/>\n'
    lamps += f'<circle cx="{lx+8}" cy="{ly-33}" r="2" fill="#ffee88" opacity="0.95"><animate attributeName="opacity" values="0.95;0.6;0.95" dur="3s" repeatCount="indefinite"/></circle>\n'

cars = ""
car_data = [
    {"color": "#cc2244", "headlight": "#ffaaaa", "y": ROAD_Y+4,  "w": 20, "h": 8,  "speed": "9s",  "begin": "0s"},
    {"color": "#2244cc", "headlight": "#aaaaff", "y": ROAD_Y+12, "w": 22, "h": 8,  "speed": "14s", "begin": "3s"},
    {"color": "#22aa55", "headlight": "#aaffcc", "y": ROAD_Y+4,  "w": 18, "h": 7,  "speed": "7s",  "begin": "5s"},
    {"color": "#aa6600", "headlight": "#ffddaa", "y": ROAD_Y+12, "w": 20, "h": 8,  "speed": "11s", "begin": "1.5s"},
]
for c in car_data:
    cw, ch, cy = c["w"], c["h"], c["y"]
    cars += f'''<g>
  <rect x="0" y="{cy}" width="{cw}" height="{ch}" fill="{c["color"]}" rx="2">
    <animateTransform attributeName="transform" type="translate" from="-30 0" to="{WIDTH+30} 0" dur="{c["speed"]}" begin="{c["begin"]}" repeatCount="indefinite"/>
  </rect>
  <rect x="{cw-4}" y="{cy+2}" width="4" height="3" fill="{c["headlight"]}" opacity="0.9">
    <animateTransform attributeName="transform" type="translate" from="-30 0" to="{WIDTH+30} 0" dur="{c["speed"]}" begin="{c["begin"]}" repeatCount="indefinite"/>
  </rect>
  <rect x="0" y="{cy+2}" width="3" height="3" fill="#ff3300" opacity="0.7">
    <animateTransform attributeName="transform" type="translate" from="-30 0" to="{WIDTH+30} 0" dur="{c["speed"]}" begin="{c["begin"]}" repeatCount="indefinite"/>
  </rect>
</g>\n'''

svg = f'''<svg width="{WIDTH}" height="{HEIGHT}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}">
{defs}{sun}{stars}{bg}{buildings}{ground}{lamps}{cars}
<text x="16" y="{HEIGHT-8}" font-family="'Courier New', monospace" font-size="8" fill="#9966cc" opacity="0.65">{total} commits · {streak}d streak · {timestamp}</text>
<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#scanlines)"/>
<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="none" stroke="#1a0535" stroke-width="3"/>
</svg>'''

os.makedirs("dist", exist_ok=True)
with open("dist/city.svg", "w") as f:
    f.write(svg)

print(f"Done! {len(months)} buildings, {total} commits, {streak}d streak.")
