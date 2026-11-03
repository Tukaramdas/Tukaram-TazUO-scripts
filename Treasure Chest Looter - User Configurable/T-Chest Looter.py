import API
import time
import re

# ==============================================================================
#                      USER CONFIGURATION: LOOT THRESHOLDS
# ==============================================================================

# 1. Minimum Max-Durability for Armor & Weapons
# Any armor/weapon with a max durability below this number stays in the chest.
# (Most CUB junk rolls 20 to 60 max dur. Set to 0 to disable).
MIN_MAX_DURABILITY = 70

# 2. Jewelry Rules
# Always loot rings and bracelets regardless of durability/tier filters?
ALWAYS_LOOT_JEWELRY = True

# 3. Target Rarity Tiers (Set to True to Loot, False to Skip)
LOOT_TIERS = {
    "GREEN_LESSER_MAGIC": False,   # #20E31C - Lesser Magic (almost 100% CUB trash)
    "CYAN_GREATER_MAGIC": False,   # #1CE1E3 - Greater Magic (mostly filler)
    "BLUE_MAJOR_MAGIC":   False,   # #0070FF - Major Magic
    "PURPLE_LESSER_ART":  True,    # #A335EE - Lesser Artifact
    "YELLOW_GREATER_ART": True,    # #FAFF06 - Greater Artifact
    "ORANGE_MAJOR_ART":   True,    # #FF8000 - Major Artifact
    "RED_LEGENDARY_ART":  True,    # #EE0707 - Legendary Artifact
}

# 4. Item Delays
DRAG_DELAY = 0.65  # Seconds between item drops (avoids queue collisions)

# ==============================================================================
#                        END OF USER CONFIGURATION
# ==============================================================================

PICKS = 5372
SUCCESS_LOCKPICKING = ["The lock quickly yields", "This does not appear to be locked"]
SUCCESS_REMOVE_TRAP = ["You successfully render the trap", "That doesn't appear to be trapped"]

TIER_PATTERNS = [
    ("GREEN_LESSER_MAGIC", re.compile(r'(#20E31C|Lesser Magic)', re.I)),
    ("CYAN_GREATER_MAGIC", re.compile(r'(#1CE1E3|Greater Magic)', re.I)),
    ("BLUE_MAJOR_MAGIC",   re.compile(r'(#0070FF|Major Magic)', re.I)),
    ("PURPLE_LESSER_ART",  re.compile(r'(#A335EE|Lesser Artifact)', re.I)),
    ("YELLOW_GREATER_ART", re.compile(r'(#FAFF06|Greater Artifact)', re.I)),
    ("ORANGE_MAJOR_ART",   re.compile(r'(#FF8000|Major Artifact)', re.I)),
    ("RED_LEGENDARY_ART",  re.compile(r'(#EE0707|Legendary Artifact)', re.I)),
]

DURABILITY_REGEX = re.compile(r'Durability\s+\d+\s*/\s*(\d+)', re.I)

# Setup / Load Persistent Loot Bag
loot_bag_serial = API.GetPersistentVar("CHEST_LOOT_BAG", "0", API.PersistentVar.Char)
if not loot_bag_serial or loot_bag_serial == "0" or not API.FindItem(int(loot_bag_serial)):
    API.HeadMsg("Target your destination LOOT BAG...", API.Player)
    target_bag = API.RequestTarget(timeout=10)
    if not target_bag or target_bag == 0:
        API.HeadMsg("No bag selected. Aborted.", API.Player)
        API.Stop()
    loot_bag_serial = str(target_bag)
    API.SavePersistentVar("CHEST_LOOT_BAG", loot_bag_serial, API.PersistentVar.Char)
    API.SysMsg("Loot bag saved to character!", 68)

LOOT_BAG = int(loot_bag_serial)

def HasActiveGuardians(scan_range=12):
    mobiles = API.GetAllMobiles()
    if not mobiles:
        return False

    for m in mobiles:
        if m.Serial == API.Player.Serial:
            continue
        # Exclude innocent (1) and friend/pet (2)
        if m.Notoriety in [1, 2]:
            continue
        # Hostile / Grey / Criminal / Enemy / Murderer
        if m.Notoriety in [3, 4, 5, 6] and m.Distance <= scan_range and not m.IsDead:
            return True
    return False

