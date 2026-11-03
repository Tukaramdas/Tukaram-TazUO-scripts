import API
import time
import os
import re

# Comprehensive list of UO container graphic IDs (bags, pouches, backpacks, boxes, chests, crates)
CONTAINER_GRAPHICS = {
    0x0E75, 0x0E76, 0x0E79, 0x0E7D, 0x0E7E, 0x0E80, 0x09B0, 0x09A8,
    0x09A9, 0x09AA, 0x0E40, 0x0E41, 0x0E42, 0x0E43, 0x0E3C, 0x0E3D,
    0x09B2, 0x24DA, 0x24DB, 0x2DF3, 0x2DF4, 0x0E7C, 0x0E7A, 0x0E77
}

CONTAINER_WORDS = ["backpack", "bag", "pouch", "box", "chest", "crate", "basket", "barrel", "tub"]

# --- Step 1: Multi-Container Selection ---
root_containers = []
API.SysMsg("Target top-level containers one by one. Press ESC or target ground when done.", 88)

while not API.StopRequested:
    API.SysMsg(f"Target container #{len(root_containers) + 1} (or ESC to finish)...", 68)
    c_serial = API.RequestTarget(timeout=8)

    if not c_serial or c_serial == 0:
        break

    if c_serial not in root_containers:
        root_containers.append(c_serial)
        API.SysMsg(f"Container #{len(root_containers)} added! ({hex(c_serial)})", 68)
        time.sleep(0.2)
    else:
        API.SysMsg("Container already selected, choose another or finish.", 38)

if not root_containers:
    API.SysMsg("No containers selected! Exporter cancelled.", 32)
    API.Stop()

# --- Step 2: Auto-Incrementing File Path ---
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
base_name = "loot_inventory"
ext = ".csv"

index = 1
csv_path = os.path.join(desktop, f"{base_name}_{index}{ext}")
while os.path.exists(csv_path):
    index += 1
    csv_path = os.path.join(desktop, f"{base_name}_{index}{ext}")

