import API
import time
import re

# Graphic IDs for SOS scrolls / waterstained SOS
SOS_GRAPHICS = [0x14ED, 0x14EE, 0x099F]

# Matches coordinates with 1 to 4 digits: e.g. "(3107, 1480)" or "(363, 69)"
COORD_REGEX = re.compile(r'\(\s*(\d{1,4})\s*,\s*(\d{1,4})\s*\)')
FACET_REGEX = re.compile(r'(Trammel|Felucca)', re.IGNORECASE)

SECTOR_KEYS = ["N_W", "N_MID", "N_E", "MID_W", "MID_MID", "MID_E", "S_W", "S_MID", "S_E"]

def get_sector_key(x, y):
    # Column: West / Mid / East
    if x < 1700:
        col = "W"
    elif x <= 3000:
        col = "MID"
    else:
        col = "E"

    # Row: North / Mid / South
    if y < 1400:
        row = "N"
    elif y <= 2400:
        row = "MID"
    else:
        row = "S"

    return f"{row}_{col}"

# --- Step 1: Check Saved Persistent Pouches ---
pouches = {}
needs_setup = False

for key in SECTOR_KEYS:
    val = API.GetPersistentVar(f"SOS_POUCH_{key}", "0", API.PersistentVar.Char)
    if not val or val == "0":
        needs_setup = True
        break
    pouches[key] = int(val)

if needs_setup:
    API.SysMsg("First-time setup: Target your 9 destination pouches in order...", 88)
    sector_prompts = [
        ("N_W",     "1/9: Top-Left (NW: Yew / Ice)"),
        ("N_MID",   "2/9: Top-Center (North: Cove / Vesper)"),
        ("N_E",     "3/9: Top-Right (NE: Nujel'm / Moonglow)"),
        ("MID_W",   "4/9: Mid-Left (West: Skara Brae)"),
        ("MID_MID", "5/9: Center (Central: Britain / Bucs)"),
        ("MID_E",   "6/9: Mid-Right (East: Magincia / Ocllo)"),
        ("S_W",     "7/9: Bottom-Left (SW: Destard / Jhelom)"),
        ("S_MID",   "8/9: Bottom-Center (South: Trinsic / Haven)"),
        ("S_E",     "9/9: Bottom-Right (SE: Serpents / Fire Isle)"),
    ]
    for key, prompt in sector_prompts:
        API.SysMsg(prompt, 68)
        p_serial = API.RequestTarget(timeout=15)
        if not p_serial or p_serial == 0:
            API.SysMsg("Pouch targeting cancelled! Setup aborted.", 32)
            API.Stop()
        pouches[key] = int(p_serial)
        API.SavePersistentVar(f"SOS_POUCH_{key}", str(p_serial), API.PersistentVar.Char)
        time.sleep(0.15)
    API.SysMsg("9 Pouches saved to profile!", 68)
else:
    API.SysMsg("Loaded saved 9-pouch layout.", 68)

# --- Step 2: Target the Raw / Unsorted SOS Container ---
API.SysMsg("Target the container with your unsorted SOS bottles...", 88)
source_bag = API.RequestTarget(timeout=10)
if not source_bag or source_bag == 0:
    API.SysMsg("Cancelled.", 32)
    API.Stop()

# --- Step 3: Sort All SOS & Add Map Markers ---
API.SysMsg("Sorting and placing map markers...", 68)
sorted_count = 0
items = API.ItemsInContainer(source_bag)

for item in items:
    if API.StopRequested:
        break

    if item.Graphic in SOS_GRAPHICS:
        props_text = ""
        for _ in range(6):
            props_text = API.ItemNameAndProps(item.Serial)
            if props_text and "(" in props_text:
                break
            time.sleep(0.25)

        match = COORD_REGEX.search(props_text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))

            # Move to corresponding regional pouch
            sector = get_sector_key(x, y)
            dest_pouch = pouches.get(sector)

            if dest_pouch:
                API.MoveItem(item.Serial, dest_pouch)
                sorted_count += 1

                # Detect map facet
                facet_match = FACET_REGEX.search(props_text)
                map_id = 0 if (facet_match and facet_match.group(1).lower() == "felucca") else API.GetMap()

                # Place verified marker: (label, x, y, map_id)
                API.AddMapMarker(f"SOS ({x},{y})", x, y, map_id)

                # Delay to respect server drag/drop limits
                time.sleep(0.75)
        else:
            API.SysMsg(f"Could not read coordinates on SOS {hex(item.Serial)}", 38)

API.SysMsg(f"Done! Sorted and mapped {sorted_count} SOS bottles.", 68)