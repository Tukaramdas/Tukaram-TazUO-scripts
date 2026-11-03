# See examples at
#   https://github.com/PlayTazUO/PublicLegionScripts/
# Or documentation at
#   https://tazuo.org/legion/legionapi/
import API

POLE_GRAPHIC = 0x0DC0

# Directions mapped to 2-tile relative offsets
OFFSETS = {
    "north":     (0, -2),
    "right":     (2, -2),  # NorthEast
    "northeast": (2, -2),
    "east":      (2, 0),
    "down":      (2, 2),   # SouthEast
    "southeast": (2, 2),
    "south":     (0, 2),
    "left":      (-2, 2),  # SouthWest
    "southwest": (-2, 2),
    "west":      (-2, 0),
    "up":        (-2, -2), # NorthWest
    "northwest": (-2, -2)
}

# 1. Check hands first (Layer "OneHanded" or "TwoHanded")
held = API.FindLayer("OneHanded", API.Player.Serial)
if not held:
    held = API.FindLayer("TwoHanded", API.Player.Serial)

pole = None

# If holding an item, check its graphic property
if held and getattr(held, "Graphic", 0) == POLE_GRAPHIC:
    pole = held
else:
    # If not holding it, look inside your backpack
    pole = API.FindType(POLE_GRAPHIC, API.Backpack)

# 2. Use pole and target 2 tiles out
if pole:
    API.UseObject(pole)
    if API.WaitForTarget(timeout=1500):
        dir_name = str(API.Player.Direction).lower().strip()
        dx, dy = OFFSETS.get(dir_name, (0, 2))
        API.TargetRel(dx, dy, tilesOnly=True)
else:
    API.SysMsg("Fishing pole not found in hand or backpack!", 32)