def get_val(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else "0"

# Rearranged: "All Properties" placed between "Durability Tag" and "HCI%"
HEADERS = [
    "Location Path",
    "Serial",
    "Item Name",
    "Durability Tag",
    "All Properties",
    # Core Combat & Casting
    "HCI%",
    "DCI%",
    "DI%",
    "SSI%",
    "FC",
    "FCR",
    "LMC%",
    "LRC%",
    # Leech & Weapon Specifics
    "HML%",
    "HLL%",
    "HSL%",
    "Spell Channeling",
    "Slayer",
    # Stats & Pools
    "Mana Inc",
    "Mana Regen",
    "Stam Inc",
    "Stam Regen",
    "HP Inc",
    "HP Regen",
    "Str Bonus",
    "Dex Bonus",
    "Int Bonus",
    # Resists & Armor Specifics
    "Phys Resist",
    "Fire Resist",
    "Cold Resist",
    "Pois Resist",
    "Nrgy Resist",
    "Mage Armor",
    # Misc
    "Skills"
]

rows = []
scanned_containers = set()

def scan_container(container_serial, path_name):
    if API.StopRequested:
        return

    if container_serial in scanned_containers:
        return
    scanned_containers.add(container_serial)

    # 1. Open container
    API.UseObject(container_serial)

    # 2. Poll for contents
    items = []
    for _ in range(10):
        time.sleep(0.2)
        items = API.ItemsInContainer(container_serial)
        if items and len(items) > 0:
            break

    if not items:
        return

    for item in items:
        if API.StopRequested:
            break

        # Tooltip wait loop
        props = ""
        for _ in range(8):
            props = API.ItemNameAndProps(item.Serial)
            if props and len(props.strip()) > 0:
                break
            time.sleep(0.15)

        name_line = props.splitlines()[0] if props else "Unknown"

        # Check sub-containers
        graphic = getattr(item, "Graphic", 0)
        is_sub = (
            graphic in CONTAINER_GRAPHICS or 
            any(w in name_line.lower() for w in CONTAINER_WORDS)
        )

        if is_sub:
            sub_label = name_line if name_line != "Unknown" else f"SubBag({hex(item.Serial)})"
            scan_container(item.Serial, f"{path_name} -> {sub_label}")
            continue

        if not props:
            continue

        # Durability Flags
        flags = []
        for flag in ["Antique", "Prized", "Cursed", "Brittle", "Cannot be Repaired"]:
            if flag.lower() in props.lower():
                flags.append(flag)
        flag_str = "/".join(flags) if flags else "Clean"

        # Combat & Casting
        hci = get_val(r"Hit Chance Increase (\d+)%?", props)
        dci = get_val(r"Defense Chance Increase (\d+)%?", props)
        di = get_val(r"Damage Increase (\d+)%?", props)
        ssi = get_val(r"Swing Speed Increase (\d+)%?", props)
        fc = get_val(r"Faster Casting (\d+)", props)
        fcr = get_val(r"Faster Cast Recovery (\d+)", props)
        lmc = get_val(r"Lower Mana Cost (\d+)%?", props)
        lrc = get_val(r"Lower Reagent Cost (\d+)%?", props)

        # Leech & Weapon Specifics
        hml = get_val(r"Hit Mana Leech (\d+)%?", props)
        hll = get_val(r"Hit Life Leech (\d+)%?", props)
        hsl = get_val(r"Hit Stamina Leech (\d+)%?", props)
        sc = "Yes" if "spell channeling" in props.lower() else "No"

        slayer_m = re.search(r"(\w+ Slayer)", props, re.IGNORECASE)
        slayer = slayer_m.group(1) if slayer_m else "None"

        # Stats & Pools
        mana_inc = get_val(r"Mana Increase (\d+)", props)
        mr = get_val(r"Mana Regeneration (\d+)", props)
        stam_inc = get_val(r"Stamina Increase (\d+)", props)
        sr = get_val(r"Stamina Regeneration (\d+)", props)
        hp_inc = get_val(r"Hit Point Increase (\d+)", props)
        hpr = get_val(r"Hit Point Regeneration (\d+)", props)
        str_bonus = get_val(r"Strength Bonus (\d+)", props)
        dex = get_val(r"Dexterity Bonus (\d+)", props)
        intel = get_val(r"Intelligence Bonus (\d+)", props)

        # Resists & Armor Specifics
        phys = get_val(r"Physical Resist (\d+)%?", props)
        fire = get_val(r"Fire Resist (\d+)%?", props)
        cold = get_val(r"Cold Resist (\d+)%?", props)
        pois = get_val(r"Poison Resist (\d+)%?", props)
        nrgy = get_val(r"Energy Resist (\d+)%?", props)
        mage_armor = "Yes" if "mage armor" in props.lower() else "No"

        # Skill Bonuses
        skill_matches = re.findall(r"([A-Za-z\s]+)\s*\+(\d+)", props)
        skills = []
        excluded_terms = [
            "hit chance increase", "defense chance increase", "damage increase",
            "swing speed increase", "dexterity bonus", "intelligence bonus",
            "strength bonus", "mana increase", "mana regeneration",
            "stamina increase", "stamina regeneration", "hit point increase",
            "hit point regeneration", "lower mana cost", "lower reagent cost",
            "physical resist", "fire resist", "cold resist", "poison resist",
            "energy resist", "faster cast recovery", "faster casting"
        ]

        for s_name, s_val in skill_matches:
            s_clean = s_name.strip()
            if not any(sw in s_clean.lower() for sw in excluded_terms):
                skills.append(f"{s_clean} +{s_val}")
        skill_str = "; ".join(skills) if skills else "None"

        # Raw tooltip string
        clean_raw = " | ".join([line.strip() for line in props.splitlines() if line.strip()])

        # Row data matched to HEADERS: clean_raw placed between flag_str and hci
        rows.append([
            path_name,
            hex(item.Serial),
            name_line,
            flag_str,
            clean_raw,
            hci,
            dci,
            di,
            ssi,
            fc,
            fcr,
            lmc,
            lrc,
            hml,
            hll,
            hsl,
            sc,
            slayer,
            mana_inc,
            mr,
            stam_inc,
            sr,
            hp_inc,
            hpr,
            str_bonus,
            dex,
            intel,
            phys,
            fire,
            cold,
            pois,
            nrgy,
            mage_armor,
            skill_str
        ])

# --- Step 3: Run Recursive Scan ---
API.SysMsg(f"Scanning {len(root_containers)} root containers and all sub-bags...", 88)

for c_idx, root_serial in enumerate(root_containers, start=1):
    if API.StopRequested:
        break
    scan_container(root_serial, f"Chest #{c_idx}")

# --- Step 4: Write Out CSV ---
try:
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(f'"{h}"' for h in HEADERS) + "\n")
        for row in rows:
            escaped = [f'"{str(col).replace(chr(34), chr(34)+chr(34))}"' for col in row]
            f.write(",".join(escaped) + "\n")

    out_file = os.path.basename(csv_path)
    API.SysMsg(f"Done! {len(rows)} items across all bags exported.", 68)
    API.SysMsg(f"Saved to: {out_file}", 88)
except Exception as e:
    API.SysMsg(f"Error saving CSV: {str(e)}", 32)