from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "event-monitoring-workflow.png"
WIDTH, HEIGHT = 2400, 1470

font_candidates = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]
bold_candidates = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
]

def load_font(candidates, size):
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

FONT_TITLE = load_font(bold_candidates, 54)
FONT_SUBTITLE = load_font(font_candidates, 27)
FONT_SECTION = load_font(bold_candidates, 22)
FONT_LABEL = load_font(bold_candidates, 27)
FONT_SMALL = load_font(font_candidates, 21)
FONT_SMALL_BOLD = load_font(bold_candidates, 23)

NAVY = (18, 50, 74)
BLUE = (20, 93, 160)
BLUE_DARK = (11, 60, 93)
BLUE_LIGHT = (232, 240, 248)
TEXT_MUTED = (82, 112, 135)
BORDER = (170, 197, 213)
ORANGE = (221, 107, 25)
WHITE = (255, 255, 255)
LINE = (57, 112, 143)

image = Image.new("RGB", (WIDTH, HEIGHT), (248, 251, 255))
draw = ImageDraw.Draw(image)

# Soft background bands.
draw.polygon([(0, 0), (WIDTH, 0), (WIDTH, 250), (1250, 160), (650, 240), (0, 160)], fill=(217, 234, 245))
draw.rectangle((0, 1280, WIDTH, HEIGHT), fill=(238, 245, 249))

def centered(text, box, font, fill):
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    x = x1 + ((x2 - x1) - (bbox[2] - bbox[0])) / 2
    y = y1 + ((y2 - y1) - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)

def section(text, x, y):
    draw.text((x, y), text, font=FONT_SECTION, fill=LINE)

def box(x, y, w, h, title_lines, details, fill, text_fill=WHITE, border=None):
    draw.rounded_rectangle((x, y, x+w, y+h), radius=24, fill=fill, outline=border, width=4 if border else 0)
    title_y = y + 35
    for line in title_lines:
        centered(line, (x+18, title_y, x+w-18, title_y+38), FONT_LABEL, text_fill)
        title_y += 34
    detail_y = y + h - 70 if len(details) == 2 else y + h - 43
    for line in details:
        centered(line, (x+16, detail_y, x+w-16, detail_y+29), FONT_SMALL, text_fill)
        detail_y += 28

def arrow(points, color=LINE, width=6):
    draw.line(points, fill=color, width=width, joint="curve")
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    import math
    angle = math.atan2(y2-y1, x2-x1)
    length = 24
    wing = 0.55
    p1 = (x2 - length*math.cos(angle-wing), y2 - length*math.sin(angle-wing))
    p2 = (x2 - length*math.cos(angle+wing), y2 - length*math.sin(angle+wing))
    draw.polygon([(x2, y2), p1, p2], fill=color)

# Header.
draw.text((120, 70), "Event Monitoring System", font=FONT_TITLE, fill=NAVY)
draw.text((120, 125), "End-to-end event ingestion, asynchronous processing, alerting, querying, and observability", font=FONT_SUBTITLE, fill=TEXT_MUTED)

section("EVENT PRODUCERS", 120, 245)
box(120, 295, 360, 168, ["Client / Test Script"], ["POST /api/events", "application, security, performance"], WHITE, NAVY, BORDER)

section("INGESTION", 592, 245)
box(578, 295, 375, 168, ["event-ingestor"], ["Flask API + validation", "Redis cache + metrics"], BLUE_DARK)

section("MESSAGE BROKER", 1065, 245)
box(1058, 295, 405, 168, ["RabbitMQ"], ["event_queue", "durable asynchronous delivery"], ORANGE)

section("PROCESSING", 1575, 245)
box(1553, 295, 405, 168, ["event-processor"], ["FastAPI + background consumer", "retry failed messages"], BLUE_DARK)

arrow([(480, 379), (578, 379)])
arrow([(953, 379), (1058, 379)])
arrow([(1463, 379), (1553, 379)])

section("STATE AND ALERTING", 120, 595)
box(180, 665, 375, 168, ["Redis"], ["short-lived event records", "one-hour expiry"], WHITE, NAVY, BORDER)
box(765, 665, 405, 168, ["PostgreSQL"], ["events + processed_events", "dashboard query source"], WHITE, NAVY, BORDER)
box(1385, 665, 405, 168, ["notification_queue"], ["critical / high severity", "RabbitMQ durable queue"], ORANGE)
box(1950, 665, 330, 168, ["notification-", "service"], ["simulated alerts"], BLUE_DARK)

arrow([(765, 463), (765, 550), (368, 550), (368, 665)])
arrow([(1755, 463), (1755, 550), (967, 550), (967, 665)])
arrow([(1755, 463), (1755, 550), (1587, 550), (1587, 665)], ORANGE)
arrow([(1790, 749), (1950, 749)], ORANGE)

section("QUERY AND USER EXPERIENCE", 120, 925)
box(330, 995, 405, 168, ["event-query-api"], ["recent events + statistics", "FastAPI read service"], WHITE, NAVY, BORDER)
box(1005, 995, 405, 168, ["dashboard"], ["severity cards", "recent processed events"], BLUE_DARK)
arrow([(967, 833), (967, 900), (532, 900), (532, 995)])
arrow([(735, 1079), (1005, 1079)])

section("OBSERVABILITY", 1580, 925)
box(1580, 995, 315, 168, ["Prometheus"], ["scrapes /metrics", "service counters"], WHITE, NAVY, BORDER)
box(2010, 995, 300, 168, ["Grafana"], ["health dashboards", "event metrics"], WHITE, NAVY, BORDER)
arrow([(1755, 463), (1755, 930), (1737, 995)], LINE, 4)
arrow([(1895, 1079), (2010, 1079)])

# Kubernetes boundary.
draw.rounded_rectangle((120, 1310, 2280, 1400), radius=20, fill=NAVY)
centered("Kubernetes: namespace, Deployments, StatefulSets, Services, ConfigMaps, Secrets, probes, Job, Ingress, resource limits", (145, 1323, 2255, 1388), FONT_SMALL_BOLD, WHITE)

image.save(OUTPUT, format="PNG", optimize=True)
print(f"created {OUTPUT} ({WIDTH}x{HEIGHT})")