def SafeMoveItem(item_serial, dest_bag, max_retries=6):
    for _ in range(max_retries):
        if API.StopRequested:
            return False

        # If client is holding an item (AutoLoot busy), yield cursor
        while getattr(API.Player, "Holding", False) and not API.StopRequested:
            time.sleep(0.15)

        try:
            API.MoveItem(item_serial, dest_bag)
            time.sleep(DRAG_DELAY)
            return True
        except Exception:
            time.sleep(0.4)

    return False

def _is_item_wanted(props):
    name_line = props.splitlines()[0].lower() if props else ""
    is_jewelry = ("ring" in name_line or "bracelet" in name_line)

    if ALWAYS_LOOT_JEWELRY and is_jewelry:
        return True

    # Drop low durability armor/weapons
    if MIN_MAX_DURABILITY > 0 and not is_jewelry:
        dur_match = DURABILITY_REGEX.search(props)
        if dur_match:
            max_dur = int(dur_match.group(1))
            if max_dur < MIN_MAX_DURABILITY:
                return False

    # Check rarity tiers
    for tier_key, regex in TIER_PATTERNS:
        if regex.search(props):
            return LOOT_TIERS.get(tier_key, False)

    return False

def LootChest(chest_serial, dest_bag):
    while not API.StopRequested:
        # Pause if an active guardian spawned
        if HasActiveGuardians(scan_range=12):
            API.SysMsg("Guardian nearby. Pausing loot sweep...", 48)
            while HasActiveGuardians(scan_range=12) and not API.StopRequested:
                time.sleep(0.5)
            time.sleep(1.5)  # Let AutoLoot clear the corpse

        # Ensure chest exists and is within range
        chest = API.FindItem(chest_serial)
        if not chest:
            break

        if chest.Distance > 1:
            API.Pathfind(chest.X, chest.Y, chest.Z, 1)
            while API.Pathfinding():
                API.Pause(0.1)

        # Retrieve contents (re-open if gump was closed by combat)
        items = API.ItemsInContainer(chest_serial)
        if not items:
            API.UseObject(chest_serial)
            time.sleep(0.5)
            items = API.ItemsInContainer(chest_serial)
            if not items:
                break

        moved_any = False
        for it in items:
            if API.StopRequested:
                break

            if HasActiveGuardians(scan_range=12):
                moved_any = True
                break

            props = ""
            for _ in range(6):
                props = API.ItemNameAndProps(it.Serial)
                if props and len(props.strip()) > 0:
                    break
                time.sleep(0.1)

            if props and _is_item_wanted(props):
                if SafeMoveItem(it.Serial, dest_bag):
                    moved_any = True

        if not moved_any and not HasActiveGuardians(scan_range=12):
            break

def Unlock(what):
    if API.FindType(PICKS, API.Backpack):
        API.UseObject(API.Found)
        API.WaitForTarget()
        API.Target(what)
        API.Pause(3)
        if not API.InJournalAny(SUCCESS_LOCKPICKING):
            API.Pause(9)
            Unlock(what)

def UnTrap(what):
    API.UseSkill("Remove Trap")
    API.WaitForTarget()
    API.Target(what)
    API.Pause(3)
    if not API.InJournalAny(SUCCESS_REMOVE_TRAP):
        API.Pause(9)
        UnTrap(what)

# --- Main Entry Point ---
API.HeadMsg("Target a chest to open and loot", API.Player)
targ = API.RequestTarget(timeout=10)

if targ:
    item = API.FindItem(targ)
    if item and item.Distance > 1:
        API.Pathfind(item.X, item.Y, item.Z, 1)
        while API.Pathfinding():
            API.Pause(0.1)

    Unlock(targ)
    UnTrap(targ)
    API.UseObject(targ)
    API.Pause(1)

    # Built-in resource/gold pull
    API.AutoLootContainer(targ)
    API.Pause(0.5)

    # Equipment sweep
    LootChest(targ, LOOT_BAG)
    API.SysMsg("Chest looting complete.", 68)