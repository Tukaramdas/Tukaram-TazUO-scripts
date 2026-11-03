import API
import time
import re

# Treasure Map graphics (flat scrolls)
MAP_GRAPHICS = [0x14EC, 0x14ED, 0x14EE]

# Matches coordinates formatted as "X:1695  Y:2409", "X: 1695, Y: 2409", or "(1695, 2409)"
COORD_REGEX = re.compile(r'(?:X:\s*(\d{1,4})[,\s]+Y:\s*(\d{1,4})|\(\s*(\d{1,4})\s*,\s*(\d{1,4})\s*\))', re.IGNORECASE)
FACET_REGEX = re.compile(r'(Trammel|Felucca|Ilshenar|Malas|Tokuno|Ter\s*Mur)', re.IGNORECASE)

# Standardized 1-5 level conversion mapping
TIER_MAP = {
    "level 1": 1, "stash": 1, "plainly": 1,
    "level 2": 2, "supply": 2, "expertly": 2, "adeptly": 2,
    "level 3": 3, "cache": 3, "cleverly": 3, "deviously": 3,
    "level 4": 4, "hoard": 4, "ingeniously": 4,
    "level 5": 5, "trove": 5, "diabolically": 5
}

TIER_REGEX = re.compile(r'(Level\s*[1-5]|Stash|Supply|Cache|Hoard|Trove|Plainly|Expertly|Adeptly|Cleverly|Deviously|Ingeniously|Diabolically)', re.IGNORECASE)

FACET_MAP = {
    "felucca": 0,
    "trammel": 1,
    "ilshenar": 2,
    "malas": 3,
    "tokuno": 4,
    "ter mur": 5
}

def parse_level(text):
    m = TIER_REGEX.search(text)
    if m:
        key = m.group(1).lower().strip()
        lvl = TIER_MAP.get(key)
        if lvl:
            return f" [Level {lvl}]"
    return ""

API.SysMsg("Target the bag holding your treasure maps...", 88)
bag_serial = API.RequestTarget(timeout=10)
if not bag_serial or bag_serial == 0:
    API.SysMsg("Targeting cancelled.", 32)
    API.Stop()

# Open the bag to request items from server
API.UseObject(bag_serial)

# Wait for container items to load
items = []
for attempt in range(12):
    time.sleep(0.2)
    items = API.ItemsInContainer(bag_serial)
    if items and len(items) > 0:
        break

if not items or len(items) == 0:
    API.SysMsg("Bag returned 0 items from server. Open it manually first and re-run.", 32)
    API.Stop()

API.SysMsg(f"Found {len(items)} items in bag. Scanning...", 68)
marked_count = 0

for item in items:
    if API.StopRequested:
        break

    # Request tooltip properties from server
    props = ""
    for _ in range(8):
        props = API.ItemNameAndProps(item.Serial)
        if props and ("map" in props.lower() or "x:" in props.lower() or "(" in props):
            break
        time.sleep(0.12)

    if not props:
        continue

    # Verify item is a treasure map
    is_map = (item.Graphic in MAP_GRAPHICS) or ("treasure map" in props.lower())
    if not is_map:
        continue

    coord_match = COORD_REGEX.search(props)
    if coord_match:
        if coord_match.group(1) is not None:
            x = int(coord_match.group(1))
            y = int(coord_match.group(2))
        else:
            x = int(coord_match.group(3))
            y = int(coord_match.group(4))

        facet_match = FACET_REGEX.search(props)
        if facet_match:
            facet_name = facet_match.group(1).lower()
            map_id = FACET_MAP.get(facet_name, 1)
        else:
            map_id = API.GetMap()

        lvl_tag = parse_level(props)
        label = f"T-Map{lvl_tag} ({x},{y})"

        API.AddMapMarker(label, x, y, map_id)
        marked_count += 1
        API.SysMsg(f"Marked: {label} on Map {map_id}", 68)
        time.sleep(0.05)
    else:
        API.SysMsg(f"Skipping map {hex(item.Serial)}: Coords not decoded.", 38)

API.SysMsg(f"Done! Marked {marked_count} treasure maps.", 68)